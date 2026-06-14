"""Mandell 讀書筆記工具：把 Bookshelf 匯出的重點 → Gemini 結構化整理 → Notion。

設計：
- 純函式（_clean_text / md_to_blocks）不依賴任何金鑰或網路，可單獨測試。
- 需要 Gemini / Notion 用戶端的 I/O 都包在 MandellNotes 類別裡，金鑰由環境變數帶入。
"""
from __future__ import annotations

import os
import re

SYSTEM_PROMPT = """你是一位資深感染科主治醫師，正在閱讀 Mandell's Principles and Practice of Infectious Diseases。
使用者會提供從電子書匯出的重點文字。請依下列格式整理成結構化中文筆記：

## Overview
（2-3句話概述本節重點）

## Pathogen / Etiology
（病原體、分類、特性）

## Pathophysiology
（致病機轉、宿主反應）

## Clinical Presentation
（症狀、體徵、典型與非典型表現）

## Diagnosis
（診斷方式、檢驗、影像、判讀重點）

## Treatment
（藥物選擇、劑量原則、療程、特殊情況）

## Key Pearls
（3-5個臨床重點，考試或臨床最常用到的）

規則：
- 只根據提供的原文整理，原文未涵蓋的 section 標記「原文未涵蓋」，勿自行補充。
- 專有名詞（菌名、藥名、檢驗）保留英文，其餘用繁體中文。
- 只輸出筆記本身，不要加開場白或結語。"""


# ---------------------------------------------------------------------------
# 純函式（無金鑰、無網路，可單獨測試）
# ---------------------------------------------------------------------------
_BOILERPLATE_PATTERNS = [
    r"PRINTED BY:.*?Violators will be prosecuted\.",                                  # 版權聲明
    r"\d{4}/\d{1,2}/\d{1,2}\s*[上下]午\s*\d{1,2}:\d{2}\s*Highlights & Notes:.*",        # 時間戳 + 書名
    r"about:blank\s*\d+/\d+",                                                          # 頁碼
    r"^.*?\d{1,2}/\d{1,2}/\d{4}\s*\n",                                                 # 開頭使用者名 + 日期
    r"\n\s*Side Notes\s*\n",                                                           # 空的 Side Notes 標頭
]


def _clean_text(raw: str) -> str:
    """清掉 Bookshelf 匯出 PDF 的頁首/頁尾雜訊。純字串處理，方便測試。"""
    text = raw
    for pat in _BOILERPLATE_PATTERNS:
        text = re.sub(pat, "\n", text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def extract_clean_pdf(path: str) -> str:
    """讀取 PDF 真文字並清理。需要 pypdf。"""
    from pypdf import PdfReader

    reader = PdfReader(path)
    raw = "\n".join((page.extract_text() or "") for page in reader.pages)
    return _clean_text(raw)


def _rich_text(text: str) -> list:
    """把含 **bold** 的一行轉成 Notion rich_text（支援粗體、切到 2000 字）。"""
    out = []
    for tok in re.split(r"(\*\*[^*]+\*\*)", text):
        if not tok:
            continue
        bold = tok.startswith("**") and tok.endswith("**")
        content = tok[2:-2] if bold else tok
        for i in range(0, len(content), 2000):
            out.append({
                "type": "text",
                "text": {"content": content[i:i + 2000]},
                "annotations": {"bold": bold},
            })
    return out or [{"type": "text", "text": {"content": text[:2000]}}]


def md_to_blocks(md: str) -> list:
    """markdown 筆記 → Notion blocks。純函式。"""
    blocks = []
    for line in md.split("\n"):
        s = line.rstrip()
        if not s.strip():
            continue
        if s.startswith("### "):
            t, body = "heading_3", s[4:]
        elif s.startswith("## "):
            t, body = "heading_2", s[3:]
        elif s.startswith("# "):
            t, body = "heading_1", s[2:]
        elif s.lstrip().startswith(("- ", "* ")):
            t, body = "bulleted_list_item", s.lstrip()[2:]
        elif re.match(r"^\d+\.\s", s.lstrip()):
            t, body = "numbered_list_item", re.sub(r"^\d+\.\s", "", s.lstrip())
        else:
            t, body = "paragraph", s
        blocks.append({"object": "block", "type": t, t: {"rich_text": _rich_text(body)}})
    return blocks


# ---------------------------------------------------------------------------
# 需要金鑰 / 網路的 I/O
# ---------------------------------------------------------------------------
class MandellNotes:
    """包住 Gemini 與 Notion 用戶端的主要工具。"""

    def __init__(self, gemini_api_key: str, notion_token: str,
                 notion_database_id: str, model: str = "gemini-2.5-flash"):
        from google import genai
        from notion_client import Client

        self.gemini = genai.Client(api_key=gemini_api_key)
        self.notion = Client(auth=notion_token)
        self.model = model
        # 新版 Notion API：查詢/建頁改用 data source
        db = self.notion.databases.retrieve(database_id=notion_database_id)
        self.data_source_id = db["data_sources"][0]["id"]

    @classmethod
    def from_env(cls) -> "MandellNotes":
        """從環境變數建立（若有 .env 會自動載入）。"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        return cls(
            gemini_api_key=os.environ["GEMINI_API_KEY"],
            notion_token=os.environ["NOTION_TOKEN"],
            notion_database_id=os.environ["NOTION_DATABASE_ID"],
        )

    # ---- 產生筆記 ----
    def notes_from_text(self, title: str, raw_text: str) -> str:
        resp = self.gemini.models.generate_content(
            model=self.model,
            contents=f"{SYSTEM_PROMPT}\n\n章節：{title}\n\n原文：\n{raw_text}",
        )
        return resp.text

    def notes_from_pdf(self, title: str, pdf_path: str) -> str:
        return self.notes_from_text(title, extract_clean_pdf(pdf_path))

    def notes_from_images(self, title: str, image_paths: list) -> str:
        from PIL import Image

        images = [Image.open(p) for p in image_paths]
        contents = [
            f"{SYSTEM_PROMPT}\n\n章節：{title}\n\n以下是教科書頁面截圖，請先完整讀出文字再整理："
        ] + images
        resp = self.gemini.models.generate_content(model=self.model, contents=contents)
        return resp.text

    # ---- 寫入 Notion ----
    def _append_chunked(self, page_id: str, blocks: list) -> None:
        for i in range(0, len(blocks), 100):
            self.notion.blocks.children.append(block_id=page_id, children=blocks[i:i + 100])

    def save(self, title: str, notes_md: str) -> str:
        blocks = md_to_blocks(notes_md)
        results = self.notion.data_sources.query(
            data_source_id=self.data_source_id,
            filter={"property": "title", "title": {"equals": title}},
        )
        if results["results"]:
            page_id = results["results"][0]["id"]
            self._append_chunked(page_id, [{"object": "block", "type": "divider", "divider": {}}])
            self._append_chunked(page_id, blocks)
        else:
            resp = self.notion.pages.create(
                parent={"type": "data_source_id", "data_source_id": self.data_source_id},
                properties={"title": {"title": [{"text": {"content": title}}]}},
                children=blocks[:100],
            )
            page_id = resp["id"]
            if len(blocks) > 100:
                self._append_chunked(page_id, blocks[100:])
        return "https://www.notion.so/" + page_id.replace("-", "")
