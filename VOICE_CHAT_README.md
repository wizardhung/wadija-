# 台語 AI 語音對話系統

這是一個整合了語音識別 (STT)、自然語言處理 (LLM) 和語音合成 (TTS) 的完整台語對話系統。

## 🎯 系統架構

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   語音輸入   │ ---> │  STT 模組   │ ---> │   文字訊息   │
│  (麥克風)    │      │  (yating1)  │      │             │
└─────────────┘      └─────────────┘      └─────────────┘
                                                  │
                                                  ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  語音輸出   │ <--- │  TTS 模組   │ <--- │  LLM 模組   │
│  (喇叭)     │      │(taiwanese...) │      │(wadija_llm) │
└─────────────┘      └─────────────┘      └─────────────┘
```

## 📦 系統組件

### 1. STT (語音轉文字)
- **位置**: `yating1/`
- **技術**: Google Cloud Speech-to-Text
- **功能**: 將用戶的語音輸入轉換為文字
- **支援語言**: 台語 (nan-TW)、華語 (zh-TW)、英語 (en-US)

### 2. LLM (自然語言處理)
- **位置**: `wadija_llm/`
- **技術**: OpenAI GPT-4 (微調模型)
- **功能**: 理解用戶意圖，生成合適的回應
- **特色**: RAG (檢索增強生成) + 長輩資料檔案

### 3. TTS (文字轉語音)
- **位置**: `taiwanese_tonal_tlpa_tacotron2_hsien1/`
- **技術**: Tacotron2 + WaveGlow
- **功能**: 將 AI 回應轉換為台語語音
- **特色**: 支援台語聲調和自然發音

## 🚀 快速開始

### 前置需求

1. **Anaconda 或 Miniconda**
2. **Python 3.8+**
3. **Google Cloud 認證金鑰** (用於 STT)
4. **OpenAI API Key** (用於 LLM)

### 安裝步驟

1. **創建並啟動 conda 環境**
```bash
conda create -n c2t python=3.8
conda activate c2t
```

2. **安裝必要套件**
```bash
pip install flask flask-cors google-cloud-speech openai python-dotenv pyaudio
```

3. **配置環境**

   a. 設置 Google Cloud 認證 (STT):
   - 將 Google Cloud 金鑰放在 `yating1/newproject0901-470807-038aaaad5572.json`
   
   b. 設置 OpenAI API Key (LLM):
   - 在 `wadija_llm/` 目錄下創建 `.env` 文件
   - 添加: `OPENAI_API_KEY=your_api_key_here`

4. **啟動系統**
```bash
chmod +x start_voice_chat.sh
./start_voice_chat.sh
```

5. **開啟網頁介面**
   - 在瀏覽器中打開 `voice_chat_interface.html`
   - 或直接雙擊該文件

## 📝 使用說明

### 基本操作

1. **開始對話**
   - 點擊紅色麥克風按鈕開始錄音
   - 說出你想說的話
   - 再次點擊按鈕結束錄音

2. **查看結果**
   - 你的語音會被轉換為文字並顯示在對話框中
   - AI 會生成回應並顯示在對話框中

3. **播放語音**
   - 點擊 AI 回應旁的喇叭圖示 🔊
   - 系統會將回應轉換為台語語音並播放

4. **清除對話**
   - 點擊對話框右上角的"清除對話"按鈕
   - 重置對話歷史

### 進階功能

- **多語言支援**: 系統自動識別台語、華語和英語
- **對話記憶**: 系統會記住之前的對話內容
- **語音質量**: 支援台語聲調和自然語氣

## 🔧 API 端點

後端 API 服務運行在 `http://localhost:5000`

### 端點列表

| 端點 | 方法 | 功能 | 參數 |
|------|------|------|------|
| `/api/health` | GET | 系統健康檢查 | - |
| `/api/stt` | POST | 語音轉文字 | audio (文件或 base64) |
| `/api/chat` | POST | LLM 對話 | message, session_id |
| `/api/tts` | POST | 文字轉語音 | text |
| `/api/reset_session` | POST | 重置會話 | session_id |

### 使用範例

**語音轉文字**
```javascript
const formData = new FormData();
formData.append('audio', audioBlob, 'recording.wav');

fetch('http://localhost:5000/api/stt', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data.transcript));
```

**LLM 對話**
```javascript
fetch('http://localhost:5000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: '你好',
        session_id: 'session_123'
    })
})
.then(response => response.json())
.then(data => console.log(data.reply));
```

**文字轉語音**
```javascript
fetch('http://localhost:5000/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: '你好，很高興認識你'
    })
})
.then(response => response.blob())
.then(blob => {
    const audio = new Audio(URL.createObjectURL(blob));
    audio.play();
});
```

## 🐛 常見問題

### 1. 麥克風無法使用
- **問題**: 瀏覽器無法訪問麥克風
- **解決**: 確保在瀏覽器中允許麥克風權限
- **注意**: HTTPS 或 localhost 才能使用麥克風

### 2. STT 服務無法使用
- **問題**: Google Cloud 認證失敗
- **解決**: 
  - 確認金鑰文件存在於正確位置
  - 檢查金鑰是否有效
  - 確認 Google Cloud Speech-to-Text API 已啟用

### 3. LLM 回應失敗
- **問題**: OpenAI API 錯誤
- **解決**:
  - 檢查 API Key 是否正確
  - 確認有足夠的 API 額度
  - 檢查網路連接

### 4. TTS 語音合成失敗
- **問題**: 模型文件缺失或配置錯誤
- **解決**:
  - 確認模型文件存在
  - 檢查 Tacotron2 和 WaveGlow 模型路徑
  - 查看後端日誌了解詳細錯誤

### 5. 瀏覽器兼容性
- **建議瀏覽器**: Chrome, Edge, Firefox (最新版本)
- **不支援**: Safari (部分功能可能不可用)

## 📂 專案結構

```
專題tts/
├── integrated_voice_chat_api.py    # 整合後端 API
├── voice_chat_interface.html       # 網頁前端介面
├── start_voice_chat.sh            # 啟動腳本
├── VOICE_CHAT_README.md           # 本說明文件
│
├── yating1/                       # STT 模組
│   ├── main_corrector.py
│   └── newproject0901-470807-038aaaad5572.json
│
├── wadija_llm/                    # LLM 模組
│   ├── main.py
│   ├── rag_tools_v2.py
│   ├── profile_db.json
│   └── .env
│
└── taiwanese_tonal_tlpa_tacotron2_hsien1/  # TTS 模組
    ├── taiwanese_tts_v2.py
    ├── synthesizer.py
    └── ...
```

## 🔐 安全性注意事項

1. **API 金鑰保護**
   - 不要將 `.env` 文件提交到版本控制
   - 不要在前端代碼中暴露 API 金鑰

2. **認證文件**
   - Google Cloud 金鑰應妥善保管
   - 定期輪換 API 金鑰

3. **CORS 設定**
   - 生產環境應限制 CORS 來源
   - 不要在公網暴露未保護的 API

## 📊 性能優化建議

1. **錄音長度**: 建議單次錄音不超過 30 秒
2. **對話歷史**: 系統自動保留最近 20 輪對話
3. **音頻格式**: 使用 16kHz, 16-bit PCM WAV 格式
4. **快取**: 可考慮快取常用的 TTS 音頻

## 🤝 技術支援

如有問題，請檢查:
1. 後端 API 日誌輸出
2. 瀏覽器控制台錯誤訊息
3. 各模組的獨立測試

## 📄 授權

本專案整合多個開源專案，請參考各子專案的授權條款。

---

**製作**: 專題 TTS 團隊  
**更新日期**: 2025-12-17
