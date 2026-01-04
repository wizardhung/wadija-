# -*- coding: utf-8 -*-
"""
台語文字處理整合模組
結合 tai5-uan5_gian5-gi2_kang1-ku7 臺灣言語工具
支援漢字轉台羅拼音及數字調號格式
"""

import os
import re
import sys
import unicodedata
from typing import Dict, List, Optional, Tuple, Union

# 添加臺灣言語工具路徑
TAIWAN_LANG_TOOLS_PATH = os.path.join(os.path.dirname(__file__), "tai5-uan5_gian5-gi2_kang1-ku7")
if TAIWAN_LANG_TOOLS_PATH not in sys.path:
    sys.path.insert(0, TAIWAN_LANG_TOOLS_PATH)

try:
    from 臺灣言語工具.斷詞.拄好長度辭典揣詞 import 拄好長度辭典揣詞
    from 臺灣言語工具.解析整理.拆文分析器 import 拆文分析器
    from 臺灣言語工具.語音合成 import 台灣話口語講法
    from 臺灣言語工具.語音合成.閩南語音韻規則 import 閩南語音韻規則
    from 臺灣言語工具.辭典.型音辭典 import 型音辭典
    from 臺灣言語工具.音標系統.閩南語.臺灣閩南語羅馬字拼音 import 臺灣閩南語羅馬字拼音
    TAIWAN_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"警告：無法導入臺灣言語工具: {e}")
    TAIWAN_TOOLS_AVAILABLE = False

class TaiwaneseTextProcessor:
    """台語文字處理器"""
    
    def __init__(self, use_advanced_tools: bool = True):
        """
        初始化文字處理器
        
        Args:
            use_advanced_tools: 是否使用臺灣言語工具（需要安裝）
        """
        self.use_advanced_tools = use_advanced_tools and TAIWAN_TOOLS_AVAILABLE
        self.dictionary = None
        
        if self.use_advanced_tools:
            self._init_taiwan_tools()
        
        # 備用的簡單轉換字典（基本功能）
        self._init_basic_dict()
    
    def _init_taiwan_tools(self):
        """初始化臺灣言語工具"""
        try:
            # 建立基本辭典
            self.dictionary = 型音辭典(4)
            
            # 載入基本詞彙（可以根據需要擴充）
            basic_words = [
                ("我", "gua2"),
                ("你", "li2"),
                ("伊", "i1"),
                ("咱", "lan2"),
                ("恁", "lin2"),
                ("in", "in1"),
                ("是", "si7"),
                ("講", "kong2"),
                ("聽", "thiann1"),
                ("看", "khuann3"),
                ("食", "tsia8h"),
                ("飲", "lim1"),
                ("行", "kiann5"),
                ("坐", "tse7"),
                ("歇", "hioh4"),
                ("睏", "khun3"),
                ("好", "ho2"),
                ("歹", "phainn2"),
                ("大", "tua7"),
                ("細", "se3"),
                ("濟", "tse7"),
                ("少", "tso2"),
                ("台語", "tai5-gi2"),
                ("華語", "hua5-gi2"),
                ("英語", "ing1-gi2"),
            ]
            
            for han, tlpa in basic_words:
                try:
                    word_obj = 拆文分析器.建立詞物件(han, tlpa)
                    self.dictionary.加詞(word_obj)
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"初始化臺灣言語工具失敗: {e}")
            self.use_advanced_tools = False
    
    def _init_basic_dict(self):
        """初始化基本轉換字典（fallback）"""
        self.basic_dict = {
            # 基本代詞
            "我": "gua2",
            "你": "li2", 
            "伊": "i1",
            "是": "si7",
            "講": "kong2",
            "好": "ho2",
            "台語": "tai5-gi2",
            "機器人": "ki1-khi3-lang5",
            "大家": "tak8-ke1",
            "會": "e7",
            "說": "kong2",
            "的": "e5",
            "一": "tsi8t",
            "隻": "tsiah4",
            # 常用字 - 人名相關
            "阿": "a1",
            "強": "kiong5",
            "咱": "guan2",  # 或 lan2
            "台": "tai5",
            "北": "pak4",
            "天": "tshing1",
            "氣": "khi3",
            "較": "kha7",
            "冷": "ling2",
            "捏": "nia7",
            "南": "lam5",
            "咧": "ia7",  # 或 ue7
            "還": "huan5",
            "熱": "jua8h",
            "乎": "hoo7",
            # 其他常用字
            "和": "hua5",
            "在": "tsai7",
            "不": "put4",
            "有": "uu2",
            "無": "buu5",
            "來": "liah4",  # 或 lai5
            "去": "khi3",
            "過": "kueh4",
            "時": "tsi5",
            "那": "gua2",  # 或 tsia1
            "這": "tsia7",  # 或 tse7
            "做": "tsueh4",  # 或 tso3
            "給": "hoo7",
            "把": "pe2",
            "拿": "gia2",
            "看": "khuann3",
            "聽": "thiann1",
            "行": "kiann5",
            "來": "lai5",
            "去": "khu3",
            "到": "kua3",
            "著": "tio8h",
            "有": "uu7",
            "沒": "bue7",
            "著": "tsiok4",
            "呢": "ne1",
            "啦": "la7",
            "嘛": "ma7",
            "那": "tsia1",
            "得": "tik4",
            "所": "sua2",
            "以": "i2",
            "若": "gio8h",  # 或 jok4
            "啥": "tsi2",
            "物": "mi8h",  # 或 but4
            "項": "hong7",
            "擺": "puai2",
            "代": "tsi3",
            "年": "gui5",  # 或 lin5
            "月": "gue8h",
            "日": "jit4",
            "時": "tsi5",
            "刻": "khik4",
            "點": "tiam2",
            "鐘": "tsiong1",
            "鐘": "tsiong1",
            "尾": "bue2",
            "頭": "thau5",
            "面": "bin7",
            "身": "sin1",
            "心": "sim1",
            "手": "tshiu2",
            "腳": "kua2",
            "頭": "thau5",
            "囝": "gin2",
            "查": "tsha1",
            "某": "boo2",
            "父": "hu7",
            "母": "boo2",
            "兄": "hinn1",
            "弟": "tsi7",
            "姊": "tsia2",
            "妹": "bue7",
            "新": "sin1",
            "舊": "kiu7",
            "好": "ho2",
            "歹": "phainn2",
            "美": "bui2",
            "醜": "tshio2",
            "光": "kuinn1",
            "暗": "am3",
            "紅": "hong5",
            "白": "pe8h",
            "青": "tshing1",
            "黑": "tsi8h",
            "黃": "n5",
            "藍": "nn5",
            "紫": "tsi2",
            "綠": "lio8h",
            "橙": "tshinn5",
            "粉": "hun2",
            "灰": "hui1",
            "褐": "hua8h",
            "色": "sik4",
            "綠": "lio8h",
            "藍": "nn5",
            "黃": "n5",
            "橘": "tsi8h",
            "棕": "tsiong1",
            "銀": "gun5",
            "金": "kim1",
            "銅": "thn5",
            "鐵": "tshue7",
            "鋼": "kinn1",
            "玻": "po5",
            "璃": "li5",
            "木": "bo8h",
            "紙": "tsi2",
            "布": "poo3",
            "絹": "kuan2",
            "皮": "phuinn5",
            "毛": "m5",
            "絲": "si1",
            "線": "tshuann3",
            "繩": "tsiun5",
            "帶": "tua3",
            "草": "tshoo2",
            "竹": "tsiok4",
            "樹": "tshioh4",
            "花": "hue1",
            "葉": "hio8h",
            "根": "kin1",
            "莖": "tsiann5",
            "果": "kue2",
            "籽": "tsi2",
            "米": "bi2",
            "麥": "bik4",
            "豆": "tau7",
            "菜": "tshhai3",
            "肉": "bik4",
            "魚": "hi5",
            "蝦": "hia1",
            "蟹": "khuenn2",
            "蚌": "bong2",
            "貝": "puinn2",
            "蛋": "tuan3",
            "雞": "ke1",
            "鴨": "ah4",
            "鵝": "gueh5",
            "豬": "ti1",
            "牛": "gu5",
            "羊": "iunn5",
            "馬": "be2",
            "象": "tsiong3",
            "獅": "sai1",
            "虎": "hoo2",
            "貓": "buee1",
            "狗": "kau2",
            "鼠": "tshia2",
            "兔": "too3",
            "龍": "liong5",
            "蛇": "tsueh5",
            "猴": "kau5",
            "雞": "ke1",
            "狗": "kau2",
            "豬": "ti1",
            "鼠": "tshia2",
            "牛": "gu5",
            "虎": "hoo2",
            "兔": "too3",
            "龍": "liong5",
            "蛇": "tsueh5",
            "馬": "be2",
            "羊": "iunn5",
            "猴": "kau5",
        }
    
    def han_to_tlpa(self, text: str, format_type: str = "number") -> str:
        """
        漢字轉台羅拼音
        
        Args:
            text: 輸入的漢字文本
            format_type: 輸出格式 ("number": 數字調號, "diacritic": 符號調號)
            
        Returns:
            轉換後的台羅拼音
        """
        if self.use_advanced_tools:
            return self._advanced_han_to_tlpa(text, format_type)
        else:
            return self._basic_han_to_tlpa(text, format_type)
    
    def _advanced_han_to_tlpa(self, text: str, format_type: str = "number") -> str:
        """使用臺灣言語工具進行轉換"""
        try:
            # 建立章物件
            章物件 = 拆文分析器.建立章物件(text)
            
            # 轉音標
            標準章物件 = 章物件.轉音(臺灣閩南語羅馬字拼音)
            
            # 斷詞（如果有辭典）
            if self.dictionary:
                標準章物件 = 標準章物件.揣詞(拄好長度辭典揣詞, self.dictionary)
            
            # 套用音韻規則
            if format_type == "spoken":
                # 套用變調規則
                音值物件 = 標準章物件.轉音(臺灣閩南語羅馬字拼音, 函式='音值')
                結果 = 台灣話口語講法(音值物件)
            else:
                # 基本音標
                結果 = 標準章物件.看音()
            
            return self._format_output(結果, format_type)
            
        except Exception as e:
            print(f"高級轉換失敗，使用基本轉換: {e}")
            return self._basic_han_to_tlpa(text, format_type)
    
    def _basic_han_to_tlpa(self, text: str, format_type: str = "number") -> str:
        """基本的字典對應轉換 - 每個音節之間加入空格"""
        words = []
        for char in text:
            if char in self.basic_dict:
                # 漢字轉換為台羅拼音
                tlpa_syllable = self.basic_dict[char]
                words.append(tlpa_syllable)
            elif char.isspace():
                # 空格 - 用作詞界標記
                if words and words[-1] != " ":
                    words.append(" ")
            elif char in "，。！？；：":
                # 標點 - 保持為分隔符
                if words and words[-1] != " ":
                    words.append(" ")
                words.append(char)
                words.append(" ")
            else:
                # 未知字符 - 標記為 [x]
                words.append(f"[{char}]")
        
        # 加入空格在每個音節之間（除了標點）
        result = []
        for item in words:
            if item == " ":
                continue  # 暫時跳過空格標記
            elif item in "，。！？；：":
                result.append(item)
            else:
                if result and result[-1] not in "，。！？；：":
                    result.append(" ")
                result.append(item)
        
        # 清理結果
        final_text = "".join(result).strip()
        # 清理多餘空格
        final_text = re.sub(r'\s+', ' ', final_text)
        
        return self._format_output(final_text, format_type)
    
    def _format_output(self, tlpa: str, format_type: str) -> str:
        """格式化輸出"""
        if format_type == "number":
            # 數字調號格式（Tacotron2 標準）
            return tlpa
        elif format_type == "diacritic":
            # 轉換為符號調號（如果需要）
            return self._number_to_diacritic(tlpa)
        else:
            return tlpa
    
    def _number_to_diacritic(self, text: str) -> str:
        """數字調號轉符號調號（簡化版）"""
        # 這是一個簡化的轉換，實際使用可能需要更複雜的規則
        replacements = {
            "a1": "a",
            "a2": "á", 
            "a3": "à",
            "a4": "ah",
            "a5": "â",
            "a7": "ā",
            "a8": "a̍h",
            "e1": "e",
            "e2": "é",
            "e3": "è", 
            "e5": "ê",
            "e7": "ē",
            "i1": "i",
            "i2": "í",
            "i3": "ì",
            "i5": "î", 
            "i7": "ī",
            "o1": "o",
            "o2": "ó",
            "o3": "ò",
            "o5": "ô",
            "o7": "ō",
            "u1": "u",
            "u2": "ú", 
            "u3": "ù",
            "u5": "û",
            "u7": "ū",
        }
        
        result = text
        for num_tone, diac_tone in replacements.items():
            result = result.replace(num_tone, diac_tone)
        
        return result
    
    def preprocess_for_tacotron2(self, text: str, add_pauses: bool = True) -> str:
        """
        為 Tacotron2 預處理文本
        
        Args:
            text: 輸入文本
            add_pauses: 是否添加停頓符號
            
        Returns:
            適合 Tacotron2 的格式化文本
        """
        # 轉換為台羅拼音
        tlpa = self.han_to_tlpa(text, format_type="number")
        
        if add_pauses:
            # 在標點符號處添加停頓
            tlpa = re.sub(r'[，,]', ' , ', tlpa)
            tlpa = re.sub(r'[。.]', ' . ', tlpa)
            tlpa = re.sub(r'[！!]', ' ! ', tlpa)
            tlpa = re.sub(r'[？?]', ' ? ', tlpa)
            
        # 清理多餘空格
        tlpa = re.sub(r'\s+', ' ', tlpa).strip()
        
        return tlpa
    
    def batch_convert(self, texts: List[str], format_type: str = "number") -> List[str]:
        """批量轉換"""
        return [self.han_to_tlpa(text, format_type) for text in texts]


class TaiwaneseTextToSpeech:
    """整合的台語文字轉語音系統"""
    
    def __init__(self, tacotron_model_path: str, waveglow_model_path: str):
        """
        初始化 TTS 系統
        
        Args:
            tacotron_model_path: Tacotron2 模型路徑
            waveglow_model_path: WaveGlow 模型路徑
        """
        self.text_processor = TaiwaneseTextProcessor()
        
        # 這裡可以初始化 Tacotron2 和 WaveGlow 模型
        # 具體實現取決於您的模型載入方式
        self.tacotron_model_path = tacotron_model_path
        self.waveglow_model_path = waveglow_model_path
    
    def synthesize_from_han(self, han_text: str, output_path: str) -> str:
        """
        從漢字直接合成語音
        
        Args:
            han_text: 漢字文本
            output_path: 輸出音檔路徑
            
        Returns:
            處理後的台羅拼音文本
        """
        # 轉換為 Tacotron2 格式
        tlpa_text = self.text_processor.preprocess_for_tacotron2(han_text)
        
        print(f"[漢字] {han_text}")
        print(f"[台羅] {tlpa_text}")
        
        # 這裡會調用您現有的 TTS 合成邏輯
        # 例如：調用 han2tts.py 中的 Synthesizer 類
        
        return tlpa_text


def main():
    """測試函數"""
    processor = TaiwaneseTextProcessor()
    
    test_texts = [
        "大家好",
        "我是台語機器人", 
        "今天天氣真好",
        "你會講台語嗎？"
    ]
    
    print("=== 台語文字處理測試 ===")
    for text in test_texts:
        tlpa = processor.han_to_tlpa(text)
        formatted = processor.preprocess_for_tacotron2(text)
        print(f"原文: {text}")
        print(f"台羅: {tlpa}")
        print(f"格式化: {formatted}")
        print("-" * 40)


if __name__ == "__main__":
    main()