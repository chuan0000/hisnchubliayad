# 國際佛光會新竹青年分團 - 動態成果管理系統 (BLIA Hsinchu Youth CMS)

一套專為道場實體個人電腦（Windows / macOS / Linux）設計的高效、全動態化成果展示與 CMS 管理系統。

---

## 🌟 系統核心特色

1. **完全動態化（CMS 架構）**：
   - 網站上的所有文字、看版統計數字、四大宗旨（文化/教育/共修/慈善）佐證清單、幹部團隊名冊、健康跑步打卡記錄、即時跑馬燈公告與頂部 Banner，均**不寫死在程式碼中**。
   - 所有內容均可在後台 CMS 視覺化介面即時新增、修改、刪除（CRUD），前台即刻同步呈現。

2. **本地存儲與零依賴備份（SQLite + ./uploads）**：
   - **文字與資料庫**：全數存於單一 `hsinchu_youth.db` 檔案中。幹部或評鑑秘書若需備份，**直接拷貝該 .db 檔案至隨身碟或雲端硬碟即可完成 100% 備份**。
   - **佐證檔案與照片**：自動歸檔於專案目錄下的 `./uploads` 資料夾，前台可直接線上調閱預覽，後台亦支援隨時下載回個人電腦。

3. **使用者權限控管（RBAC 角色劃分）**：
   - **訪客（青年/社會大眾）**：免登入瀏覽前台成果庫、檢視四大宗旨活動公文/照片、查看 VEGRUN 健康打卡紀錄、直接登記個人打卡。
   - **活動幹部 (cadre)**：登入後可登記活動成果、上傳活動照片與 PDF 佐證、管理打卡紀錄。
   - **超級管理員 (super_admin - 分團長/評鑑秘書)**：具備最高權限，可修改全站所有動態區塊、自訂首頁看板數字、調整幹部名單排序、開設或停用幹部帳號與重設密碼。

4. **超輕量現代技術棧**：
   - **後端**：Python FastAPI + SQLite（內建自動 Swagger API 互動文件，效能極高）。
   - **前台與後台**：原生 HTML5 + Tailwind CSS + Vue 3（CDN 模式），**無需 Node.js、NPM 或 Webpack 複雜前端編譯鏈**，打開終端機單一命令即可運作。

---

## 📁 系統目錄結構樹

```text
hsinchu_youth_cms/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 核心入口、靜態檔案掛載、CORS 與路由聚合
│   ├── config.py            # 全域設定 (JWT Secret、本地資料庫路徑、上傳目錄)
│   ├── database.py          # SQLite 資料庫連接引擎與 Session 依賴
│   ├── models.py            # 5 大資料庫模型 (User, SiteBlock, EvidenceItem, TeamMember, HealthLog)
│   ├── schemas.py           # Pydantic 資料驗證與序列化 Schema
│   ├── auth.py              # PBKDF2 安全密碼雜湊、JWT 簽章與 RBAC 權限驗證中介軟體
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # 使用者認證與幹部帳號管理 API
│   │   ├── blocks.py        # 全站區塊動態內容 (Key-Value CMS) API
│   │   ├── evidence.py      # 四大宗旨活動佐證資料 (CRUD) API
│   │   ├── health.py        # VEGRUN 健走跑步打卡 API
│   │   ├── team.py          # 幹部團隊名冊 API
│   │   └── upload.py        # 佐證照片與 PDF 公文本機上傳與調閱 API
│   └── static/
│       ├── index.html       # 前台首頁 (Vue 3 + Tailwind CSS CDN, 四大宗旨展示、看板、打卡)
│       └── admin.html       # 後台管理儀表板 (Vue 3 + Tailwind CSS CDN, 視覺化區塊編輯、檔案管理)
├── uploads/                 # 本機佐證檔案與照片儲存庫 (PDF、JPG、PNG)
├── init_db.py               # 資料庫初始化與預設新竹青年分團成果示範種子腳本
├── requirements.txt         # Python 依賴清單
├── run.bat                  # Windows 系統一鍵啟動腳本
├── run.sh                   # macOS / Linux 系統一鍵啟動腳本
└── README.md                # 系統部署與維護操作指南
```

---

## 🛠️ 環境需求與安裝指南

### 1. 必備軟體
- **Python 3.9 或以上版本**（建議 3.10 ~ 3.12）。
  - Windows 使用者安裝時，**請務必勾選「Add Python to PATH」**。
- 一台可上網下載套件的個人電腦（Windows / macOS / Linux 皆可）。

---

## 🚀 啟動方式

### 【方案 A：一鍵快速啟動（推薦）】
- **Windows**：直接雙擊執行目錄下的 `run.bat`。
- **macOS / Linux**：
  在終端機進入該目錄並執行：
  ```bash
  chmod +x run.sh
  ./run.sh
  ```
腳本將自動建立虛擬環境、安裝套件、初始化示範資料庫並啟動伺服器。

---

### 【方案 B：手動指令啟動】

1. **開啟終端機（命令提示字元 / Terminal）並進入專案目錄**：
   ```bash
   cd hsinchu_youth_cms
   ```

2. **建立並啟用 Python 虛擬環境**：
   - Windows:
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```
   - macOS / Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **安裝依賴套件**：
   ```bash
   pip install -r requirements.txt
   ```

4. **初始化資料庫與新竹分團示範資料**：
   ```bash
   python init_db.py
   ```

5. **啟動 FastAPI 服務**：
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 
   ```

---

## 🌐 系統訪問網址與預設帳號

啟動完成後，請使用瀏覽器（Chrome、Edge、Safari）開啟：

- **前台成果展示首頁**：[http://localhost:8000](http://localhost:8000)
- **後台 CMS 管理系統**：[http://localhost:8000/admin](http://localhost:8000/admin)
- **FastAPI 官方 Swagger 互動式 API 文件**：[http://localhost:8000/docs](http://localhost:8000/docs)

### 預設管理員與幹部登入資訊
| 角色 | 登入帳號 | 預設密碼 | 權限範圍 |
| :--- | :--- | :--- | :--- |
| **超級管理員 (分團長/評鑑秘書)** | `admin` | `xxxxxxxx` | 具備全站最高權限：可修改首頁所有標題、看板數字、公告開關、幹部帳號開設與密碼重設 |
| **活動幹部 (活動總召)** | `cadre` | `xxxxxxxx` | 可上傳四大宗旨佐證照片與 PDF 公文、管理健康打卡紀錄 |

> 💡 **安全提示**：首次登入後，請至後台「帳號權限管理 (RBAC)」修改預設密碼。

---

## 💾 資料庫備份與資料遷移

- **SQLite 資料庫備份**：
  直接拷貝專案根目錄下的 `hsinchu_youth.db` 檔案，即可備份所有使用者、全站文字設定、四大宗旨佐證記錄與打卡數據。
- **附件檔案備份**：
  直接拷貝 `./uploads` 資料夾，即可備份所有活動照片與 PDF 公文。
- **還原系統**：
  在新電腦上安裝好環境後，將備份的 `hsinchu_youth.db` 與 `uploads` 資料夾覆蓋至相同目錄，啟動即可無縫轉移！
