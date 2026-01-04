# -*- coding: utf-8 -*-
import csv
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

# 臺灣言語工具路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tai5-uan5_gian5-gi2_kang1-ku7"))

class AdvancedChineseToTaiwaneseConverter:
    """進階華文字轉台語漢字轉換器
    
    結合以下資源：
    1. 教育部台語字典 CSV 檔案 (ChhoeTaigi_KauiokpooTaigiSutian.csv)
    2. tai5-uan5_gian5-gi2_kang1-ku7 語言工具
    3. 手工維護的對照表
    """
    
    def __init__(self, csv_path: str = None):
        # 確保使用絕對路徑
        if csv_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(base_dir, "ChhoeTaigi_KauiokpooTaigiSutian.csv")
        self.csv_path = csv_path
        
        # 從CSV載入的字典
        self.csv_dict = {}
        # 詞彙對照字典
        self.word_dict = {}
        # 短語對照字典
        self.phrase_dict = {}
        
        # 手工維護的基本對照表 (從原本的字典保留)
        self.manual_dict = self._build_manual_dict()
        
        # 載入外部資源
        self._load_csv_dictionary()
        self._init_taiwan_tools()
        
        print(f"✓ 進階轉換器初始化完成")
        print(f"  - CSV字典條目: {len(self.csv_dict)}")
        print(f"  - 詞彙對照: {len(self.word_dict)}")
        print(f"  - 短語對照: {len(self.phrase_dict)}")
        print(f"  - 手工對照: {len(self.manual_dict)}")
    
    def _build_manual_dict(self) -> Dict[str, str]:
        """建立手工維護的基本對照表"""
        return {
            # 人稱代詞
            '我們': '阮',
            '我': '我',
            '你們': '恁',
            '你': '你',
            '他們': '𪜶',
            '他': '伊',
            '她': '伊',
            '它': '伊',
            
            # 家族稱謂
            '爸爸': '阿爸',
            '父親': '老父',
            '媽媽': '阿母',
            '母親': '阿母',
            '爺爺': '阿公',
            '祖父': '阿公',
            '奶奶': '阿嫲',
            '祖母': '阿嫲',
            '叔叔': '阿叔',
            '阿姨': '阿姨',
            '哥哥': '阿兄',
            '姐姐': '阿姊',
            '弟弟': '小弟',
            '妹妹': '小妹',
            
            # 常用動詞
            '吃': '食',
            '喝': '飲',
            '說': '講',
            '看': '看',
            '聽': '聽',
            '走': '行',
            '跑': '走',
            '睡覺': '睏',
            '睡': '睏',
            '買': '買',
            '賣': '賣',
            '來': '來',
            '去': '去',
            '回': '轉',
            '回家': '轉厝',
            '工作': '做工',
            '上班': '上班',
            '下班': '落班',
            '學習': '學',
            '讀書': '讀冊',
            '寫字': '寫字',
            '玩': '耍',
            '游泳': '沖水',
            '洗澡': '洗身軀',
            '穿': '穿',
            '脫': '褪',
            '開': '開',
            '關': '關',
            '打開': '開',
            '關閉': '關',
            
            # 時間詞彙
            '今天': '今仔日',
            '明天': '明仔載',
            '昨天': '昨昏',
            '現在': '這馬',
            '等一下': '等咧',
            '早上': '透早',
            '中午': '中晝',
            '下午': '下晡',
            '晚上': '暗時',
            '半夜': '半暝',
            '年': '年',
            '月': '月',
            '日': '日',
            '天': '天',
            '天氣': '天氣',
            '小時': '點鐘',
            '分鐘': '分',
            '秒': '秒',
            '星期': '禮拜',
            '週末': '禮拜',
            
            # 形容詞
            '漂亮': '媠',
            '美': '媠',
            '醜': '醜',
            '好': '好',
            '壞': '歹',
            '大': '大',
            '小': '細',
            '高': '懸',
            '矮': '短',
            '胖': '粗',
            '瘦': '幼',
            '長': '長',
            '短': '短',
            '新': '新',
            '舊': '舊',
            '快': '緊',
            '慢': '慢',
            '多': '濟',
            '少': '少',
            '貴': '貴',
            '便宜': '俗',
            '熱': '熱',
            '冷': '冷',
            '甜': '甜',
            '酸': '酸',
            '苦': '苦',
            '辣': '辣',
            '鹹': '鹹',
            '乾淨': '清氣',
            '髒': '垃圾',
            '累': '疲勞',
            '餓': '枵',
            '飽': '飽',
            '渴': '渴',
            
            # 醫療用詞
            '吃藥': '食藥',
            '看醫生': '看醫生',
            '生病': '生病',
            '感冒': '著感冒',
            '發燒': '發燒',
            '頭痛': '頭殼疼',
            '肚子痛': '腹肚疼',
            '牙痛': '齒疼',
            '醫院': '醫院',
            '診所': '診所',
            '藥': '藥',
            '藥水': '藥水',
            '藥丸': '藥丸仔',
            '打針': '拍針',
            '手術': '開刀',
            '檢查': '檢查',
            '復健': '復健',
            '護士': '護士',
            '醫師': '醫師',
            
            # 食物
            '飯': '飯',
            '麵': '麵',
            '麵包': '麵包',
            '菜': '菜',
            '肉': '肉',
            '魚': '魚',
            '蛋': '卵',
            '雞蛋': '雞卵',
            '牛奶': '牛奶',
            '水': '水',
            '茶': '茶',
            '咖啡': '咖啡',
            '果汁': '果汁',
            '水果': '果子',
            '蘋果': '蘋果',
            '香蕉': '芎蕉',
            '橘子': '柑仔',
            '米': '米',
            '油': '油',
            '鹽': '鹽',
            '糖': '糖',
            '醋': '醋',
            '醬油': '醬油',
            
            # 地點
            '家': '厝',
            '房子': '厝',
            '學校': '學校',
            '公司': '公司',
            '醫院': '醫院',
            '銀行': '銀行',
            '郵局': '郵局',
            '市場': '市場',
            '商店': '商店',
            '餐廳': '餐廳',
            '公園': '公園',
            '車站': '車頭',
            '機場': '飛行場',
            '台灣': '台灣',
            '台北': '台北',
            '台中': '台中',
            '台南': '台南',
            '高雄': '高雄',
            
            # 量詞和數詞
            '個': '个',
            '些': '寡',
            '點': '點',
            '次': '擺',
            '遍': '擺',
            '年': '年',
            '歲': '歲',
            
            # 語氣詞和助詞
            '的': '的',
            '了': '矣',
            '嗎': '無',
            '吧': '好無',
            '呢': '咧',
            '啊': '啊',
            '啦': '啦',
            '唷': '喔',
            '哦': '喔',
            
            # 常用動詞片語
            '記得': '會記得',
            '忘記': '袂記得',
            '知道': '知影',
            '不知道': '毋知影',
            '喜歡': '佮意',
            '討厭': '嫌',
            '想要': '欲',
            '需要': '愛',
            '可以': '會使',
            '不可以': '袂使',
            '應該': '應該',
            '必須': '一定愛',
            '可能': '敢若',
            '也許': '敢若',
            '當然': '當然',
            '應該': '應該',
            
            # 疑問詞
            '什麼': '啥物',
            '哪裡': '佗位',
            '誰': '啥人',
            '什麼時候': '當時陣',
            '怎麼': '按怎',
            '為什麼': '按怎',
            '多少': '偌濟',
            '幾個': '幾个',
            '哪個': '佗一个',
            
            # 連接詞和介詞
            '和': '佮',
            '跟': '佮',
            '與': '佮',
            '或': '抑是',
            '但是': '毋過',
            '可是': '毋過',
            '不過': '毋過',
            '因為': '因為',
            '所以': '所以',
            '如果': '若是',
            '雖然': '雖然',
            '然後': '了後',
            '先': '先',
            '再': '閣',
            '又': '閣',
            '還': '猶',
            '已經': '已經',
            '正在': '當咧',
            '剛剛': '拄才',
            '馬上': '隨',
            '立刻': '隨',
            '慢慢': '細膩',
            '突然': '忽然間',
            
            # 否定詞
            '不': '毋',
            '沒': '無',
            '沒有': '無',
            '不是': '毋是',
            '不要': '毋愛',
            '不會': '袂',
            '不能': '袂使',
            '不好': '毋好',
            '不行': '袂使',
            
            # 問候語
            '你好': '你好',
            '早安': '早',
            '晚安': '暗安',
            '再見': '閣會',
            '謝謝': '多謝',
            '對不起': '歹勢',
            '不客氣': '免客氣',
            '請': '請',
            '歡迎': '歡迎',
            '恭喜': '恭喜',
            
            # 程度副詞
            '很': '足',
            '非常': '足',
            '真的': '真正',
            '太': '忒',
            '特別': '特別',
            '比較': '較',
            '最': '上',
            '更': '較',
            '還': '猶',
            '只': '干焦',
            '都': '攏',
            '全部': '攏總',
            '一起': '做伙',
            '一樣': '仝款',
            '不同': '無仝',
            '差不多': '差不多',
            '大概': '大概',
            '可能': '可能',
            '一定': '一定',
            '當然': '當然',
            '果然': '果然',
            '居然': '居然',
            '竟然': '竟然',
        }
    
    def _load_csv_dictionary(self):
        """載入CSV字典檔案"""
        if not os.path.exists(self.csv_path):
            print(f"⚠ CSV檔案不存在: {self.csv_path}")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # 跳過的字詞 - 避免過度轉換
                skip_words = {
                    '我', '你', '日', '工', '人', '會', '看', '公', '學校', '買', '說', '不', '很', '好', '了', '的', 
                    '她', '他', '它', '在', '去', '來', '和', '多', '少', '是', '有', '無', '都', '也', '還', '但',
                    '可', '要', '能', '大', '小', '高', '低', '新', '舊', '快', '慢', '上', '下', '前', '後',
                    '左', '右', '裡', '外', '中', '同', '不同', '一樣', '對', '錯', '真', '假', '開', '關', '天', '天氣'
                }
                
                for row in reader:
                    han_lo = row.get('HanLoTaibunKip', '').strip()  # 台語漢字
                    hoa_bun = row.get('HoaBun', '').strip()  # 華語
                    
                    if han_lo and hoa_bun and han_lo != hoa_bun:
                        # 處理華語欄位中的多個詞彙（用頓號、逗號分隔）
                        hoa_bun_variants = re.split('[、，,]', hoa_bun)
                        
                        for variant in hoa_bun_variants:
                            variant = variant.strip()
                            # 過濾掉數字和其他不適合的條目
                            if (variant and variant != han_lo and 
                                variant not in skip_words and
                                not re.match(r'^[0-9]+$', variant) and  # 跳過純數字
                                not re.match(r'^[a-zA-Z]+$', variant) and  # 跳過純英文
                                len(variant) >= 2):  # 只處理2字以上的詞彙
                                
                                # 按長度分類：詞、短語
                                if len(variant) <= 4:
                                    self.word_dict[variant] = han_lo
                                else:
                                    self.phrase_dict[variant] = han_lo
                
        except Exception as e:
            print(f"⚠ 載入CSV檔案失敗: {e}")
    
    def _init_taiwan_tools(self):
        """初始化臺灣言語工具"""
        try:
            from 臺灣言語工具.解析整理.拆文分析器 import 拆文分析器
            from 臺灣言語工具.音標系統.閩南語.臺灣閩南語羅馬字拼音 import 臺灣閩南語羅馬字拼音
            
            self.拆文分析器 = 拆文分析器
            self.臺灣閩南語羅馬字拼音 = 臺灣閩南語羅馬字拼音
            self.use_taiwan_tools = True
            print("✓ 臺灣言語工具載入成功")
        except ImportError as e:
            print(f"⚠ 臺灣言語工具載入失敗: {e}")
            self.use_taiwan_tools = False
    
    def convert(self, text: str, verbose: bool = False) -> str:
        """
        華文字轉台語漢字
        
        Args:
            text: 輸入的華文字文本
            verbose: 是否顯示詳細轉換過程
            
        Returns:
            轉換後的台語漢字文本
        """
        if not text.strip():
            return text
        
        result = text
        conversions = []
        
        # 1. 先處理短語（最長匹配）
        result, phrase_conversions = self._convert_with_dict(result, self.phrase_dict, "短語")
        conversions.extend(phrase_conversions)
        
        # 2. 處理詞彙
        result, word_conversions = self._convert_with_dict(result, self.word_dict, "詞彙")
        conversions.extend(word_conversions)
        
        # 3. 處理手工維護的對照表
        result, manual_conversions = self._convert_with_dict(result, self.manual_dict, "手工")
        conversions.extend(manual_conversions)
        
        # 4. 處理單字
        result, char_conversions = self._convert_with_dict(result, self.csv_dict, "單字")
        conversions.extend(char_conversions)
        
        # 顯示轉換過程
        if verbose and conversions:
            print("轉換過程:")
            for conv_type, original, converted in conversions:
                print(f"  [{conv_type}] {original} → {converted}")
        
        return result
    
    def _convert_with_dict(self, text: str, convert_dict: Dict[str, str], dict_type: str) -> Tuple[str, List[Tuple[str, str, str]]]:
        """
        使用指定字典進行轉換
        
        Args:
            text: 輸入文本
            convert_dict: 轉換字典
            dict_type: 字典類型（用於記錄）
            
        Returns:
            (轉換後文本, 轉換記錄列表)
        """
        result = text
        conversions = []
        
        # 按鍵的長度降序排列，確保最長匹配
        sorted_keys = sorted(convert_dict.keys(), key=len, reverse=True)
        
        for original in sorted_keys:
            converted = convert_dict[original]
            if original in result and original != converted:
                result = result.replace(original, converted)
                conversions.append((dict_type, original, converted))
        
        return result, conversions
    
    def get_conversion_stats(self) -> Dict[str, int]:
        """獲取轉換器統計資訊"""
        return {
            'csv_entries': len(self.csv_dict),
            'word_entries': len(self.word_dict),
            'phrase_entries': len(self.phrase_dict),
            'manual_entries': len(self.manual_dict),
            'total_entries': len(self.csv_dict) + len(self.word_dict) + len(self.phrase_dict) + len(self.manual_dict)
        }
    
    def test_conversion(self, test_cases: List[str] = None):
        """測試轉換功能"""
        if test_cases is None:
            test_cases = [
                "你好，我今天吃了很多好吃的東西",
                "爺爺，你今天有沒有吃藥？要記得去看醫生喔！",
                "媽媽，今天的飯很好吃，謝謝你！",
                "我們明天一起去公園玩好不好？",
                "弟弟很喜歡吃蘋果和香蕉",
                "哥哥在學校學習很認真",
                "奶奶說她昨天買了很多漂亮的衣服",
                "爸爸每天早上都會喝咖啡看報紙"
            ]
        
        print("\n=== 轉換測試 ===")
        for i, text in enumerate(test_cases, 1):
            converted = self.convert(text, verbose=True)
            print(f"\n{i}. 原文: {text}")
            print(f"   轉換: {converted}")
            print("-" * 50)


def main():
    """測試進階轉換器"""
    converter = AdvancedChineseToTaiwaneseConverter()
    
    # 顯示統計資訊
    stats = converter.get_conversion_stats()
    print(f"\n=== 轉換器統計資訊 ===")
    print(f"CSV字典條目: {stats['csv_entries']}")
    print(f"詞彙對照條目: {stats['word_entries']}")
    print(f"短語對照條目: {stats['phrase_entries']}")
    print(f"手工對照條目: {stats['manual_entries']}")
    print(f"總計條目: {stats['total_entries']}")
    
    # 執行測試
    converter.test_conversion()


if __name__ == "__main__":
    main()