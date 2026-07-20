#!/usr/bin/env python3
"""proposal skill 工具集 — v3 canonical/context/realization + legacy 装配与 QA。

自包含，仅依赖标准库。所有读取用 utf-8-sig（BOM 容错），写入用 utf-8 无 BOM。
非 ASCII 文本一律走文件参数，不进 shell argv。
"""
import argparse
import json
import os
import re
import shutil
import sys
import datetime
import tempfile
import unicodedata

try:
    from . import prop_v3
except ImportError:  # direct ``python tools/prop_tools.py`` execution
    import prop_v3


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
        'project': '项目名称', 'project_no': '项目编号', 'buyer': '采购人',
        'bidder': '投标人', 'tbd_bidder': '【待填写：投标人全称并加盖公章】',
        'bid_date': '投标日期', 'tbd_date': '【待填写】',
        'budget_resp': '预算响应', 'chars': '字数', 'gen': '生成时间',
        'mode': '深度模式', 'version': '工具版本', 'through_line': '叙事主线',
        'toc': '## 目录', 'matrix': '## 应标响应与评分对照表',
        'toc_label_file': '目录', 'matrix_label_file': '应标响应与评分对照表',
        'combined_name': '技术方案-完整版.md', 'parts_dir': '分册',
        'brief_name': '_内部研判.md', 'brief_title': '# 内部研判（⚠️ 不随投标文件递交）',
        'brief_warn': ('> 本文件仅供投标人内部使用。生成参数、叙事策略、情报来源等信息**绝不能**'
                       '出现在递交给评委的投标文件里——那等于把说服策略和工具痕迹亮给对方。'),
        'brief_params': '生成参数', 'brief_sources': '情报来源（供投标人自行核验）',
        'brief_sources_note': ('> 正文中的数据均以行内方式标注来源（如「据XX研究院2026年报告」）。'
                               '下列 URL 清单供你核验，**不要**附进投标文件——投标文件不带网址书目。'),
        'narrative': '叙事策略', 'brief_decisions': '投标决策地图',
        'decision_destination': '终点', 'decision_resolved': '已确认',
        'decision_assumed': 'AI 假设（待人工复核）', 'decision_open': '未解决',
        'decision_fog': '尚未具体化', 'decision_out': '范围外',
        'exec_summary': '## 方案综述', 'exec_summary_label': '方案综述',
        'todo_title': '# 人工待办清单', 'todo_note': ('> 下列内容 AI 不应替你决定或编造，需投标人本人填写/核实后再定稿。'
                                                 '按「不填会丢多少分」排序，废标风险项排最前。'),
        'todo_blocking': '## ⚠ 废标风险项（必须处理）', 'todo_scoring': '## 丢分项（建议处理）',
        'todo_assumptions': '## AI 策略假设（递交前必须复核）',
        'todo_intel_gaps': '## 情报缺口与假设冲突（人工核验）',
        'todo_weak': '## 竞争力薄弱项（自评信号，供人工强化）', 'todo_none': '（无）',
        'todo_v3': '## v3 递交阻断与关键诊断',
        'todo_ch': '章节', 'todo_item': '待办', 'todo_impact': '不处理的后果',
        'todo_decision': '决策', 'todo_assumption': '当前假设',
        'todo_topic': '主题', 'todo_gap': '情报缺口',
        'm_req': '要求项', 'm_cat': '类别', 'm_wt': '权重/性质', 'm_sec': '响应章节',
        'cat_qual': '资格', 'cat_subst': '实质性', 'cat_fmt': '格式', 'cat_score': '评分项',
        'cat_deliverable': '交付要求',
        'uncovered': '⚠ 未覆盖（需补）', 'budget_within': '≤{v}{u}（预算带内）',
        'budget_range': '按行业合理区间测算', 'no_src': '暂无联网来源',
        'matrix_note': '> 下表逐条对应标书的资格/实质性/格式条款与评分办法，确保应标零遗漏。',
    },
    'en': {
        'project': 'Project', 'project_no': 'Project No.', 'buyer': 'Buyer',
        'bidder': 'Bidder', 'tbd_bidder': '[TBD: bidder full name + official seal]',
        'bid_date': 'Bid date', 'tbd_date': '[TBD]',
        'budget_resp': 'Budget', 'chars': 'Characters', 'gen': 'Generated',
        'mode': 'Depth mode', 'version': 'Tool version', 'through_line': 'Through-line',
        'toc': '## Table of Contents', 'matrix': '## Compliance & Scoring Matrix',
        'toc_label_file': 'Table of Contents', 'matrix_label_file': 'Compliance Matrix',
        'combined_name': 'Technical-Proposal-Full.md', 'parts_dir': 'parts',
        'brief_name': '_internal-brief.md', 'brief_title': '# Internal Brief (DO NOT SUBMIT)',
        'brief_warn': ('> For the bidder only. Generation params, narrative strategy and intel sources '
                       'must never appear in the submitted bid document.'),
        'brief_params': 'Generation parameters', 'brief_sources': 'Intel sources (for your own verification)',
        'brief_sources_note': ('> Body text cites sources inline. This URL list is for your verification only — '
                               'do not attach it to the bid document.'),
        'narrative': 'Narrative', 'brief_decisions': 'Bid decision map',
        'decision_destination': 'Destination', 'decision_resolved': 'Confirmed',
        'decision_assumed': 'AI assumption (verify)', 'decision_open': 'Unresolved',
        'decision_fog': 'Not yet specified', 'decision_out': 'Out of scope',
        'exec_summary': '## Executive Summary', 'exec_summary_label': 'Executive Summary',
        'todo_title': '# Human To-Do', 'todo_note': ('> The items below must be filled or verified by the bidder. '
                                                    'Sorted by score impact; disqualification risks first.'),
        'todo_blocking': '## Disqualification risks (must fix)', 'todo_scoring': '## Score losses (should fix)',
        'todo_assumptions': '## AI strategy assumptions (verify before submission)',
        'todo_intel_gaps': '## Intel gaps and assumption conflicts (verify)',
        'todo_weak': '## Weak items (self-score signals)', 'todo_none': '(none)',
        'todo_v3': '## v3 submission blockers and major diagnostics',
        'todo_ch': 'Chapter', 'todo_item': 'To-do', 'todo_impact': 'If ignored',
        'todo_decision': 'Decision', 'todo_assumption': 'Current assumption',
        'todo_topic': 'Topic', 'todo_gap': 'Intel gap',
        'm_req': 'Requirement', 'm_cat': 'Category', 'm_wt': 'Weight/Type', 'm_sec': 'Addressed in',
        'cat_qual': 'Qualification', 'cat_subst': 'Substantive', 'cat_fmt': 'Format', 'cat_score': 'Scoring',
        'cat_deliverable': 'Deliverable',
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


def _strip_heading_number(title):
    """Remove a writer-supplied chapter/subsection number before renumbering."""
    value = re.sub(r'\s+#+\s*$', '', title.strip())
    patterns = (
        r'^[（(]\d+[）)]\s*',
        r'^\d+(?:(?:\.\d+)+|[.．、])\s+',
        r'^[一二三四五六七八九十百零〇两]+[、.．]\s*',
    )
    for pattern in patterns:
        stripped = re.sub(pattern, '', value, count=1)
        if stripped != value:
            return stripped.strip()
    return value


def _normalize_section_body(body, chapter_n, expected_title):
    """Compile writer-local headings into the final proposal hierarchy.

    Writers may use H2/H3 locally because they only see one chapter.  The
    assembled report owns the chapter H2, so local headings are shifted and
    deterministically numbered as H3 ``N.x`` and H4 ``(x)`` headings.
    """
    lines = body.strip().splitlines()
    if not lines:
        return ''

    first = re.match(r'^(#{1,2})[ \t]+(.+?)\s*$', lines[0])
    if first:
        first_title = _strip_heading_number(first.group(2))
        if first.group(1) == '#' or first_title == expected_title.strip():
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines.pop(0)

    headings = []
    fenced = False
    fence_marker = None
    for index, line in enumerate(lines):
        marker = re.match(r'^\s*(```+|~~~+)', line)
        if marker:
            token = marker.group(1)[0]
            if not fenced:
                fenced, fence_marker = True, token
            elif token == fence_marker:
                fenced, fence_marker = False, None
            continue
        if fenced:
            continue
        match = re.match(r'^(#{1,6})[ \t]+(.+?)\s*$', line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))

    if not headings:
        return '\n'.join(lines).strip()

    shift = max(0, 3 - min(level for _, level, _ in headings))
    subsection = 0
    subsubsection = 0
    replacements = {}
    for index, level, title in headings:
        normalized_level = min(6, level + shift)
        clean_title = _strip_heading_number(title)
        if normalized_level == 3:
            subsection += 1
            subsubsection = 0
            clean_title = f"{chapter_n}.{subsection} {clean_title}"
        elif normalized_level == 4:
            subsubsection += 1
            clean_title = f"({subsubsection}) {clean_title}"
        replacements[index] = f"{'#' * normalized_level} {clean_title}"

    for index, value in replacements.items():
        lines[index] = value
    return '\n'.join(lines).strip()


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


def write_json_atomic(path, value):
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


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
    text = re.sub(r'^[ \t]*\|?[ \t:|-]+\|[ \t:|-]*$', '', text, flags=re.MULTILINE)
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
    for d in req.get('deliverables') or []:
        if isinstance(d, dict) and d.get('id'):
            ids.append(d['id'])
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


def out_of_scope_items(strategy):
    """兼容旧字符串格式，统一返回 item/reason/forbidden_terms 对象。"""
    decision_map = strategy.get('decision_map') or {}
    normalized = []
    for raw in decision_map.get('out_of_scope') or []:
        if isinstance(raw, str):
            normalized.append({"item": raw, "reason": "", "forbidden_terms": []})
        elif isinstance(raw, dict):
            normalized.append({
                "item": raw.get('item') or '',
                "reason": raw.get('reason') or '',
                "forbidden_terms": raw.get('forbidden_terms') or [],
            })
    return normalized


# ── 参考来源提取 ────────────────────────────────────────────────────────────
def extract_refs(intel):
    if isinstance(intel, dict) and isinstance(intel.get('evidence'), list):
        seen = set()
        entries = []
        src_freq = {}
        for evidence in intel.get('evidence') or []:
            if not isinstance(evidence, dict):
                continue
            url = (evidence.get('url') or '').strip()
            src = (evidence.get('source') or '').strip()
            title = (evidence.get('title') or '').strip()
            observed = evidence.get('observed_at', '')
            visibility = evidence.get('visibility')
            if src:
                src_freq[src] = src_freq.get(src, 0) + 1
            if visibility != 'public' or not url or url in seen:
                continue
            seen.add(url)
            entries.append((title or src or url, src, observed, url))
        entries.sort(key=lambda x: (x[1].lower() if x[1] else 'zzz', x[0]))
        top_sources = sorted(src_freq, key=src_freq.get, reverse=True)[:6]
        return entries, top_sources
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
                      sections_dir, mode, output_path, lang, allow_assumed=False):
    """产出技术标卷册目录：
        <dir>/技术方案-完整版.md      递交稿（合并版）
        <dir>/分册/NN-*.md            递交稿（分册，便于拼 Word / 单章重写）
        <dir>/_内部研判.md            ⚠️ 不递交：生成参数 / 情报来源 / 竞争力信号

    递交稿里**不得出现任何内部信息**（模式、叙事策略、工具版本、生成时间、
    字数、阅读时间、URL 书目）——那是研报的东西，写进投标文件等于把底牌
    亮给评委。所有这些一律进 _内部研判.md。
    """
    strategy_check = check_strategy(
        strategy_path, mode=mode, require_settled=True, allow_assumed=allow_assumed)
    if not strategy_check['passed']:
        return {
            "passed": False,
            "issues": [f"Strategy not settled: {issue}" for issue in strategy_check['issues']],
        }

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
    stamp = now.strftime('%Y%m%d-%H%M%S')
    base_dir = output_path or 'reports'
    bundle_dir = os.path.join(base_dir, f"{safe_title}-{stamp}")
    final_parts_dir = os.path.join(bundle_dir, L['parts_dir'])
    final_output_path = os.path.join(bundle_dir, L['combined_name'])

    # 执行摘要（section-0.md，可选；不参与章节编号）
    exec_text = ''
    exec_path = os.path.join(sections_dir, 'section-0.md')
    if os.path.exists(exec_path):
        exec_body = read_text(exec_path).strip()
        exec_body = re.sub(r'^#{1,2} .+?\n+', '', exec_body, count=1)  # 去掉误写的标题
        if exec_body:
            exec_text = f"{L['exec_summary']}\n\n{exec_body}"

    # 章节正文
    chapter_texts = []
    for sec in sections:
        n = sec.get('n')
        spath = os.path.join(sections_dir, f"section-{n}.md")
        if not os.path.exists(spath):
            issues.append(f"Missing section file: section-{n}.md")
            continue
        body = _normalize_section_body(
            read_text(spath), n, sec.get('title', '')
        )
        heading = chapter_heading(lang, n, sec.get('title', ''))
        chapter_texts.append(f"{heading}\n\n{body}")

    # 目录（纯文本，无锚点——投标文件要转 Word/PDF，锚点链接是研报的产物）
    toc_lines = []
    if exec_text:
        toc_lines.append(f"- {L['exec_summary_label']}")
    for sec in sections:
        toc_lines.append(f"- {toc_label(lang, sec.get('n'), sec.get('title', ''))}")
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
    for d in req.get('deliverables') or []:
        if not isinstance(d, dict) or not d.get('id'):
            continue
        item = (d.get('item') or '').replace('|', '/')
        matrix_rows.append(
            f"| {item} | {L['cat_deliverable']} | "
            f"{'必须交付' if lang=='zh' else 'Required'} | {sec_refs(d.get('id'))} |"
        )
    for s in req.get('scoring') or []:
        item = (s.get('item') or '').replace('|', '/')
        dim = (s.get('dimension') or '').replace('|', '/')
        wt = s.get('weight', '')
        cat_txt = f"{L['cat_score']}·{dim}" if lang == 'zh' else f"{L['cat_score']}·{dim}"
        matrix_rows.append(f"| {item} | {cat_txt} | {wt} | {sec_refs(s.get('id'))} |")
    matrix_text = '\n'.join(matrix_rows)

    # 项目信息头（投标文件该有的；字数/阅读时间/生成时间/模式/叙事/版本一概不写）
    cap = req.get('budget_cap') or {}
    info_rows = [f"{L['project']}：{req.get('project_name','')}"]
    if req.get('project_no'):
        info_rows.append(f"{L['project_no']}：{req.get('project_no')}")
    info_rows.append(f"{L['buyer']}：{req.get('buyer','')}")
    info_rows.append(f"{L['bidder']}：{L['tbd_bidder']}")
    info_rows.append(f"{L['bid_date']}：{L['tbd_date']}")
    info_text = '\n'.join(info_rows)

    # 递交稿：标题 → 项目信息 → 目录 → 应标响应对照表 → 方案综述 → 正文各章
    full = "\n".join([
        f"# {title}\n",
        info_text, "",
        f"{L['toc']}\n",
        toc_text, "",
        f"{L['matrix']}\n",
        L['matrix_note'], "",
        matrix_text, "",
        *([exec_text, ""] if exec_text else []),
        "\n\n".join(chapter_texts),
    ]) + "\n"

    wc = word_count_text(full)

    # 先在 staging 构建完整卷册。只有全部文件和编码检查成功后才切换，
    # 上一份成功卷册同时进入隐藏的 .last-good；失败构建不碰当前交付物。
    os.makedirs(base_dir, exist_ok=True)
    staging_dir = tempfile.mkdtemp(prefix='.proposal-bundle-staging-', dir=base_dir)
    try:
        parts_dir = os.path.join(staging_dir, L['parts_dir'])
        output_path = os.path.join(staging_dir, L['combined_name'])
        os.makedirs(parts_dir, exist_ok=True)
        write_text_atomic(output_path, full)

        # 分册（便于拼 Word / 单章重写）
        idx = 0
        part_files = []

        def _emit(name, body):
            nonlocal idx
            fn = f"{idx:02d}-{re.sub(r'[<>:\"/\\\\|?*]', '-', name)}.md"
            write_text_atomic(os.path.join(parts_dir, fn), body.rstrip() + "\n")
            part_files.append(fn)
            idx += 1

        _emit(L['toc_label_file'], f"{L['toc']}\n\n{toc_text}")
        _emit(L['matrix_label_file'], f"{L['matrix']}\n\n{L['matrix_note']}\n\n{matrix_text}")
        if exec_text:
            _emit(L['exec_summary_label'], exec_text)
        for sec, body in zip(sections, chapter_texts):
            _emit(toc_label(lang, sec.get('n'), sec.get('title', '')), body)

        # ⚠️ 内部研判（不递交）：把所有会暴露底牌的东西关在这里
        nar = strategy.get('narrative') or {}
        entries, _ = extract_refs(intel)
        budget_str = (L['budget_within'].format(v=cap.get('value'), u=cap.get('unit', ''))
                      if cap.get('value') is not None else L['budget_range'])
        brief = [
            L['brief_title'], '', L['brief_warn'], '',
            f"## {L['brief_params']}", '',
            f"- {L['gen']}：{gen_time}",
            f"- {L['mode']}：{mode}",
            f"- {L['narrative']}：{nar.get('mode', '-')}"
            + (f" + {nar.get('secondary')}" if nar.get('secondary') else ''),
            f"- {L['through_line']}：{nar.get('through_line', '-')}",
            f"- {L['budget_resp']}：{budget_str}",
            f"- {L['chars']}：{wc}",
            f"- {L['version']}：v{read_version()}",
        ]

        page = strategy.get('one_page_strategy') or {}
        if isinstance(page, dict) and page:
            tension = page.get('customer_tension') or {}
            insight = page.get('sharp_insight') or {}
            thesis = page.get('core_thesis') or {}
            differentiation = page.get('differentiation') or {}
            approval = page.get('approval') or {}
            strategy_title = '一页纸策略' if lang == 'zh' else 'One-page strategy'
            brief.extend(['', f"## {strategy_title}", ''])
            fields = [
                ('客户张力' if lang == 'zh' else 'Customer tension',
                 tension.get('underlying_tension')),
                ('尖锐洞察' if lang == 'zh' else 'Sharp insight',
                 insight.get('statement')),
                ('核心命题' if lang == 'zh' else 'Core thesis',
                 thesis.get('statement')),
                ('记忆句' if lang == 'zh' else 'Recall line',
                 thesis.get('recall_line')),
                ('互换测试' if lang == 'zh' else 'Name-swap test',
                 differentiation.get('name_swap_test')),
                ('批准状态' if lang == 'zh' else 'Approval',
                 approval.get('status')),
            ]
            for label, value in fields:
                if value not in (None, ''):
                    brief.append(f"- **{label}**：{value}")
            rubric = page.get('rubric_review') or {}
            if rubric:
                rendered = '；'.join(
                    f"{key}={value.get('level', '-')}"
                    for key, value in rubric.items()
                    if isinstance(value, dict)
                )
                if rendered:
                    brief.append(
                        f"- **{'五维自评' if lang == 'zh' else 'Rubric'}**：{rendered}")

        # 决策地图只进内部研判：保留用户确认与 -auto 假设，TMPDIR 清理后仍可追溯。
        decision_map = strategy.get('decision_map') or {}
        decisions = strategy.get('open_questions') or []
        if decision_map or decisions:
            brief.extend(['', f"## {L['brief_decisions']}", ''])
            destination = decision_map.get('destination')
            if destination:
                brief.append(f"- **{L['decision_destination']}**：{destination}")
            status_labels = {
                'resolved': L['decision_resolved'],
                'assumed': L['decision_assumed'],
                'open': L['decision_open'],
            }
            for status in ('resolved', 'assumed', 'open'):
                for decision in decisions:
                    if decision.get('status', 'open') != status:
                        continue
                    title = decision.get('title') or decision.get('q') or '-'
                    answer = decision.get('resolved') or decision.get('ai_assumption') or '-'
                    risk = decision.get('why_matters') or ''
                    suffix = f" — {risk}" if status in ('assumed', 'open') and risk else ''
                    brief.append(f"- **{status_labels[status]} · {title}**：{answer}{suffix}")
            fog = decision_map.get('not_yet_specified') or []
            if fog:
                names = [item.get('name', '-') if isinstance(item, dict) else str(item) for item in fog]
                brief.append(f"- **{L['decision_fog']}**：{'；'.join(names)}")
            out_of_scope = out_of_scope_items(strategy)
            if out_of_scope:
                rendered = []
                for item in out_of_scope:
                    text = item['item']
                    if item['reason']:
                        text += f"（{item['reason']}）"
                    rendered.append(text)
                brief.append(f"- **{L['decision_out']}**：{'；'.join(rendered)}")

        brief.extend(['', f"## {L['brief_sources']}", '', L['brief_sources_note'], ''])
        if entries:
            for name, src, yr, url in entries:
                label = name if not src or src == name else f"{name} · {src}"
                if yr:
                    label += f" · {yr}"
                brief.append(f"- [{label}]({url})")
        else:
            brief.append(L['no_src'])
        staging_brief = os.path.join(staging_dir, L['brief_name'])
        write_text_atomic(staging_brief, '\n'.join(brief) + '\n')
        enc = check_encoding(output_path)
        if not enc['passed']:
            issues.append(f"Encoding issue: {enc['issues']}")
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    if issues:
        shutil.rmtree(staging_dir, ignore_errors=True)
        return {
            "passed": False,
            "issues": issues,
            "bundle_dir": bundle_dir,
        }

    pat = re.compile(r'^' + re.escape(safe_title) + r'-\d{8}-\d{6}$')
    previous = sorted(
        os.path.join(base_dir, fn) for fn in os.listdir(base_dir)
        if pat.match(fn) and os.path.isdir(os.path.join(base_dir, fn))
    )
    previous_path = previous[-1] if previous else None
    last_good_root = os.path.join(base_dir, '.last-good')
    last_good_dir = os.path.join(last_good_root, safe_title)
    retiring_dir = last_good_dir + '.retiring'
    moved_previous = False
    retired_last_good = False

    try:
        # Reconcile a prior interrupted rotation before starting a new one.
        if os.path.exists(retiring_dir):
            if prop_v3.recovery_point_nonempty(last_good_dir):
                shutil.rmtree(retiring_dir, ignore_errors=True)
                if os.path.exists(retiring_dir):
                    raise OSError(f"Cannot clear stale recovery point: {retiring_dir}")
            else:
                prop_v3.restore_retiring_recovery(
                    retiring_dir, last_good_dir)
        if previous_path:
            os.makedirs(last_good_root, exist_ok=True)
            if os.path.exists(last_good_dir):
                os.replace(last_good_dir, retiring_dir)
                retired_last_good = True
            os.replace(previous_path, last_good_dir)
            moved_previous = True
        os.replace(staging_dir, bundle_dir)
        staging_dir = None
        if os.path.exists(retiring_dir):
            shutil.rmtree(retiring_dir, ignore_errors=True)
        for old in previous[:-1]:
            if old != bundle_dir:
                shutil.rmtree(old, ignore_errors=True)
    except Exception:
        if moved_previous and previous_path and not os.path.exists(previous_path):
            try:
                os.replace(last_good_dir, previous_path)
            except Exception:
                pass
        if retired_last_good:
            try:
                prop_v3.restore_retiring_recovery(
                    retiring_dir, last_good_dir)
            except Exception:
                pass
        if staging_dir and os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return {
        "passed": True,
        "output_path": final_output_path,
        "bundle_dir": bundle_dir,
        "parts_dir": final_parts_dir,
        "part_count": len(part_files),
        "internal_brief": os.path.join(bundle_dir, L['brief_name']),
        "last_good_bundle": last_good_dir if moved_previous else None,
        "line_count": full.count('\n') + 1,
        "chapter_count": len(chapter_texts),
        "exec_summary": bool(exec_text),
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
    deli = [(d.get('id'), d.get('item', '')) for d in (req.get('deliverables') or [])
            if isinstance(d, dict) and d.get('id')]

    missing_mandatory = [{"id": i, "item": it} for i, it in mand if i not in mapped]
    missing_scoring = [{"id": i, "item": it} for i, it in scor if i not in mapped]
    missing_deliverables = [{"id": i, "item": it} for i, it in deli if i not in mapped]

    total = len(mand) + len(scor) + len(deli)
    covered = total - len(missing_mandatory) - len(missing_scoring) - len(missing_deliverables)
    coverage_pct = round(covered / total * 100) if total else 100

    # 校验报告章节数与 strategy 一致（漏写章节会导致映射的评分项其实没落地）
    report = read_text(report_path)
    chapter_headings = re.findall(r'^## (?:[一二三四五六七八九十]+、|\d+\. )', report, re.MULTILINE)
    expected_chapters = len(strategy.get('sections') or [])
    chapter_ok = len(chapter_headings) >= expected_chapters

    matrix_present = ('## 应标响应与评分对照表' in report) or ('## Compliance & Scoring Matrix' in report)

    passed = (not missing_mandatory) and (not missing_scoring) and (not missing_deliverables) and chapter_ok and matrix_present
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
        "addressed_deliverables": len(deli) - len(missing_deliverables),
        "total_deliverables": len(deli),
        "missing_deliverables": missing_deliverables,
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

    is_v3 = strategy.get('schema_version') in ('strategy/v3', 'strategy/v4', 'strategy/v5')

    # 差异化点 → 覆盖的评分 id（仅 legacy；v3 由 customer-fit 评价组合充分性）
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
            if has_diff and not is_v3:
                frac += 0.15
            elif w >= 15 and not is_v3:
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
        "min_differentiators": None if is_v3 else min_diff,
        "diff_ok": True if is_v3 else diff_count >= min_diff,
        "within_budget": within_budget,
        "weak_items": weak_list,
        "deprecated": is_v3,
        "note": ("v3 仅保留 mandatory/scoring 机械兼容信号；客户价值请读取 customer-fit"
                 if is_v3 else None),
    }


# ── 人工待办清单 ───────────────────────────────────────────────────────────
PLACEHOLDER_RE = re.compile(r'【([^】\n]{1,80})】')


def human_todo(requirements_path, strategy_path, report_path, mode, output_path, lang,
               intel_path=None, state_dir=None, canonical_result=None):
    """汇总策略假设、情报缺口、正文占位符与自评薄弱项。
    顺序：废标风险 > 未确认策略假设 > 情报缺口 > 高/低权重丢分 > 竞争力薄弱。"""
    req = read_json(requirements_path)
    strategy = read_json(strategy_path)
    report = read_text(report_path)
    L = lab(lang)

    sections = {s.get('n'): s for s in (strategy.get('sections') or [])}
    scoring_by_id = {s.get('id'): s for s in (req.get('scoring') or []) if s.get('id')}
    mand_by_id = {m.get('id'): m for m in (req.get('mandatory') or []) if m.get('id')}

    blocking, scoring_loss = [], []
    first_chapter = re.search(
        r'^## (?:[一二三四五六七八九十]+、|\d+\. ).+$',
        report,
        re.MULTILINE,
    )
    front_matter = report[:first_chapter.start()] if first_chapter else report
    front_label = '卷首/方案综述' if lang == 'zh' else 'Front matter / Executive summary'
    for ph in PLACEHOLDER_RE.findall(front_matter):
        blocking.append((
            front_label,
            ph,
            '废标风险（卷首或方案综述占位符未替换）',
        ))

    for n, text in split_chapters(report):
        sec = sections.get(n, {})
        ch_label = toc_label(lang, n, sec.get('title', ''))
        addrs = sec.get('addresses') or []
        weights = [scoring_by_id[a].get('weight', 0) or 0 for a in addrs if a in scoring_by_id]
        max_w = max(weights) if weights else 0
        hit_mand = [mand_by_id[a] for a in addrs if a in mand_by_id]

        for ph in PLACEHOLDER_RE.findall(text):
            if hit_mand:
                impact = f"废标风险（{hit_mand[0].get('type', '强制')}项：{hit_mand[0].get('item', '')[:24]}）"
                blocking.append((ch_label, ph, impact))
            else:
                impact = f"丢 {max_w} 分" if max_w else "影响完整性"
                scoring_loss.append((max_w, ch_label, ph, impact))

    scoring_loss.sort(key=lambda x: -x[0])

    # -auto 的策略假设不能伪装成用户确认；即使正文没有占位符也要进入人工待办。
    assumptions = []
    for decision in strategy.get('open_questions') or []:
        status = decision.get('status', 'open')
        if status not in ('open', 'assumed'):
            continue
        title = decision.get('title') or decision.get('q') or '-'
        current = decision.get('resolved') or decision.get('ai_assumption') or '-'
        impact = decision.get('why_matters') or '-'
        assumptions.append((title, current, impact))
    strategy_page = strategy.get('one_page_strategy') or {}
    strategy_approval = ((strategy_page.get('approval') or {})
                         if isinstance(strategy_page, dict) else {})
    if strategy_approval.get('status') in (
            'pending', 'changes_requested', 'assumed'):
        thesis = (strategy_page.get('core_thesis') or {}) if isinstance(
            strategy_page, dict) else {}
        assumptions.append((
            '一页纸策略批准' if lang == 'zh' else 'One-page strategy approval',
            strategy_approval.get('status'),
            thesis.get('recall_line') or (
                '写作前需人工确认策略方向' if lang == 'zh'
                else 'Human strategy review required before submission'),
        ))

    intel_gaps = []
    if intel_path and os.path.exists(intel_path):
        try:
            intel = read_json(intel_path)
        except Exception:
            intel = []
        records = intel if isinstance(intel, list) else [intel]
        for record in records:
            if not isinstance(record, dict):
                continue
            topic = record.get('topic') or ('v3 Evidence' if record.get('schema_version') == 'intel-pool/v3' else '-')
            for gap in record.get('gaps') or []:
                if isinstance(gap, dict):
                    item = (gap.get('item') or gap.get('gap') or gap.get('observed')
                            or gap.get('target_ref') or '-')
                    decision = gap.get('decision') or gap.get('target_ref')
                    if decision:
                        item = f"{item}（关联决策：{decision}）"
                    impact = (gap.get('impact') or gap.get('next_action')
                              or gap.get('kind') or '信息不足，需人工核验')
                else:
                    item = str(gap)
                    impact = '信息不足，需人工核验'
                intel_gaps.append((topic, item, impact))

    ss = self_score(requirements_path, strategy_path, report_path, mode)
    weak = ss.get('weak_items') or []

    v3_diagnostics = []
    if state_dir:
        checked = canonical_result
        if not isinstance(checked, dict) or checked.get('stage') != 'submission':
            realization_dir = os.path.join(state_dir, 'derived', 'realization')
            checked = prop_v3.check_canonical(
                state_dir, stage='submission', realization_dir=realization_dir)
        for diagnostic in checked.get('diagnostics') or []:
            if diagnostic.get('severity') not in ('fatal', 'blocker', 'major'):
                continue
            v3_diagnostics.append(diagnostic)

    def _table(rows):
        if not rows:
            return L['todo_none']
        out = [f"| {L['todo_ch']} | {L['todo_item']} | {L['todo_impact']} |", "|:---|:---|:---|"]
        for ch, ph, impact in rows:
            out.append(f"| {ch} | {ph.replace('|', '/')} | {impact} |")
        return '\n'.join(out)

    def _assumption_table(rows):
        if not rows:
            return L['todo_none']
        out = [
            f"| {L['todo_decision']} | {L['todo_assumption']} | {L['todo_impact']} |",
            "|:---|:---|:---|",
        ]
        for title, current, impact in rows:
            safe = [str(v).replace('|', '/').replace('\n', ' ') for v in (title, current, impact)]
            out.append(f"| {safe[0]} | {safe[1]} | {safe[2]} |")
        return '\n'.join(out)

    def _intel_gap_table(rows):
        if not rows:
            return L['todo_none']
        out = [
            f"| {L['todo_topic']} | {L['todo_gap']} | {L['todo_impact']} |",
            "|:---|:---|:---|",
        ]
        for topic, gap, impact in rows:
            safe = [str(v).replace('|', '/').replace('\n', ' ') for v in (topic, gap, impact)]
            out.append(f"| {safe[0]} | {safe[1]} | {safe[2]} |")
        return '\n'.join(out)

    weak_lines = [L['todo_none']] if not weak else [
        f"- [ ] **{scoring_by_id.get(w['id'], {}).get('item', w['id'])}** — {w['reason']}"
        for w in weak
    ]

    def _v3_table(rows):
        if not rows:
            return L['todo_none']
        out = [
            "| Severity | Kind | Observed | Owner / repair |",
            "|:---|:---|:---|:---|",
        ]
        for item in rows:
            repair = (item.get('repair_options') or ['-'])[0] or '-'
            values = [
                item.get('severity') or '-', item.get('kind') or '-',
                item.get('observed') or '-',
                f"{item.get('owner') or '-'} · {repair}",
            ]
            safe = [str(value).replace('|', '/').replace('\n', ' ') for value in values]
            out.append(f"| {safe[0]} | {safe[1]} | {safe[2]} | {safe[3]} |")
        return '\n'.join(out)

    parts = [
        L['todo_title'], '',
        L['todo_note'], '',
        L['todo_blocking'], '',
        _table(blocking), '',
        L['todo_assumptions'], '',
        _assumption_table(assumptions), '',
        L['todo_intel_gaps'], '',
        _intel_gap_table(intel_gaps), '',
        L['todo_scoring'], '',
        _table([(ch, ph, im) for _, ch, ph, im in scoring_loss]), '',
        L['todo_weak'], '',
        '\n'.join(weak_lines), '',
        L['todo_v3'], '',
        _v3_table(v3_diagnostics), '',
    ]
    write_text_atomic(output_path, '\n'.join(parts) + '\n')

    return {"passed": True, "output_path": output_path,
            "blocking_count": len(blocking), "scoring_count": len(scoring_loss),
            "assumption_count": len(assumptions), "intel_gap_count": len(intel_gaps),
            "weak_count": len(weak),
            "canonical_blocker_count": sum(
                1 for item in v3_diagnostics
                if item.get('severity') in ('fatal', 'blocker')),
            "canonical_major_count": sum(
                1 for item in v3_diagnostics if item.get('severity') == 'major'),
            "todo_count": len(blocking) + len(assumptions) + len(intel_gaps)
            + len(scoring_loss) + len(v3_diagnostics)}


def _load_profile(mode):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        profiles = read_json(os.path.join(base, 'profiles.json'))
        return profiles.get(mode, profiles.get('standard', {}))
    except Exception:
        return {}


# ── 甲方导向词频（"这份方案在讲谁"的机械信号）──────────────────────────────
BUYER_TERMS_ZH = ['贵单位', '贵局', '贵委', '贵办', '贵中心', '贵司', '贵公司', '贵方', '采购人']
SELF_TERMS_ZH = ['我司', '我方', '我们', '我公司', '本公司', '本单位', '本项目组', '本团队']


def buyer_focus(report, req, lang):
    """甲方提及数 / 我方提及数。比值低 = 方案在自夸而非解决甲方问题。
    启发式信号，警告级——不阻断交付，交给人在定稿关卡判断。"""
    if lang != 'zh':
        return {"passed": True, "warning": True, "skipped": "仅 zh 启用"}

    buyer_name = (req.get('buyer') or '').strip()
    buyer_n = sum(report.count(t) for t in BUYER_TERMS_ZH)
    if buyer_name:
        buyer_n += report.count(buyer_name)
    self_n = sum(report.count(t) for t in SELF_TERMS_ZH)

    ratio = round(buyer_n / self_n, 2) if self_n else (99.0 if buyer_n else 0.0)
    passed = buyer_n > 0 and ratio >= 0.8
    return {"passed": passed, "warning": True, "buyer_mentions": buyer_n,
            "self_mentions": self_n, "ratio": ratio, "min_ratio": 0.8,
            "hint": "甲方提及少于我方 → 检查各章是否以甲方问题开篇，而非自我推销"}


def _sensitive_fingerprint(value):
    if not isinstance(value, str):
        return ''
    folded = unicodedata.normalize('NFKC', value).casefold()
    return ''.join(
        ch for ch in folded
        if unicodedata.category(ch).startswith(('L', 'N'))
    )


def _private_raw_leaks(report, state_dir):
    """Find exact/normalized private canonical wording reintroduced into a report."""
    if not state_dir:
        return []
    documents, _ = prop_v3.load_state(state_dir)
    report_fingerprint = _sensitive_fingerprint(report)
    candidates = []

    def add(ref, field, value, approved=()):
        fingerprint = _sensitive_fingerprint(value)
        approved_fingerprints = {
            _sensitive_fingerprint(item) for item in approved if isinstance(item, str)
        }
        # Short labels and generic fragments create too many false positives.
        if len(fingerprint) < 8 or fingerprint in approved_fingerprints:
            return
        candidates.append({"ref": ref, "field": field, "fingerprint": fingerprint})

    intel = documents.get('intel-pool.json') or {}
    for evidence in intel.get('evidence') or []:
        if not isinstance(evidence, dict):
            continue
        visibility = evidence.get('visibility')
        if visibility not in ('private', 'internal', 'unknown', 'approved_anonymized'):
            continue
        ref = evidence.get('id') or 'Evidence'
        approved = (evidence.get('safe_title'), evidence.get('approved_projection'))
        add(ref, 'content', evidence.get('content'), approved)
        add(ref, 'title', evidence.get('title'), approved)
        add(ref, 'source', evidence.get('source'), approved)

    customer = documents.get('customer-value.json') or {}
    for collection in ('needs', 'criteria'):
        for item in customer.get(collection) or []:
            if not isinstance(item, dict):
                continue
            publication = item.get('publication_status')
            if publication not in ('internal_only', 'publicly_supportable', None):
                continue
            add(item.get('id') or collection, 'statement', item.get('statement'),
                (item.get('approved_projection'),))

    for role in customer.get('roles') or []:
        if not isinstance(role, dict):
            continue
        for field in ('private_notes', 'notes'):
            add(role.get('id') or 'Role', field, role.get(field),
                (role.get('approved_projection'),))

    strategy = documents.get('strategy.json') or {}
    for decision in strategy.get('open_questions') or []:
        if not isinstance(decision, dict):
            continue
        if decision.get('status') not in ('resolved', 'assumed'):
            continue
        add(decision.get('id') or decision.get('ref') or 'Gate', 'resolved',
            decision.get('resolved'), (decision.get('safe_constraint'),))

    leaks = []
    seen = set()
    for candidate in candidates:
        if candidate['fingerprint'] not in report_fingerprint:
            continue
        key = (candidate['ref'], candidate['field'])
        if key in seen:
            continue
        seen.add(key)
        leaks.append({"ref": candidate['ref'], "field": candidate['field']})
    return leaks


# ── QA ─────────────────────────────────────────────────────────────────────
def qa_proposal(report_path, mode, strategy_path, lang, requirements_path=None,
                state_dir=None):
    checks = {}
    report = read_text(report_path)
    lines = report.split('\n')
    L = lab(lang)

    enc = check_encoding(report_path)
    checks['encoding'] = enc

    # 卷册结构：标题 → 项目信息 → 目录 → 应标响应对照表 → 方案综述 → 正文各章
    struct_issues = []
    if not lines or not lines[0].startswith('# '):
        struct_issues.append("第 1 行不是 # 标题")
    if L['project'] not in report:
        struct_issues.append(f"缺项目信息头（{L['project']}）")
    if L['toc'] not in report:
        struct_issues.append(f"缺目录标题 {L['toc']}")
    if L['matrix'] not in report:
        struct_issues.append(f"缺应标响应与评分对照表 {L['matrix']}")
    checks['structure'] = {"passed": len(struct_issues) == 0, "issues": struct_issues}

    # ⚡ 内部信息泄露（硬阻断）——递交稿绝不能带工具痕迹与说服策略底牌
    leaks = []
    for pat, why in [
        (r'叙事\s*[:：]?\s*(logic|story|vision|evidence|custom)', '叙事策略（等于把说服底牌给评委）'),
        (r'(模式|深度模式)\s*[:：]?\s*(quick|standard|deep)', '内部深度模式'),
        (r'(版本|工具版本)\s*[:：]?\s*v?\d+\.\d+\.\d+', '工具版本号'),
        (r'阅读\s*\d+\s*分钟', '研报式阅读时间'),
        (r'^[>\-* \t]*(?:\*\*投标方案\*\*[ \t]*·[ \t]*)?'
         r'生成时间\s*[:：]\s*\d{4}(?:[-/.年]\d{1,2})?', '生成时间戳'),
        (r'^>\s*\*\*投标方案\*\*\s*·', '研报式元数据块'),
        (r'\b(?:DecisionJob|ValueProposition|customer[- ]fit|realization manifest|'
         r'canonical(?:[ -](?:state|ready)))\b',
         'v3 内部模型或审计术语'),
    ]:
        if re.search(pat, report, re.MULTILINE | re.IGNORECASE):
            leaks.append(why)
    for line_no, line in enumerate(lines, 1):
        if re.search(r'https?://', line, re.IGNORECASE):
            leaks.append(
                f"URL（第 {line_no} 行；投标文件不带网址书目，来源改行内标注）"
            )
    checks['no_internal_leak'] = {"passed": len(leaks) == 0, "leaked": leaks,
                                  "hint": "这些只能进 _内部研判.md，不能进递交稿"}

    private_raw_leaks = _private_raw_leaks(report, state_dir)
    checks['no_private_raw_leak'] = {
        "passed": len(private_raw_leaks) == 0,
        "warning": False,
        "found": private_raw_leaks[:20],
        "hint": "命中 private/internal/匿名前 raw canonical 原句；只能使用 approved projection",
    }

    # 章节数
    chapter_headings = re.findall(r'^## (?:[一二三四五六七八九十]+、|\d+\. )', report, re.MULTILINE)
    prof = _load_profile(mode)
    strategy_for_count = (read_json(strategy_path)
                          if strategy_path and os.path.exists(strategy_path)
                          else {})
    if strategy_for_count.get('schema_version') in ('strategy/v3', 'strategy/v4', 'strategy/v5'):
        expected_chapters = len(strategy_for_count.get('sections') or [])
        checks['chapter_count'] = {
            "passed": len(chapter_headings) == expected_chapters,
            "count": len(chapter_headings), "expected": expected_chapters,
            "rule": "exact strategy.sections count",
        }
    else:
        min_ch = prof.get('legacy_min_chapters', prof.get('min_chapters', 6))
        checks['chapter_count'] = {
            "passed": len(chapter_headings) >= min_ch,
            "count": len(chapter_headings), "min": min_ch,
            "rule": "legacy profile minimum",
        }

    # 子节汉字编号（应为阿拉伯数字 N.x）
    zh_sub = [
        i + 1 for i, line in enumerate(lines)
        if re.match(r'^### [一二三四五六七八九十]+\s*[、.．)）]', line)
    ]
    checks['subsection_numbering'] = {"passed": len(zh_sub) == 0,
                                      "issues": [f"line {n} 用汉字编号子节" for n in zh_sub[:5]]}

    # 章为 H2，一级子节为 H3 N.x，子子节为 H4 (x)。客户稿的
    # 层级必须由装配结果确定，不能受分章 writer 的局部标题习惯影响。
    hierarchy_issues = []
    current_chapter = None
    saw_subsection = False
    chapter_counter = 0
    for line_no, line in enumerate(lines, 1):
        if re.match(r'^## (?:[一二三四五六七八九十]+、|\d+\. )', line):
            chapter_counter += 1
            current_chapter = chapter_counter
            saw_subsection = False
            continue
        if current_chapter is None:
            continue
        if line.startswith('## '):
            hierarchy_issues.append(
                f"line {line_no} 章内标题不得与章同为 H2"
            )
        elif line.startswith('### '):
            if not re.match(rf'^### {current_chapter}\.\d+\s+\S', line):
                hierarchy_issues.append(
                    f"line {line_no} 一级子节应为 {current_chapter}.x"
                )
            saw_subsection = True
        elif line.startswith('#### '):
            if not saw_subsection or not re.match(r'^#### \(\d+\)\s+\S', line):
                hierarchy_issues.append(
                    f"line {line_no} 子子节应位于子节后并使用 (x)"
                )
    checks['heading_hierarchy'] = {
        "passed": len(hierarchy_issues) == 0,
        "issues": hierarchy_issues[:10],
    }

    # 内部 id 泄露：legacy S/M/D 编号 + v3 typed refs。任何命中都不能递交。
    # typed ref 大小写敏感，且纯数字 AC-* 留给 state 精确 ID 检查，避免误伤 AC-3 音频标准。
    typed_id_pattern = (
        r'(?<![A-Za-z0-9])'
        r'(?:REQ|ROLE|NEED|CRIT|VP|CL|MET|EL|EV|DR|DA|RES|DEP|AC|DJ|CH|OUT|'
        r'GATE|SRC|RN|NC|RC)-(?=[A-Z0-9_.-]*[A-Z])[A-Z0-9_.-]+'
        r'(?![A-Za-z0-9])'
        r'|(?<![A-Za-z0-9])(?:CH|RN|NC|RC)-\d{1,3}(?![A-Za-z0-9])'
    )
    leak = re.findall(typed_id_pattern, report)

    # S3/M2 既可能是 legacy ID，也可能是常见技术名词；只豁免明确的技术搭配。
    legacy_tech_context = {
        'S3': r'(?:对象存储\s*S3|S3\s*对象存储)',
        'M2': r'(?:芯片\s*M2|M2\s*芯片)',
    }
    for match in re.finditer(r'(?<!\w)[SMD]\d{1,2}(?!\w)', report):
        ref = match.group(0)
        context = report[max(0, match.start() - 12):match.end() + 12]
        tech_pattern = legacy_tech_context.get(ref)
        if tech_pattern and re.search(tech_pattern, context):
            continue
        leak.append(ref)

    exact_ids = set()
    id_check_degraded = False
    if state_dir:
        try:
            documents, _ = prop_v3.load_state(state_dir)
            for document in documents.values():
                if not isinstance(document, dict):
                    continue
                for value in document.values():
                    if not isinstance(value, list):
                        continue
                    for item in value:
                        if isinstance(item, dict):
                            ref = item.get('id') or item.get('ref')
                            if isinstance(ref, str) and ref:
                                exact_ids.add(ref)
            source_path = os.path.join(state_dir, 'source-manifest.json')
            if os.path.isfile(source_path):
                for item in read_json(source_path).get('sources') or []:
                    if isinstance(item, dict) and item.get('id'):
                        exact_ids.add(item['id'])
            strategy = documents.get('strategy.json') or {}
            for item in strategy.get('open_questions') or []:
                if isinstance(item, dict) and (item.get('id') or item.get('ref')):
                    exact_ids.add(item.get('id') or item.get('ref'))
        except Exception:
            id_check_degraded = True
    for ref in exact_ids:
        if re.search(r'(?<![A-Za-z0-9])' + re.escape(ref) + r'(?![A-Za-z0-9])', report):
            leak.append(ref)
    checks['no_id_leak'] = {
        "passed": len(leak) == 0 and not id_check_degraded,
        "warning": False,
        "found": sorted(set(leak))[:10],
        "degraded": id_check_degraded,
    }
    if id_check_degraded:
        checks['no_id_leak']["hint"] = (
            "state 加载失败，无法完成精确 ID 检查；请修复 state 后重新运行 QA"
        )

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
        if strat.get('schema_version') in ('strategy/v3', 'strategy/v4', 'strategy/v5'):
            checks['differentiators'] = {
                "passed": True, "warning": True, "deprecated": True,
                "count": dc, "min": None,
                "hint": "v3 使用 selected ValueProposition 组合充分性，不检查固定亮点数量",
            }
        else:
            checks['differentiators'] = {"passed": dc >= min_diff, "count": dc, "min": min_diff}

        scope_hits = []
        unchecked = []
        folded_report = report.casefold()
        for scope in out_of_scope_items(strat):
            terms = scope.get('forbidden_terms') or []
            if not terms:
                unchecked.append(scope.get('item'))
            for term in terms:
                if term.casefold() in folded_report:
                    scope_hits.append({"item": scope.get('item'), "term": term})
        decision_map = strat.get('decision_map') or {}
        checks['scope_guard'] = {
            "passed": len(scope_hits) == 0,
            "warning": True,
            "destination": decision_map.get('destination'),
            "hits": scope_hits,
            "unchecked": [item for item in unchecked if item],
            "hint": "命中范围外禁用词需人工复核；无 forbidden_terms 的范围项交红队做语义检查",
        }

    # LaTeX 公式残留（$ 后数字未转义）——警告级
    math = re.findall(r'(?<!\\)\$\d', report)
    checks['no_latex'] = {"passed": len(math) == 0, "warning": True, "found": len(math)}

    # 方案综述（执行摘要）——警告级
    checks['exec_summary'] = {"passed": L['exec_summary'] in report, "warning": True,
                              "hint": "评委只精读前两页，建议有方案综述"}

    # 甲方导向词频——警告级
    if requirements_path and os.path.exists(requirements_path):
        checks['buyer_focus'] = buyer_focus(report, read_json(requirements_path), lang)

    # CTA / 排除项残留（销售提案措辞混入投标文件 → 不懂规则 / 负偏离风险）——警告级
    bad_phrases = ['下一步行动', '下周会议', '期待与您沟通', '签约条款']
    found_bad = [p for p in bad_phrases if p in report]
    for phrase in ('排除项', '不包含以下服务'):
        if re.search(r'^[ \t#>*\-]*' + re.escape(phrase), report, re.MULTILINE):
            found_bad.append(phrase)
    checks['no_sales_cta'] = {"passed": len(found_bad) == 0, "warning": True, "found": found_bad,
                              "hint": "投标是密封递交，无 CTA；『排除项』易被认定实质性负偏离"}

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
    for i, d in enumerate(req.get('deliverables') or []):
        if isinstance(d, dict) and not d.get('id'):
            issues.append(f"deliverables[{i}] 缺 id")
    ids = all_requirement_ids(req)
    if len(ids) != len(set(ids)):
        issues.append("存在重复 id")
    return {"passed": len(issues) == 0, "issues": issues,
            "scoring_count": len(req.get('scoring') or []),
            "mandatory_count": len(req.get('mandatory') or [])}


# ── check-strategy / 决策前沿 ───────────────────────────────────────────────
def check_strategy(path, mode=None, require_settled=False, allow_assumed=False):
    """校验策略骨架与本地决策地图，并动态计算当前决策前沿。"""
    issues = []

    def _has_text(value):
        return isinstance(value, str) and bool(value.strip())

    try:
        strategy = read_json(path)
    except Exception as e:
        return {"passed": False, "issues": [f"JSON 解析失败: {e}"],
                "frontier": [], "blocked": []}

    declared_mode = strategy.get('depth_mode')
    actual_mode = mode or declared_mode or 'standard'
    if actual_mode not in ('quick', 'standard', 'deep'):
        issues.append(f"depth_mode 非法: {actual_mode}")
        actual_mode = 'standard'
    if mode and declared_mode and mode != declared_mode:
        issues.append(f"depth_mode 不一致: strategy={declared_mode}, cli={mode}")

    narrative = strategy.get('narrative')
    if not isinstance(narrative, dict):
        issues.append("缺 narrative 对象")
    else:
        narrative_mode = narrative.get('mode')
        if narrative_mode not in ('logic', 'story', 'vision', 'evidence', 'custom'):
            issues.append(f"narrative.mode 非法: {narrative_mode}")
        if not _has_text(narrative.get('rationale')):
            issues.append("narrative 缺 rationale")
        if not narrative.get('through_line'):
            issues.append("narrative 缺 through_line")

    sections = strategy.get('sections')
    if not isinstance(sections, list) or not sections:
        issues.append("缺 sections[]")
    else:
        section_numbers = []
        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                issues.append(f"sections[{i}] 必须是对象")
                continue
            number = section.get('n')
            if (not isinstance(number, int) or isinstance(number, bool)
                    or number <= 0):
                issues.append(f"sections[{i}] 缺 n 或 n 非正整数")
            else:
                section_numbers.append((i, number))
            if not section.get('narrative_role'):
                issues.append(f"sections[{i}] 缺 narrative_role")
            addresses = section.get('addresses')
            if not isinstance(addresses, list) or not addresses:
                issues.append(f"sections[{i}].addresses 必须是非空数组")
            elif any(not _has_text(item) for item in addresses):
                issues.append(f"sections[{i}].addresses 含非法 id")

        first_index_by_number = {}
        for i, number in section_numbers:
            if number in first_index_by_number:
                first = first_index_by_number[number]
                issues.append(
                    f"sections[{i}].n 重复: {number}（首次见于 sections[{first}]）"
                )
            else:
                first_index_by_number[number] = i

    decision_map = strategy.get('decision_map')
    fog = []
    if not isinstance(decision_map, dict):
        issues.append("缺 decision_map 对象")
        decision_map = {}
    else:
        if not _has_text(decision_map.get('destination')):
            issues.append("decision_map 缺 destination")
        fog = decision_map.get('not_yet_specified')
        if not isinstance(fog, list):
            issues.append("decision_map.not_yet_specified 必须是数组")
            fog = []
        out_of_scope = decision_map.get('out_of_scope')
        if not isinstance(out_of_scope, list):
            issues.append("decision_map.out_of_scope 必须是数组")
        else:
            for i, item in enumerate(out_of_scope):
                if isinstance(item, str):
                    if not _has_text(item):
                        issues.append(f"decision_map.out_of_scope[{i}] 必须是非空文本")
                    continue
                if not isinstance(item, dict):
                    issues.append(f"decision_map.out_of_scope[{i}] 必须是对象")
                    continue
                if not _has_text(item.get('item')):
                    issues.append(f"decision_map.out_of_scope[{i}] 缺 item")
                if not _has_text(item.get('reason')):
                    issues.append(f"decision_map.out_of_scope[{i}] 缺 reason")
                terms = item.get('forbidden_terms', [])
                if not isinstance(terms, list) or any(not _has_text(term) for term in terms):
                    issues.append(f"decision_map.out_of_scope[{i}].forbidden_terms 必须是文本数组")

    decisions = strategy.get('open_questions')
    if not isinstance(decisions, list):
        issues.append("open_questions 必须是数组")
        decisions = []

    required_fields = ('title', 'q', 'why_matters', 'ai_assumption')
    titles = []
    for i, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            issues.append(f"open_questions[{i}] 必须是对象")
            continue
        for field in required_fields:
            if not _has_text(decision.get(field)):
                issues.append(f"open_questions[{i}] 缺 {field}")
        title = decision.get('title')
        if _has_text(title):
            titles.append(title)
        if 'depends_on' not in decision or not isinstance(decision.get('depends_on'), list):
            issues.append(f"open_questions[{i}].depends_on 必须是数组")
        else:
            for j, dep in enumerate(decision['depends_on']):
                if not _has_text(dep):
                    issues.append(f"open_questions[{i}].depends_on[{j}] 必须是非空文本")
        status = decision.get('status')
        if status not in ('open', 'resolved', 'assumed'):
            issues.append(f"open_questions[{i}].status 非法: {status}")
        if 'resolved' not in decision:
            issues.append(f"open_questions[{i}] 缺 resolved")
        if 'assumption_risk' not in decision or not isinstance(decision.get('assumption_risk'), bool):
            issues.append(f"open_questions[{i}].assumption_risk 必须是布尔值")
        answer = decision.get('resolved')
        risk = decision.get('assumption_risk')
        if status == 'open':
            if answer is not None:
                issues.append(f"open_questions[{i}] 仍为 open 但 resolved 已有值")
            if risk is not False:
                issues.append(f"open_questions[{i}] 为 open 时 assumption_risk 必须为 false")
        elif status == 'resolved':
            if not _has_text(answer):
                issues.append(f"open_questions[{i}] 状态为 resolved 但 resolved 为空")
            if risk is not False:
                issues.append(f"open_questions[{i}] 为 resolved 时 assumption_risk 必须为 false")
        elif status == 'assumed':
            if not allow_assumed:
                issues.append(f"open_questions[{i}] 使用 assumed，但当前不是 -auto 模式")
            if not _has_text(answer):
                issues.append(f"open_questions[{i}] 状态为 assumed 但 resolved 为空")
            elif answer != decision.get('ai_assumption'):
                issues.append(f"open_questions[{i}] 为 assumed 时 resolved 必须等于 ai_assumption")
            if risk is not True:
                issues.append(f"open_questions[{i}] 为 assumed 时 assumption_risk 必须为 true")

    duplicate_titles = sorted({title for title in titles if titles.count(title) > 1})
    if duplicate_titles:
        issues.append(f"决策 title 重复: {', '.join(duplicate_titles)}")

    title_set = set(titles)
    status_by_title = {
        decision.get('title'): decision.get('status')
        for decision in decisions
        if isinstance(decision, dict) and _has_text(decision.get('title'))
    }
    graph = {}
    for i, decision in enumerate(decisions):
        if not isinstance(decision, dict) or not _has_text(decision.get('title')):
            continue
        title = decision['title']
        deps = [dep for dep in decision.get('depends_on', []) if _has_text(dep)] \
            if isinstance(decision.get('depends_on'), list) else []
        graph[title] = deps
        for dep in deps:
            if dep == title:
                issues.append(f"决策「{title}」不能依赖自身")
            elif dep not in title_set:
                issues.append(f"决策「{title}」依赖不存在的决策「{dep}」")

    # DFS 检测循环依赖。
    state = {}
    found_cycles = set()

    def _visit(title, path):
        state[title] = 1
        for dep in graph.get(title, []):
            if dep not in graph:
                continue
            if state.get(dep) == 1:
                start = path.index(dep) if dep in path else 0
                cycle = tuple(path[start:] + [dep])
                if cycle not in found_cycles:
                    found_cycles.add(cycle)
                    issues.append(f"决策存在循环依赖: {' -> '.join(cycle)}")
            elif state.get(dep, 0) == 0:
                _visit(dep, path + [dep])
        state[title] = 2

    for title in graph:
        if state.get(title, 0) == 0:
            _visit(title, [title])

    for i, item in enumerate(fog):
        if not isinstance(item, dict):
            issues.append(f"not_yet_specified[{i}] 必须是对象")
            continue
        if not _has_text(item.get('name')):
            issues.append(f"not_yet_specified[{i}] 缺 name")
        blocked_by = item.get('blocked_by')
        if not isinstance(blocked_by, list):
            issues.append(f"not_yet_specified[{i}].blocked_by 必须是数组")
            blocked_by = []
        for j, dep in enumerate(blocked_by):
            if not _has_text(dep):
                issues.append(f"not_yet_specified[{i}].blocked_by[{j}] 必须是非空文本")
                continue
            if dep not in title_set:
                issues.append(f"迷雾「{item.get('name', i)}」依赖不存在的决策「{dep}」")
        if not _has_text(item.get('promotion_signal')):
            issues.append(f"not_yet_specified[{i}] 缺 promotion_signal")

    settled_statuses = {'resolved'} | ({'assumed'} if allow_assumed else set())
    frontier = []
    blocked = []
    for decision in decisions:
        if not isinstance(decision, dict) or decision.get('status') != 'open':
            continue
        title = decision.get('title') or decision.get('q') or '-'
        deps = [dep for dep in decision.get('depends_on', []) if _has_text(dep)] \
            if isinstance(decision.get('depends_on'), list) else []
        if all(status_by_title.get(dep) in settled_statuses for dep in deps):
            frontier.append(title)
        else:
            blocked.append(title)

    unresolved_count = len(frontier) + len(blocked)
    if unresolved_count and not frontier:
        issues.append("仍有 open 决策但决策前沿为空；检查依赖链")
    if require_settled:
        if unresolved_count:
            issues.append(f"决策地图未清：仍有 {unresolved_count} 条 open 决策")
        if fog:
            issues.append(f"决策地图未清：仍有 {len(fog)} 条 not_yet_specified")

    resolved_count = sum(1 for d in decisions if isinstance(d, dict) and d.get('status') == 'resolved')
    assumed_count = sum(1 for d in decisions if isinstance(d, dict) and d.get('status') == 'assumed')
    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "mode": actual_mode,
        "allow_assumed": allow_assumed,
        "decision_count": len(decisions),
        "resolved_count": resolved_count,
        "assumed_count": assumed_count,
        "open_count": unresolved_count,
        "frontier": frontier,
        "blocked": blocked,
        "fog_count": len(fog),
        "out_of_scope_count": len(decision_map.get('out_of_scope') or []),
        "settled": unresolved_count == 0 and len(fog) == 0
        and (allow_assumed or assumed_count == 0),
    }


def apply_auto_decisions(path):
    """把仍为 open 的决策原子化转换为 -auto 假设；不处理语义性的迷雾归位。"""
    try:
        strategy = read_json(path)
    except Exception as e:
        return {"passed": False, "issues": [f"JSON 解析失败: {e}"], "converted": 0}

    decisions = strategy.get('open_questions')
    if not isinstance(decisions, list):
        return {"passed": False, "issues": ["open_questions 必须是数组"], "converted": 0}
    decision_map = strategy.get('decision_map') or {}
    fog = decision_map.get('not_yet_specified') or []
    if fog:
        return {"passed": False,
                "issues": ["not_yet_specified 未清，先把迷雾归入决策/intel_needs/out_of_scope"],
                "converted": 0}

    issues = []
    converted = 0
    for i, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            issues.append(f"open_questions[{i}] 必须是对象")
            continue
        status = decision.get('status')
        if status == 'open':
            assumption = decision.get('ai_assumption')
            if not isinstance(assumption, str) or not assumption.strip():
                issues.append(f"open_questions[{i}] 缺 ai_assumption，不能自动决策")
                continue
            decision['status'] = 'assumed'
            decision['resolved'] = assumption
            decision['assumption_risk'] = True
            converted += 1
        elif status == 'assumed':
            if (decision.get('resolved') != decision.get('ai_assumption')
                    or decision.get('assumption_risk') is not True):
                issues.append(f"open_questions[{i}] 的 assumed 状态不一致")
        elif status != 'resolved':
            issues.append(f"open_questions[{i}].status 非法: {status}")

    if issues:
        return {"passed": False, "issues": issues, "converted": 0}

    write_json_atomic(path, strategy)
    return {"passed": True, "issues": [], "converted": converted}


# ── detect-engine ───────────────────────────────────────────────────────────
def detect_engine():
    import urllib.request as _req
    probe_url = os.environ.get("PROPOSAL_SEARCH_PROBE_URL")
    if not probe_url:
        return {
            "engine": "none",
            "available": False,
            "hint": "set PROPOSAL_SEARCH_PROBE_URL to enable probing",
        }
    try:
        r = _req.Request(probe_url,
                         headers={"User-Agent": "Mozilla/5.0"}, method="GET")
        with _req.urlopen(r, timeout=5) as resp:
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


def _gate2_attestation(path):
    if not path:
        return {
            "passed": False, "attested": False,
            "issues": ["Gate 2 human disposition is not attested"],
        }
    try:
        document = read_json(path)
    except Exception as exc:
        return {"passed": False, "attested": False,
                "issues": [f"Gate 2 attestation unreadable: {exc}"]}
    open_causes = document.get('open_root_causes') or []
    schema_ok = document.get('schema_version') == 'gate2-decision/v1'
    passed = schema_ok and document.get('status') == 'resolved' and not open_causes
    return {
        "passed": passed, "attested": True,
        "status": document.get('status'),
        "open_root_causes": open_causes,
        "issues": [] if passed else [
            "Gate 2 schema/status is invalid or root causes remain unresolved"
        ],
        "path": os.path.abspath(path),
        "hash": prop_v3.file_hash(path),
    }


def validate_run(state_dir, report_path, mode='standard', lang='zh',
                 judgments_path=None, gate2_path=None, todo_output=None,
                 output_path=None):
    """Run the report-level acceptance stack once for one state/report pair."""
    state_dir = os.path.abspath(state_dir)
    report_path = os.path.abspath(report_path)
    requirements_path = os.path.join(state_dir, 'requirements.json')
    strategy_path = os.path.join(state_dir, 'strategy.json')
    intel_path = os.path.join(state_dir, 'intel-pool.json')
    realization_dir = os.path.join(state_dir, 'derived', 'realization')
    if not os.path.isfile(report_path):
        return {"passed": False, "issues": ["report does not exist"]}

    canonical = prop_v3.check_canonical(
        state_dir, stage='submission', realization_dir=realization_dir,
        write_derived=True)
    compliance = check_compliance(
        requirements_path, strategy_path, report_path)
    qa = qa_proposal(
        report_path, mode, strategy_path, lang, requirements_path, state_dir)
    compiled_judgments = None
    if judgments_path is None:
        compiled_judgments = prop_v3.compile_redteam_judgments(
            state_dir, report_path)
        if compiled_judgments.get('passed'):
            judgments_path = compiled_judgments.get('output_path')
    fit = prop_v3.customer_fit(
        state_dir, checkpoint='submission', judgments_path=judgments_path,
        realization_dir=realization_dir, checked_result=canonical,
        coverage_result=canonical.get('coverage'))
    if todo_output is None:
        todo_output = os.path.join(state_dir, 'derived', 'human-todo.md')
    todo = human_todo(
        requirements_path, strategy_path, report_path, mode, todo_output, lang,
        intel_path, state_dir, canonical_result=canonical)
    gate2 = _gate2_attestation(gate2_path)
    todo_clear = (todo.get('blocking_count', 0) == 0
                  and todo.get('assumption_count', 0) == 0
                  and todo.get('canonical_blocker_count', 0) == 0)
    component_passed = {
        "compliance": bool(compliance.get('passed')),
        "qa": bool(qa.get('passed')),
        "canonical_submission": bool(canonical.get('submission_ready')),
        "customer_fit": bool(fit.get('passed')),
        "human_todo_clear": todo_clear,
        "gate2": bool(gate2.get('passed')),
    }
    submission_ready = all(component_passed.values())
    result = {
        "schema_version": prop_v3.SCHEMA_VERSIONS['validation'],
        "passed": submission_ready,
        "submission_ready": submission_ready,
        "safe_draft_ready": bool(canonical.get('safe_draft_ready')),
        "state_hash": canonical.get('state_hash'),
        "report_hash": prop_v3.file_hash(report_path),
        "report_path": report_path,
        "component_passed": component_passed,
        "compliance": compliance,
        "qa": qa,
        "canonical": canonical,
        "customer_fit": fit.get('scorecard'),
        "customer_fit_judgments": compiled_judgments,
        "human_todo": todo,
        "gate2": gate2,
        "issues": [name for name, passed in component_passed.items()
                   if not passed],
    }
    if output_path is None:
        output_path = os.path.join(
            state_dir, 'derived', 'manifests', 'run-validation.json')
    write_json_atomic(output_path, result)
    result['output_path'] = os.path.abspath(output_path)
    return result


def finalize_run(state_dir, report_path, bundle_dir, mode='standard', lang='zh',
                 judgments_path=None, gate2_path=None, todo_output=None,
                 validation_output=None, receipt_output=None, allow_draft=False):
    """Validate, atomically archive, and issue a report/state-bound receipt."""
    validation = validate_run(
        state_dir, report_path, mode, lang, judgments_path, gate2_path,
        todo_output, validation_output)
    if not validation.get('state_hash') or not validation.get('report_hash'):
        return {
            "passed": False, "submission_ready": False,
            "issues": validation.get('issues') or
            ["validation did not produce state/report hashes"],
            "validation": validation,
        }
    if not validation.get('submission_ready') and not allow_draft:
        return {
            "passed": False, "submission_ready": False,
            "safe_draft_ready": validation.get('safe_draft_ready', False),
            "issues": validation.get('issues') or ["final validation failed"],
            "validation": validation,
        }
    canonical = validation.get('canonical') or {}
    archived = prop_v3.archive_state(
        state_dir, bundle_dir, require_submission_ready=not allow_draft,
        checked_result=canonical)
    delivery_status = ('submission_ready'
                       if validation.get('submission_ready') else 'draft_only')
    receipt = {
        "schema_version": prop_v3.SCHEMA_VERSIONS['receipt'],
        "state_hash": validation.get('state_hash'),
        "report_hash": validation.get('report_hash'),
        "validation_hash": prop_v3.content_hash({
            key: value for key, value in validation.items()
            if key != 'output_path'
        }),
        "delivery_status": delivery_status,
        "submission_ready": bool(validation.get('submission_ready')),
        "archive_passed": bool(archived.get('passed')),
        "archive_path": archived.get('state_archive'),
        "policy_version": prop_v3.POLICY_VERSION,
    }
    receipt['receipt_hash'] = prop_v3.content_hash(receipt)
    if receipt_output is None:
        receipt_output = os.path.join(
            os.path.abspath(bundle_dir), '_acceptance-receipt.json')
    if archived.get('passed'):
        write_json_atomic(receipt_output, receipt)
        archived_receipt = os.path.join(
            archived['state_archive'], 'derived', 'manifests',
            'acceptance-receipt.json')
        write_json_atomic(archived_receipt, receipt)
    return {
        "passed": bool(archived.get('passed')),
        "submission_ready": bool(validation.get('submission_ready')),
        "delivery_status": delivery_status,
        "issues": archived.get('issues') or [],
        "validation": validation,
        "archive": archived,
        "receipt": receipt,
        "receipt_output": (os.path.abspath(receipt_output)
                           if archived.get('passed') else None),
    }


# ── CLI ─────────────────────────────────────────────────────────────────────
def _print_result(result):
    print("PASS" if result.get('passed') else "FAIL")
    for iss in result.get('issues', []):
        print(f"  - {iss}")
    sys.exit(0 if result.get('passed') else 1)


def main():
    _init_stdout()
    parser = argparse.ArgumentParser(description='proposal tools 3.3 — comparative-strategy canonical/context/acceptance pipeline')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('check-encoding'); p.add_argument('file')
    p = sub.add_parser('word-count'); p.add_argument('file')
    p = sub.add_parser('json-validate'); p.add_argument('file')
    p = sub.add_parser('json-get'); p.add_argument('file'); p.add_argument('key_path')
    p = sub.add_parser('check-requirements'); p.add_argument('file')
    p = sub.add_parser('check-strategy')
    p.add_argument('file')
    p.add_argument('--mode', default=None, choices=['quick', 'standard', 'deep'])
    p.add_argument('--require-settled', action='store_true')
    p.add_argument('--auto', action='store_true', help='允许 assumed 决策（仅 -auto 流程）')
    p = sub.add_parser('apply-auto-decisions'); p.add_argument('file')
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
    p.add_argument('--auto', action='store_true', help='允许已留痕的 assumed 决策')

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
    p.add_argument('--requirements', default=None)
    p.add_argument('--lang', default='zh')
    p.add_argument('--state-dir', default=None)

    p = sub.add_parser('human-todo')
    p.add_argument('--requirements', required=True)
    p.add_argument('--strategy', required=True)
    p.add_argument('--report', required=True)
    p.add_argument('--mode', default='standard', choices=['quick', 'standard', 'deep'])
    p.add_argument('--output', required=True)
    p.add_argument('--lang', default='zh')
    p.add_argument('--intel', default=None)
    p.add_argument('--state-dir', default=None)

    for command in ('validate-run', 'finalize-run'):
        p = sub.add_parser(command)
        p.add_argument('--state-dir', required=True)
        p.add_argument('--report', required=True)
        p.add_argument('--mode', default='standard',
                       choices=['quick', 'standard', 'deep'])
        p.add_argument('--lang', default='zh')
        p.add_argument('--judgments', default=None)
        p.add_argument('--gate2', default=None)
        p.add_argument('--todo-output', default=None)
        p.add_argument('--validation-output', default=None)
        if command == 'finalize-run':
            p.add_argument('--bundle-dir', required=True)
            p.add_argument('--receipt-output', default=None)
            p.add_argument('--allow-draft', action='store_true')

    # v3 is the default pipeline.  Historic commands remain available for the
    # explicit ``-legacy`` workflow and for old bundle maintenance.
    prop_v3.add_cli_parsers(sub)

    args = parser.parse_args()

    v3_exit = prop_v3.dispatch_cli(args)
    if v3_exit is not None:
        sys.exit(v3_exit)

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
    elif args.command == 'check-strategy':
        r = check_strategy(args.file, args.mode, args.require_settled, args.auto)
        print("DECISIONS: "
              f"total={r.get('decision_count', 0)} resolved={r.get('resolved_count', 0)} "
              f"assumed={r.get('assumed_count', 0)} open={r.get('open_count', 0)} "
              f"fog={r.get('fog_count', 0)}")
        print("FRONTIER: " + (" | ".join(r.get('frontier') or []) or "-"))
        print("BLOCKED: " + (" | ".join(r.get('blocked') or []) or "-"))
        _print_result(r)
    elif args.command == 'apply-auto-decisions':
        r = apply_auto_decisions(args.file)
        print(f"AUTO_DECISIONS: converted={r.get('converted', 0)}")
        _print_result(r)
    elif args.command == 'detect-engine':
        print(json.dumps(detect_engine(), ensure_ascii=False)); sys.exit(0)
    elif args.command == 'escape-currency':
        r = escape_currency(args.report)
        print(f"Escaped {r['changes']} dollar signs in: {args.report}"); sys.exit(0)
    elif args.command == 'assemble-proposal':
        r = assemble_proposal(args.strategy, args.requirements, args.intel,
                              args.sections_dir, args.mode, args.output, args.lang, args.auto)
        if r['passed']:
            print(f"Proposal assembled: {r['output_path']}")
            print(f"BundleDir: {r['bundle_dir']}")
            print(f"InternalBrief: {r['internal_brief']}")
            print(f"({r['line_count']} lines, {r['chapter_count']} chapters, {r['part_count']} parts, "
                  f"{r['word_count']} chars, exec_summary={'yes' if r['exec_summary'] else 'no'})")
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
        r = qa_proposal(args.report, args.mode, args.strategy, args.lang,
                        args.requirements, args.state_dir)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0 if r['passed'] else 1)
    elif args.command == 'human-todo':
        r = human_todo(args.requirements, args.strategy, args.report,
                       args.mode, args.output, args.lang, args.intel, args.state_dir)
        print(f"HUMANTODO: blocking={r['blocking_count']} scoring={r['scoring_count']} "
              f"assumptions={r['assumption_count']} intel_gaps={r['intel_gap_count']} "
              f"weak={r['weak_count']} canonical_blockers={r['canonical_blocker_count']} "
              f"canonical_major={r['canonical_major_count']} -> {r['output_path']}")
        sys.exit(0)
    elif args.command == 'validate-run':
        r = validate_run(
            args.state_dir, args.report, args.mode, args.lang, args.judgments,
            args.gate2, args.todo_output, args.validation_output)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0 if r.get('passed') else 1)
    elif args.command == 'finalize-run':
        r = finalize_run(
            args.state_dir, args.report, args.bundle_dir, args.mode, args.lang,
            args.judgments, args.gate2, args.todo_output,
            args.validation_output, args.receipt_output, args.allow_draft)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0 if r.get('passed') else 1)


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
