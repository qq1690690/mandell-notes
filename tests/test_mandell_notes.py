"""針對純函式的最小測試，不需金鑰、不碰網路，可直接在 CI 跑。

    pytest
"""
from mandell_notes import _clean_text, md_to_blocks


def test_clean_text_removes_boilerplate():
    raw = (
        "Mellow Yellow 6/12/2026\n"
        "Definition Acute laryngitis is a clinical syndrome.\n"
        "Side Notes\n"
        "PRINTED BY: qq1690690@gmail.com. Printing of Notes and Highlights is "
        "for personal, private use only. Notes created by user are not part of "
        "publisher content. No part of this book may be reproduced or transmitted "
        "without publisher's prior permission. Violators will be prosecuted.\n"
        "2026/6/12 上午 10:28 Highlights & Notes: Mandell, Douglas, and Bennett's "
        "Principles and Practice of Infectious Diseases\n"
        "about:blank 1/1"
    )
    out = _clean_text(raw)
    assert "Acute laryngitis is a clinical syndrome." in out
    # 雜訊全部清掉
    assert "PRINTED BY" not in out
    assert "qq1690690" not in out
    assert "about:blank" not in out
    assert "Mellow Yellow" not in out
    assert "Highlights & Notes:" not in out


def test_md_to_blocks_types():
    md = "## Overview\n- 重點一\n一般段落"
    blocks = md_to_blocks(md)
    types = [b["type"] for b in blocks]
    assert types == ["heading_2", "bulleted_list_item", "paragraph"]


def test_md_to_blocks_bold():
    blocks = md_to_blocks("這是 **重點** 字")
    spans = blocks[0]["paragraph"]["rich_text"]
    assert any(s["annotations"]["bold"] and s["text"]["content"] == "重點" for s in spans)
