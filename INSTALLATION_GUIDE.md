# 台語 AI 語音對話系統 - 完整安裝指南

## 📋 安裝清單

請按照以下步驟完成系統安裝：

### ✅ 第一步：安裝缺少的 Python 套件

在 c2t conda 環境中執行：

```bash
conda activate c2t

# 安裝所有缺少的套件
pip install flask-cors google-cloud-speech openai pyaudio

# 或者使用 requirements 文件一次安裝全部
pip install -r requirements_voice_chat.txt
```

### ✅ 第二步：配置 OpenAI API Key

1. 前往 [OpenAI Platform](https://platform.openai.com/api-keys) 獲取 API Key

2. 在 `wadija_llm` 目錄創建 `.env` 文件：

```bash
cd wadija_llm
nano .env
```

3. 在 `.env` 文件中添加：

```
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

4. 保存並退出（Ctrl+O, Enter, Ctrl+X）

### ✅ 第三步：驗證配置

```bash
# 回到專題tts目錄
cd /home/wizard/專題tts

# 再次運行配置檢查
python check_voice_chat_setup.py
```

應該看到：
```
通過: 17/17
✅ 所有檢查通過！系統已準備就緒。
```

## 🚀 啟動系統

配置完成後，啟動系統：

```bash
# 確保在 c2t 環境中
conda activate c2t

# 啟動後端 API
./start_voice_chat.sh
```

你應該看到：

```
==================================
  台語 AI 語音對話系統
==================================

🚀 啟動後端 API 服務...
   服務地址: http://localhost:5000

==================================
  按 Ctrl+C 停止服務
==================================

 * Serving Flask app 'integrated_voice_chat_api'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

## 🌐 開啟網頁介面

1. 打開新的終端視窗
2. 使用瀏覽器打開文件：

```bash
# 方法 1: 直接雙擊文件
# voice_chat_interface.html

# 方法 2: 使用命令行打開
xdg-open voice_chat_interface.html

# 方法 3: 在瀏覽器輸入
file:///home/wizard/專題tts/voice_chat_interface.html
```

## 🎯 開始使用

1. **檢查狀態**: 確保頁面上方顯示 "🟢 系統正常運行中"

2. **第一次對話**:
   - 點擊紅色麥克風按鈕
   - 說："你好，今天天氣真好"
   - 再次點擊麥克風停止錄音
   - 等待 AI 回應

3. **播放語音**:
   - 點擊 AI 回應旁的 🔊 圖示
   - 聆聽台語語音輸出

## 📱 使用測試指令 (可選)

如果你想在不使用網頁介面的情況下測試 API：

```bash
# 測試健康檢查
curl http://localhost:5000/api/health

# 測試 LLM 對話
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","session_id":"test123"}'

# 測試 TTS (會下載音頻文件)
curl -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，歡迎使用台語對話系統"}' \
  -o test_output.wav
```

## 🔍 驗證安裝

檢查清單：

- [ ] Python 3.8+ 已安裝
- [ ] conda 環境 'c2t' 已創建並啟動
- [ ] 所有 Python 套件已安裝
- [ ] Google Cloud 認證金鑰已配置
- [ ] OpenAI API Key 已設置在 .env 文件
- [ ] 後端 API 成功啟動
- [ ] 網頁介面可以打開
- [ ] 系統狀態顯示為正常 (綠色)
- [ ] 可以進行錄音
- [ ] AI 可以回應
- [ ] 語音可以播放

## ⚠️ 常見安裝問題

### 問題 1: pyaudio 安裝失敗

```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev python3-pyaudio

# 然後再安裝
pip install pyaudio
```

### 問題 2: Google Cloud 認證錯誤

確保：
1. 金鑰文件在正確位置
2. 金鑰文件有讀取權限：`chmod 600 yating1/newproject0901-470807-038aaaad5572.json`
3. Google Cloud Speech-to-Text API 已啟用

### 問題 3: OpenAI API 錯誤

常見原因：
1. API Key 格式錯誤（應該以 `sk-` 開頭）
2. API 額度不足
3. 網路連接問題

檢查：
```bash
# 測試 API Key 是否有效
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 問題 4: 端口被佔用

如果 5000 端口被佔用：

```bash
# 查找佔用端口的進程
lsof -i :5000

# 殺死該進程
kill -9 <PID>

# 或修改 integrated_voice_chat_api.py 使用其他端口
# app.run(port=8000)
```

## 📞 需要幫助？

1. 查看詳細文檔：`VOICE_CHAT_README.md`
2. 查看使用流程：`USAGE_FLOW.md`
3. 查看整合概要：`INTEGRATION_OVERVIEW.txt`
4. 檢查後端日誌輸出
5. 檢查瀏覽器控制台 (F12)

---

**安裝完成後，盡情享受台語 AI 對話吧！** 🎉
