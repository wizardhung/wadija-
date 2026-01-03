# 台羅數字調轉換 - 快速參考

## 🎯 核心概念

**完整流程**: LLM 輸出 → **一次完整台羅轉換** → TTS 直接合成

## 📋 API 端點

### 1. Chat API - LLM 對話 + 台羅轉換
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "你好，你叫什麼名字？",
  "session_id": "test123"  # 可選
}
```

**回應**:
```json
{
  "success": true,
  "reply": "我無名，你叫我小助手就好。",           # LLM 原始回應
  "reply_tlpa": "gua2 bo5 , li2 gua2 se3 to7 ho2 .",  # 台羅數字調
  "session_id": "test123"
}
```

### 2. TTS API - 台羅轉語音
```bash
POST /api/tts
Content-Type: application/json

{
  "text": "gua2 e7 kong2 tai5-gi2 !"  # 台羅或中文皆可
}
```

**回應**:
```json
{
  "success": true,
  "text": "gua2 e7 kong2 tai5-gi2 !",      # 輸入文字
  "tlpa": "gua2 e7 kong2 tai5-gi2 !",      # 使用的台羅
  "audio": "base64_encoded_audio...",       # 音檔（base64）
  "file_size": 278572                       # 檔案大小（bytes）
}
```

## 🔄 使用模式

### 模式 1: 完整對話流程（推薦）
```bash
# Step 1: Chat API
RESPONSE=$(curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}')

# Step 2: 提取 reply_tlpa
TLPA=$(echo $RESPONSE | jq -r '.reply_tlpa')

# Step 3: TTS API
curl -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$TLPA\"}"
```

### 模式 2: 直接 TTS（自動轉換）
```bash
# 輸入中文，自動轉換
curl -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界"}'

# 輸入台羅，直接合成
curl -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "li2-ho2 si3"}'
```

## 🧪 快速測試

### 測試 Chat API
```bash
curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你會說台語嗎？"}' | jq
```

### 測試 TTS API
```bash
curl -s -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "li2-ho2"}' | jq
```

### 完整測試腳本
```bash
cd /home/wizard/專題tts
python test_complete_tlpa_flow.py
```

## ✅ 驗證要點

### Chat API 回應檢查
- ✓ `reply` 欄位存在（台語漢字）
- ✓ `reply_tlpa` 欄位存在（台羅數字調）
- ✓ 台羅包含數字 0-9
- ✓ 台羅長度 > 0

### TTS API 回應檢查
- ✓ `success: true`
- ✓ `tlpa` 欄位與輸入一致
- ✓ `audio` 欄位包含 base64 資料
- ✓ `file_size` > 10000 bytes

## 📊 性能參考

| 文字長度 | 台羅長度 | 音檔大小 | 音檔時長 |
|---------|---------|---------|---------|
| 15 字   | 48 字元  | 217 KB  | 4.9 秒  |
| 27 字   | 89 字元  | 397 KB  | 9.0 秒  |
| 25 字   | 83 字元  | 430 KB  | 9.8 秒  |

## 🐛 常見問題

### Q: Chat API 返回中文而非台語？
A: 檢查系統提示詞，應包含「請用台語（台羅漢字或台灣台語漢字）直接回答」

### Q: TTS 合成失敗？
A: 確認：
1. 輸入文字非純標點
2. 台羅格式正確（含數字調）
3. API 日誌中無錯誤

### Q: 音檔過小（< 1KB）？
A: 可能原因：
1. 輸入文字太短
2. TTS 合成器未初始化
3. 模型檔案載入失敗

## 🔍 除錯

### 查看 API 日誌
```bash
tail -f /tmp/api_new.log
```

### 檢查健康狀態
```bash
curl http://localhost:5000/api/health | jq
```

### 重啟 API
```bash
pkill -9 -f "python.*integrated_voice_chat_api"
cd /home/wizard/專題tts
python integrated_voice_chat_api.py > /tmp/api.log 2>&1 &
```

## 📁 相關檔案

- **API**: `integrated_voice_chat_api.py`
- **TTS**: `taiwanese_tts_v2.py`
- **測試**: `test_complete_tlpa_flow.py`
- **文檔**: `TLPA_CONVERSION_FLOW.md`

## 🎉 成功指標

✓ LLM 輸出台語漢字（非中文）  
✓ reply_tlpa 包含完整台羅數字調  
✓ TTS 輸入 = reply_tlpa（無二次轉換）  
✓ 音檔生成成功（> 10KB）  
✓ 語義完全一致（LLM → TTS）

---
**最後更新**: 2024-12-24  
**版本**: 1.0  
**狀態**: ✓ 已完成並測試通過
