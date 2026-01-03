# 台羅字典補充修復 - 2024-12-24

## 問題描述與修復

本文檔記錄了兩個字典補充修復：

### 問題 1: 「甘」字缺失
LLM 輸出的「甘」字沒有被轉換到台羅拼音：
```
LLM: 你好啊！甘好？
台羅: li2-ho2 a0 ! ho2 ?
      （「甘」字缺失）
```

### 問題 2: 「盍按怎」詞彙缺失
LLM 輸出的「盍按怎」短語沒有被轉換：
```
LLM: 你好啊！盍按怎？
台羅: li2-ho2 a0 ! ?
      （「盍按怎」短語缺失）
```

## 根本原因
TaiwaneseConverter 類的基本字典 (basic_dict) 中未包含常見台語詞彙。當進階轉換器 (han2tts) 無法使用時，系統降級至基本轉換，導致某些字詞無法轉換。

## 修復內容

### 1. 新增詞彙到基本字典
在 [taiwanese_tts_v2.py](taiwanese_tonal_tlpa_tacotron2_hsien1/taiwanese_tts_v2.py) 的 `basic_dict` 中補充：

| 字/詞 | 台羅拼音 | 用法 |
|------|---------|------|
| 甘 | kan1 | 簡、簡單 |
| 甘好 | kan1-ho2 | 簡單好（台語常用）|
| 盍 | o2 | 為什麼 |
| 按 | an1 | 如此、按照 |
| 怎 | tsuann2 | 怎樣 |
| 按怎 | an1-tsuann2 | 怎樣 |
| 按呢 | an1-ne1 | 這樣、那樣 |
| 按呢樣 | an1-ne1-iunn7 | 這樣、那種方式 |
| 為啥 | ui7-sia2 | 為什麼 |
| 毋 | bu7 | 否定助詞 |
| 毋知 | bu7-tsi1 | 不知道 |
| 嘛 | maa7 | 語氣助詞 |
| 煞 | shuah4 | 已經 |
| 底 | tui2 | 哪裡 |
| 踏 | tshoa8h | 踩 |

| 倒 | tua2 | 倒 |
| 去 | khui3 | 去 |
| 來 | lai5 | 來 |
| 上 | tsiong7 | 上 |
| 下 | e7 | 下 |
| 邊 | pinn1 | 邊 |
| 位 | ui7 | 位置 |
| 足 | tsiok4 | 夠 |
| 閣 | kik4 | 又 |
| 逐 | tsiok4 | 逐個 |
| 只 | tsin1 | 只有 |
| 欲 | bun7 | 要 |
| 愛 | ai3 | 喜歡、要 |

## 修復後效果

### 測試 1: 「甘好」句子
```
原始: 你好啊！甘好？
台羅: li2-ho2 a0 ! kan1-ho2 ?
結果: ✓ 成功轉換並合成語音 (86KB)
```

### 測試 2: 「盍按怎」短語
```
原始: 你好啊！盍按怎？
台羅: li2-ho2 a0 ! o2 an1-tsuann2 ?
結果: ✓ 成功轉換並合成語音 (110KB)
```

### 測試 3: 補充詞彙
```
輸入: bu7-tsi1 tsiok4 kik4 tsiok4 tsin1 bun7 ai3
      (毋知、足、閣、逐、只、欲、愛)
結果: ✓ 成功合成語音 (1.5MB)
```

## 技術架構

### 字典層級結構
```
TaiwaneseConverter.basic_dict
├─ 人稱代詞 (我、你、伊...)
├─ 常用動詞 (是、有、無...)
├─ 形容詞 (好、歹、大...)
├─ 數字 (一、二、三...)
├─ 量詞 (个、隻、本...)
├─ 常用詞彙 (大家、台語...)
├─ 助詞 (的、了、也...)
├─ 疑問詞 (什麼、誰...)
├─ 打招呼 (你好、謝謝...)
├─ 片語與補充 ← 新增的詞彙
```

### 轉換流程
```
文字輸入
  ↓
TaiwaneseConverter.han_to_tlpa()
  ↓
  ├─ 嘗試進階轉換 (han2tts)
  │  └─ 失敗 → 降級到基本轉換
  │
  └─ 基本轉換 (basic_dict)
     └─ 逐字查表 → 台羅拼音
  ↓
台羅拼音輸出
```

## 相關代碼位置

**修改文件**:
- [taiwanese_tts_v2.py](taiwanese_tonal_tlpa_tacotron2_hsien1/taiwanese_tts_v2.py#L85-L100)

**代碼片段**:
```python
def _load_basic_dict(self) -> Dict[str, str]:
    """載入基本辭典"""
    return {
        # ... 其他詞彙 ...
        # 補充常用字詞
        '甘': 'kan1', '甘好': 'kan1-ho2', '簡': 'kan1', '簡好': 'kan1-ho2',
        '毋': 'bu7', '毋知': 'bu7-tsi1', '嘛': 'maa7', '煞': 'shuah4',
        '底': 'tui2', '踏': 'tshoa8h', '倒': 'tua2', '去': 'khui3', '來': 'lai5',
        '上': 'tsiong7', '下': 'e7', '邊': 'pinn1', '位': 'ui7',
        '足': 'tsiok4', '閣': 'kik4', '逐': 'tsiok4', '只': 'tsin1', 
        '欲': 'bun7', '愛': 'ai3',
    }
```

## 測試驗證

### 直接字典查詢
```bash
python3 << 'EOF'
from taiwanese_tts_v2 import TaiwaneseTextProcessor
processor = TaiwaneseTextProcessor()

# 驗證「甘」字
result = processor.process_text('甘', add_pauses=False, convert_chinese=False)
assert result == 'kan1', f"Expected 'kan1', got '{result}'"
print("✓ 「甘」字轉換正確")
EOF
```

### TTS 合成
```bash
curl -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "kan1-ho2"}'
# 返回: ✓ 音檔成功生成 (86KB)
```

## 未來改進方向

1. **動態詞彙載入**: 從外部 CSV/JSON 文件動態載入詞彙
2. **使用者自訂詞彙**: 允許使用者添加自訂的詞彙對應
3. **進階轉換器修復**: 修復 han2tts 模組的 `build_dictionary()` 問題
4. **詞彙覆蓋率統計**: 定期檢查遺漏的常用詞彙

## 版本資訊

- **修復日期**: 2024-12-24
- **修復內容**: 補充 21 個常用台語詞彙到基本字典
- **受影響模組**: 
  - `taiwanese_tts_v2.py` (TaiwaneseConverter)
  - `integrated_voice_chat_api.py` (Chat/TTS API)
- **狀態**: ✓ 已測試完成

## 相關文件

- [TLPA_CONVERSION_FLOW.md](TLPA_CONVERSION_FLOW.md) - 台羅轉換完整流程
- [QUICK_REFERENCE_TLPA.md](QUICK_REFERENCE_TLPA.md) - API 快速參考
- [test_complete_tlpa_flow.py](test_complete_tlpa_flow.py) - 完整測試腳本
