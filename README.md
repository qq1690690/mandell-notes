# mandell-notes

把 VitalSource Bookshelf 匯出的 Mandell 讀書重點，用 Gemini 依感染科模板整理成結構化筆記，自動寫入 Notion。

## 結構

```
mandell-notes/
├── mandell_notes.py     # 核心模組：抽取/清理/整理/寫入（純函式與 I/O 分離）
├── run.py               # 命令列入口
├── mandell_colab.ipynb  # Colab 薄入口（拉本 repo → 呼叫模組）
├── requirements.txt
├── .env.example         # 環境變數範本（複製成 .env 填入）
├── .gitignore           # 擋掉金鑰與匯出的書本內容
└── tests/               # 純函式測試，pytest 可直接跑
```

## 設定

三個金鑰透過環境變數帶入，**不寫進程式碼**：

```bash
cp .env.example .env   # 編輯 .env 填入你的值
```

| 變數 | 說明 |
| --- | --- |
| `GEMINI_API_KEY` | Google AI Studio 的 API key |
| `NOTION_TOKEN` | Notion integration token |
| `NOTION_DATABASE_ID` | 目標資料庫 ID（需把 integration 加進該資料庫的 Connections） |

## 使用

本機：

```bash
pip install -r requirements.txt
python run.py --title "Chapter 62 Acute Laryngitis" --pdf laryngitis.pdf
python run.py --title "Chapter 62" --pdf laryngitis.pdf --dry-run   # 只看整理結果，不寫入
python run.py --title "Chapter 62" --images p1.png p2.png            # fixed-layout 改用截圖
```

Colab：把 `mandell_colab.ipynb` 裡的 `USER/REPO` 換成自己的 repo，用左側鑰匙設好三個 secret，跑下去即可。
（小技巧：notebook 的 GitHub 網址把 `github.com` 換成 `githubtocolab.com` 可直接在 Colab 開啟。）

測試：

```bash
pytest
```

## 注意

- 僅供個人讀書整理小段落，請勿系統性匯出全書。
- 匯出的 PDF / 截圖、`.env` 都已被 `.gitignore` 擋住，避免版權內容或金鑰進版控。
