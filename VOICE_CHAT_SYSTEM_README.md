# 🎙️ 台語 AI 語音對話系統

> 整合 STT、LLM 和 TTS 的完整台語語音對話解決方案

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## ✨ 功能特色

🎤 **語音輸入** - 支援台語、華語、英語混合輸入  
🤖 **智能對話** - OpenAI GPT-4 微調模型，具備 RAG 增強  
🔊 **台語輸出** - 自然的台語語音合成  
💬 **對話記憶** - 保留最近 20 輪對話歷史  
🎨 **現代界面** - 美觀的響應式設計  

---

## 🚀 快速開始

### 1️⃣ 安裝依賴

```bash
conda activate c2t
pip install -r requirements_voice_chat.txt
```

### 2️⃣ 配置服務

```bash
# 設置 OpenAI API Key
cd wadija_llm
echo "OPENAI_API_KEY=your-key-here" > .env
```

### 3️⃣ 啟動系統

```bash
./start_voice_chat.sh
```

### 4️⃣ 開啟界面

在瀏覽器打開 `voice_chat_interface.html`

---

## 📚 完整文檔

| 文檔 | 說明 |
|------|------|
| **[📖 文檔索引](INDEX.md)** | 所有文檔的導航中心 |
| **[🚀 快速開始](QUICK_START_VOICE_CHAT.md)** | 5分鐘快速設置指南 |
| **[📦 安裝指南](INSTALLATION_GUIDE.md)** | 詳細的安裝步驟 |
| **[📘 系統說明](VOICE_CHAT_README.md)** | 完整的功能說明 |
| **[🎨 系統架構](system_architecture.html)** | 視覺化架構圖 |
| **[📊 專案總結](PROJECT_SUMMARY.md)** | 專案概況總結 |

**👉 從 [文檔索引](INDEX.md) 開始瀏覽所有文檔**

---

## 🏗️ 系統架構

```
用戶語音 → STT (Google) → 文字
                              ↓
                         LLM (OpenAI) → AI回應
                                           ↓
                        TTS (Tacotron2) → 台語語音
```

### 三大核心模組

| 模組 | 技術 | 功能 |
|------|------|------|
| **STT** | Google Cloud Speech-to-Text | 語音識別 |
| **LLM** | OpenAI GPT-4 (Fine-tuned) | 智能對話 |
| **TTS** | Tacotron2 + WaveGlow | 語音合成 |

---

## 🎯 使用方法

1. **錄音** - 點擊麥克風按鈕 🎤
2. **說話** - 說出你想說的話
3. **停止** - 再次點擊麥克風
4. **查看** - AI 回應顯示在對話框
5. **播放** - 點擊 🔊 聆聽語音

---

## 🛠️ 開發工具

### 啟動腳本
```bash
./start_voice_chat.sh
```

### 配置檢查
```bash
python check_voice_chat_setup.py
```

### API 測試
```bash
# 健康檢查
curl http://localhost:5000/api/health

# 測試對話
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","session_id":"test"}'
```

---

## 📋 系統需求

### 必需
- Python 3.8+
- Conda 環境
- Google Cloud 認證
- OpenAI API Key

### 推薦瀏覽器
- Chrome (推薦)
- Edge
- Firefox

---

## 📂 專案結構

```
專題tts/
├── integrated_voice_chat_api.py    # 後端 API
├── voice_chat_interface.html       # 前端界面
├── start_voice_chat.sh            # 啟動腳本
├── requirements_voice_chat.txt    # 依賴列表
│
├── yating1/                       # STT 模組
├── wadija_llm/                    # LLM 模組
└── taiwanese_tonal_*/             # TTS 模組
```

---

## 🔍 API 端點

| 端點 | 方法 | 功能 |
|------|------|------|
| `/api/health` | GET | 健康檢查 |
| `/api/stt` | POST | 語音轉文字 |
| `/api/chat` | POST | LLM 對話 |
| `/api/tts` | POST | 文字轉語音 |
| `/api/reset_session` | POST | 重置會話 |

---

## ⚙️ 配置說明

### Google Cloud (STT)
```
位置: yating1/newproject0901-470807-038aaaad5572.json
```

### OpenAI (LLM)
```
位置: wadija_llm/.env
格式: OPENAI_API_KEY=sk-...
```

---

## 🐛 常見問題

### Q: 麥克風無法使用？
確保瀏覽器允許麥克風權限

### Q: STT 識別不準？
1. 確保環境安靜
2. 靠近麥克風說話
3. 語速適中

### Q: 如何更換模型？
修改 `integrated_voice_chat_api.py` 中的模型 ID

**更多問題？** 查看 [完整文檔](VOICE_CHAT_README.md)

---

## 📊 性能指標

- 語音識別準確率: >85%
- AI 回應時間: 2-5秒
- 語音合成時間: 3-8秒
- 支援錄音長度: 最長30秒

---

## 🎓 學習資源

- **新手**: [快速開始指南](QUICK_START_VOICE_CHAT.md)
- **開發者**: [整合概要](INTEGRATION_OVERVIEW.txt)
- **全部**: [文檔索引](INDEX.md)

---

## 🤝 參與貢獻

歡迎提出問題和建議！

### 模組貢獻者
- STT: yating1
- LLM: wadija_llm
- TTS: taiwanese_tonal_tlpa_tacotron2_hsien1

---

## 📄 授權

本專案整合多個開源專案，請遵守各組件的授權條款。

---

## 🌟 快速鏈接

- [📖 完整文檔索引](INDEX.md)
- [🚀 快速開始](QUICK_START_VOICE_CHAT.md)
- [📦 安裝指南](INSTALLATION_GUIDE.md)
- [🎨 系統架構圖](system_architecture.html)
- [💡 使用流程](USAGE_FLOW.md)

---

## 📞 技術支援

1. 運行配置檢查: `python check_voice_chat_setup.py`
2. 查看文檔: [INDEX.md](INDEX.md)
3. 檢查日誌輸出

---

## 🎉 開始使用

```bash
# 一鍵啟動
./start_voice_chat.sh

# 然後打開
# voice_chat_interface.html
```

**享受台語 AI 對話的樂趣吧！** 🎊

---

**版本**: 1.0.0  
**日期**: 2025-12-17  
**團隊**: 專題 TTS

---

Made with ❤️ in Taiwan
