"""薄入口：本機命令列使用。

範例：
    python run.py --title "Chapter 62 Acute Laryngitis" --pdf laryngitis.pdf
    python run.py --title "Chapter 62" --pdf laryngitis.pdf --dry-run
    python run.py --title "Chapter 62" --images p1.png p2.png
"""
import argparse

from mandell_notes import MandellNotes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mandell 重點 → Gemini 整理 → Notion")
    parser.add_argument("--title", required=True, help="Notion 頁面標題（章節名）")
    parser.add_argument("--pdf", help="Bookshelf 匯出的 PDF 路徑")
    parser.add_argument("--images", nargs="+", help="截圖路徑（可多張）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只印出整理結果，不寫入 Notion")
    args = parser.parse_args()

    if not args.pdf and not args.images:
        parser.error("請提供 --pdf 或 --images 其中一種輸入")

    app = MandellNotes.from_env()

    if args.pdf:
        notes = app.notes_from_pdf(args.title, args.pdf)
    else:
        notes = app.notes_from_images(args.title, args.images)

    print("===== 整理結果 =====\n")
    print(notes)

    if args.dry_run:
        print("\n[dry-run] 未寫入 Notion")
    else:
        url = app.save(args.title, notes)
        print(f"\n完成 → {url}")


if __name__ == "__main__":
    main()
