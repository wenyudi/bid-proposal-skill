"""Task 0 摄入测试：路由矩阵、本地解析器、API 响应解析、离线 ingest 全流程。全部离线，不打真实 API。"""

import json
import os
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import prop_ingest as pi  # noqa: E402


def _make_docx(path, text="第一段甲方需求。"):
    xml = (f'<?xml version="1.0"?><w:document xmlns:w="x"><w:body>'
           f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>'
           f'<w:p><w:r><w:t>第二段：预算 90 万。</w:t></w:r></w:p></w:body></w:document>')
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", xml)


def _make_pptx(path):
    slide = ('<?xml version="1.0"?><p:sld xmlns:a="x" xmlns:p="y">'
             '<a:t>标题：入围方案</a:t><a:t>要点一</a:t></p:sld>')
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("ppt/slides/slide1.xml", slide)
        zf.writestr("ppt/slides/slide2.xml", '<p:sld xmlns:a="x"><a:t>第二页</a:t></p:sld>')


class RouteTests(unittest.TestCase):
    def test_matrix(self):
        R = pi.route_file
        self.assertEqual(R(".md", False, False), "direct")
        self.assertEqual(R(".docx", False, False), "local")
        self.assertEqual(R(".pdf", True, True), "pdftotext")
        self.assertEqual(R(".pdf", True, True, pdf_scanned=True), "baidu")  # 百度本地上传已验证，优先
        self.assertEqual(R(".pdf", True, False, pdf_scanned=True), "mineru")
        self.assertEqual(R(".pdf", False, True, pdf_scanned=True), "baidu")
        self.assertEqual(R(".pdf", False, False, pdf_scanned=True), "manual")
        self.assertEqual(R(".doc", True, True), "mineru")
        self.assertEqual(R(".doc", False, True), "manual")
        self.assertEqual(R(".jpg", True, True), "baidu")
        self.assertEqual(R(".jpg", True, False), "mineru")
        self.assertEqual(R(".jpg", False, False), "vision")
        self.assertEqual(R(".exe", True, True), "skip")


class LocalExtractTests(unittest.TestCase):
    def test_docx(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.docx")
            _make_docx(p)
            t = pi.extract_docx(p)
            self.assertIn("第一段甲方需求", t)
            self.assertIn("预算 90 万", t)
            self.assertIn("\n", t)  # 段落成行

    def test_pptx(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.pptx")
            _make_pptx(p)
            t = pi.extract_pptx(p)
            self.assertIn("入围方案", t)
            self.assertIn("第 2 页", t)

    def test_scanned_heuristic(self):
        self.assertTrue(pi.is_scanned_pdf_text("  \n x \n"))
        self.assertFalse(pi.is_scanned_pdf_text("有效文字" * 200))


class ParserTests(unittest.TestCase):
    def test_mineru_batch_result(self):
        resp = {"code": 0, "data": {"extract_result": [
            {"file_name": "a.doc", "state": "done", "full_zip_url": "https://x/z.zip"},
            {"file_name": "b.pdf", "state": "failed", "err_msg": "页数超限"},
        ]}}
        out = pi.parse_mineru_batch_result(resp)
        self.assertEqual(out["a.doc"]["state"], "done")
        self.assertEqual(out["b.pdf"]["err_msg"], "页数超限")

    def test_baidu_jsonl(self):
        jsonl = "\n".join([
            json.dumps({"result": {"layoutParsingResults": [{"markdown": {"text": "第一页文字"}}]}}),
            json.dumps({"result": {"layoutParsingResults": [{"markdown": {"text": "第二页文字"}}]}}),
        ])
        t = pi.parse_baidu_jsonl(jsonl)
        self.assertIn("第一页文字", t)
        self.assertIn("第二页文字", t)

    def test_multipart_body(self):
        body, boundary = pi._multipart({"model": "M"}, "证书.jpg", b"\xff\xd8bytes")
        self.assertIn(boundary.encode(), body)
        self.assertIn("证书.jpg".encode(), body)
        self.assertIn(b"\xff\xd8bytes", body)
        self.assertTrue(body.endswith(f"--{boundary}--\r\n".encode()))


class IngestOfflineTests(unittest.TestCase):
    def test_end_to_end_ocr_off(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            with open(os.path.join(src, "brief.md"), "w", encoding="utf-8") as f:
                f.write("# 标书\n预算 90 万")
            _make_docx(os.path.join(src, "资质.docx"))
            _make_pptx(os.path.join(src, "过往方案.pptx"))
            open(os.path.join(src, "老合同.doc"), "wb").write(b"\xd0\xcf\x11\xe0old")
            open(os.path.join(src, "现场.jpg"), "wb").write(b"\xff\xd8\xffjpg")
            res = pi.ingest(src, out, ocr="off")
            self.assertTrue(res["passed"])
            self.assertEqual(res["files"], 5)
            self.assertIn("老合同.doc", res["needs_manual"][0])
            manifest = open(os.path.join(out, "manifest.md"), encoding="utf-8").read()
            self.assertIn("直读", manifest)
            self.assertIn("已转换·本地", manifest)
            self.assertIn("须人工转换", manifest)
            self.assertIn("视觉直读", manifest)
            # 转换产物真实存在且含内容
            arts = [n for n in os.listdir(out) if n.endswith(".md") and n != "manifest.md"]
            self.assertEqual(len(arts), 2)  # docx + pptx


if __name__ == "__main__":
    unittest.main()
