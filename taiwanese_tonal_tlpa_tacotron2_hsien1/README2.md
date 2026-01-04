# 專案檔案總覽

以下為本專案主要檔案與目錄的整理（繁體中文）。此檔以標題與條列方式呈現，便於快速查閱與後續維護。

## 一、專案高階概覽

- 主題：臺語（台灣閩南語）語音合成系統。
- 核心：Tacotron2（聲學模型） + WaveGlow（聲碼器 / vocoder）。
- 功能：從中文/漢字或羅馬字（TLPA）輸入，經文字處理、發音映射、聲學模型、聲碼器生成語音檔。

## 二、根目錄主要檔案說明

- `123.py`

  - 交大 API 測試檔案。

- `advanced_chinese_converter.py`

  - 高階中文轉換器，負責繁簡轉換、數字與標點處理等進階文字正規化與映射。
  - 高階華文字轉漢字。

- `chinese_to_taiwanese_converter.py`

  - 中文到臺語的轉換核心，使用詞典與規則將漢字轉成臺語文字或注音（如 TLPA（數字調））。
  - 華文字轉漢字（用查字典方式）。

- `han2tlpa.py`

  - 漢字 → 數字調(TLPA) 的專用轉換腳本（針對 TLPA 拼音系統）。

- `han2tts.py`

  - TLPA → TTS

- `integrated_taiwanese_tts.py`

  - 整合入口：將文字處理、發音轉換、Tacotron2 與 WaveGlow 串接為完整文字 → 語音流程。
  - taiwanese_text_processor 與 han2tts 結合。
  - 漢字轉語音。

- `synthesizer.py`

  - 高階合成器 API：接受處理後的文本或音素序列，呼叫模型生成 mel-spectrogram 或 waveform。

- `taiwanese_text_processor.py`

  - 文字前處理模組：標準化、斷詞、數字正規化、特殊符號處理、羅馬字轉換等。
  - 漢字轉台羅拼音及數字調。

- `taiwanese_tts_v2.py`

  - 第二版/改良版的 TTS 介面或實驗性 pipeline。
  - 把 taiwanese_text_processor 直接寫在檔案裏面然後接 tts。

- `turn.py`

  - 與句子/對話（turn）相關的工具：可能處理分段、編號或順序資訊。

- / `end.tsv`

- `end.tsv` 為資料檔。

- `phrases.tsv`、`lexicon.tsv`、`tlpa.txt`、`dict-twblg.json`

  - 詞彙與發音資料：
    - `lexicon.tsv`：常見為 word<TAB>pronunciation 映射，用於發音查詢與文字 → 音素轉換。
    - `phrases.tsv`：短語資料表，可能用於評估或合成範例。
    - `tlpa.txt`：TLPA 拼音範例或清單。
    - `dict-twblg.json`：結構化字典，來源可能為「台灣閩南語辭典」。

- `README.md` / `README2.md`
  - 專案說明與使用指引；`README2.md`（即本檔）用於整理檔案總覽與快速導覽。

## 三、資料檔與語料

- `ChhoeTaigi_KauiokpooTaigiSutian.csv`

  - CSV 格式的詞彙/語料集，可能含字、注音與音節資訊。

- `txt/taiwanese.txt`（目錄內的語料檔）

  - 文字語料，用於訓練或測試。

## 四、Tacotron2（位於 `tacotron2/`）

- `model.py`：Tacotron2 模型定義（encoder, decoder, attention）。
- `train.py`：訓練腳本（資料讀取、訓練迴圈、檢查點儲存）。
- `hparams.py`：超參數設定（batch size、learning rate、mel 參數等）。
- `audio_processing.py` / `stft.py`：音訊處理與 spectrogram/STFT 工具。
- `data_utils.py`：資料處理與 filelist 支援。
- `pre/`：預處理腳本（`M1_pre.py`、`M1_new_pre.py`）— 負責建立 mel、清洗資料與 filelist。
- `text/`：文字前處理（`cleaners.py`、`numbers.py`、`twdict.py` 等）。
- `filelists/`：`train-filelist_under25s.txt`、`eval-filelist_under25s.txt` 等。

## 五、WaveGlow 與聲碼器（位於 `waveglow/`）

- `config.json`：WaveGlow 設定檔。
- `inference.py`：mel → waveform 推理腳本。
- `mel2samp.py`：將 mel 還原為音訊的工具。
- `denoiser.py`：去噪處理，改善生成音質。
- `convert_model.py`：模型格式或權重轉換工具。
- `glow.py` / `glow_old.py`：Glow-based vocoder 實作。
- 已訓練權重：`model/waveglow/waveglow_main.pt`（可直接用於推理，視版本相容性）。

## 六、其他重要子套件與文件

- `tai5-uan5_gian5-gi2_kang1-ku7/`（臺語工具套件）

  這是專案內的一個完整子套件 / 函式庫，提供臺語（閩南語）處理的基礎功能與工具，包含大量文件與測試。主要子目錄與用途如下：

  - `__init__.py`, `setup.py`, `MANIFEST.in`, `LICENSE`, `版本.py`

    - 套件宣告與封裝資訊，方便以 pip / setup.py 安裝、發佈或本地引用。

  - `文件/`

    - 內容：大量使用說明與教學文件（`.md`、`.rst`、建置腳本等）。
    - 用途：說明如何安裝、使用各個模組（斷詞、變調、語音合成、語音辨識等）、提供教學與設計文件，對開發者與研究者非常重要。
    - 典型檔案：`安裝.md`、`斷詞.md`、`語音合成.md`、`變調.md`、`平行語料語句對齊.md` 等。

  - `docker/`

    - 內容：部署與重現環境所需的 Dockerfile 與範例（包含 `全編譯/` 下的完整映像建置設定）。
    - 用途：快速建立可重現的運行環境（例如訓練所需的依賴、系統工具），方便在 CI 或其他機器上運行。

  - `臺灣言語工具/`

    - 概述：套件的核心程式庫，分成多個子模組（下列各子目錄），提供字詞物件、斷詞、正規化、羅馬字處理、解析整理、語言模型、語音合成與語音辨識等功能。

    - `基本物件/`

      - 提供資料結構與基本類別（例如字、詞、句、組、章、集等），以及公用變數與常用功能。這是整個套件的底層抽象，其他模組以此為基礎。
      - 典型檔案：`字.py`、`詞.py`、`句.py`、`功能.py`、`公用變數.py`。

    - `斷詞/`

      - 功能：詞切分與分詞策略，包含多種字典與語言模型結合的斷詞演算法（例如「上長詞優先」、「尾字辭典」與語言模型候選選擇）。
      - 典型檔案：`上長詞優先辭典揣詞.py`、`尾字辭典揣詞.py`、`辭典語言模型斷詞.py`。

    - `正規/`

      - 功能：文字正規化工具，例如阿拉伯數字展開（把「123」轉為「一百二十三」）、標點處理與其他預處理規則，確保輸入文字一致性。

    - `系統整合/`

      - 功能：與系統環境或外部程式的整合接口、安裝腳本與調用外部工具的包裝（例如呼叫外部斷詞工具或編碼轉換）。

    - `羅馬字/`

      - 功能：羅馬字（如 TLPA 或臺羅）相關處理、格式化、轉換與輸出。會包含專門處理臺語拼音細節的程式。

    - `解析整理/`

      - 功能：解析（parsing）與整理輸出結構，處理拆文分析、座標/索引、錯誤處理以及將分析結果整理為內部資料結構可用的形式。

    - `語言模型/`

      - 功能：語言模型相關程式（例如 KenLM 的介面、實際語言模型訓練/載入與查詢），用於斷詞或序列評分。

    - `語音合成/`

      - 功能：包含將文字或音標轉為語音標記（phone）或決策樹相關工具、閩南語音韻規則與轉換函式，支援 HTS/其他合成後端的輸出格式。

    - `語音辨識/`

      - 功能：聲音檔處理的輔助工具（例如聲音檔讀取與基本前處理），供語音辨識流程使用。

    - `辭典/`

      - 功能：各類辭典資料結構與查詢介面（型音辭典、尾字辭典、文字辭典、現掀辭典等），提供字詞到音標、音值或詞性等資訊的查詢。

    - `音標系統/`
      - 功能：不同語言或方言的音標系統實作與轉換（包含台語、官話、客話、以及原住民族語音標），支援跨系統轉換與標準化。

  - `試驗/`

    - 內容：大量單元測試與整合測試（`Test...py`），涵蓋基本物件、斷詞、正規、羅馬字、解析整理、語言模型、語音合成與辨識等模組。
    - 用途：用來驗證模組行為、迴歸測試與開發時的自動化檢查；對理解模組行為與 API 很有幫助。

  - 其他：`.travis.yml`、`requirements_travisci.*`、`tox.ini`、`sonar-project.properties`
    - 這些檔案提供 CI 設定、測試環境需求與靜態分析工具設定，方便在持續整合 (CI) 平台上執行測試與品質檢查。

  總結：`tai5-uan5_gian5-gi2_kang1-ku7/` 是一個完整、模組化的臺語處理套件，從字詞物件、斷詞、正規化、羅馬字、語言模型到語音合成/辨識都有覆蓋，並且包含豐富的文件與測試，適合作為本專案的文字處理與語言資源基底。

- CI / 品質工具（專案根目錄）

  - `tox.ini`：定義本地與 CI 測試環境的測試命令與虛擬環境設定。
  - `requirements_travisci.*`：CI 執行所需的套件清單（供 Travis-CI 或類似平台使用）。
  - `sonar-project.properties`：SonarQube 的專案設定，用於靜態分析與品質門檻。

  建議：若要在 CI 中完整執行 `tai5-uan5_gian5-gi2_kang1-ku7` 的測試，請以該資料夾內的 `requirements_travisci.*` 為基礎，並確認 `tox.ini` 的環境與當前 Python 版本相容。

## 七、輸入 → 處理 → 輸出（簡明流程）

1. 輸入：漢字或中文句子（或已標註的 TLPA/羅馬字）。
2. 文字前處理：使用 `taiwanese_text_processor.py` 與轉換器（`chinese_to_taiwanese_converter.py` / `han2tlpa.py`）進行正規化與發音映射（利用 `lexicon.tsv` / `dict-twblg.json`）。
3. 聲學模型：Tacotron2（`tacotron2/model.py`）產生 mel-spectrogram。
4. 聲碼器：WaveGlow（`waveglow/`）將 mel 轉為 waveform（.wav）。

## 八、注意事項與建議

- 詞典覆蓋率：若詞典無法涵蓋所有字詞，需設置 fallback 規則或人工標註流程。
- 編碼與字元處理：確保 UTF-8 編碼與特殊符號的正規化。
- 相依性：Tacotron2 與 WaveGlow 需相容的 PyTorch / CUDA 環境，請以 `requirements.txt` 為依據安裝。
- 權重相容性：不同版本的 checkpoint 可能需 `convert_model.py` 轉換。
