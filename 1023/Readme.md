# 臺語翻譯 API - 使用說明

這個專案提供一個簡單的 Flask API (`translation_api.py`)，將華語轉為臺語羅馬字（TLPA）。
專案包含一個 Fairseq 訓練好的模型（放在 `c2t/` 目錄），以及一個簡單的前端測試頁面 `index.html`。

本文檔包含：

- 在 Windows（PowerShell + conda）下的環境建立步驟
- 所需套件（`requirements.txt`）說明
- 啟動與測試 API 的指令範例
- 常見問題排查要點

---

## 快速上手（PowerShell 範例）

1. 啟用或建立 conda 環境（範例以 `c2t` 為名稱）：

```powershell
conda create -n c2t python=3.7 -y
conda activate c2t
```

2. 在專案根目錄安裝依賴：

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3. 啟動 API：

- **Windows / PowerShell（僅翻譯 + 調號合成備援）**

	```powershell
	python .\translation_api.py
	```

- **WSL / Linux（使用 GPU 載入真實 Tacotron2 + WaveGlow）**

	```bash
	# 確保在專案根目錄 1023/
	export LD_LIBRARY_PATH=/usr/lib/wsl/lib:$LD_LIBRARY_PATH
	conda run -n c2t python translation_api.py
	```

應該會在 console 顯示類似：

- Encoding Patch 成功應用（表示 BPE 編碼補丁已生效）
- 如果載入 GPU TTS：會載入 Tacotron2 + WaveGlow，並在首次 /synthesize_tonal_number 請求時生成真實台語語音
- Flask running on http://127.0.0.1:5000

4. 測試 API（PowerShell 範例）：

直接在瀏覽器中開啟 `index.html`，輸入文字並按「開始翻譯」。

---

## 檔案說明

- `translation_api.py`：Flask API 入口。程式會嘗試載入 `c2t/checkpoint_last.pt` 與相關資源。
- `c2t/`：模型資料夾（包含 `checkpoint_last.pt`, `code`, `dict.tw.txt`, `dict.zh.txt`）。
- `index.html`：前端測試介面。
- `requirements.txt`：建議安裝的 Python 套件清單。

---

## 注意與排錯

- 若 5000 port 被占用：檢查 `netstat -ano | findstr 5000`，或修改 `translation_api.py` 中的 `app.run(port=...)`。
