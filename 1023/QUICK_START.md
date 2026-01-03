# 快速開始指南

## 一句話總結
在網頁上輸入台語數字調，點擊按鈕直接生成並試聽語音！

## 最快開始方式（3步）

### 步驟1: 啟動API伺服器
```bash
cd /home/wizard/專題tts/1023
python translation_api.py
```
等待出現 `Running on http://0.0.0.0:5000` 訊息

### 步驟2: 打開網頁
在瀏覽器中打開：`file:///home/wizard/專題tts/1023/index.html`

### 步驟3: 開始使用
- 輸入框: `gua2 tsiann5 tsiok4 huann7 hi2`
- 按鈕: 點擊「開始合成語音」
- 試聽: 等待後在播放器中試聽

## 功能亮點

✨ **新功能特色:**
- 台語數字調 → 自然語音（直接在網頁試聽）
- 維持原有華語翻譯功能
- 無需離開瀏覽器，一個網頁搞定一切

## 預期時間

| 步驟 | 耗時 |
|------|------|
| API啟動（首次） | 2-3分鐘 |
| 每次合成 | 30秒-1分鐘 |
| 頁面加載 | <1秒 |

## 台語數字調範例

| 台語 | 數字調 | 說明 |
|------|--------|------|
| 我 | gua2 | 第2聲 |
| 愛 | tsua3 | 第3聲 |
| 清 | tsiann1 | 第1聲 |
| 飯 | pn̄g7 | 第7聲 |

## 常見問題速解

❓ **「無法連線」怎麼辦？**
→ 確認 `translation_api.py` 還在運行（看終端有無錯誤）

❓ **「為什麼要等這麼久？」**
→ 首次載入AI模型檔案（1GB+），之後會快一點

❓ **「語音很奇怪」**
→ 檢查輸入台語數字調是否正確（空格分隔）

❓ **「有GPU會更快嗎？」**
→ 有的話可快5-10倍！本系統會自動檢測

## 進階設定

### 修改模型路徑
編輯 `translation_api.py` 中的 `load_tts_model()` 函數：
```python
tacotron_ckpt = "/自定義/模型/路徑/checkpoint_100000"
waveglow_ckpt = "/自定義/模型/路徑/waveglow_main.pt"
```

### 調整超時時間
在 `index.html` 中修改：
```javascript
signal: AbortSignal.timeout(60000), // 改為更大的毫秒數
```

## 支援的台語系統

目前系統訓練於台語全臺優越音（Taiwanese Prestige System），適用於：
- ✅ 台灣台語音系
- ✅ 臺灣言語工具(Tai5-Uan5)相容

## 檔案結構說明

```
1023/
├── index.html              ← 打開這個！
├── translation_api.py      ← 執行這個！
├── c2t/                    ← 翻譯模型
├── USAGE_GUIDE.md          ← 詳細指南
├── IMPLEMENTATION_SUMMARY.md ← 技術細節
└── QUICK_START.md          ← 本文件
```

## 故障排除

### 問題：`ImportError: No module named 'han2tts'`
**解決**: API會自動尋找模型，若找不到會提示日誌

### 問題：API佔用5000 port
**解決**: 
```bash
# 查看佔用狀況
lsof -i :5000

# 若要用其他port，修改API最後一行：
app.run(host='0.0.0.0', port=8000, debug=False)
```

### 問題：瀏覽器控制台有CORS錯誤
**確認**: API已啟用CORS（已內建，無需修改）

## 下載/備份

若要備份當前設定：
```bash
cd /home/wizard/專題tts/1023
tar -czf backup.tar.gz translation_api.py index.html *.md
```

## 聯絡支援

遇到問題？檢查以下檔案：
1. `USAGE_GUIDE.md` - 完整功能說明
2. `IMPLEMENTATION_SUMMARY.md` - 技術實現細節

---

**準備好了嗎？** 現在就按照前面的3個步驟開始使用吧！🎉
