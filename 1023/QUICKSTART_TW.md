# 快速使用指南 - 台語文本語音合成系統

## ⚡ 3步啟動

### 1️⃣ 啟動API服務
```bash
cd /home/wizard/專題tts/1023
python translation_api.py
```

您應該看到:
```
模型載入成功。服務已就緒。
 * Running on http://127.0.0.1:5000
```

### 2️⃣ 打開網頁介面
在瀏覽器中開啟:
```
file:///home/wizard/專題tts/1023/index.html
```

或通過檔案管理器雙擊 `index.html`

### 3️⃣ 開始使用

#### 功能 A: 華語→台語音標
1. 在**左側**輸入華語文本 (例如: "你好")
2. 點擊"翻譯為台語音標"
3. 看到台語羅馬字結果

**例子**:
- 華語: `我好` → 台語: `gua2 hoo2`
- 華語: `謝謝` → 台語: `tsieh3 tsieh3`

#### 功能 B: 台語數字調→合成音頻
1. 在**右側**輸入台語數字調 (例如: "gua2 tsiann5")
2. 點擊"開始合成語音"
3. 等待 (~0.1秒 for 模擬 / 1-2分鐘 for GPU)
4. 在音頻播放器中點擊▶️播放

**例子**:
```
tsiann5 oo7          (台灣語 台灣)
kong2 oo7 tsi7 oo7   (恭喜你)
gua2 tsiann5         (我好)
```

---

## 📡 API端點 (進階)

### 翻譯端點
```bash
curl -X POST http://127.0.0.1:5000/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"你好"}'
```

**回應**:
```json
{
  "original_text": "你好",
  "tlpa_result": "li2 hoo2"
}
```

### 合成端點
```bash
curl -X POST http://127.0.0.1:5000/synthesize_tonal_number \
  -H "Content-Type: application/json" \
  -d '{"text":"gua2 tsiann5"}'
```

**回應**:
```json
{
  "tonal_number_text": "gua2 tsiann5",
  "audio": "UklGRv...==",  // Base64編碼的WAV
  "status": "success",
  "mode": "mock",
  "note": "演示模式..."
}
```

---

## ❓ 常見問題

### Q1: API無法啟動
**A**: 確認:
1. 確認port 5000未被佔用: `lsof -i :5000`
2. 如果被佔用，停止該進程: `pkill -f translation_api`
3. 確認conda環境活躍: `conda activate c2t`

### Q2: 網頁無法連接到API
**A**: 
1. 確認API正在運行 (查看日誌)
2. 確認使用 `file://` 協議打開HTML
3. 檢查瀏覽器控制台 (F12) 查看錯誤信息

### Q3: 為何音頻是"模擬的"?
**A**: 在WSL/CPU環境中，真實TTS會導致記憶體崩潰。在GPU環境中可啟用真實TTS。詳見 `TROUBLESHOOTING_TTS.md`

### Q4: 翻譯結果不對?
**A**: 模型針對現代台語進行了優化。對於罕見字詞或方言變體，準確性可能不同。

---

## 🎵 台語數字調參考

| 數字 | 聲調 | 例子 |
|------|------|------|
| 1 | 高 | `kong1` (恭) |
| 2 | 上升 | `hoo2` (好) |
| 3 | 低 | `tsieh3` (謝) |
| 5 | 上降 | `tsiann5` (台) |
| 7 | 短 | `oo7` (灣) |
| 8 | 入聲 | `tshik8` (吃) |
| 9 | 中聲 | `tshi9` (次) |

---

## 📂 檔案結構

```
1023/
  ├── translation_api.py          # Flask API主程式
  ├── index.html                  # 網頁前端介面
  ├── QUICK_START.md             # 本檔案
  ├── TROUBLESHOOTING_TTS.md      # 故障排除詳文
  └── USAGE_GUIDE.md             # 詳細使用指南
```

---

## 🚀 進階使用

### 自訂API埠號
編輯 `translation_api.py` 最後一行:
```python
app.run(host='0.0.0.0', port=5001, debug=False)  # 改為 5001
```

### 啟用調試模式
```python
app.run(host='0.0.0.0', port=5000, debug=True)  # debug=True
```

### 在有GPU的環境中啟用真實TTS
詳見 `TROUBLESHOOTING_TTS.md` "如何在GPU上啟用真實TTS" 部分

---

## 📞 支持

遇到問題？:
1. 檢查 `TROUBLESHOOTING_TTS.md` 故障排除部分
2. 查看API日誌輸出
3. 在瀏覽器控制台 (F12) 檢查JavaScript錯誤

---

*最後更新: 2025-12-09*
*支持的瀏覽器: Chrome/Firefox/Safari (需HTML5支持)*
