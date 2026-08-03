#!/usr/bin/env python3
"""proposal v5 方案库工具——120GB 级 PPT/PDF 库的分层接入。

借鉴第二大脑 vault 的分层（原始证据 → 编译理解 → 金标准）：
  原始层   120GB 库文件原地不动（不可变证据）
  索引层   library-index 只走文件系统不读内容，分钟级建全库地图
  编译层   方案卡 cards/<id>.md —— agent 读文本后沉淀的"这份方案值得偷师什么"，
           渐进编译：每次投标用到哪份编译哪份，跨标复用
  金标准   最好的整份方案经用户审定晋升 references/exemplars/

子命令：
  library-index    建/刷索引（index.json + manifest.md 统计）
  library-search   词面检索：关键词/板块/年份 → 排序候选（有卡优先）
  library-extract  按需下钻：单文件文本抽取（复用 ingest 全链含 OCR），缓存复用
  library-status   库健康：文件数/已抽取/已编卡覆盖率

索引与缓存默认在 <库根>/_proposal_index/（库只读时用 config 的 index_dir 改址）。
配置 ~/.config/proposal/library.json：{"path": "/mnt/方案库", "index_dir": "可选"}
只用标准库。
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import prop_ingest

DEFAULT_CONFIG = os.path.expanduser("~/.config/proposal/library.json")
LIBRARY_EXTS = {".ppt", ".pptx", ".pdf", ".doc", ".docx", ".key", ".txt", ".md"}
INDEX_DIRNAME = "_proposal_index"

# 六大业务板块的路径关键词先验（见 references/strategy-patterns.md）
SECTOR_KEYWORDS = {
    "video": ["宣传片", "视频", "TVC", "tvc", "短片", "动画", "品牌片", "拍摄", "剪辑", "微电影", "纪录片"],
    "social-media": ["新媒体", "抖音", "小红书", "视频号", "代运营", "矩阵", "社媒", "直播", "增长", "运营方案"],
    "brand-strategy": ["品牌全案", "品牌策划", "品牌定位", "品牌诊断", "品牌战略", "全案", "IP打造", "命名"],
    "event": ["发布会", "峰会", "年会", "庆典", "开业", "赛事", "路演", "活动", "论坛", "开幕", "启动仪式", "晚会"],
    "space-design": ["展厅", "展馆", "文化墙", "空间", "特装", "园区", "展位", "美陈", "陈列", "导视"],
    "graphic-design": ["logo", "LOGO", "VI", "vi设计", "画册", "包装", "海报", "物料", "折页", "版式"],
}
YEAR_RE = re.compile(r"(20[0-3][0-9])")


def _result(passed, errors, warnings, extra=None):
    out = {"passed": bool(passed and not errors), "errors": errors, "warnings": warnings}
    if extra:
        out.update(extra)
    return out


def load_config(path=None):
    p = path or DEFAULT_CONFIG
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def resolve_dirs(args):
    """(库根, 索引目录)。优先级：命令行 > config > 报错。"""
    cfg = load_config(getattr(args, "config", None)) or {}
    src = getattr(args, "src", None) or cfg.get("path")
    if not src:
        raise SystemExit(json.dumps({"passed": False, "errors": [
            f"未指定方案库路径：传 --src 或配置 {DEFAULT_CONFIG}"], "warnings": []}, ensure_ascii=False))
    index_dir = getattr(args, "index_dir", None) or cfg.get("index_dir") or os.path.join(src, INDEX_DIRNAME)
    return os.path.abspath(src), os.path.abspath(index_dir)


def file_id(relpath):
    return hashlib.sha1(relpath.encode("utf-8")).hexdigest()[:12]


def guess_sectors(relpath):
    low = relpath.lower()
    hits = [s for s, kws in SECTOR_KEYWORDS.items() if any(k.lower() in low for k in kws)]
    return hits


def guess_sectors_from_content(full, head_chars=4000, min_hits=2):
    """路径猜不出时读正文开头做板块识别（MD 库在本地，代价极小）。"""
    try:
        with open(full, "r", encoding="utf-8", errors="ignore") as fh:
            head = fh.read(head_chars).lower()
    except OSError:
        return []
    scores = {s: sum(head.count(k.lower()) for k in kws) for s, kws in SECTOR_KEYWORDS.items()}
    best = max(scores.values() or [0])
    if best < min_hits:
        return []
    return [s for s, v in scores.items() if v == best or v >= max(min_hits, best // 2 + 1)]


def guess_year(name):
    years = YEAR_RE.findall(name)
    return max(years) if years else None


# ---------------------------------------------------------------- index

def build_index(src, index_dir):
    entries, skipped = [], 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != INDEX_DIRNAME]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in LIBRARY_EXTS:
                skipped += 1
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, src)
            try:
                st = os.stat(full)
            except OSError:
                continue
            sectors, sector_from = guess_sectors(rel), "path"
            if not sectors and ext == ".md":
                sectors, sector_from = guess_sectors_from_content(full), "content"
            entries.append({
                "id": file_id(rel), "path": rel, "name": f, "ext": ext,
                "size_mb": round(st.st_size / 1048576, 2), "mtime": int(st.st_mtime),
                "sectors": sectors, "sector_from": sector_from if sectors else "",
                "year": guess_year(rel),
            })
    os.makedirs(os.path.join(index_dir, "cards"), exist_ok=True)
    os.makedirs(os.path.join(index_dir, "text"), exist_ok=True)
    with open(os.path.join(index_dir, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"src": src, "files": entries}, fh, ensure_ascii=False)

    by_sector, by_ext, by_year = {}, {}, {}
    for e in entries:
        for s in (e["sectors"] or ["未识别"]):
            by_sector[s] = by_sector.get(s, 0) + 1
        by_ext[e["ext"]] = by_ext.get(e["ext"], 0) + 1
        if e["year"]:
            by_year[e["year"]] = by_year.get(e["year"], 0) + 1
    lines = [f"# 方案库索引 · {len(entries)} 份", "",
             "| 板块 | 份数 |", "|:--|--:|"]
    lines += [f"| {s} | {n} |" for s, n in sorted(by_sector.items(), key=lambda x: -x[1])]
    lines += ["", "| 格式 | 份数 |", "|:--|--:|"]
    lines += [f"| {e} | {n} |" for e, n in sorted(by_ext.items(), key=lambda x: -x[1])]
    if by_year:
        lines += ["", "年份分布：" + "、".join(f"{y}×{n}" for y, n in sorted(by_year.items()))]
    with open(os.path.join(index_dir, "manifest.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return _result(True, [], [], {"files": len(entries), "skipped_non_library": skipped,
                                  "index": os.path.join(index_dir, "index.json"),
                                  "manifest": os.path.join(index_dir, "manifest.md")})


def cmd_index(args):
    src, index_dir = resolve_dirs(args)
    if not os.path.isdir(src):
        return _result(False, [f"方案库路径不存在：{src}"], [])
    return build_index(src, index_dir)


# ---------------------------------------------------------------- search

def _load_index(index_dir):
    p = os.path.join(index_dir, "index.json")
    if not os.path.exists(p):
        raise SystemExit(json.dumps({"passed": False, "errors": [
            f"索引不存在：{p}（先跑 library-index）"], "warnings": []}, ensure_ascii=False))
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def search_index(idx, index_dir, query="", sector=None, year_min=None, top=8):
    tokens = [t for t in re.split(r"[\s,，、/]+", query.lower()) if t]
    results = []
    for e in idx["files"]:
        if sector and sector not in e["sectors"]:
            continue
        if year_min and (not e["year"] or e["year"] < str(year_min)):
            continue
        low_path, low_name = e["path"].lower(), e["name"].lower()
        score = sum((3 if t in low_name else (1 if t in low_path else 0)) for t in tokens)
        if tokens and score == 0:
            continue
        card = os.path.join(index_dir, "cards", e["id"] + ".md")
        has_card = os.path.exists(card)
        has_text = os.path.isdir(os.path.join(index_dir, "text", e["id"]))
        score += (2 if has_card else 0) + (1 if has_text else 0)
        if e["year"] and e["year"] >= "2023":
            score += 1
        results.append({**e, "score": score, "card": card if has_card else None, "extracted": has_text})
    results.sort(key=lambda r: (-r["score"], -r["mtime"]))
    return results[:top]


def cmd_search(args):
    _, index_dir = resolve_dirs(args)
    idx = _load_index(index_dir)
    hits = search_index(idx, index_dir, query=args.query or "", sector=args.sector,
                        year_min=args.year_min, top=args.top)
    return _result(True, [], [], {"hits": hits, "total_indexed": len(idx["files"])})


# ---------------------------------------------------------------- extract

def cmd_extract(args):
    src, index_dir = resolve_dirs(args)
    idx = _load_index(index_dir)
    target = next((e for e in idx["files"] if e["path"] == args.file or e["id"] == args.file), None)
    if not target:
        return _result(False, [f"索引里找不到：{args.file}（用 library-search 拿 path 或 id）"], [])
    cache = os.path.join(index_dir, "text", target["id"])
    card = os.path.join(index_dir, "cards", target["id"] + ".md")
    if os.path.isdir(cache) and not args.force:
        files = sorted(os.listdir(cache))
        return _result(True, [], [], {"id": target["id"], "cached": True, "text_dir": cache,
                                      "files": files, "card": card if os.path.exists(card) else None,
                                      "card_path_for_agent": card})
    full = os.path.join(src, target["path"])
    if not os.path.exists(full):
        return _result(False, [f"文件不存在（索引过期？重跑 library-index）：{full}"], [])
    tmp = tempfile.mkdtemp(prefix="prop-lib-")
    try:
        os.symlink(full, os.path.join(tmp, target["name"]))
        if os.path.isdir(cache):
            shutil.rmtree(cache)
        res = prop_ingest.ingest(tmp, cache, ocr=args.ocr, config_path=None,
                                 timeout=args.timeout, log=lambda m: None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    files = sorted(os.listdir(cache)) if os.path.isdir(cache) else []
    warnings = []
    if isinstance(res, dict) and res.get("须人工转换"):
        warnings.append("本地与 OCR 均未解出文本，须人工转换")
    return _result(True, [], warnings, {"id": target["id"], "cached": False, "text_dir": cache,
                                        "files": files, "card_path_for_agent": card})


# ---------------------------------------------------------------- convert（整库批量转 MD 镜像）

CONVERT_EXTS = {".ppt", ".pptx", ".pdf", ".doc", ".docx", ".xlsx", ".txt", ".md"}
MINERU_CHUNK = 15
MANIFEST_NAME = "_conversion.json"


def _write_md(out_path, rel, how, text, note=""):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    head = f"# {os.path.basename(rel)}\n\n> 来源：{rel}\n> 转换：{how}\n"
    if note:
        head += f"> 备注：{note}\n"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(head + "\n" + (text or "").strip() + "\n")


def _soffice_to(path, target_ext, tmpdir):
    """LibreOffice 就地转格式（.ppt→pdf / .doc→docx）；不可用或失败返回 None。"""
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        return None
    try:
        subprocess.run([exe, "--headless", "--convert-to", target_ext, "--outdir", tmpdir, path],
                       capture_output=True, timeout=180)
    except Exception:
        return None
    cand = os.path.join(tmpdir, os.path.splitext(os.path.basename(path))[0] + "." + target_ext)
    return cand if os.path.exists(cand) else None


def _load_manifest(out):
    p = os.path.join(out, MANIFEST_NAME)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {"files": {}}


def _save_manifest(out, manifest):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, MANIFEST_NAME), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False)


def _convert_local(full, rel, ext):
    """本地转换一个文件。返回 (status, how, text_or_none)；status=ocr 表示需 OCR。"""
    if ext in (".md", ".txt"):
        with open(full, "r", encoding="utf-8", errors="ignore") as fh:
            return "converted", "直读", fh.read()
    if ext in (".docx", ".pptx", ".xlsx"):
        fn = {".docx": prop_ingest.extract_docx, ".pptx": prop_ingest.extract_pptx,
              ".xlsx": prop_ingest.extract_xlsx}[ext]
        text = fn(full)
        if ext == ".xlsx" and not text:
            return "converted", f"本地解析（{ext}）", ""  # 空表格如实留空
        return "converted", f"本地解析（{ext}）", text
    if ext == ".pdf":
        text, ok = prop_ingest.extract_pdf_text(full)
        if ok and not prop_ingest.is_scanned_pdf_text(text):
            return "converted", "pdftotext", text
        return "ocr", "扫描件或无文字层", None
    if ext in (".ppt", ".doc"):
        tmp = tempfile.mkdtemp(prefix="prop-conv-")
        try:
            target = "pdf" if ext == ".ppt" else "docx"
            conv = _soffice_to(full, target, tmp)
            if conv:
                if target == "docx":
                    return "converted", "LibreOffice→docx", prop_ingest.extract_docx(conv)
                text, ok = prop_ingest.extract_pdf_text(conv)
                if ok and not prop_ingest.is_scanned_pdf_text(text):
                    return "converted", "LibreOffice→pdftotext", text
            return "ocr", "老格式（无 LibreOffice 或转换后无文字层）", None
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return "manual", f"不支持的格式 {ext}", None


def cmd_convert(args):
    cfg = load_config(getattr(args, "config", None)) or {}
    src = args.src or cfg.get("path")
    if not src or not os.path.isdir(src):
        return _result(False, [f"方案库路径无效：{src}（--src 或 config 的 path）"], [])
    src = os.path.abspath(src)
    out = os.path.abspath(args.out or cfg.get("md_path") or src.rstrip("/\\") + "-md")
    manifest = _load_manifest(out)
    seen = manifest["files"]

    ocr_cfg = prop_ingest.load_ocr_config(None)
    use_mineru = args.ocr in ("auto", "mineru") and bool(ocr_cfg.get("mineru_token"))
    use_baidu = args.ocr in ("auto", "baidu") and bool(ocr_cfg.get("baidu_token"))

    stats = {"scanned": 0, "cached": 0, "converted": 0, "queued_ocr": 0,
             "ocr_done": 0, "ocr_failed": 0, "manual": 0, "failed": 0}
    ocr_queue = []  # (full, rel, out_path)
    processed = 0

    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != INDEX_DIRNAME]
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext not in CONVERT_EXTS or f.startswith("."):
                continue
            stats["scanned"] += 1
            full = os.path.join(root, f)
            rel = os.path.relpath(full, src)
            try:
                st = os.stat(full)
            except OSError:
                continue
            entry = seen.get(rel)
            fresh = entry and entry.get("mtime") == int(st.st_mtime) and entry.get("size") == st.st_size
            if fresh and not args.force:
                s = entry.get("status")
                if s == "converted":
                    stats["cached"] += 1
                    continue
                if s == "needs_ocr" and not (use_mineru or use_baidu):
                    stats["queued_ocr"] += 1
                    continue
                if s == "manual":
                    stats["manual"] += 1
                    continue
            if args.limit and processed >= args.limit:
                continue
            processed += 1
            out_path = os.path.join(out, rel + ".md")
            try:
                status, how, text = _convert_local(full, rel, ext)
            except Exception as e:
                seen[rel] = {"mtime": int(st.st_mtime), "size": st.st_size,
                             "status": "failed", "how": f"异常：{e}"}
                stats["failed"] += 1
                continue
            if status == "converted":
                _write_md(out_path, rel, how, text)
                seen[rel] = {"mtime": int(st.st_mtime), "size": st.st_size,
                             "status": "converted", "how": how, "out": rel + ".md"}
                stats["converted"] += 1
            elif status == "ocr":
                if use_mineru or use_baidu:
                    ocr_queue.append((full, rel, out_path, int(st.st_mtime), st.st_size))
                else:
                    seen[rel] = {"mtime": int(st.st_mtime), "size": st.st_size,
                                 "status": "needs_ocr", "how": how}
                    stats["queued_ocr"] += 1
            else:
                seen[rel] = {"mtime": int(st.st_mtime), "size": st.st_size,
                             "status": "manual", "how": how}
                stats["manual"] += 1
            if processed % 200 == 0:
                _save_manifest(out, manifest)
                print(f"  进度：已处理 {processed}（本地转换 {stats['converted']}）", file=sys.stderr)

    # OCR 队列：MinerU 分批，Baidu 逐个兜底
    def _ocr_write(full, rel, out_path, mtime, size, text, err, how):
        if text:
            _write_md(out_path, rel, how, text)
            seen[rel] = {"mtime": mtime, "size": size, "status": "converted", "how": how, "out": rel + ".md"}
            stats["ocr_done"] += 1
        else:
            seen[rel] = {"mtime": mtime, "size": size, "status": "needs_ocr", "how": f"OCR失败：{err}"}
            stats["ocr_failed"] += 1

    if ocr_queue and use_mineru:
        for i in range(0, len(ocr_queue), MINERU_CHUNK):
            chunk = ocr_queue[i:i + MINERU_CHUNK]
            try:
                results = prop_ingest.mineru_batch([c[0] for c in chunk], ocr_cfg["mineru_token"],
                                                   timeout=args.timeout,
                                                   log=lambda m: print(m, file=sys.stderr))
            except Exception as e:
                results = {c[0]: ("", str(e)) for c in chunk}
            for full, rel, out_path, mtime, size in chunk:
                text, err = results.get(full, ("", "无结果"))
                _ocr_write(full, rel, out_path, mtime, size, text, err, "MinerU OCR")
            _save_manifest(out, manifest)
    elif ocr_queue and use_baidu:
        for full, rel, out_path, mtime, size in ocr_queue:
            try:
                text = prop_ingest.baidu_parse(full, ocr_cfg["baidu_token"], ocr_cfg.get("baidu_job_url"),
                                               ocr_cfg.get("baidu_model"), log=lambda m: None)
                _ocr_write(full, rel, out_path, mtime, size, text, "", "PaddleOCR-VL")
            except Exception as e:
                _ocr_write(full, rel, out_path, mtime, size, "", str(e), "PaddleOCR-VL")
        _save_manifest(out, manifest)

    _save_manifest(out, manifest)
    remaining = stats["queued_ocr"] + stats["ocr_failed"]
    warnings = []
    if remaining:
        warnings.append(f"{remaining} 份需 OCR 未完成（配置 ~/.config/proposal/ocr.json 后重跑，或装 LibreOffice 减少 OCR 量）")
    if stats["manual"]:
        warnings.append(f"{stats['manual']} 份须人工转换（.key 等）")
    return _result(True, [], warnings, {**stats, "out": out,
                                        "hint": "转换完成后把 config 的 path 指向 MD 库并跑 library-index"})


# ---------------------------------------------------------------- pages（按需页面渲染）

def _render_pdf_pages(pdf, out_dir, first=None, last=None, dpi=100):
    os.makedirs(out_dir, exist_ok=True)
    cmd = ["pdftoppm", "-png", "-r", str(dpi)]
    if first:
        cmd += ["-f", str(first)]
    if last:
        cmd += ["-l", str(last)]
    cmd += [pdf, os.path.join(out_dir, "page")]
    subprocess.run(cmd, capture_output=True, timeout=600)
    return sorted(f for f in os.listdir(out_dir) if f.endswith(".png"))


def cmd_pages(args):
    """把库内一份方案的页面渲染成 PNG（图的单位是'页'，与 MD 里'第 N 页'对齐）。
    源文件是 PDF 直接渲；PPT/PPTX/DOC/DOCX 先经 LibreOffice 转 PDF。缓存于 pages/<id>/。"""
    cfg = load_config(getattr(args, "config", None)) or {}
    src_root = args.src or cfg.get("source_path") or cfg.get("path")
    _, index_dir = resolve_dirs(args)
    idx = _load_index(index_dir)
    # 允许用 MD 库里的 path（去掉末尾 .md 即源文件相对路径）
    key = args.file[:-3] if args.file.endswith(".md") else args.file
    target = next((e for e in idx["files"]
                   if e["path"] in (args.file, key + ".md") or e["id"] == args.file), None)
    if not target:
        return _result(False, [f"索引里找不到：{args.file}"], [])
    rel_src = target["path"][:-3] if target["path"].endswith(".md") else target["path"]
    full = os.path.join(src_root, rel_src)
    if not os.path.exists(full):
        return _result(False, [f"源文件不存在：{full}（config 需含 source_path 指向原始库）"], [])
    pages_dir = os.path.join(index_dir, "pages", target["id"])
    rng = f"{args.first or 1}-{args.last or 'end'}"
    marker = os.path.join(pages_dir, ".complete")  # 只有整本渲染过才算完整缓存，局部渲染不冒充
    existing = sorted(f for f in os.listdir(pages_dir) if f.endswith(".png")) if os.path.isdir(pages_dir) else []
    if existing and not args.force and not (args.first or args.last) and os.path.exists(marker):
        return _result(True, [], [], {"id": target["id"], "cached": True,
                                      "pages_dir": pages_dir, "pages": len(existing)})
    ext = os.path.splitext(rel_src)[1].lower()
    pdf = full
    tmp = None
    try:
        if ext != ".pdf":
            tmp = tempfile.mkdtemp(prefix="prop-pages-")
            pdf = _soffice_to(full, "pdf", tmp)
            if not pdf:
                return _result(False, [f"{ext} 转 PDF 失败（需 LibreOffice）"], [])
        files = _render_pdf_pages(pdf, pages_dir, args.first, args.last, args.dpi)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    if not files:
        return _result(False, [f"渲染失败或无页面：{rel_src}"], [])
    if not (args.first or args.last):
        with open(marker, "w") as fh:
            fh.write("full\n")
    return _result(True, [], [], {"id": target["id"], "cached": False, "range": rng,
                                  "pages_dir": pages_dir, "pages": len(files)})


# ---------------------------------------------------------------- status

def cmd_status(args):
    _, index_dir = resolve_dirs(args)
    idx = _load_index(index_dir)
    n = len(idx["files"])
    cards = len([f for f in os.listdir(os.path.join(index_dir, "cards")) if f.endswith(".md")]) \
        if os.path.isdir(os.path.join(index_dir, "cards")) else 0
    texts = len(os.listdir(os.path.join(index_dir, "text"))) \
        if os.path.isdir(os.path.join(index_dir, "text")) else 0
    return _result(True, [], [], {"indexed": n, "extracted": texts, "cards": cards,
                                  "card_coverage": f"{cards}/{n}"})


def register_subcommands(sub):
    """挂到 prop_tools 的 CLI 上。"""
    common = dict()  # noqa: F841 —— 占位说明：各子命令共享 --src/--index-dir/--config

    def add_common(p):
        p.add_argument("--src", default=None, help="方案库根目录（默认读 config）")
        p.add_argument("--index-dir", dest="index_dir", default=None)
        p.add_argument("--config", default=None, help=f"默认 {DEFAULT_CONFIG}")

    i = sub.add_parser("library-index", help="方案库建/刷元数据索引（不读内容，分钟级）")
    add_common(i)
    i.set_defaults(func=cmd_index)

    s = sub.add_parser("library-search", help="方案库词面检索：关键词/板块/年份 → 排序候选")
    add_common(s)
    s.add_argument("--query", default="")
    s.add_argument("--sector", default=None, choices=sorted(SECTOR_KEYWORDS))
    s.add_argument("--year-min", dest="year_min", default=None)
    s.add_argument("--top", type=int, default=8)
    s.set_defaults(func=cmd_search)

    c = sub.add_parser("library-convert", help="整库批量转 MD 镜像（断点续跑；本地优先，OCR 兜底）")
    add_common(c)
    c.add_argument("--out", default=None, help="MD 库输出目录（默认 config 的 md_path 或 <src>-md）")
    c.add_argument("--ocr", default="off", choices=["off", "auto", "mineru", "baidu"],
                   help="默认 off：先本地转完、统计 OCR 缺口，再决定开 OCR 重跑")
    c.add_argument("--limit", type=int, default=0, help="本次最多处理 N 份（分批跑大库）")
    c.add_argument("--timeout", type=int, default=1800)
    c.add_argument("--force", action="store_true", help="忽略缓存全部重转")
    c.set_defaults(func=cmd_convert)

    e = sub.add_parser("library-extract", help="单文件文本抽取（缓存复用；OCR 兜底同 ingest）")
    add_common(e)
    e.add_argument("--file", required=True, help="索引里的 path 或 id")
    e.add_argument("--ocr", default="auto", choices=["auto", "mineru", "baidu", "off"])
    e.add_argument("--timeout", type=int, default=900)
    e.add_argument("--force", action="store_true")
    e.set_defaults(func=cmd_extract)

    p = sub.add_parser("library-pages", help="按需渲染方案页面为 PNG（页与 MD'第 N 页'对齐；缓存复用）")
    add_common(p)
    p.add_argument("--file", required=True, help="索引里的 path 或 id（MD 库路径亦可）")
    p.add_argument("--first", type=int, default=None)
    p.add_argument("--last", type=int, default=None)
    p.add_argument("--dpi", type=int, default=100)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_pages)

    t = sub.add_parser("library-status", help="方案库健康：索引/抽取/编卡覆盖率")
    add_common(t)
    t.set_defaults(func=cmd_status)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="prop_library")
    subs = parser.add_subparsers(dest="cmd", required=True)
    register_subcommands(subs)
    a = parser.parse_args()
    r = a.func(a)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r.get("passed") else 1)
