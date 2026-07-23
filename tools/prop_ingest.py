#!/usr/bin/env python3
"""proposal v4.5 Task 0 摄入：把混合格式素材目录转成 Task 1 可读的 _materials/。

本地优先，OCR 兜底：
  .md/.txt          直读（manifest 记路径，不转换）
  .docx/.pptx/.xlsx 标准库解 zip+XML 抽文本
  .pdf              pdftotext；抽不出文字（扫描件）→ OCR
  .doc/.ppt(OLE)    本地无解 → MinerU；未配置则标"须人工转换"
  图片               百度 PaddleOCR-VL 优先，MinerU 兜底；都没有→"视觉直读"（agent 用 Read 看图）

OCR 后端（密钥在仓库外，绝不入库）：
  MinerU 精准解析   POST /api/v4/file-urls/batch → PUT 预签名 → 轮询 batch → full_zip_url 取 full.md
  PaddleOCR-VL      AI Studio 异步 jobs：multipart 上传 → 轮询 job → 取 JSONL 合并 markdown

配置 ~/.config/proposal/ocr.json（或环境变量 MINERU_TOKEN / PADDLEOCR_VL_TOKEN）：
  {"mineru": {"token": "..."}, "baidu_paddleocr_vl": {"token": "...", "job_url": "可选", "model": "可选"}}

只用标准库；网络失败/未配置都降级为如实标注，不阻塞流程。
"""

import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

DEFAULT_CONFIG = os.path.expanduser("~/.config/proposal/ocr.json")

DIRECT_EXTS = {".md", ".txt"}
LOCAL_ZIP_EXTS = {".docx", ".pptx", ".xlsx"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
OLE_EXTS = {".doc", ".ppt", ".xls"}
SCANNED_PDF_MIN_CHARS = 200  # pdftotext 少于此字数视为扫描件


# ---------------------------------------------------------------- config

def load_ocr_config(path=None):
    cfg = {}
    p = path or DEFAULT_CONFIG
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as fh:
                cfg = json.load(fh)
        except Exception:
            cfg = {}
    mineru = (cfg.get("mineru") or {}).get("token") or os.environ.get("MINERU_TOKEN") or ""
    b = cfg.get("baidu_paddleocr_vl") or {}
    baidu_tok = b.get("token") or os.environ.get("PADDLEOCR_VL_TOKEN") or ""
    return {
        "mineru_token": "" if mineru.startswith("YOUR_") else mineru,
        "baidu_token": "" if baidu_tok.startswith("YOUR_") else baidu_tok,
        "baidu_job_url": (b.get("job_url") or os.environ.get("PADDLEOCR_VL_JOB_URL") or BAIDU_JOB_URL).rstrip("/"),
        "baidu_model": b.get("model") or BAIDU_MODEL,
    }


# ---------------------------------------------------------------- routing (pure, testable)

def route_file(ext, has_mineru, has_baidu, pdf_scanned=False):
    """返回处理方式：direct/local/pdftotext/mineru/baidu/vision/manual/skip"""
    ext = ext.lower()
    if ext in DIRECT_EXTS:
        return "direct"
    if ext in LOCAL_ZIP_EXTS:
        return "local"
    if ext == ".pdf":
        if pdf_scanned:
            # 百度 jobs 本地上传已验证可用；MinerU 批量上传触发目前服务端不稳，作次选
            return "baidu" if has_baidu else ("mineru" if has_mineru else "manual")
        return "pdftotext"
    if ext in OLE_EXTS:
        return "mineru" if has_mineru else "manual"
    if ext in IMAGE_EXTS:
        if has_baidu:
            return "baidu"
        return "mineru" if has_mineru else "vision"
    return "skip"


# ---------------------------------------------------------------- local extractors (stdlib)

def _xml_text(xml, para_tag=None):
    if para_tag:
        xml = re.sub(r"</%s>" % re.escape(para_tag), "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    return html.unescape(xml)


def extract_docx(path):
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", "ignore")
    text = _xml_text(xml, para_tag="w:p")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_pptx(path):
    out = []
    with zipfile.ZipFile(path) as zf:
        slides = sorted(
            (n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
            key=lambda n: int(re.search(r"(\d+)", n).group(1)),
        )
        for i, name in enumerate(slides, 1):
            xml = zf.read(name).decode("utf-8", "ignore")
            texts = re.findall(r"<a:t[^>]*>(.*?)</a:t>", xml, re.S)
            body = "\n".join(html.unescape(t) for t in texts if t.strip())
            out.append(f"## 第 {i} 页\n\n{body}")
        notes = sorted(n for n in zf.namelist() if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", n))
        for name in notes:
            xml = zf.read(name).decode("utf-8", "ignore")
            texts = re.findall(r"<a:t[^>]*>(.*?)</a:t>", xml, re.S)
            body = "\n".join(html.unescape(t) for t in texts if t.strip())
            if body:
                out.append(f"## 备注（{os.path.basename(name)}）\n\n{body}")
    return "\n\n".join(out).strip()


def extract_xlsx(path):
    with zipfile.ZipFile(path) as zf:
        try:
            xml = zf.read("xl/sharedStrings.xml").decode("utf-8", "ignore")
        except KeyError:
            return ""
    cells = re.findall(r"<t[^>]*>(.*?)</t>", xml, re.S)
    return "\n".join(html.unescape(c) for c in cells if c.strip()).strip()


def extract_pdf_text(path):
    """返回 (text, ok)；pdftotext 缺失或失败 ok=False。"""
    if not shutil.which("pdftotext"):
        return "", False
    try:
        r = subprocess.run(["pdftotext", "-layout", path, "-"],
                           capture_output=True, timeout=120)
        return r.stdout.decode("utf-8", "ignore").strip(), r.returncode == 0
    except Exception:
        return "", False


def is_scanned_pdf_text(text):
    return len(re.sub(r"\s", "", text)) < SCANNED_PDF_MIN_CHARS


# ---------------------------------------------------------------- http helpers

# mineru.net 的 WAF 会 403 掉 Python-urllib 默认 UA，统一带浏览器式 UA
UA = "Mozilla/5.0 (X11; Linux x86_64) prop-ingest/1.0"


def _http_json(url, payload=None, headers=None, method=None, timeout=60):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", UA)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def _http_put(url, data, timeout=300):
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("User-Agent", UA)
    # OSS 预签名按空 Content-Type 计算签名；urllib 默认会补 form-urlencoded 导致 403
    req.add_header("Content-Type", "")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status


def _http_get_bytes(url, timeout=300):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------- MinerU（批量：上传→轮询→取 full.md）

def parse_mineru_batch_result(resp):
    """从轮询响应抽 {file_name: {state, full_zip_url, err_msg}}；结构防御式解析。"""
    data = resp.get("data") or resp
    results = data.get("extract_result") or data.get("extract_results") or []
    out = {}
    for r in results:
        name = r.get("file_name") or r.get("data_id") or ""
        out[name] = {
            "state": r.get("state") or "",
            "full_zip_url": r.get("full_zip_url") or "",
            "err_msg": r.get("err_msg") or "",
        }
    return out


def _zip_full_md(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        cands = [n for n in zf.namelist() if n.endswith("full.md")] or \
                [n for n in zf.namelist() if n.endswith(".md")]
        if not cands:
            return ""
        return zf.read(cands[0]).decode("utf-8", "ignore")


def mineru_batch(paths, token, timeout=900, log=lambda m: None):
    """批量解析本地文件。返回 {path: (text, err)}。"""
    hdr = {"Authorization": f"Bearer {token}"}
    files = [{"name": os.path.basename(p), "data_id": str(i)} for i, p in enumerate(paths)]
    resp = _http_json("https://mineru.net/api/v4/file-urls/batch",
                      {"files": files, "model_version": "vlm", "language": "ch",
                       "enable_table": True, "enable_formula": False},
                      headers=hdr)
    data = resp.get("data") or {}
    batch_id = data.get("batch_id")
    urls = data.get("file_urls") or []
    if not batch_id or len(urls) != len(paths):
        raise RuntimeError(f"MinerU 批量创建失败：{resp.get('msg') or resp}")
    for p, u in zip(paths, urls):
        with open(p, "rb") as fh:
            _http_put(u, fh.read())
        log(f"  已上传 {os.path.basename(p)}")
    out = {}
    deadline = time.time() + timeout
    poll = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
    while time.time() < deadline:
        states = parse_mineru_batch_result(_http_json(poll, headers=hdr))
        pending = [n for n, s in states.items() if s["state"] not in ("done", "failed")]
        log(f"  MinerU 进度：{len(states) - len(pending)}/{len(paths)}")
        if not pending and len(states) >= len(paths):
            break
        time.sleep(6)
    for p in paths:
        st = states.get(os.path.basename(p), {})
        if st.get("state") == "done" and st.get("full_zip_url"):
            try:
                out[p] = (_zip_full_md(_http_get_bytes(st["full_zip_url"])), "")
            except Exception as e:
                out[p] = ("", f"结果下载失败：{e}")
        else:
            err = st.get("err_msg") or f"state={st.get('state') or '超时'}"
            if (st.get("state") or "") == "waiting-file":
                err += "（MinerU 服务端未感知已上传文件；请稍后重试或将该文件转存 docx/pdf）"
            out[p] = ("", err)
    return out


# ---------------------------------------------------------------- 百度 PaddleOCR-VL（AI Studio 异步 jobs）

BAIDU_JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
BAIDU_MODEL = "PaddleOCR-VL-1.6"


def _multipart(fields, filename, blob):
    boundary = "----prop-ingest-" + os.urandom(8).hex()
    buf = io.BytesIO()
    for k, v in fields.items():
        buf.write((f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n').encode())
    buf.write((f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
               f'filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode())
    buf.write(blob)
    buf.write(f"\r\n--{boundary}--\r\n".encode())
    return buf.getvalue(), boundary


def parse_baidu_jsonl(text):
    out = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        result = json.loads(line).get("result") or {}
        for res in result.get("layoutParsingResults") or []:
            t = (res.get("markdown") or {}).get("text") or ""
            if t:
                out.append(t)
    return "\n\n".join(out).strip()


def baidu_parse(path, token, job_url=None, model=None, timeout=600, log=lambda m: None):
    """本地文件（图片/PDF 同一入口）multipart 提交 → 轮询 job → 取 JSONL 合并 markdown。"""
    job_url = (job_url or BAIDU_JOB_URL).rstrip("/")
    fields = {"model": model or BAIDU_MODEL,
              "optionalPayload": json.dumps({"useDocOrientationClassify": True,
                                             "useDocUnwarping": False,
                                             "useChartRecognition": False})}
    with open(path, "rb") as fh:
        body, boundary = _multipart(fields, os.path.basename(path), fh.read())
    req = urllib.request.Request(job_url, data=body, method="POST")
    req.add_header("Authorization", f"bearer {token}")
    req.add_header("User-Agent", UA)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read().decode("utf-8", "ignore"))
    job_id = (resp.get("data") or {}).get("jobId")
    if not job_id:
        raise RuntimeError(f"PaddleOCR-VL 提交失败：{resp.get('msg') or resp.get('errorMsg') or resp}")
    hdr = {"Authorization": f"bearer {token}"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = (_http_json(f"{job_url}/{job_id}", headers=hdr).get("data")) or {}
        state = data.get("state")
        if state == "done":
            json_url = (data.get("resultUrl") or {}).get("jsonUrl") or ""
            if not json_url:
                raise RuntimeError("PaddleOCR-VL 完成但无结果 URL")
            return parse_baidu_jsonl(_http_get_bytes(json_url).decode("utf-8", "ignore"))
        if state == "failed":
            raise RuntimeError(f"PaddleOCR-VL 失败：{data.get('errorMsg')}")
        log(f"  PaddleOCR-VL {os.path.basename(path)}: {state or '提交中'}")
        time.sleep(5)
    raise RuntimeError("PaddleOCR-VL 轮询超时")


# ---------------------------------------------------------------- ingest 主流程

def _slug(i, name):
    stem = os.path.splitext(os.path.basename(name))[0]
    stem = re.sub(r"[\\/:*?\"<>|\s]+", "-", stem)[:60]
    return f"{i:02d}-{stem}.md"


def _write_material(out_dir, fname, src, how, text):
    p = os.path.join(out_dir, fname)
    head = f"# {os.path.basename(src)}\n\n> 来源：{src}\n> 转换：{how}\n\n"
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(head + (text or "").strip() + "\n")
    return p


def ingest(src_dir, out_dir, ocr="auto", config_path=None, timeout=900, log=lambda m: None):
    cfg = load_ocr_config(config_path)
    has_mineru = bool(cfg["mineru_token"]) and ocr in ("auto", "mineru")
    has_baidu = bool(cfg["baidu_token"]) and ocr in ("auto", "baidu")
    if ocr == "off":
        has_mineru = has_baidu = False

    os.makedirs(out_dir, exist_ok=True)
    files = []
    for root, dirs, names in os.walk(src_dir):
        dirs[:] = [d for d in dirs if not d.startswith((".", "_"))]
        for n in sorted(names):
            if not n.startswith("."):
                files.append(os.path.join(root, n))
    rows, mineru_queue, needs_manual = [], [], []

    for i, path in enumerate(files, 1):
        ext = os.path.splitext(path)[1].lower()
        size = os.path.getsize(path)
        rel = os.path.relpath(path, src_dir)
        row = {"n": i, "rel": rel, "ext": ext or "(无)", "size": size,
               "status": "", "artifact": "", "note": ""}
        rows.append(row)
        route = route_file(ext, has_mineru, has_baidu)
        try:
            if route == "direct":
                row["status"] = "直读"
                row["artifact"] = rel
            elif route == "local":
                text = {"docx": extract_docx, "pptx": extract_pptx, "xlsx": extract_xlsx}[ext[1:]](path)
                if ext == ".xlsx" and not text:
                    row["status"], row["note"] = "空提取", "表格无共享字符串，必要时走 OCR"
                else:
                    fn = _slug(i, path)
                    _write_material(out_dir, fn, rel, f"本地解析（{ext}）", text)
                    row["status"], row["artifact"] = "已转换·本地", fn
            elif route == "pdftotext":
                text, ok = extract_pdf_text(path)
                if ok and not is_scanned_pdf_text(text):
                    fn = _slug(i, path)
                    _write_material(out_dir, fn, rel, "pdftotext", text)
                    row["status"], row["artifact"] = "已转换·本地", fn
                else:
                    row["note"] = "扫描件或无文字层"
                    r2 = route_file(ext, has_mineru, has_baidu, pdf_scanned=True)
                    if r2 == "mineru":
                        mineru_queue.append((i, path, row))
                        row["status"] = "排队·MinerU"
                    elif r2 == "baidu":
                        text = baidu_parse(path, cfg["baidu_token"], cfg["baidu_job_url"],
                                           cfg["baidu_model"], log=log)
                        fn = _slug(i, path)
                        _write_material(out_dir, fn, rel, "PaddleOCR-VL", text)
                        row["status"], row["artifact"] = "已OCR·百度", fn
                    else:
                        row["status"] = "须人工转换"
                        needs_manual.append(rel)
            elif route == "mineru":
                mineru_queue.append((i, path, row))
                row["status"] = "排队·MinerU"
            elif route == "baidu":
                text = baidu_parse(path, cfg["baidu_token"], cfg["baidu_job_url"],
                                   cfg["baidu_model"], log=log)
                fn = _slug(i, path)
                _write_material(out_dir, fn, rel, "PaddleOCR-VL", text)
                row["status"], row["artifact"] = "已OCR·百度", fn
            elif route == "vision":
                row["status"], row["note"] = "视觉直读", "agent 用 Read 直接看图（未配置 OCR）"
            elif route == "manual":
                row["status"] = "须人工转换"
                row["note"] = "老二进制格式，本地无解且未配置 MinerU；请转存 docx/pdf 或配置 OCR"
                needs_manual.append(rel)
            else:
                row["status"], row["note"] = "跳过", "不识别的格式"
        except Exception as e:
            row["status"], row["note"] = "失败", str(e)[:120]

    if mineru_queue:
        log(f"MinerU 批量解析 {len(mineru_queue)} 份…")
        try:
            results = mineru_batch([p for _, p, _ in mineru_queue], cfg["mineru_token"],
                                   timeout=timeout, log=log)
            for i, path, row in mineru_queue:
                text, err = results.get(path, ("", "无结果"))
                if text:
                    fn = _slug(i, path)
                    _write_material(out_dir, fn, row["rel"], "MinerU 精准解析", text)
                    row["status"], row["artifact"] = "已OCR·MinerU", fn
                else:
                    row["status"], row["note"] = "失败", f"MinerU：{err}"[:120]
        except Exception as e:
            for _, _, row in mineru_queue:
                row["status"], row["note"] = "失败", f"MinerU 批量异常：{e}"[:120]

    lines = ["# 素材清单（Task 0 摄入）", "",
             f"> 来源：{src_dir} · 共 {len(rows)} 份 · OCR：mineru={'✓' if has_mineru else '✗'} baidu={'✓' if has_baidu else '✗'}", "",
             "| # | 文件 | 格式 | 大小 | 状态 | 产物 | 备注 |", "|--:|:--|:--|--:|:--|:--|:--|"]
    for r in rows:
        kb = f"{r['size']/1024:.0f}KB"
        lines.append(f"| {r['n']} | {r['rel']} | {r['ext']} | {kb} | {r['status']} | {r['artifact']} | {r['note']} |")
    if needs_manual:
        lines += ["", "## ⚠ 须人工转换（Task 1 前处理）"] + [f"- {m}" for m in needs_manual]
    with open(os.path.join(out_dir, "manifest.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    done = sum(1 for r in rows if r["status"].startswith(("已", "直读", "视觉")))
    return {"passed": True, "files": len(rows), "ready": done,
            "needs_manual": needs_manual,
            "failed": [r["rel"] for r in rows if r["status"] == "失败"],
            "manifest": os.path.join(out_dir, "manifest.md")}


def cmd_ingest(args):
    return ingest(args.src, args.out, ocr=args.ocr, config_path=args.config,
                  timeout=args.timeout, log=lambda m: print(m, file=sys.stderr))
