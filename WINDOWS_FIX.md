# 佛光青年 CMS 前端與後端完整修復說明 (Round 20 終極版)

## 一、本次問題根因與修復 (重要)

在截圖中所看到的「首頁一開啟就顯示白皮書彈窗，且出現 `{{ centenaryPanorama.metrics_summary... }}` 雙大括號未解析」問題，其根因在於：

1. **HTML 結構中的閉合標籤位置錯誤**：
   - 在先前版本中，`<div id="app">` 在登入 Modal 之後被過早的 `</div>` 標籤提早閉合了。
   - 導致後面新增的「百項大滿貫白皮書 Modal」以及其他功能彈窗**被排擠在 Vue 實例 `#app` 的控制範圍之外**。
   - 瀏覽器原生 HTML 解析時，將帶有 `class="flex fixed inset-0 z-50 ..."` 的彈窗當作普通 HTML 區塊直接置頂顯示，且 Vue 無法解析該區塊內的雙大括號變數。
2. **JavaScript 內字串包含 `</script>` 標籤中斷解析**：
   - 回向文疏列印函式 `printLiturgy` 曾包含 `<script>window.onload ... <\/script>` 字串，導致瀏覽器 HTML Parser 誤判該處為主要 `<script>` 的結尾，造成 Vue `createApp` 在中途終止執行。
3. **已全面修正**：
   - 重新整理並嚴格校對 `index.html` 與 `admin.html` 的全部 DOM 樹結構，確保所有彈窗均 100% 包含於 `<div id="app">` 內部，且預設隱藏（`v-if="showCentenaryModal"` 配合 `v-cloak`）。
   - 將文疏列印改為安全標準的 `<body onload="window.print()">`，徹底避免 `<script>` 標籤誤閉合。
   - 所有非同步請求改用標準原生 `fetch()` API，並額外引入 Axios CDN 防呆備援。

---

## 二、Windows 本機啟動與瀏覽指南

1. **啟動後端伺服器**：
   在解壓縮目錄執行：
   ```cmd
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   終端機顯示 `Application startup complete.` 即代表後端啟動成功。

2. **開啟瀏覽器首頁**：
   - 請至瀏覽器網址列輸入：`http://localhost:8000`
   - **請務必按下 `Ctrl + F5` 或 `Ctrl + Shift + R`（強制重新整理）**，避免瀏覽器讀取舊版 HTML 快取。
   - 正常情況下，畫面會顯示乾淨流暢的佛光青年分團首頁，頂部導航列包含「百項大滿貫」按鈕。
   - 點擊「百項大滿貫」按鈕後，白皮書彈窗才會展開，且各項數據（100 項功能、1280.0 hr、420 篇日記、137.3 kg 減碳）均完整呈現。

3. **後台 CMS 管理系統**：
   - 網址：`http://localhost:8000/admin`
   - 預設管理員帳號：`admin` / 密碼：`blia123456`
