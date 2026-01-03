# 台羅數字調完整轉換流程說明

## 概述
本系統實現了從 LLM 輸出到 TTS 語音合成的完整台羅數字調轉換流程，確保語義一致性和高品質的台語語音輸出。

## 核心流程

```
用戶輸入（中文/台語）
    ↓
LLM 生成回應（台語漢字）
    ↓
完整台羅數字調轉換（add_pauses=True）
    ↓
TTS 語音合成（convert_chinese=False）
    ↓
語音輸出
```

## 技術實現

### 1. Chat API (`/api/chat`)
**功能**: LLM 對話並完整轉換為台羅數字調

**流程**:
1. 接收用戶輸入
2. 呼叫 OpenAI fine-tuned 模型生成台語回應
3. **完整轉換**為台羅數字調格式（包含停頓）
   ```python
   tlpa_text = tts_system.text_processor.process_text(
       ai_reply, 
       add_pauses=True,      # 添加標點停頓
       convert_chinese=True  # 華文轉台語漢字
   )
   ```
4. 返回兩個欄位：
   - `reply`: LLM 原始回應（台語漢字）
   - `reply_tlpa`: 完整台羅數字調文本

**範例**:
```json
{
  "reply": "我會講台語！有啥物欲問的，盡量問。",
  "reply_tlpa": "gua2 e7 kong2 tai5-gi2 ! u7 sia2 mih8 bun7 e5 , bun7 .",
  "session_id": "default",
  "success": true
}
```

### 2. TTS API (`/api/tts`)
**功能**: 台羅文本轉語音合成

**智能檢測**:
- 檢測輸入是否已含數字調（正則: `[0-9]`）
- 已是台羅格式 → 直接合成（`convert_chinese=False`）
- 非台羅格式 → 先轉換再合成（`convert_chinese=True`）

**流程**:
```python
# 檢測是否已是台羅格式
is_tlpa = bool(re.search(r'[0-9]', text))

if is_tlpa:
    # 已是台羅，直接使用
    tlpa_text = text
else:
    # 需要轉換
    tlpa_text = tts_system.text_processor.process_text(
        text, add_pauses=True, convert_chinese=True
    )

# 使用台羅文本合成（不再二次轉換）
result = tts_system.synthesize(
    tlpa_text, 
    output_path, 
    convert_chinese=False
)
```

**範例**:
```json
{
  "success": true,
  "text": "gua2 e7 kong2 tai5-gi2 !",
  "tlpa": "gua2 e7 kong2 tai5-gi2 !",
  "audio": "base64_encoded_audio_data...",
  "file_size": 278572
}
```

### 3. TTS 系統 (`taiwanese_tts_v2.py`)
**synthesize() 方法更新**:
- 新增 `convert_chinese` 參數
- `convert_chinese=False`: 直接使用輸入（已是台羅）
- `convert_chinese=True`: 進行華文轉台語轉台羅

```python
def synthesize(self, text: str, output_path: str = None, 
               convert_chinese: bool = True) -> Optional[str]:
    if convert_chinese:
        # 需要轉換
        tlpa_text = self.text_processor.process_text(text, convert_chinese=True)
        print(f"台羅轉換: {tlpa_text}")
    else:
        # 已是台羅，直接使用
        tlpa_text = text
        print(f"台羅文本（無需轉換）: {tlpa_text}")
    
    # 使用台羅文本合成
    self.synthesizer.tts(tlpa_text, output_path)
```

## 關鍵優勢

### ✓ 一次完整轉換
- LLM 輸出後**立即完整轉換**為台羅數字調
- TTS 階段**不再進行轉換**，直接使用
- 避免多次轉換造成的不一致

### ✓ 語義一致性
```
LLM 回應: "我會講台語！"
   ↓ (轉換一次)
台羅文本: "gua2 e7 kong2 tai5-gi2 !"
   ↓ (直接合成)
語音輸出: [台語語音]
```

### ✓ 靈活性
- 支援直接輸入台羅數字調（自動檢測）
- 支援輸入華文/台語漢字（自動轉換）
- 兩種模式無縫切換

### ✓ 透明度
- Chat API 返回轉換後的台羅文本
- TTS API 確認使用的台羅文本
- 完整的日誌記錄轉換過程

## 測試結果

### 測試案例 1
```
用戶: "你好，你叫什麼名字？"
LLM:  "你好！我無名，按怎若乎你叫我「小助手」就好。"
台羅: "li2-ho2 ! gua2 bo5 , hoo7 li2 gua2 se3 to7 ho2 ."
音檔: 4.92 秒, 217KB
狀態: ✓ 成功
```

### 測試案例 2
```
用戶: "今天天氣如何？"
LLM:  "我毋知乎即時天氣，但你可以去查查手機的天氣預報軟體，彼會較準。"
台羅: "gua2 tsai1 hoo7 thinn1-khi3 , li2 thiann1 ho2 khi3 tshiu2-ki1 e5 thinn1-khi3 , e7 khah4 ."
音檔: 9.01 秒, 397KB
狀態: ✓ 成功
```

### 測試案例 3
```
用戶: "你會說台語嗎？"
LLM:  "我會講台語！有啥物欲問的，盡量問，我會當幫你解答。"
台羅: "gua2 e7 kong2 tai5-gi2 ! u7 sia2 mih8 bun7 e5 , bun7 , gua2 e7 pang1 li2 kai2 tap ."
音檔: 9.75 秒, 430KB
狀態: ✓ 成功
```

## API 使用方式

### 完整流程（推薦）
```bash
# 1. 呼叫 Chat API 獲取 LLM 回應和台羅轉換
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 回應中包含 reply_tlpa 欄位
# {"reply": "你好！", "reply_tlpa": "li2-ho2 !", ...}

# 2. 使用台羅文本呼叫 TTS API
curl -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "li2-ho2 !"}'
```

### 直接 TTS（自動轉換）
```bash
# 輸入中文，自動轉換為台羅
curl -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好"}'
```

## 測試腳本

執行完整測試：
```bash
cd /home/wizard/專題tts
python test_complete_tlpa_flow.py
```

測試內容：
- 3 個測試案例
- 完整 Chat → TTS 流程
- 自動生成音檔（test_output_1.wav, test_output_2.wav, test_output_3.wav）
- 詳細的過程記錄

## 系統日誌範例

```
[台羅轉換] 原文: 我會講台語！
[台羅轉換] 台羅: gua2 e7 kong2 tai5-gi2 !

============================================================
📝 TTS 請求
============================================================
輸入文字: gua2 e7 kong2 tai5-gi2 !
✓ 檢測到台羅數字調格式，直接使用
==================================================
台語文字轉語音
==================================================
輸入文字: gua2 e7 kong2 tai5-gi2 !
台羅文本（無需轉換）: gua2 e7 kong2 tai5-gi2 !
✓ 音檔已生成: /tmp/tmpxxxx.wav
```

## 技術要點

1. **add_pauses=True**: 在標點處添加適當停頓，讓語音更自然
2. **convert_chinese 雙階段控制**: 
   - Chat 階段: `True` (進行完整轉換)
   - TTS 階段: `False` (使用已轉換的台羅)
3. **正則檢測**: `[0-9]` 識別台羅數字調格式
4. **Base64 編碼**: 音檔在 JSON 中傳輸

## 相關檔案

- `integrated_voice_chat_api.py`: 主 API 服務
- `taiwanese_tts_v2.py`: TTS 核心系統
- `taiwanese_text_processor.py`: 文字處理器
- `advanced_chinese_converter.py`: 華文轉台語漢字
- `test_complete_tlpa_flow.py`: 完整測試腳本

## 更新日期
2024-12-24
