#!/usr/bin/env python3
"""proposal skill 工具集 — 装配 / 合规校验 / 竞争力自评 / QA / 编码。

自包含，仅依赖标准库。所有读取用 utf-8-sig（BOM 容错），写入用 utf-8 无 BOM。
非 ASCII 文本一律走文件参数，不进 shell argv。
"""
import argparse
import json
import os
import re
import sys
import datetime
import unicodedata


# ── 编码安全 stdout ────────────────────────────────────────────────────────
def _init_stdout():
    for stream in (sys.stdout, sys.stderr):
        enc = getattr(stream, 'encoding', None)
        if enc and enc.upper() not in ('UTF-8', 'UTF8'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass


# ── 语言标签（zh 默认，其余回退 en）────────────────────────────────────────
LABELS = {
    'zh': {
        'doc_kind': '投标方案', 'project': '项目', 'buyer': '采购人',
        'budget_resp': '预算响应', 'chars': '字', 'reading': '阅读',
        'minutes': '分钟', 'gen': '生成', 'mode': '模式', 'version': '版本',
        'refs_label': '**参考来源**：', 'refs_count': '共引用 {n} 个来源',
        'toc': '## 目录', 'matrix': '## 应标响应与评分对照表',
        'refs': '## 参考来源', 'disclaimer': '## 声明',
        'disclaimer_text': ('本方案为投标响应文件，所含创意、数据与案例基于公开信息与专业判断编制，'
                            '最终执行以合同约定为准。引用的第三方数据版权归原机构所有。'),
        'gen_time': '生成时间：{time}',
        'narrative': '叙事',
        'm_req': '要求项', 'm_cat': '类别', 'm_wt': '权重/性质', 'm_sec': '响应章节',
        'cat_qual': '资格', 'cat_subst': '实质性', 'cat_fmt': '格式', 'cat_score': '评分项',
        'uncovered': '⚠ 未覆盖（需补）', 'budget_within': '≤{v}{u}（预算带内）',
        'budget_range': '按行业合理区间测算', 'no_src': '暂无联网来源',
        'matrix_note': '> 下表逐条对应标书的资格/实质性/格式条款与评分办法，确保应标零遗漏。',
    },
    'en': {
        'doc_kind': 'Bid Proposal', 'project': 'Project', 'buyer': 'Buyer',
        'budget_resp': 'Budget', 'chars': 'chars', 'reading': 'Reading',
        'minutes': 'min', 'gen': 'Generated', 'mode': 'Mode', 'version': 'Version',
        'refs_label': '**References**: ', 'refs_count': 'Total {n} sources',
        'toc': '## Table of Contents', 'matrix': '## Compliance & Scoring Matrix',
        'refs': '## References', 'disclaimer': '## Disclaimer',
        'disclaimer_text': ('This is a bid response document. Ideas, data and cases are compiled from '
                            'public information and professional judgment; execution follows the contract.'),
        'gen_time': 'Generated: {time}',
        'narrative': 'Narrative',
        'm_req': 'Requirement', 'm_cat': 'Category', 'm_wt': 'Weight/Type', 'm_sec': 'Addressed in',
        'cat_qual': 'Qualification', 'cat_subst': 'Substantive', 'cat_fmt': 'Format', 'cat_score': 'Scoring',
        'uncovered': '⚠ Not covered (fix)', 'budget_within': '<= {v}{u} (within budget)',
        'budget_range': 'estimated at industry range', 'no_src': 'No online sources',
        'matrix_note': '> The table below maps every mandatory clause and scoring item for zero omission.',
    },
}

CHINESE_NUMERALS = [
    '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
    '二十一', '二十二', '二十三', '二十四', '二十五',
]


def lab(lang):
    return LABELS.get(lang, LABELS['en'])


def chapter_heading(lang, n, title):
    if lang == 'zh':
        num = CHINESE_NUMERALS[n - 1] if n <= len(CHINESE_NUMERALS) else str(n)
        return f"## {num}、{title}"
    return f"## {n}. {title}"


def toc_label(lang, n, title):
    if lang == 'zh':
        num = CHINESE_NUMERALS[n - 1] if n <= len(CHINESE_NUMERALS) else str(n)
        return f"{num}、{title}"
    return f"{n}. {title}"


# ── 文件 IO ────────────────────────────────────────────────────────────────
def read_text(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return f.read()


def read_json(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def write_text_atomic(path, content):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    os.replace(tmp, path)


# ── 编码 / Mojibake 检查 ────────────────────────────────────────────────────
MOJIBAKE = ['涓枃', '绯荤粺', '鍦ㄧ嚎', 'ç³»', 'å·²', 'æ ']


def check_encoding(path):
    issues = []
    with open(path, 'rb') as f:
        raw = f.read()
    if raw[:3] == b'\xef\xbb\xbf':
        return {"passed": False, "issues": ["BOM detected (EF BB BF)"]}
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        return {"passed": False, "issues": [f"Invalid UTF-8: {e}"]}
    if '�' in text:
        line = text[:text.index('�')].count('\n') + 1
        issues.append(f"Replacement char U+FFFD at line {line}")
    for p in MOJIBAKE:
        if p in text:
            issues.append(f"Mojibake pattern '{p}' present")
    if re.search(r'\?{3,}', text):
        issues.append("Suspected CP936 question-mark corruption (???)")
    return {"passed": len(issues) == 0, "issues": issues}


# ── 字数 ─────────────────────────────────────────────────────────────────
def _clean_md(text):
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = text.replace('|', '').replace('`', '')
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    return text


def word_count_text(text):
    return len(re.sub(r'\s+', '', _clean_md(text)))


def word_count(path):
    return word_count_text(read_text(path))


# ── GitHub 锚点 ─────────────────────────────────────────────────────────────
def github_anchor(text):
    text = text.lower()
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith(('L', 'N')) or ch in (' ', '_', '-'):
            out.append(ch)
    s = ''.join(out)
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s


# ── 版本 ─────────────────────────────────────────────────────────────────
def read_version():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'VERSION')
    try:
        return read_text(p).strip()
    except Exception:
        return ""


# ── 需求 id 汇总 ────────────────────────────────────────────────────────────
def all_requirement_ids(req):
    ids = []
    for m in req.get('mandatory') or []:
        if m.get('id'):
            ids.append(m['id'])
    for s in req.get('scoring') or []:
        if s.get('id'):
            ids.append(s['id'])
    return ids


def mapped_ids(strategy):
    mapped = set()
    for sec in strategy.get('sections') or []:
        for a in sec.get('addresses') or []:
            mapped.add(a)
    return mapped


def id_to_chapters(strategy):
    """id -> list of (n, title)"""
    m = {}
    for sec in strategy.get('sections') or []:
        n = sec.get('n')
        title = sec.get('title', '')
        for a in sec.get('addresses') or []:
            m.setdefault(a, []).append((n, title))
    return m


# ── 参考来源提取 ────────────────────────────────────────────────────────────
def extract_refs(intel):
    records = intel if isinstance(intel, list) else [intel]
    seen = set()
    entries = []
    src_freq = {}
    for rec in records:
        for fact in (rec.get('facts') or []):
            url = (fact.get('url') or '').strip()
            src = (fact.get('src') or '').strip()
            yr = fact.get('yr', '')
            title = (fact.get('title') or '').strip()
            if src:
                src_freq[src] = src_freq.get(src, 0) + 1
            if not url:
                continue
            key = url
            if key in seen:
                continue
            seen.add(key)
            entries.append((title or src or url, src, yr, url))
        for case in (rec.get('cases') or []):
            url = (case.get('url') or '').strip()
            name = (case.get('name') or '').strip()
            who = (case.get('who') or '').strip()
            if not url or url in seen:
                continue
            seen.add(url)
            entries.append((name or who or url, who, '', url))
    entries.sort(key=lambda x: (x[1].lower() if x[1] else 'zzz', x[0]))
    top_sources = sorted(src_freq, key=src_freq.get, reverse=True)[:6]
    return entries, top_sources


# ── 装配 ─────────────────────────────────────────────────────────────────
def assemble_proposal(strategy_path, requirements_path, intel_path,
                      sections_dir, mode, output_path, lang):
    issues = []
    strategy = read_json(strategy_path)
    req = read_json(requirements_path)
    try:
        intel = read_json(intel_path)
    except Exception:
        intel = []
    L = lab(lang)

    title = strategy.get('title') or req.get('project_name') or '投标方案'
    sections = sorted(strategy.get('sections') or [], key=lambda s: s.get('n', 0))
    now = datetime.datetime.now()
    gen_time = now.strftime("%Y-%m-%d %H:%M:%S")

    safe_title = re.sub(r'[<>:"/\\|?*]', '-', title).rstrip('. ')
    if not output_path:
        output_path = f"reports/{safe_title}-{now.strftime('%Y%m%d-%H%M%S')}.md"
    elif os.path.isdir(output_path) or not output_path.endswith('.md'):
        output_path = os.path.join(output_path, f"{safe_title}-{now.strftime('%Y%m%d-%H%M%S')}.md")

    # 章节正文
    chapter_texts = []
    for sec in sections:
        n = sec.get('n')
        spath = os.path.join(sections_dir, f"section-{n}.md")
        if not os.path.exists(spath):
            issues.append(f"Missing section file: section-{n}.md")
            continue
        body = read_text(spath).strip()
        body = re.sub(r'^#{1,2} .+?\n+', '', body, count=1)  # 去掉误写的章标题
        heading = chapter_heading(lang, n, sec.get('title', ''))
        chapter_texts.append(f"{heading}\n\n{body}")

    # 目录
    toc_lines = []
    for sec in sections:
        n = sec.get('n')
        label = toc_label(lang, n, sec.get('title', ''))
        toc_lines.append(f"- [{label}](#{github_anchor(chapter_heading(lang, n, sec.get('title','')).replace('## ',''))})")
    toc_text = '\n'.join(toc_lines)

    # 应标响应与评分对照表
    id2ch = id_to_chapters(strategy)

    def sec_refs(_id):
        chs = id2ch.get(_id)
        if not chs:
            return L['uncovered']
        seen = []
        for n, t in chs:
            lbl = toc_label(lang, n, t)
            if lbl not in seen:
                seen.append(lbl)
        return "；".join(seen) if lang == 'zh' else "; ".join(seen)

    cat_map = {'资格': L['cat_qual'], '实质性': L['cat_subst'], '格式': L['cat_fmt']}
    matrix_rows = [f"| {L['m_req']} | {L['m_cat']} | {L['m_wt']} | {L['m_sec']} |",
                   "|:---|:---|:---|:---|"]
    for m in req.get('mandatory') or []:
        cat = cat_map.get(m.get('type', ''), m.get('type', ''))
        item = (m.get('item') or '').replace('|', '/')
        matrix_rows.append(f"| {item} | {cat} | {'必须满足' if lang=='zh' else 'Mandatory'} | {sec_refs(m.get('id'))} |")
    for s in req.get('scoring') or []:
        item = (s.get('item') or '').replace('|', '/')
        dim = (s.get('dimension') or '').replace('|', '/')
        wt = s.get('weight', '')
        cat_txt = f"{L['cat_score']}·{dim}" if lang == 'zh' else f"{L['cat_score']}·{dim}"
        matrix_rows.append(f"| {item} | {cat_txt} | {wt} | {sec_refs(s.get('id'))} |")
    matrix_text = '\n'.join(matrix_rows)

    # 参考来源
    entries, top_sources = extract_refs(intel)
    ref_lines = [L['refs'], '']
    if entries:
        for name, src, yr, url in entries:
            label = name if not src or src == name else f"{name} · {src}"
            if yr:
                label += f" · {yr}"
            ref_lines.append(f"- [{label}]({url})")
    else:
        ref_lines.append(L['no_src'])
    ref_text = '\n'.join(ref_lines)

    # 预算响应串
    cap = req.get('budget_cap') or {}
    if cap.get('value') is not None:
        budget_str = L['budget_within'].format(v=cap.get('value'), u=cap.get('unit', ''))
    else:
        budget_str = L['budget_range']

    version = read_version()

    narrative_mode = (strategy.get('narrative') or {}).get('mode') or ''
    narrative_str = f" · {L['narrative']} {narrative_mode}" if narrative_mode else ''

    # 先拼一次算字数
    def build(wc, rt):
        meta1 = (f"> **{L['doc_kind']}** · {L['project']}：{req.get('project_name','')} · "
                 f"{L['buyer']}：{req.get('buyer','')} · {L['budget_resp']}：{budget_str} · "
                 f"{wc} {L['chars']} · {L['reading']} {rt} {L['minutes']} · "
                 f"{L['gen']} {gen_time} · {L['mode']} {mode}{narrative_str} · {L['version']} v{version}")
        sep = "、" if lang == 'zh' else ", "
        src_join = sep.join(top_sources) if top_sources else ("公开信息" if lang == 'zh' else "public sources")
        meta2 = f"> {L['refs_label']}{src_join} {'等' if lang=='zh' else 'et al.'} · {L['refs_count'].format(n=len(entries))}"
        parts = [
            f"# {title}\n",
            f"{meta1}\n>\n{meta2}\n",
            f"{L['toc']}\n",
            toc_text, "",
            f"{L['matrix']}\n",
            L['matrix_note'], "",
            matrix_text, "",
            "\n\n".join(chapter_texts),
            "\n---\n",
            ref_text,
            f"\n{L['disclaimer']}\n\n{L['disclaimer_text']}\n",
            f"\n{L['gen_time'].format(time=gen_time)}\n",
        ]
        return "\n".join(parts)

    draft = build(0, 1)
    wc = word_count_text(draft)
    rt = max(1, round(wc / 500))
    full = build(wc, rt)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # 去重同名旧稿
    out_dir = os.path.dirname(output_path)
    pat = re.compile(r'^' + re.escape(safe_title) + r'-\d{8}-\d{6}\.md$')
    for fn in os.listdir(out_dir):
        if pat.match(fn) and fn != os.path.basename(output_path):
            try:
                os.remove(os.path.join(out_dir, fn))
            except OSError:
                pass

    write_text_atomic(output_path, full)
    enc = check_encoding(output_path)
    if not enc['passed']:
        issues.append(f"Encoding issue: {enc['issues']}")

    return {
        "passed": len(issues) == 0,
        "output_path": output_path,
        "line_count": full.count('\n') + 1,
        "chapter_count": len(chapter_texts),
        "word_count": wc,
        "issues": issues,
    }


# ── 合规校验 ─────────────────────────────────────────────────────────────
def check_compliance(requirements_path, strategy_path, report_path):
    req = read_json(requirements_path)
    strategy = read_json(strategy_path)
    mapped = mapped_ids(strategy)

    mand = [(m.get('id'), m.get('item', '')) for m in (req.get('mandatory') or []) if m.get('id')]
    scor = [(s.get('id'), s.get('item', '')) for s in (req.get('scoring') or []) if s.get('id')]

    missing_mandatory = [{"id": i, "item": it} for i, it in mand if i not in mapped]
    missing_scoring = [{"id": i, "item": it} for i, it in scor if i not in mapped]

    total = len(mand) + len(scor)
    covered = total - len(missing_mandatory) - len(missing_scoring)
    coverage_pct = round(covered / total * 100) if total else 100

    # 校验报告章节数与 strategy 一致（漏写章节会导致映射的评分项其实没落地）
    report = read_text(report_path)
    chapter_headings = re.findall(r'^## (?:[一二三四五六七八九十]+、|\d+\. )', report, re.MULTILINE)
    expected_chapters = len(strategy.get('sections') or [])
    chapter_ok = len(chapter_headings) >= expected_chapters

    matrix_present = ('## 应标响应与评分对照表' in report) or ('## Compliance & Scoring Matrix' in report)

    passed = (not missing_mandatory) and (not missing_scoring) and chapter_ok and matrix_present
    result = {
        "passed": passed,
        "coverage_pct": coverage_pct,
        "total_requirements": total,
        "addressed_mandatory": len(mand) - len(missing_mandatory),
        "total_mandatory": len(mand),
        "addressed_scoring": len(scor) - len(missing_scoring),
        "total_scoring": len(scor),
        "missing_mandatory": missing_mandatory,
        "missing_scoring": missing_scoring,
        "chapter_count_in_report": len(chapter_headings),
        "expected_chapters": expected_chapters,
        "chapter_count_ok": chapter_ok,
        "matrix_present": matrix_present,
    }
    return result


# ── 章节切分（用于自评的按章字数）──────────────────────────────────────────
def split_chapters(report):
    """返回 [(chapter_index_1based, text)]，按 ## 汉字、/ ## N. 切分。"""
    pat = re.compile(r'^## (?:[一二三四五六七八九十]+、|\d+\. ).+$', re.MULTILINE)
    starts = [m.start() for m in pat.finditer(report)]
    chapters = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(report)
        chapters.append((i + 1, report[s:e]))
    return chapters


# ── 竞争力自评 ─────────────────────────────────────────────────────────────
def self_score(requirements_path, strategy_path, report_path, mode):
    req = read_json(requirements_path)
    strategy = read_json(strategy_path)
    report = read_text(report_path)
    mapped = mapped_ids(strategy)
    id2ch = id_to_chapters(strategy)

    # 每章字数
    chapters = split_chapters(report)
    ch_words = {n: word_count_text(t) for n, t in chapters}
    total_secs = max(len(strategy.get('sections') or []), 1)

    prof = _load_profile(mode)
    target_per = prof.get('max_chars', 20000) / total_secs

    # 差异化点 → 覆盖的评分 id
    diff_ids = set()
    diffs = strategy.get('differentiators') or []
    for d in diffs:
        for a in d.get('addresses_scoring') or []:
            diff_ids.add(a)
    diff_count = len(diffs)
    min_diff = prof.get('min_differentiators', 3)

    scoring = req.get('scoring') or []
    scoring_total = req.get('scoring_total') or sum(s.get('weight', 0) for s in scoring) or 100

    est = 0.0
    weak_items = []
    for s in scoring:
        sid = s.get('id')
        w = s.get('weight', 0) or 0
        addressed = sid in mapped
        chs = [n for n, _ in id2ch.get(sid, [])]
        sec_words = sum(ch_words.get(n, 0) for n in chs)
        has_diff = sid in diff_ids
        if not addressed:
            frac = 0.30
            weak_items.append({"id": sid, "item": s.get('item', ''), "reason": "未映射到任何章节"})
        else:
            frac = 0.75
            thin = sec_words < 0.6 * target_per * max(len(chs), 1)
            if thin:
                frac += 0.0
                weak_items.append({"id": sid, "item": s.get('item', ''), "reason": "对应章节篇幅偏薄"})
            else:
                frac += 0.10
            if has_diff:
                frac += 0.15
            elif w >= 15:
                weak_items.append({"id": sid, "item": s.get('item', ''), "reason": "高权重项缺差异化亮点"})
        frac = min(frac, 1.0)
        est += frac * w

    estimated_score = round(est / scoring_total * 100) if scoring_total else 0
    addressed_scoring = sum(1 for s in scoring if s.get('id') in mapped)
    addressed_pct = round(addressed_scoring / len(scoring) * 100) if scoring else 100

    cap = req.get('budget_cap') or {}
    within_budget = "n/a" if cap.get('value') is None else "check"

    # 去重 weak_items（同 id 保留最严重原因）
    seen_ids = {}
    for w in weak_items:
        seen_ids[w['id']] = w
    weak_list = list(seen_ids.values())

    return {
        "estimated_score": estimated_score,
        "addressed_pct": addressed_pct,
        "addressed_scoring": addressed_scoring,
        "total_scoring": len(scoring),
        "diff_count": diff_count,
        "min_differentiators": min_diff,
        "diff_ok": diff_count >= min_diff,
        "within_budget": within_budget,
        "weak_items": weak_list,
    }


def _load_profile(mode):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        profiles = read_json(os.path.join(base, 'profiles.json'))
        return profiles.get(mode, profiles.get('standard', {}))
    except Exception:
        return {}


# ── QA ─────────────────────────────────────────────────────────────────────
def qa_proposal(report_path, mode, strategy_path, lang):
    checks = {}
    report = read_text(report_path)
    lines = report.split('\n')
    L = lab(lang)

    enc = check_encoding(report_path)
    checks['encoding'] = enc

    # 四段式结构
    struct_issues = []
    if not lines or not lines[0].startswith('# '):
        struct_issues.append("第 1 行不是 # 标题")
    if not any(l.startswith('> ') for l in lines[1:8]):
        struct_issues.append("标题后缺元数据块（> 开头）")
    if L['toc'] not in report:
        struct_issues.append(f"缺目录标题 {L['toc']}")
    if L['matrix'] not in report:
        struct_issues.append(f"缺应标响应与评分对照表 {L['matrix']}")
    if L['refs'] not in report:
        struct_issues.append(f"缺参考来源 {L['refs']}")
    if L['disclaimer'] not in report:
        struct_issues.append(f"缺声明 {L['disclaimer']}")
    checks['structure'] = {"passed": len(struct_issues) == 0, "issues": struct_issues}

    # 章节数
    chapter_headings = re.findall(r'^## (?:[一二三四五六七八九十]+、|\d+\. )', report, re.MULTILINE)
    prof = _load_profile(mode)
    min_ch = prof.get('min_chapters', 6)
    checks['chapter_count'] = {"passed": len(chapter_headings) >= min_ch,
                               "count": len(chapter_headings), "min": min_ch}

    # 子节汉字编号（应为阿拉伯数字 N.x）
    zh_sub = [i + 1 for i, l in enumerate(lines) if re.match(r'^### [一二三四五六七八九十]', l)]
    checks['subsection_numbering'] = {"passed": len(zh_sub) == 0,
                                      "issues": [f"line {n} 用汉字编号子节" for n in zh_sub[:5]]}

    # 内部 id 泄露（S/M/D + 数字，作为独立 token）——警告级
    leak = re.findall(r'(?<![A-Za-z0-9])[SMD]\d{1,2}(?![A-Za-z0-9])', report)
    checks['no_id_leak'] = {"passed": len(leak) == 0, "warning": True,
                            "found": sorted(set(leak))[:10]}

    # 字数
    wc = word_count_text(report)
    max_chars = prof.get('max_chars', 28000)
    checks['word_count'] = {"passed": True, "count": wc, "limit": max_chars,
                            "exceeded": wc > max_chars}

    # 差异化下限（若给了 strategy）
    if strategy_path and os.path.exists(strategy_path):
        strat = read_json(strategy_path)
        dc = len(strat.get('differentiators') or [])
        min_diff = prof.get('min_differentiators', 3)
        checks['differentiators'] = {"passed": dc >= min_diff, "count": dc, "min": min_diff}

    # LaTeX 公式残留（$ 后数字未转义）——警告级
    math = re.findall(r'(?<!\\)\$\d', report)
    checks['no_latex'] = {"passed": len(math) == 0, "warning": True, "found": len(math)}

    hard_fail = any(
        not v.get('passed', True) and not v.get('warning', False)
        for v in checks.values()
    )
    return {"passed": not hard_fail, "checks": checks}


# ── 货币转义 ─────────────────────────────────────────────────────────────
def escape_currency(report_path):
    content = read_text(report_path)
    protected = {}
    counter = [0]

    def _protect(pattern, tmpl, flags=0):
        nonlocal content

        def rep(m):
            counter[0] += 1
            k = tmpl.format(counter[0])
            protected[k] = m.group(0)
            return k
        content = re.sub(pattern, rep, content, flags=flags)

    _protect(r'```.*?```', '__CODE_{}__', re.DOTALL)
    _protect(r'`[^`]+`', '__ICODE_{}__')
    _protect(r'\[([^\[\]]*)\]\(([^)]*)\)', '__LINK_{}__')
    _protect(r'https?://[^\s\)]+', '__URL_{}__')
    _protect(r'<[^>]+>', '__TAG_{}__')

    changes = [0]

    def esc(m):
        changes[0] += 1
        return m.group(1) + '\\' + m.group(2)

    content = re.sub(r'(^|[^\\])(\$)(?=\d)', esc, content)

    for k, v in reversed(list(protected.items())):
        content = content.replace(k, v)

    write_text_atomic(report_path, content)
    return {"passed": True, "changes": changes[0]}


# ── check-requirements ──────────────────────────────────────────────────────
def check_requirements(path):
    issues = []
    try:
        req = read_json(path)
    except Exception as e:
        return {"passed": False, "issues": [f"JSON 解析失败: {e}"]}
    if not req.get('scoring'):
        issues.append("缺 scoring[]（评分办法未拆解）")
    else:
        for i, s in enumerate(req['scoring']):
            if not s.get('id'):
                issues.append(f"scoring[{i}] 缺 id")
            if 'weight' not in s:
                issues.append(f"scoring[{i}] 缺 weight")
    if not req.get('mandatory'):
        issues.append("缺 mandatory[]（强制/资格/格式条款未拆解）")
    else:
        for i, m in enumerate(req['mandatory']):
            if not m.get('id'):
                issues.append(f"mandatory[{i}] 缺 id")
    if 'budget_cap' not in req:
        issues.append("缺 budget_cap 字段")
    ids = all_requirement_ids(req)
    if len(ids) != len(set(ids)):
        issues.append("存在重复 id")
    return {"passed": len(issues) == 0, "issues": issues,
            "scoring_count": len(req.get('scoring') or []),
            "mandatory_count": len(req.get('mandatory') or [])}


# ── detect-engine ───────────────────────────────────────────────────────────
def detect_engine():
    import urllib.request as _req
    try:
        r = _req.Request("https://search.h33.top/search?q=test&format=json",
                         headers={"User-Agent": "Mozilla/5.0"}, method="GET")
        with _req.urlopen(r, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and "results" in data:
                return {"engine": "searxng", "available": True}
    except Exception:
        pass
    return {"engine": "none", "available": False}


# ── json-get ────────────────────────────────────────────────────────────────
def json_get(path, key_path):
    data = read_json(path)
    val = data
    for key in key_path.split('.'):
        val = val[int(key)] if isinstance(val, list) else val[key]
    return val


# ── CLI ─────────────────────────────────────────────────────────────────────
def _print_result(result):
    print("PASS" if result.get('passed') else "FAIL")
    for iss in result.get('issues', []):
        print(f"  - {iss}")
    sys.exit(0 if result.get('passed') else 1)


def main():
    _init_stdout()
    parser = argparse.ArgumentParser(description='proposal tools — 装配/合规/自评/QA')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('check-encoding'); p.add_argument('file')
    p = sub.add_parser('word-count'); p.add_argument('file')
    p = sub.add_parser('json-validate'); p.add_argument('file')
    p = sub.add_parser('json-get'); p.add_argument('file'); p.add_argument('key_path')
    p = sub.add_parser('check-requirements'); p.add_argument('file')
    p = sub.add_parser('detect-engine')
    p = sub.add_parser('escape-currency'); p.add_argument('report')

    p = sub.add_parser('assemble-proposal')
    p.add_argument('--strategy', required=True)
    p.add_argument('--requirements', required=True)
    p.add_argument('--intel', required=True)
    p.add_argument('--sections-dir', required=True)
    p.add_argument('--mode', default='standard', choices=['quick', 'standard', 'deep'])
    p.add_argument('--output', default=None)
    p.add_argument('--lang', default='zh')

    p = sub.add_parser('check-compliance')
    p.add_argument('--requirements', required=True)
    p.add_argument('--strategy', required=True)
    p.add_argument('--report', required=True)

    p = sub.add_parser('self-score')
    p.add_argument('--requirements', required=True)
    p.add_argument('--strategy', required=True)
    p.add_argument('--report', required=True)
    p.add_argument('--mode', default='standard', choices=['quick', 'standard', 'deep'])

    p = sub.add_parser('qa-proposal')
    p.add_argument('report')
    p.add_argument('--mode', default='standard', choices=['quick', 'standard', 'deep'])
    p.add_argument('--strategy', default=None)
    p.add_argument('--lang', default='zh')

    args = parser.parse_args()

    if args.command == 'check-encoding':
        _print_result(check_encoding(args.file))
    elif args.command == 'word-count':
        print(word_count(args.file)); sys.exit(0)
    elif args.command == 'json-validate':
        try:
            read_json(args.file); print("PASS"); sys.exit(0)
        except Exception as e:
            print(f"FAIL\n  - {e}"); sys.exit(1)
    elif args.command == 'json-get':
        v = json_get(args.file, args.key_path)
        print(json.dumps(v, ensure_ascii=False, indent=2) if isinstance(v, (dict, list)) else v)
        sys.exit(0)
    elif args.command == 'check-requirements':
        r = check_requirements(args.file)
        print(f"SCORING:{r.get('scoring_count',0)} MANDATORY:{r.get('mandatory_count',0)}")
        _print_result(r)
    elif args.command == 'detect-engine':
        print(json.dumps(detect_engine(), ensure_ascii=False)); sys.exit(0)
    elif args.command == 'escape-currency':
        r = escape_currency(args.report)
        print(f"Escaped {r['changes']} dollar signs in: {args.report}"); sys.exit(0)
    elif args.command == 'assemble-proposal':
        r = assemble_proposal(args.strategy, args.requirements, args.intel,
                              args.sections_dir, args.mode, args.output, args.lang)
        if r['passed']:
            print(f"Proposal assembled: {r['output_path']} "
                  f"({r['line_count']} lines, {r['chapter_count']} chapters, {r['word_count']} chars)")
        else:
            print("FAIL")
            for iss in r['issues']:
                print(f"  - {iss}")
        sys.exit(0 if r['passed'] else 1)
    elif args.command == 'check-compliance':
        r = check_compliance(args.requirements, args.strategy, args.report)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0 if r['passed'] else 1)
    elif args.command == 'self-score':
        r = self_score(args.requirements, args.strategy, args.report, args.mode)
        weak = ";".join(f"{w['id']}:{w['reason']}" for w in r['weak_items'][:6])
        print(f"SELFSCORE: estimated_score={r['estimated_score']} "
              f"addressed_pct={r['addressed_pct']} "
              f"diff_count={r['diff_count']} diff_ok={r['diff_ok']} "
              f"within_budget={r['within_budget']} "
              f"weak_items=[{weak}]")
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0)
    elif args.command == 'qa-proposal':
        r = qa_proposal(args.report, args.mode, args.strategy, args.lang)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0 if r['passed'] else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr); sys.exit(130)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
