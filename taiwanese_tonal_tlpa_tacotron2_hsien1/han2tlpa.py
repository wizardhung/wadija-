# han2tlpa.py
# -*- coding: utf-8 -*-
import csv
import os
import re
import sys
import unicodedata
from typing import Dict, List, Tuple

# 斷詞／揀詞／語言模型
from 臺灣言語工具.斷詞.拄好長度辭典揣詞 import 拄好長度辭典揣詞
from 臺灣言語工具.斷詞.語言模型揀集內組 import 語言模型揀集內組
# 拆句／建立詞物件
from 臺灣言語工具.解析整理.拆文分析器 import 拆文分析器
from 臺灣言語工具.解析整理.解析錯誤 import 解析錯誤
from 臺灣言語工具.語言模型.實際語言模型 import 實際語言模型
# 辭典（漢字→羅馬字）
from 臺灣言語工具.辭典.型音辭典 import 型音辭典
# TLPA（數字調）輸出
from 臺灣言語工具.音標系統.閩南語.臺灣語言音標 import 臺灣語言音標  # TLPA

# ===== 路徑都寫在這裡 =====
BASE = r"D:\Users\User\Desktop\project\0912\taiwanese_tonal_tlpa_tacotron2"
LEXICON_TSV  = os.path.join(BASE, "lexicon.tsv")   # 你的主詞表（可不存在）
PHRASES_TSV  = os.path.join(BASE, "phrases.tsv")   # 硬指定讀法（整句）
END_TSV      = os.path.join(BASE, "end.tsv")       # 句尾語氣詞名單（例：咧\t--leh）
# ========================

#（可選）內建幾個基本詞，避免詞表空時完全無法轉
BUILTIN_PAIRS = [
    ("電腦", "tian7-nau2"), ("會", "e7"), ("講", "kong2"), ("台語", "tai5-gi2"),
    ("明仔載", "bing5-a2-tsai3"), ("開會", "khui1-hue7"), ("簡報", "kian2-po3"),
    ("記得", "ki3-tit4"), ("今天", "kin1-jit8"), ("明天", "bing5-thian1"),
]

def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)

def normalize_lomaji(s: str) -> str:
    s = nfc(s.strip())
    s = s.replace("－", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", "-", s)     # 空白全變成連字號，避免「詞內含空白」對不齊
    s = re.sub(r"-{2,}", "-", s)
    return s

def load_lexicon_pairs(tsv_path: str) -> List[Tuple[str, str]]:
    pairs = []
    if not os.path.exists(tsv_path):
        return pairs
    with open(tsv_path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row or len(row) < 2: continue
            han, lomaji = row[0].strip(), row[1].strip()
            if not han or not lomaji or han.startswith("#"): continue
            pairs.append((nfc(han), normalize_lomaji(lomaji)))
    return pairs

def load_phrases(tsv_path: str) -> Dict[str, str]:
    """整句優先表：漢字句 -> 羅馬字（直接輸出用）"""
    d = {}
    if not os.path.exists(tsv_path):
        return d
    with open(tsv_path, encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if not row or len(row) < 2: continue
            han = nfc(row[0].strip())
            lomaji = normalize_lomaji(row[1])
            if han and lomaji and not han.startswith("#"):
                d[han] = lomaji
    return d

def load_endings(tsv_path: str) -> List[str]:
    """句尾語氣詞的『漢字鍵』清單（長度優先，避免多字尾被短字搶先）"""
    keys = []
    if not os.path.exists(tsv_path):
        return keys
    with open(tsv_path, encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if not row: continue
            key = row[0].strip()
            if not key or key.startswith("#"): continue
            keys.append(nfc(key))
    keys.sort(key=len, reverse=True)  # 先比長的尾
    return keys

def build_dict(lex_pairs: List[Tuple[str, str]]) -> 型音辭典:
    d = 型音辭典(4)
    for han, lomaji in lex_pairs:
        try:
            d.加詞(拆文分析器.建立詞物件(han, lomaji))
        except 解析錯誤:
            continue
    return d

def han_to_tlpa_number(sentence_han: str, 辭典: 型音辭典) -> str:
    語言模型 = 實際語言模型(2)  # Demo：雙元語言模型
    句 = (拆文分析器.建立句物件(sentence_han)
          .揣詞(拄好長度辭典揣詞, 辭典)
          .揀(語言模型揀集內組, 語言模型))
    out = 句.轉音(臺灣語言音標).看音()
    return " ".join(out.split())  # 壓成單一空白

# 分詞/標點簡易判別
_WORD_RE = re.compile(r"[0-9A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u0300-\u036F\-]+")
def _split_tokens(s: str):
    # word(含重音/變音符、數字、連字號) 或 非空白單字元（當成標點）
    return re.findall(r"[0-9A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u0300-\u036F\-]+|[^\s]", s)

def _is_word(tok: str) -> bool:
    return bool(_WORD_RE.fullmatch(tok))

def _join_tokens(tokens) -> str:
    out = []
    for i, tok in enumerate(tokens):
        if i > 0 and _is_word(tok) and _is_word(tokens[i-1]):
            out.append(" ")
        out.append(tok)
    return "".join(out)

_TRAIL_PUNCT_RE = re.compile(r"[，,。．！？!？…⋯、；;：:~～—\-——（）()《》「」『』【】\s]*$")

def merge_tail_if_ending(sentence_han: str, tlpa_out: str, ending_keys: List[str]) -> str:
    # 去掉句尾標點後判斷
    core = _TRAIL_PUNCT_RE.sub("", sentence_han.strip())
    matched = None
    for key in ending_keys:
        if core.endswith(key):
            matched = key
            break
    if not matched:
        return tlpa_out

    tokens = _split_tokens(tlpa_out)
    # 從尾端找最後兩個「詞」索引
    word_idx = [i for i, t in enumerate(tokens) if _is_word(t)]
    if len(word_idx) < 2:
        return tlpa_out
    i2 = word_idx[-1]  # 最後一個詞
    i1 = word_idx[-2]  # 倒數第二個詞

    tokens[i1] = tokens[i1] + "-" + tokens[i2]
    del tokens[i2]
    return _join_tokens(tokens)

def main():
    if len(sys.argv) < 2:
        print("用法：python han2tlpa.py <漢字句>", file=sys.stderr)
        sys.exit(2)

    sentence = nfc(" ".join(sys.argv[1:]).strip())

    # 1) 先查硬指定整句
    phrases = load_phrases(PHRASES_TSV)
    if sentence in phrases:
        print(phrases[sentence])
        return

    # 2) 載入詞表並建立辭典（這段是你漏掉的）
    lex_pairs: List[Tuple[str, str]] = []
    lex_pairs.extend(BUILTIN_PAIRS)                # 可保留/刪除，視需求
    lex_pairs.extend(load_lexicon_pairs(LEXICON_TSV))
    辭典 = build_dict(lex_pairs)

    # 3) 正常轉 TLPA
    tlpa = han_to_tlpa_number(sentence, 辭典)

    # 4) 若句尾是 end.tsv 的語尾，併最後兩詞
    endings = load_endings(END_TSV)
    tlpa = merge_tail_if_ending(sentence, tlpa, endings)

    print(tlpa)

if __name__ == "__main__":
    main()
