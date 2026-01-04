# STT 音聲辨識工具（主校正器）

## 概述
此工具用於測試和修正台灣語音的文字轉換與語意檢查。

### 特色
- **自動降級**：WSL 環境無麥克風時自動進入檔案輸入模式
- **Google Cloud Speech API**：支援高精度語音辨識
- **語意評分**：使用 pycorrector + 流暢度指標評估文本合理性
- **Fallback 機制**：不符合閾值時自動調用 `1.py` 進行進一步處理

---

## 安裝

### 依賴
```bash
# 已在 py311 環境中安裝
conda activate py311
pip list | grep -E "google-cloud|pycorrector|jieba|wordfreq|pyaudio"
```

### 必要檔案
- `newproject0901-470807-038aaaad5572.json` - Google Cloud 認證金鑰（放在本目錄）
- `1.py` - Fallback 腳本（備援使用）

---

## 使用方式

### 方式 1：互動檔案模式（推薦用於 WSL）
```bash
conda activate py311
python main_corrector.py
```
程式會自動檢測是否有麥克風。若無，進入檔案輸入模式：
```
📂 WAV 檔案: test_440hz.wav
📤 上傳 32044 bytes 至 Google Cloud…
📝 辨識結果: ...
📊 信心度: 0.95
🧠 合理度: 0.87（更動 0 處）
✅ 通過：信心度與合理度皆達標。
```

### 方式 2：CLI 模式（單一檔案）
```bash
conda activate py311
python main_corrector_cli.py test_440hz.wav
```

---

## 測試

### 建立測試 WAV 檔案
```bash
python3 << 'EOF'
import wave, struct, math
rate, freq = 16000, 440  # 16kHz, A4 note
with wave.open('test.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    for i in range(rate):
        s = int(32767 * 0.5 * math.sin(2*3.14159*freq*i/rate))
        w.writeframes(struct.pack('<h', s))
print("✅ Created test.wav")
EOF
```

### 執行測試
```bash
conda activate py311
python main_corrector_cli.py test_440hz.wav
```

---

## 設定調整

### 信心度門檻
編輯 `main_corrector.py`：
```python
CONF_MIN = 0.80  # Google STT 信心度（0~1，越高越嚴格）
```

### 語意合理度門檻
```python
LOGIC_MIN = 0.4  # 語意合理度（0~1，越高越嚴格）
```

---

## 故障排除

### 🔴 `PermissionDenied: 403 BILLING_DISABLED`
**原因**：Google Cloud 專案未啟用計費
**解決**：
1. 訪問 [Google Cloud Console](https://console.cloud.google.com)
2. 啟用計費
3. 或建立新的服務帳戶金鑰

### 🔴 `FileNotFoundError: newproject0901-470807-038aaaad5572.json`
**原因**：缺少認證金鑰
**解決**：
1. 從 Google Cloud Console 下載服務帳戶金鑰
2. 放在 `yating1/` 目錄下

### ⚠️ `無法載入 pycorrector.corrector`
**原因**：pycorrector 版本問題（正常）
**影響**：語意評分會略過改動密度訊號，仍可使用流暢度指標

---

## 工作流程圖

```
開始
  ↓
檢查麥克風
  ├─ 有 → Live 錄音模式
  │    └─ Google STT → 評分 → 判斷 → Fallback/完成
  │
  └─ 無 → 檔案輸入模式 (WSL)
       └─ 輸入檔案 → Google STT → 評分 → 判斷 → Fallback/完成
```

---

## 相關檔案
- `main_corrector.py` - 主程式
- `main_corrector_cli.py` - CLI 包裝器
- `test_440hz.wav` - 測試檔案（440Hz 正弦波）

