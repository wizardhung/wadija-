#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import re
import sys
import time
import unicodedata
import warnings
from datetime import datetime
from typing import Dict, List, Tuple

# 設定環境變數以避免警告
warnings.filterwarnings("ignore")
os.environ['KMP_WARNINGS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# 匯入臺灣言語工具相關模組
from 臺灣言語工具.斷詞.拄好長度辭典揣詞 import 拄好長度辭典揣詞
from 臺灣言語工具.斷詞.語言模型揀集內組 import 語言模型揀集內組
from 臺灣言語工具.解析整理.拆文分析器 import 拆文分析器
from 臺灣言語工具.解析整理.文章粗胚 import 文章粗胚
from 臺灣言語工具.解析整理.解析錯誤 import 解析錯誤
from 臺灣言語工具.語言模型.實際語言模型 import 實際語言模型
from 臺灣言語工具.辭典.型音辭典 import 型音辭典
from 臺灣言語工具.音標系統.閩南語.臺灣語言音標 import 臺灣語言音標
from 臺灣言語工具.音標系統.閩南語.臺灣閩南語羅馬字拼音 import 臺灣閩南語羅馬字拼音

# 引入 TTS 相關模組
try:
    import numpy as np
    import torch

    # 設定模型路徑，稍後會添加路徑處理
    PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tacotron2")
    sys.path.append(PROJECT_DIR)
    sys.path.append(os.path.join(PROJECT_DIR, "waveglow"))
    
    from denoiser import Denoiser
    from glow import WaveGlow
    from hparams import create_hparams
    from model import Tacotron2
    from scipy.io.wavfile import write as wavwrite
    from text import text_to_sequence
    
    TTS_AVAILABLE = True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.set_grad_enabled(False)
    
    print(f"TTS 模組載入成功，使用裝置: {device}")
except ImportError as e:
    print(f"無法載入 TTS 相關模組，將只提供文字轉換功能: {e}", file=sys.stderr)
    TTS_AVAILABLE = False

# 設定路徑
BASE = os.path.dirname(os.path.abspath(__file__))
CHHOETAIGI_CSV = os.path.join(BASE, "ChhoeTaigi_KauiokpooTaigiSutian.csv")
END_TSV = os.path.join(BASE, "end.tsv")
PHRASES_TSV = os.path.join(BASE, "phrases.tsv")
LEXICON_TSV = os.path.join(BASE, "lexicon.tsv")

# TTS 相關路徑
TACOTRON_CKPT = os.path.join(BASE, "tacotron2", "model", "checkpoint_100000")
WAVEGLOW_CKPT = os.path.join(BASE, "tacotron2", "model", "waveglow", "waveglow_main.pt")
OUT_DIR = os.path.join(BASE, "wavs")

# 確保輸出目錄存在
os.makedirs(OUT_DIR, exist_ok=True)

# 可調參數
MAX_WORD_LEN = 6             # 辭典允許的最長詞長
LM_ORDER = 3                 # 語言模型 n-gram：3 較顧脈絡

# TTS 聲音調整參數
CHILDIFY = True              # 使聲音更像兒童聲音，設為False則保持原聲
PITCH_STEPS = 4              # 升高的半音數（3-6常見，值越大聲音越高）

# 預設常用詞彙
BUILTIN_PAIRS = [
    ("電腦", "tian7-nau2"), ("會", "e7"), ("講", "kong2"), ("台語", "tai5-gi2"),
    ("明仔載", "bing5-a2-tsai3"), ("開會", "khui1-hue7"), ("簡報", "kian2-po3"),
    ("記得", "ki3-tit4"), ("今天", "kin1-a2-jit8"), ("明天", "bin5-a2-jit8"),
    ("大家", "tai7-ke1"), ("大家", "tak8-ke1"), ("好", "ho2"), ("我", "gua2"),
    ("是", "si7"), ("的", "e5"), ("機器人", "ki1-khi3-lang5"),
]

# 特定句型模式 (使用空列表避免寫死特定句型)
SPECIAL_PATTERNS = []

# 支援的標點符號
PUNCTUATION_MARKS = {
    '，': ',', '。': '.', '！': '!', '？': '?', '、': ',', 
    '；': ';', '：': ':', '「': '"', '」': '"', '『': ''', '』': ''',
    '（': '(', '）': ')', '《': '<', '》': '>', '…': '...', '⋯': '...'
}

def nfc(s: str) -> str:
    """Unicode 正規化"""
    return unicodedata.normalize("NFC", s)

def load_chhoetaigi_dictionary() -> Dict[str, str]:
    """載入楚台辭典的資料"""
    dictionary = {}
    
    # 手動添加核心詞彙，避免常用詞彙轉換錯誤
    manual_entries = {}
    dictionary.update(manual_entries)
    
    try:
        # 載入 CSV 辭典
        with open(CHHOETAIGI_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 漢字對應數字調拼音
                if row.get('HanLoTaibunKip') and row.get('KipInput'):
                    hanzi = row['HanLoTaibunKip'].strip()
                    kipin = row['KipInput'].strip()
                    if hanzi and kipin:
                        # 過濾掉非台語字或括號內的替代字
                        hanzi = re.sub(r'\([^)]*\)', '', hanzi).strip()
                        kipin = re.sub(r'\([^)]*\)', '', kipin).strip()
                        if hanzi and kipin:
                            # 如果不是手動添加的詞彙，才加入
                            if hanzi not in manual_entries:
                                dictionary[hanzi] = kipin
                            
                            # 同時添加單字詞彙，方便未知詞拆解
                            if len(hanzi) == 1 and hanzi not in dictionary:
                                dictionary[hanzi] = kipin
        
        print(f"成功載入詞典，共 {len(dictionary)} 個詞條")
    except Exception as e:
        print(f"載入楚台辭典資料時發生錯誤: {e}", file=sys.stderr)
    
    return dictionary

def load_lexicon_pairs(tsv_path: str) -> List[Tuple[str, str]]:
    """載入既有詞彙表"""
    pairs = []
    if not os.path.exists(tsv_path): return pairs
    try:
        with open(tsv_path, encoding="utf-8") as f:
            for row in csv.reader(f, delimiter="\t"):
                if not row or len(row) < 2: continue
                han, lomaji = row[0].strip(), row[1].strip()
                if not han or not lomaji or han.startswith("#"): continue
                pairs.append((nfc(han), normalize_tlpa_to_numeric(lomaji)))
    except Exception as e:
        print(f"載入詞彙表時發生錯誤: {e}", file=sys.stderr)
    return pairs

def normalize_tlpa_to_numeric(s: str) -> str:
    """將台羅拼音標記轉換為數字調標記"""
    # TLPA 聲調符號對應到數字調
    tone_map = {
        'á': 'a2', 'é': 'e2', 'í': 'i2', 'ó': 'o2', 'ú': 'u2', 
        'à': 'a3', 'è': 'e3', 'ì': 'i3', 'ò': 'o3', 'ù': 'u3',
        'â': 'a5', 'ê': 'e5', 'î': 'i5', 'ô': 'o5', 'û': 'u5',
        'ā': 'a7', 'ē': 'e7', 'ī': 'i7', 'ō': 'o7', 'ū': 'u7',
        'a̍': 'a8', 'e̍': 'e8', 'i̍': 'i8', 'o̍': 'o8', 'u̍': 'u8',
        'ă': 'a4', 'ĕ': 'e4', 'ĭ': 'i4', 'ŏ': 'o4', 'ŭ': 'u4',
        'ń': 'n2', 'ǹ': 'n3', 'n̂': 'n5', 'n̄': 'n7', 'n̍': 'n8',
        'ḿ': 'm2', 'm̀': 'm3', 'm̂': 'm5', 'm̄': 'm7', 'm̍': 'm8',
    }
    
    # 將輸入拆解成 NFD 形式，以便處理組合字符
    nfd_text = unicodedata.normalize('NFD', s)
    
    # 替換 TLPA 標記為數字調
    result = ''
    i = 0
    while i < len(nfd_text):
        char = nfd_text[i]
        if i+1 < len(nfd_text) and nfd_text[i+1] in ['\u0301', '\u0300', '\u0302', '\u0304', '\u030d', '\u0308']:
            # 檢查是否為帶有聲調標記的字符
            combined = unicodedata.normalize('NFC', char + nfd_text[i+1])
            if combined in tone_map:
                result += tone_map[combined][0]  # 添加基本字母
                # 保存數字調標記，稍後添加到音節尾
                tone_number = tone_map[combined][1]
                i += 2
                continue
        result += char
        i += 1
    
    # 處理沒有聲調標記的音節，預設為第一聲
    # 先分割音節 (假設以連字符號分隔)
    syllables = result.replace('-', ' - ').split()
    processed_syllables = []
    
    for i, syllable in enumerate(syllables):
        if syllable == '-':
            processed_syllables.append(syllable)
            continue
            
        # 檢查是否已有數字尾碼
        if syllable and syllable[-1].isdigit():
            processed_syllables.append(syllable)
            continue
            
        # 檢查是否為合法音節
        has_vowel = any(c in 'aeiou' for c in syllable)
        if has_vowel:
            processed_syllables.append(syllable + '1')  # 預設加上第一聲
        else:
            processed_syllables.append(syllable)  # 非音節直接保留
    
    # 重新組合音節
    result = ''.join(processed_syllables).replace(' - ', '-')
    
    # 修正任何連接問題
    result = re.sub(r'([0-9])-', r'\1-', result)  # 確保數字後的連接符號正確
    
    return result

def load_phrases(tsv_path: str) -> Dict[str, str]:
    """載入片語表"""
    d = {}
    if not os.path.exists(tsv_path): return d
    try:
        with open(tsv_path, encoding="utf-8") as f:
            for row in csv.reader(f, delimiter="\t"):
                if not row or len(row) < 2: continue
                han = nfc(row[0].strip())
                lomaji = normalize_tlpa_to_numeric(row[1].strip())
                if han and lomaji and not han.startswith("#"):
                    d[han] = lomaji
    except Exception as e:
        print(f"載入片語表時發生錯誤: {e}", file=sys.stderr)
    return d

def load_endings(tsv_path: str) -> List[str]:
    """載入句尾詞表"""
    keys = []
    if not os.path.exists(tsv_path): return keys
    try:
        with open(tsv_path, encoding="utf-8") as f:
            for row in csv.reader(f, delimiter="\t"):
                if not row: continue
                key = row[0].strip()
                if not key or key.startswith("#"): continue
                keys.append(nfc(key))
        keys.sort(key=len, reverse=True)
    except Exception as e:
        print(f"載入句尾詞表時發生錯誤: {e}", file=sys.stderr)
    return keys

def build_dict(lex_pairs: List[Tuple[str, str]], max_len: int = MAX_WORD_LEN) -> 型音辭典:
    """建立斷詞用的辭典物件
    
    根據臺灣言語工具官方文檔，使用對齊詞物件來建立詞典
    """
    d = 型音辭典(max_len)
    for han, lomaji in lex_pairs:
        try:
            # 根據官方文檔範例，使用對齊詞物件
            詞物件 = 拆文分析器.對齊詞物件(han, lomaji)
            d.加詞(詞物件)
        except 解析錯誤 as e:
            print(f"詞彙 '{han}' -> '{lomaji}' 加入詞典失敗: {e}", file=sys.stderr)
            pass
    return d

def split_sentences_keep_punct(text: str) -> List[str]:
    """分句，保留標點符號"""
    # 分句用的正規表達式
    _SENT_SPLIT_RE = re.compile(r'([。．！？!?…⋯])')
    
    parts = _SENT_SPLIT_RE.split(text)
    out = []
    cur = ""
    for p in parts:
        if not p: continue
        cur += p
        if _SENT_SPLIT_RE.fullmatch(p):
            out.append(cur.strip())
            cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out

def _split_tokens(s: str):
    return re.findall(r"[0-9A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u0300-\u036F\-]+|[^\s]", s)

def _is_word(tok: str) -> bool:
    _WORD_RE = re.compile(r"[0-9A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u0300-\u036F\-]+")
    return bool(_WORD_RE.fullmatch(tok))

def _join_tokens(tokens) -> str:
    out = []
    for i, tok in enumerate(tokens):
        if i > 0 and _is_word(tok) and _is_word(tokens[i-1]): out.append(" ")
        out.append(tok)
    return "".join(out)

def merge_tail_if_ending(sentence_han: str, numeric_out: str, ending_keys: List[str]) -> str:
    """處理句尾詞"""
    _TRAIL_PUNCT_RE = re.compile(r"[，,。．！？!？…⋯、；;：:~～—\-——（）()《》「」『』【】\s]*$")
    
    core = _TRAIL_PUNCT_RE.sub("", sentence_han.strip())
    for key in ending_keys:
        if core.endswith(key):
            tokens = _split_tokens(numeric_out)
            word_idx = [i for i, t in enumerate(tokens) if _is_word(t)]
            if len(word_idx) >= 2:
                i2 = word_idx[-1]; i1 = word_idx[-2]
                tokens[i1] = tokens[i1] + "-" + tokens[i2]
                del tokens[i2]
                return _join_tokens(tokens)
            break
    return numeric_out

# —— TTS 合成器類別 ——
class Synthesizer:
    """文字轉語音合成器"""
    def __init__(self, tacotron_ckpt: str, waveglow_ckpt: str):
        """初始化 TTS 模型"""
        if not TTS_AVAILABLE:
            raise ImportError("TTS 相關模組未正確載入，無法初始化合成器")
            
        self.hparams = create_hparams()
        self.hparams.sampling_rate = 22050
        self.hparams.max_decoder_steps = 3000
        self.hparams.fp16_run = False

        # 載入 Tacotron2 模型
        print("載入 Tacotron2 模型中...")
        self.tacotron = Tacotron2(self.hparams)
        self.tacotron.load_state_dict(torch.load(tacotron_ckpt, map_location=device)['state_dict'])
        self.tacotron = self.tacotron.to(device).eval()

        # 載入 WaveGlow 模型
        print("載入 WaveGlow 模型中...")
        self.waveglow = torch.load(waveglow_ckpt, map_location=device)['model']
        try:
            from glow import remove_weightnorm as _rm
            self.waveglow = _rm(self.waveglow)
        except Exception:
            import torch.nn.utils as _nnutils
            for m in self.waveglow.modules():
                try: _nnutils.remove_weight_norm(m)
                except Exception: pass
        self.waveglow = self.waveglow.to(device).eval()
        for k in getattr(self.waveglow, 'convinv', []):
            try: k.float()
            except Exception: pass
        self.denoiser = Denoiser(self.waveglow, device=device)
        print("TTS 模型載入完成")

    def tts(self, text: str, out_path: str, childify=None, pitch_steps=None) -> str:
        """將文字轉換為語音並保存為 WAV 檔案
        
        參數:
            text: 要合成的文字
            out_path: 輸出檔案路徑
            childify: 是否使聲音更像兒童 (None 使用全局設定)
            pitch_steps: 提高音高的半音數 (None 使用全局設定)
        """
        print(f"合成 TTS: {text}")
        
        # 使用全局設定或傳入參數
        use_childify = CHILDIFY if childify is None else childify
        
        # 如果使用兒童聲音，暫時不調整其他參數，避免回音和機器人聲音問題
        if use_childify:
            print(f"使用兒童聲音效果")
            use_pitch_steps = 0  # 不調整音高
        else:
            use_pitch_steps = PITCH_STEPS if pitch_steps is None else pitch_steps
            if use_pitch_steps > 0:
                print(f"提高音高 {use_pitch_steps} 個半音")
        
        # 處理文字，保留標點符號以確保 TTS 系統正確處理
        # 只將中文標點轉換為對應的英文標點，但保留原有結構
        text_for_tts = text
        for zh, en in PUNCTUATION_MARKS.items():
            text_for_tts = text_for_tts.replace(zh, en)
        print(f"TTS 處理文字: {text_for_tts}")
        
        seq = np.array(text_to_sequence(text_for_tts, ['basic_cleaners']))[None, :]
        seq = torch.from_numpy(seq).to(device=device, dtype=torch.int64)
        with torch.no_grad():
            _, mel, _, _ = self.tacotron.inference(seq)
            
            # 聲音調整 - 使用 childify 效果，但不調整音高
            if use_childify:
                # 兒童聲音效果但不進行音高調整
                audio = self.waveglow.infer(mel, sigma=0.666)
            elif use_pitch_steps > 0:
                # 僅在非兒童聲音模式下應用音高調整
                mel_shift = torch.zeros_like(mel)
                target_len = mel.size(2)
                shift_steps = min(use_pitch_steps, 6)  # 限制最大半音數
                
                for i in range(target_len):
                    for j in range(mel.size(1)):
                        if j + shift_steps < mel.size(1):
                            mel_shift[0, j + shift_steps, i] = mel[0, j, i]
                        else:
                            mel_shift[0, j, i] = mel[0, j, i]
                
                # 使用調整後的 mel 頻譜
                audio = self.waveglow.infer(mel_shift, sigma=0.666)
            else:
                # 使用原始 mel 頻譜
                audio = self.waveglow.infer(mel, sigma=0.666)
                
            audio = self.denoiser(audio, strength=0.01)[:, 0]
            audio = audio[0].data.cpu().numpy()
            audio *= 32767 / max(0.01, float(np.max(np.abs(audio))))
        
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        # 儲存音檔
        wavwrite(out_path, self.hparams.sampling_rate, audio.astype(np.int16))
        print(f"語音檔案已保存至: {out_path}")
        return out_path

def next_out_path() -> str:
    """產生下一個輸出檔案的路徑"""
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUT_DIR, f"{stamp}.wav")

def build_dictionary() -> 型音辭典:
    """建立完整詞典"""
    # 載入楚台辭典資料（優先使用）
    chhoetaigi_dict = load_chhoetaigi_dictionary()
    print(f"從 ChhoeTaigi_KauiokpooTaigiSutian.csv 載入了 {len(chhoetaigi_dict)} 個詞條")
    
    # 載入預設詞彙（保留核心詞彙）
    lex_pairs: List[Tuple[str, str]] = []
    lex_pairs.extend(BUILTIN_PAIRS)
    print(f"使用了 {len(BUILTIN_PAIRS)} 個內建詞條")
    
    # 轉換楚台辭典資料為配對格式
    chhoetaigi_pairs = [(k, v) for k, v in chhoetaigi_dict.items()]
    lex_pairs.extend(chhoetaigi_pairs)
    
    # 以下是可選的其他資料來源（目前暫時不使用）
    # if os.path.exists(LEXICON_TSV):
    #     lexicon_pairs = load_lexicon_pairs(LEXICON_TSV)
    #     lex_pairs.extend(lexicon_pairs)
    #     print(f"從 {LEXICON_TSV} 載入了 {len(lexicon_pairs)} 個詞條")
    
    return build_dict(lex_pairs, MAX_WORD_LEN)

def han_to_numeric(sentence_han: str, 辭典: 型音辭典) -> str:
    """白話文轉數字調
    
    根據臺灣言語工具官方使用方式：
    1. 先使用文章粗胚進行預處理（處理減號、符號等）
    2. 使用 拆文分析器.建立句物件() 建立句物件
    3. 使用 .揣詞() 進行斷詞
    4. 使用 .揀() 選擇最佳結果
    5. 使用 .看音() 取得音標
    """
    # 處理空字串或只有標點符號的情況
    if not sentence_han or re.match(r'^[，,。．！？!?…⋯、；;：:~～—\-——（）()《》「」『』【】\s]+$', sentence_han):
        return sentence_han
    
    try:
        # 根據官方文檔建議，使用文章粗胚進行預處理
        try:
            # 處理台語的輕聲標記和其他符號
            處理減號語句 = 文章粗胚.建立物件語句前處理減號(臺灣閩南語羅馬字拼音, sentence_han)
            加空白語句 = 文章粗胚.符號邊仔加空白(處理減號語句)
            預處理語句 = 加空白語句.strip()
        except Exception as e:
            print(f"預處理失敗，使用原始語句: {e}", file=sys.stderr)
            預處理語句 = sentence_han
        
        # 建立語言模型（根據文檔建議的使用方式）
        語言模型 = 實際語言模型(LM_ORDER)
        
        # 按照臺灣言語工具官方API使用方式進行處理
        句物件 = 拆文分析器.建立句物件(預處理語句)
        斷詞結果 = 句物件.揣詞(拄好長度辭典揣詞, 辭典)
        最佳結果 = 斷詞結果.揀(語言模型揀集內組, 語言模型)
        
        # 取得分詞結果，轉換為數字調格式
        words = []
        for 詞 in 最佳結果.網出詞物件():
            word = 詞.看音()
            # 確保已經是數字調格式
            if not re.search(r'\d', word):
                word = normalize_tlpa_to_numeric(word)
            words.append(word)
        
        result = " ".join(words)
        
        # 檢查結果是否包含原始漢字（未轉換），若有則嘗試單字轉換
        if any(c for c in result if '\u4e00' <= c <= '\u9fff'):
            # 處理未轉換的漢字
            chars = []
            for c in sentence_han:
                if '\u4e00' <= c <= '\u9fff':
                    try:
                        單字句物件 = 拆文分析器.建立句物件(c)
                        單字斷詞 = 單字句物件.揣詞(拄好長度辭典揣詞, 辭典)
                        單字結果 = 單字斷詞.揀(語言模型揀集內組, 語言模型)
                        tone = 單字結果.看音()
                        if not re.search(r'\d', tone):
                            tone = normalize_tlpa_to_numeric(tone)
                        chars.append(tone)
                    except (解析錯誤, Exception) as e:
                        print(f"單字 '{c}' 轉換失敗: {e}", file=sys.stderr)
                        chars.append(f"*{c}*")  # 標記未轉換的字
                else:
                    chars.append(c)
            # 如果單字轉換的結果更好（包含更少的原始漢字），則使用單字轉換結果
            chars_result = "".join(chars)
            if chars_result.count('*') < sum(1 for c in result if '\u4e00' <= c <= '\u9fff'):
                result = chars_result
        
        return result
    except (解析錯誤, Exception) as e:
        print(f"轉換時發生錯誤: {e}", file=sys.stderr)
        # 轉換失敗時，返回原始輸入，但加上標記
        return f"<轉換失敗>{sentence_han}</轉換失敗>"

def handle_special_patterns(text: str, dictionary=None) -> str:
    """處理特殊句型模式"""
    # 處理像「賣茶說茶香，賣花說花紅」這樣包含兩個句子的情況
    if "，" in text or "," in text:
        # 分割句子
        if "，" in text:
            parts = text.split("，")
        else:
            parts = text.split(",")
            
        if len(parts) == 2:
            part1, part2 = parts
            # 分別處理每個部分
            result1 = handle_special_patterns(part1)
            result2 = handle_special_patterns(part2)
            
            # 如果兩個部分都成功翻譯，合併結果
            if result1 and result2:
                return f"{result1},{result2}"
                
    # 移除標點符號以便匹配
    clean_text = re.sub(r'[，,。．！？!?…⋯、；;：:~～—\-——（）()《》「」『』【】\s]', '', text)
    
    # 完全匹配
    for pattern, replacement in SPECIAL_PATTERNS:
        if clean_text == pattern:
            return replacement
        # 檢查部分匹配
        elif pattern in clean_text:
            # 提取標點符號
            punctuation = ''
            for char in text:
                if re.match(r'[，,。．！？!?…⋯、；;：:~～—\-——（）()《》「」『』【】]', char):
                    punctuation = char
                    break
            
            # 如果有標點，添加到結果
            if punctuation:
                return f"{replacement}{punctuation}"
            else:
                return replacement
    
    return None

def han_to_numeric_full(text_han: str, 辭典: 型音辭典) -> str:
    """完整處理白話文轉數字調，包含分句及標點符號處理"""
    # 先處理常見的標點符號和空格，確保分詞正確
    text_han = re.sub(r'\s+', ' ', text_han)  # 規範化空格
    
    # 檢查特殊句型模式
    special_result = handle_special_patterns(text_han)
    if special_result:
        return special_result
    
    # 分句處理
    sentences = split_sentences_keep_punct(nfc(text_han.strip()))
    out_chunks = []
    
    # 載入片語表，用於特殊情況處理
    phrases = load_phrases(PHRASES_TSV)
    
    for sent in sentences:
        # 檢查是否整句話在片語表中
        sent_clean = re.sub(r'[，,。．！？!?…⋯、；;：:~～—\-——（）()《》「」『』【】\s]', '', sent)
        if sent_clean in phrases:
            out_chunks.append(phrases[sent_clean])
            continue

        # 嘗試查找句子中較長的片語
        has_phrase = False
        for phrase, numeric in sorted(phrases.items(), key=lambda x: len(x[0]), reverse=True):
            if phrase in sent_clean and len(phrase) >= 3:  # 只處理較長的片語
                # 分段處理，將句子分成片語前、片語和片語後三部分
                before, rest = sent_clean.split(phrase, 1)
                if before:
                    numeric_before = han_to_numeric(before, 辭典)
                    out_chunks.append(numeric_before)
                out_chunks.append(numeric)
                if rest:
                    numeric_rest = han_to_numeric(rest, 辭典)
                    out_chunks.append(numeric_rest)
                has_phrase = True
                break
                
        # 如果沒有找到片語，進行一般處理
        if not has_phrase:
            # 進行字詞切分及轉換
            numeric = han_to_numeric(sent, 辭典)
            
            # 檢查是否有未翻譯的漢字（通常表現為單個孤立的漢字）
            hanzi_pattern = re.compile(r'[\u4e00-\u9fff]')
            if hanzi_pattern.search(numeric):
                # 對未翻譯的部分進行單字級別的翻譯
                tokens = re.findall(r'[\u4e00-\u9fff]+|[^\s\u4e00-\u9fff]+', numeric)
                processed_tokens = []
                for token in tokens:
                    if hanzi_pattern.search(token):
                        # 單字級別翻譯
                        char_tokens = []
                        for char in token:
                            if hanzi_pattern.search(char):
                                # 嘗試查詞典
                                if char in 辭典.表:
                                    char_numeric = han_to_numeric(char, 辭典)
                                    char_tokens.append(char_numeric)
                                else:
                                    # 如果字典中沒有，保留原字但加上標記
                                    char_tokens.append(f"*{char}*")
                            else:
                                char_tokens.append(char)
                        processed_tokens.append(" ".join(char_tokens))
                    else:
                        processed_tokens.append(token)
                numeric = " ".join(processed_tokens)
            
            out_chunks.append(numeric)
    
    # 將句子連接，但保留標點符號的位置和換行
    result = " ".join(out_chunks)
    
    # 處理標點符號：確保標點符號與前面的詞語緊密相連，沒有多餘的空格
    punctuation_pattern = ' ([' + ''.join(list(PUNCTUATION_MARKS.keys()) + list(PUNCTUATION_MARKS.values())) + '])'
    result = re.sub(punctuation_pattern, r'\1', result)
    
    # 確保逗號、分號、冒號等不會有尾隨空格
    trailing_space_pattern = r'([,，、；;：:]) '
    result = re.sub(trailing_space_pattern, r'\1', result)
    
    # 移除多餘空格，但確保保留所有原有標點符號
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result

def main():
    """主程式"""
    import argparse

    # 解析命令行參數
    parser = argparse.ArgumentParser(description='白話文轉數字調與 TTS 合成')
    parser.add_argument('text', nargs='+', help='要轉換的白話文句子')
    parser.add_argument('--no-tts', action='store_true', help='不執行 TTS 合成，僅輸出數字調文字')
    parser.add_argument('--output', '-o', help='指定輸出檔案名稱，僅適用於 TTS 模式')
    parser.add_argument('--adult-voice', action='store_true', help='使用成人聲音（關閉兒童聲音效果）')
    parser.add_argument('--pitch', type=int, choices=range(0, 7), help='聲音音高調整，0-6之間的值（數值越大聲音越高）')
    
    args = parser.parse_args()
    
    # 記錄開始時間
    start_time = datetime.now()
    
    # 合併輸入文字
    text_han = " ".join(args.text)
    
    # 只載入字典資料
    dictionary = build_dictionary()

    # 轉換為數字調
    numeric_text = han_to_numeric_full(text_han, dictionary)

    # 輸出文字結果
    print(f"輸入：{text_han}")
    print(f"輸出：{numeric_text}")
    
    # 計算處理時間
    processing_time = datetime.now() - start_time
    print(f"文字處理耗時：{processing_time.total_seconds():.3f} 秒")
    
    # 執行 TTS 合成（如果未禁用）
    if not args.no_tts and TTS_AVAILABLE:
        try:
            # 記錄 TTS 開始時間
            tts_start_time = datetime.now()
            
            # 初始化 TTS 合成器
            synthesizer = Synthesizer(TACOTRON_CKPT, WAVEGLOW_CKPT)
            
            # 決定輸出路徑
            if args.output:
                # 使用者指定的輸出檔案名稱
                out_path = args.output
                if not out_path.endswith('.wav'):
                    out_path += '.wav'
                # 確保路徑是絕對路徑
                if not os.path.isabs(out_path):
                    out_path = os.path.join(os.getcwd(), out_path)
            else:
                # 自動生成輸出檔案名稱
                out_path = next_out_path() # 這個函數已經實作在上面了
            
            # 設定聲音參數
            childify = not args.adult_voice  # 如果指定adult_voice，則不使用兒童聲音
            pitch_steps = args.pitch if args.pitch is not None else PITCH_STEPS
            
            voice_type = "兒童聲音" if childify else "成人聲音"
            if childify:
                print(f"[TTS] 使用{voice_type}")
            else:
                print(f"[TTS] 使用{voice_type}，音高調整: {pitch_steps}")
            
            # 執行 TTS 合成
            synthesizer.tts(numeric_text, out_path, childify=childify, pitch_steps=pitch_steps)
            
            # 計算 TTS 時間
            tts_time = datetime.now() - tts_start_time
            total_time = datetime.now() - start_time
            
            print(f"[TTS] 語音已儲存至：{out_path}")
            print(f"[TTS] 合成耗時：{tts_time.total_seconds():.3f} 秒")
            print(f"[總計] 總處理時間：{total_time.total_seconds():.3f} 秒")
            
            # 嘗試自動播放音檔
            try:
                import platform
                if platform.system() == 'Windows':
                    os.system(f'start {out_path}')
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'afplay {out_path}')
                elif platform.system() == 'Linux':
                    os.system(f'aplay {out_path}')
            except Exception as e:
                print(f"無法自動播放音檔: {e}")
                
        except Exception as e:
            print(f"TTS 合成失敗: {e}", file=sys.stderr)
            
            # 即使失敗也顯示總時間
            total_time = datetime.now() - start_time
            print(f"[總計] 總處理時間：{total_time.total_seconds():.3f} 秒")
    elif not TTS_AVAILABLE and not args.no_tts:
        print("TTS 功能未啟用，請確認相關模組已正確安裝", file=sys.stderr)
        
        # 顯示總時間
        total_time = datetime.now() - start_time
        print(f"[總計] 總處理時間：{total_time.total_seconds():.3f} 秒")

if __name__ == "__main__":
    main()