# 🚀 快速開始指南

## 1️⃣ 環境設置 (第一次使用必須執行)

```bash
# 創建 conda 環境
conda create -n c2t python=3.8
conda activate c2t

# 安裝依賴套件
pip install -r requirements_voice_chat.txt
```

## 2️⃣ 配置服務

### 配置 Google Cloud STT (語音識別)

1. 確保 Google Cloud 認證金鑰在正確位置:
   ```
   yating1/newproject0901-470807-038aaaad5572.json
   ```

2. 如果沒有金鑰，請到 [Google Cloud Console](https://console.cloud.google.com/) 創建

### 配置 OpenAI LLM (對話 AI)

1. 在 `wadija_llm/` 目錄創建 `.env` 文件:
   ```bash
   cd wadija_llm
   touch .env
   ```

2. 編輯 `.env` 文件，添加你的 OpenAI API Key:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

## 3️⃣ 啟動系統

### 方法一: 使用啟動腳本 (推薦)

```bash
# 在專題tts目錄下執行
./start_voice_chat.sh
```

### 方法二: 手動啟動

```bash
# 啟動 conda 環境
conda activate c2t

# 啟動後端 API
python integrated_voice_chat_api.py
```

## 4️⃣ 開啟網頁介面

在瀏覽器中打開: `voice_chat_interface.html`

或直接雙擊檔案

## 5️⃣ 開始使用

1. ✅ 檢查系統狀態 (應該顯示綠色)
2. 🎤 點擊紅色麥克風按鈕開始錄音
3. 🗣️ 說出你想說的話
4. 🎤 再次點擊按鈕結束錄音
5. 👀 查看對話內容
6. 🔊 點擊喇叭圖示播放 AI 回應的語音

## ⚠️ 注意事項

- 使用 Chrome 或 Edge 瀏覽器以獲得最佳體驗
- 確保麥克風權限已開啟
- 錄音建議不超過 30 秒
- 首次啟動 TTS 可能需要較長時間載入模型

## 🐛 遇到問題？

查看詳細說明文件: `VOICE_CHAT_README.md`

或檢查後端日誌輸出

---

**準備好了嗎？開始你的台語 AI 對話之旅！** 🎉
