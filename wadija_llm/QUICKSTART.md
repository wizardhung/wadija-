# Wadi+ 快速開始指南 (Quick Start Guide)

## 📦 5 分鐘快速部署

### 步驟 1: 下載專案

```powershell
# 如果有 Git
git clone https://github.com/your-username/wadi-plus.git
cd wadi-plus

# 或直接下載 ZIP 解壓縮後進入資料夾
```

### 步驟 2: 安裝 Python 依賴

```powershell
# 建立虛擬環境（建議）
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安裝套件
pip install -r requirements.txt
```

### 步驟 3: 設定 API 金鑰

建立 `.env` 檔案：

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

> 💡 到 https://platform.openai.com/api-keys 取得你的 API Key

### 步驟 4: 執行程式

```powershell
# 使用虛擬環境
.\Scripts\python.exe .\main.py

# 或先啟動環境
.\Scripts\Activate.ps1
python main.py
```

### 步驟 5: 開始對話！

```
林旺伯 說: 今天天氣真好
林旺伯 的子女回: 是喔，今仔日的天氣誠水，阿爸有想欲出去行踏無？
```

輸入 `離開` 結束對話。

---

## 🎯 快速測試用例

試試這些句子：

```
✅ 我想去看醫生
✅ 今天要去菜市場買菜
✅ 孫子這禮拜考試了
✅ 我的腳會痛
✅ 要吃飯了嗎
```

---

## ⚡ 常見問題速查

### Q: 出現 `ModuleNotFoundError: No module named 'openai'`

**A**: 執行 `pip install -r requirements.txt`

### Q: 出現 `OpenAI API key not found`

**A**: 檢查 `.env` 檔案是否存在且包含 `OPENAI_API_KEY=...`

### Q: 回應都是國語怎麼辦？

**A**: 
1. 確認使用的是微調模型 ID（在 `main.py` 第 21 行）
2. 新增更多台語詞彙到 `dictionaries/common_words.json`

### Q: Token 費用太高

**A**: 編輯 `main.py` 降低 `DEFAULT_MAX_TOKENS` 從 150 改為 100

---

## 📝 下一步

- 📖 閱讀完整 [README.md](README.md) 了解系統架構
- ✏️ 編輯 `profile_db.json` 自訂長輩資料
- 📚 新增詞彙到 `dictionaries/` 字典
- 🎭 調整對話參數優化回應品質

---

## 🆘 需要幫助？

- 查看 [README.md](README.md#常見問題) 常見問題章節
- 提交 [Issue](https://github.com/your-username/wadi-plus/issues)
- Email: wadi.plus@example.com

---

**祝你使用愉快！ 🎉**
