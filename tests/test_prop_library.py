"""方案库工具测试：索引、检索、抽取缓存。"""

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import prop_library  # noqa: E402
import prop_tools  # noqa: E402


def _touch(path, content="正文内容示例。" * 5):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class Args:
    def __init__(self, **kw):
        self.src = None
        self.index_dir = None
        self.config = "/nonexistent-config.json"
        for k, v in kw.items():
            setattr(self, k, v)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = self.tmp.name
        _touch(os.path.join(self.src, "2024项目/某银行发布会活动执行方案2024.pdf"))
        _touch(os.path.join(self.src, "2024项目/某文旅宣传片创意脚本方案.pptx"))
        _touch(os.path.join(self.src, "旧档/展厅空间设计深化2019.pdf"))
        _touch(os.path.join(self.src, "旧档/无关表格.xlsx"))
        _touch(os.path.join(self.src, "杂项/抖音代运营增长方案2025.txt"))
        res = prop_library.cmd_index(Args(src=self.src))
        self.assertTrue(res["passed"], res)
        self.index_dir = os.path.join(self.src, prop_library.INDEX_DIRNAME)

    def tearDown(self):
        self.tmp.cleanup()

    def test_index_counts_and_sector_guess(self):
        idx = json.load(open(os.path.join(self.index_dir, "index.json"), encoding="utf-8"))
        self.assertEqual(len(idx["files"]), 4)  # xlsx 被跳过
        by_name = {e["name"]: e for e in idx["files"]}
        self.assertIn("event", by_name["某银行发布会活动执行方案2024.pdf"]["sectors"])
        self.assertIn("video", by_name["某文旅宣传片创意脚本方案.pptx"]["sectors"])
        self.assertIn("space-design", by_name["展厅空间设计深化2019.pdf"]["sectors"])
        self.assertEqual(by_name["某银行发布会活动执行方案2024.pdf"]["year"], "2024")
        self.assertTrue(os.path.exists(os.path.join(self.index_dir, "manifest.md")))

    def test_search_by_query_and_sector(self):
        res = prop_library.cmd_search(Args(src=self.src, query="发布会 银行", sector=None,
                                           year_min=None, top=5))
        self.assertTrue(res["passed"])
        self.assertEqual(res["hits"][0]["name"], "某银行发布会活动执行方案2024.pdf")
        res2 = prop_library.cmd_search(Args(src=self.src, query="方案", sector="video",
                                            year_min=None, top=5))
        self.assertTrue(all("video" in h["sectors"] for h in res2["hits"]))

    def test_search_prefers_carded(self):
        idx = json.load(open(os.path.join(self.index_dir, "index.json"), encoding="utf-8"))
        target = next(e for e in idx["files"] if e["ext"] == ".txt")
        _touch(os.path.join(self.index_dir, "cards", target["id"] + ".md"), "# 方案卡")
        res = prop_library.cmd_search(Args(src=self.src, query="方案", sector=None,
                                           year_min=None, top=5))
        self.assertEqual(res["hits"][0]["id"], target["id"])
        self.assertIsNotNone(res["hits"][0]["card"])

    def test_extract_and_cache(self):
        args = Args(src=self.src, file="杂项/抖音代运营增长方案2025.txt",
                    ocr="off", timeout=60, force=False)
        res = prop_library.cmd_extract(args)
        self.assertTrue(res["passed"], res)
        self.assertFalse(res["cached"])
        self.assertTrue(res["files"])
        res2 = prop_library.cmd_extract(args)
        self.assertTrue(res2["cached"])

    def test_extract_unknown_file_fails(self):
        res = prop_library.cmd_extract(Args(src=self.src, file="不存在.pdf",
                                            ocr="off", timeout=60, force=False))
        self.assertFalse(res["passed"])

    def test_pages_render_and_cache(self):
        orig = prop_library._render_pdf_pages

        def fake_render(pdf, out_dir, first=None, last=None, dpi=100):
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, "page-01.png"), "wb") as f:
                f.write(b"PNG")
            return ["page-01.png"]

        prop_library._render_pdf_pages = fake_render
        try:
            a = Args(src=self.src, file="旧档/展厅空间设计深化2019.pdf",
                     first=None, last=None, dpi=100, force=False)
            res = prop_library.cmd_pages(a)
            self.assertTrue(res["passed"], res)
            self.assertEqual(res["pages"], 1)
            self.assertFalse(res["cached"])
            res2 = prop_library.cmd_pages(a)
            self.assertTrue(res2["cached"])
        finally:
            prop_library._render_pdf_pages = orig

    def test_cli_wiring_via_prop_tools(self):
        rc = prop_tools.main(["library-status", "--src", self.src,
                              "--config", "/nonexistent-config.json"])
        self.assertEqual(rc, 0)


def _make_pptx(path, texts):
    import zipfile
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for i, t in enumerate(texts, 1):
            zf.writestr(f"ppt/slides/slide{i}.xml",
                        f'<p:sld xmlns:a="x"><a:t>{t}</a:t></p:sld>')


class ConvertArgs:
    def __init__(self, **kw):
        self.src = None
        self.out = None
        self.config = "/nonexistent-config.json"
        self.ocr = "off"
        self.limit = 0
        self.timeout = 60
        self.force = False
        for k, v in kw.items():
            setattr(self, k, v)


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = os.path.join(self.tmp.name, "库")
        self.out = os.path.join(self.tmp.name, "库-md")
        _touch(os.path.join(self.src, "a/活动方案.txt"), "活动执行正文。")
        _make_pptx(os.path.join(self.src, "a/发布会提案.pptx"), ["主标题页", "预算页"])
        _touch(os.path.join(self.src, "b/扫描件.pdf"), "%PDF-1.4 garbage")  # 无文字层→needs_ocr
        _touch(os.path.join(self.src, "b/老格式.ppt"), "binary")  # 无 LibreOffice→needs_ocr

    def tearDown(self):
        self.tmp.cleanup()

    def test_local_convert_and_ocr_gap(self):
        res = prop_library.cmd_convert(ConvertArgs(src=self.src, out=self.out))
        self.assertTrue(res["passed"], res)
        self.assertEqual(res["converted"], 2)
        self.assertEqual(res["queued_ocr"], 2)
        md = open(os.path.join(self.out, "a/发布会提案.pptx.md"), encoding="utf-8").read()
        self.assertIn("主标题页", md)
        self.assertIn("来源：a/发布会提案.pptx", md)

    def test_resume_uses_cache(self):
        prop_library.cmd_convert(ConvertArgs(src=self.src, out=self.out))
        res2 = prop_library.cmd_convert(ConvertArgs(src=self.src, out=self.out))
        self.assertEqual(res2["cached"], 2)
        self.assertEqual(res2["converted"], 0)
        self.assertEqual(res2["queued_ocr"], 2)  # 缺口保持在册，不重复本地尝试

    def test_limit_chunks_run(self):
        res = prop_library.cmd_convert(ConvertArgs(src=self.src, out=self.out, limit=1))
        self.assertEqual(res["converted"] + res["queued_ocr"], 1)

    def test_content_sector_guess_for_md(self):
        src = os.path.join(self.tmp.name, "内容库")
        _touch(os.path.join(src, "某客户年度合作.md"),
               "抖音矩阵与小红书代运营为主，抖音投放与直播增长并行。")
        res = prop_library.cmd_index(Args(src=src))
        self.assertTrue(res["passed"])
        idx = json.load(open(os.path.join(src, prop_library.INDEX_DIRNAME, "index.json"),
                             encoding="utf-8"))
        e = idx["files"][0]
        self.assertIn("social-media", e["sectors"])
        self.assertEqual(e["sector_from"], "content")

    def test_converted_md_tree_is_indexable(self):
        prop_library.cmd_convert(ConvertArgs(src=self.src, out=self.out))
        res = prop_library.cmd_index(Args(src=self.out))
        self.assertTrue(res["passed"])
        hits = prop_library.cmd_search(Args(src=self.out, query="发布会", sector=None,
                                            year_min=None, top=3))["hits"]
        self.assertTrue(hits and hits[0]["name"].endswith(".pptx.md"))


if __name__ == "__main__":
    unittest.main()
