# -*- coding: utf-8 -*-
import argparse
import os
import re
import sys
import time
import wave
import tempfile
import array
import unicodedata
from typing import Dict, List, Optional, Tuple

# 臺灣言語工具路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tai5-uan5_gian5-gi2_kang1-ku7"))

class PunctuationHandler:
    """標點符號處理器"""
    
    # 定義標點符號映射
    PAUSE_PUNCTUATION = {
        '，': ',',
        '。': '.',
        '！': '!',
        '？': '?',
        '；': ';',
        '：': ':',
        '、': ',',
        '…': '.',
        '...': '.',
        '……': '.',
    }
    
    SENTENCE_END = {'。', '.', '！', '!', '？', '?'}
    CLAUSE_BREAK = {'，', ',', '；', ';', '：', ':', '、'}
    
    @classmethod
    def normalize_punctuation(cls, text: str) -> str:
        """標準化標點符號"""
        result = text
        for chinese_punct, english_punct in cls.PAUSE_PUNCTUATION.items():
            result = result.replace(chinese_punct, english_punct)
        return result
    
    @classmethod
    def add_pauses(cls, text: str) -> str:
        """在標點符號前後添加適當的停頓"""
        # 在主要標點符號前後加空格
        text = re.sub(r'([,.!?;:])', r' \1 ', text)
        # 清理多餘空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

class TaiwaneseConverter:
    """台語轉換器"""
    
    def __init__(self):
        self.use_taiwan_tools = False
        self.basic_dict = self._load_basic_dict()
        self._init_taiwan_tools()
    
    def _load_basic_dict(self) -> Dict[str, str]:
        """載入基本辭典"""
        return {
            # 人稱代詞
            '我': 'gua2', '你': 'li2', '伊': 'i1', '咱': 'lan2', '恁': 'lin2', '阮': 'gun2',
            # 常用動詞
            '是': 'si7', '有': 'u7', '無': 'bo5', '講': 'kong2', '說': 'kong2', '聽': 'thiann1',
            '看': 'khuann3', '食': 'tsia8h', '飲': 'lim1', '行': 'kiann5', '坐': 'tse7', '睏': 'khun3',
            '會': 'e7', '袂': 'be7',
            # 形容詞
            '好': 'ho2', '歹': 'phainn2', '大': 'tua7', '細': 'se3', '長': 'ting5', '短': 'te2',
            '濟': 'tse7', '少': 'tso2', '媠': 'sui2', '醜': 'bai2',
            # 數字
            '一': 'tsi8t', '二': 'nng7', '三': 'sann1', '四': 'si3', '五': 'goo7', '六': 'la8k',
            '七': 'tshit4', '八': 'peh4', '九': 'kau2', '十': 'tsa8p',
            # 量詞
            '个': 'e5', '隻': 'tsiah4', '本': 'pun2', '台': 'tai5', '張': 'tiunn1',
            # 常用詞彙
            '大家': 'tak8-ke1', '台語': 'tai5-gi2', '華語': 'hua5-gi2', '英語': 'ing1-gi2',
            '機器人': 'ki1-khi3-lang5', '電腦': 'tian7-nau2', '手機': 'tshiu2-ki1',
            '今天': 'kin1-a2-jit8', '明天': 'bin5-a2-jit8', '昨天': 'tsa1-hng1', '天氣': 'thinn1-khi3',
            '時間': 'si5-kan1', '地方': 'te7-hong5', '吃藥': 'tsiah8 ioh8-a2', '看醫生': 'khuann3-i1-sing1',
            # 助詞
            '的': 'e5', '了': 'ah4', '也': 'maa7', '都': 'long2', '就': 'to7', '在': 'ti7',
            '和': 'kap4', '跟': 'kap4', '給': 'hoo7',
            # 疑問詞與詢問相關
            '什麼': 'siann2-mih4', '哪': 'to2-ui7', '誰': 'siann2-lang5', '怎樣': 'tsuann2-iunn7',
            '為什麼': 'ui7-siann2-mih4', '多少': 'to-tse7',
            '盍': 'o2', '按怎': 'an1-tsuann2', '怎': 'tsuann2', '按': 'an1',
            '按呢': 'an1-ne1', '按呢樣': 'an1-ne1-iunn7', '為啥': 'ui7-sia2',
            # 常用打招呼
            '你好': 'li2-ho2', '謝謝': 'to1-sia7', '對不起': 'pai2-se3',
            # 片語與補充
            '阿': 'a1', '強': 'kiong5', '台北': 'tai5 pak4', '北': 'pak4', '台南': 'tai5 lam5',
            '咧': 'ia7', '較': 'khah4', '冷': 'ling2', '捏': 'nia7', '還是': 'huan5 si7',
            '熱乎乎': 'juah8 hoo7 hoo7', '天气': 'thinn1-khi3', '還': 'huan5', '热': 'juah8', '乎': 'hoo7',
            # 補充常用字詞
            '甘': 'kan1', '甘好': 'kan1-ho2', '簡': 'kan1', '簡好': 'kan1-ho2',
            '毋': 'bu7', '毋知': 'bu7-tsi1', '嘛': 'maa7', '煞': 'shuah4',
            '底': 'tui2', '踏': 'tshoa8h', '倒': 'tua2', '去': 'khui3', '來': 'lai5',
            '上': 'tsiong7', '下': 'e7', '邊': 'pinn1', '位': 'ui7',
            '足': 'tsiok4', '閣': 'kik4', '逐': 'tsiok4', '只': 'tsin1', 
            '欲': 'bun7', '愛': 'ai3',
            # 時間與天氣相關
            '今仔日': 'kin1-a2-jit8', '今': 'kin1', '仔': 'a2', '日': 'jit8',
            '真': 'tsin1', '瀾': 'lan1', '涼': 'liong5', '涼快': 'liong5-khuai3',
            '天': 'thinn1', '氣': 'khi3', '天氣': 'thinn1-khi3',
            # 動作與行為
            '適合': 'tik4-hue7', '出': 'tshuat4', '走': 'tsau2', '走走': 'tsau2-tsau2',
            '蹓': 'tsioo2', '蹓捏': 'tsioo2-nia7',
            '過': 'kue3', '得': 'tik4', '呢': 'ne1', '樣': 'iunn7',
            # 修正發音
            '不': 'bu7',
            # LLM常用對話詞彙
            # 問候與禮貌
            '早': 'tsa2', '早安': 'tsa2-an1', '午安': 'ngoo5-an1', '晚安': 'uann2-an1',
            '請': 'tshiann2', '麻煩': 'ma5-huan5', '勞煩': 'lo5-huan5', '歹勢': 'phai2-se3',
            '失禮': 'sit4-le2', '多謝': 'to1-sia7', '無要緊': 'bo5-iau3-kin2',
            # 常用動詞補充
            '做': 'tso3', '想': 'siunn7', '知': 'tsai1', '知影': 'tsai1-iann2',
            '會曉': 'e7-hiau2', '歡喜': 'huann1-hi2', '煩惱': 'huan5-lo2',
            '幫助': 'pang1-tsoo7', '幫忙': 'pang1-bang5', '需要': 'su1-iau3',
            '問': 'mng7', '答': 'tap4', '講話': 'kong2-ue7', '話': 'ue7',
            # 形容詞補充  
            '新': 'sin1', '舊': 'ku7', '貴': 'kui3', '俗': 'siok8',
            '快': 'khuai3', '慢': 'ban7', '遠': 'hing7', '近': 'kinn7',
            '高': 'ko1', '矮': 'e2', '厚': 'kau7', '薄': 'po8h',
            '清楚': 'tshing1-tsho2', '明白': 'bing5-peh8', '艱苦': 'kan1-khoo2',
            # 時間詞補充
            '現在': 'hian7-tsai7', '等一下': 'tan2-tsi8t-e7', '馬上': 'ma2-siong7',
            '後天': 'au7-thinn1', '前天': 'tsing5-thinn1', '中晝': 'tiong1-tau3',
            '這禮拜': 'tsit4-le2-pai3', '下禮拜': 'e7-le2-pai3', '頂禮拜': 'ting2-le2-pai3',
            '隔轉工': 'kik4-tng2-kang1', '透早': 'thau3-tsa2', '下晡': 'e7-poo1',
            # 方位地點
            '這': 'tse1', '那': 'he1', '遮': 'tsia1', '遐': 'hia1',
            '這邊': 'tsit4-pinn1', '那邊': 'hit4-pinn1', '內': 'lai7', '外': 'gua7',
            '頂': 'ting2', '下': 'e7', '內面': 'lai7-bin7', '外口': 'gua7-khau2',
            '厝': 'tshu3', '厝內': 'tshu3-lai7', '店': 'tiam3', '學校': 'ha8k-hau7',
            # 程度與數量
            '誠': 'tsiann5', '有夠': 'u7-kau3', '足濟': 'tsiok4-tse7', '真正': 'tsin1-tsiann3',
            '無夠': 'bo5-kau3', '傷': 'siunn1', '傷濟': 'siunn1-tse7', '傷少': 'siunn1-tsio2',
            # 連接詞與語氣
            '若': 'na7', '如果': 'lu5-ko2', '因為': 'in1-ui7', '所以': 'soo2-i2',
            '但是': 'tan7-si7', '不過': 'put4-ko3', '毋過': 'bu7-ko3',
            '啦': 'la0', '啊': 'a0', '喔': 'oo0', '呵': 'ho0',
            # 肯定否定與疑問
            '是': 'si7', '毋是': 'bu7-si7', '袂使': 'be7-sai2', '會使': 'e7-sai2',
            '好': 'ho2', '毋好': 'bu7-ho2', '著': 'tioh8', '毋著': 'bu7-tioh8',
            '敢': 'kam2', '敢講': 'kam2-kong2', '敢有': 'kam2-u7',
            # 人際互動
            '朋友': 'ping5-iu2', '逐家': 'tak8-ke1', '儂': 'lang5', '人': 'lang5',
            '怹': 'in1', '咱儂': 'lan2-lang5', '家己': 'ka1-ki7',
            # 常用片語
            '對': 'tui3', '佮': 'kah4', '抑是': 'iah8-si7', '或是': 'hik8-si7',
            '按算': 'an1-sng3', '到': 'kau3', '予': 'hoo7', '共': 'ka7',
            # 語氣助詞與尾字
            '咩': 'mih4', '啥': 'siann2', '啥物': 'siann2-mih4', '啥貨': 'siann2-hue3',
            # 常用字補充
            '時': 'si5', '時陣': 'si5-tsun7', '最': 'tsue3', '轉': 'tng2',
            '心情': 'sim1-tsing5',
            # 自然地理相關
            '濱': 'pin1', '海': 'hai2', '浪': 'long7', '濱海': 'pin1-hai2',
            '踏浪': 'tshoa8h-long7', '山': 'suann1', '水': 'tsui2', '河': 'ho5',
            # 身體部位
            '跤': 'kha1', '手': 'tshiu2', '頭': 'thau5', '面': 'bin7', '目': 'bak8',
            '耳': 'hinn7', '嘴': 'tshui3', '鼻': 'phinn7', '喙': 'tshui3', '身體': 'sin1-the2',
            '腹': 'pak4', '心': 'sim1', '肝': 'kuann1', '骨': 'kut4', '肉': 'bah4',
            # 感覺與狀態
            '癢': 'tsiunn7', '疼': 'thiann3', '痛': 'thiann3', '痠': 'sng1', '麻': 'bua5',
            '餓': 'iau1', '飽': 'pa2', '睏': 'khun3', '醒': 'tshinn2', '渴': 'khat4',
            '生氣': 'senn1-khi3', '傷心': 'siunn1-sim1', '舒適': 'su1-sik4',
            # 常用動詞補充
            '食飯': 'tsiah8-png7', '飲水': 'lim1-tsui2', '睏眠': 'khun3-bin5',
            '讀冊': 'thak8-tsheh4', '寫字': 'sia2-ji7', '畫圖': 'ue7-too5',
            '唱歌': 'tshiunn3-kua1', '跳舞': 'thiau3-bu2', '運動': 'un7-tong7',
            '洗身': 'se2-sin1', '換衫': 'uann7-sann1', '穿鞋': 'tshing7-ue5',
            # 生活用品
            '厝': 'tshu3', '房間': 'pang5-king1', '眠床': 'bin5-tsng5', '桌仔': 'toh4-a2',
            '椅仔': 'i2-a2', '碗': 'uann2', '盤': 'puann5', '杯仔': 'pue1-a2',
            '衫': 'sann1', '褲': 'khoo3', '鞋': 'ue5', '帽仔': 'bo7-a2',
            # 飲食相關
            '飯': 'png7', '麵': 'mi7', '湯': 'thng1', '菜': 'tshai3', '肉': 'bah4',
            '魚': 'hi5', '果子': 'kue2-tsi2', '甜': 'tinn1', '鹹': 'kiam5', '苦': 'khoo2',
            '茶': 'te5', '咖啡': 'ka1-pi1', '奶': 'ling1', '糖': 'thng5',
            # 數量與程度補充
            '百': 'pah4', '千': 'tshing1', '萬': 'ban7', '濟濟': 'tse7-tse7',
            '寡': 'kua2', '幾': 'kui2', '幾个': 'kui2-e5', '幾若': 'kui2-na7',
            '一寡': 'tsi8t-kua2', '一屑仔': 'tsi8t-sut-a2', '滿': 'mua2', '空': 'khang1',
            # 天氣與季節
            '風': 'hong1', '雨': 'hoo7', '雷公': 'lui5-kong1', '日頭': 'jit8-thau5',
            '烏雲': 'oo1-hun5', '春': 'tshun1', '夏': 'ha7', '秋': 'tshiu1', '冬': 'tang1',
            '熱': 'juah8', '寒': 'kuann5', '溫': 'un1', '濕': 'sip4', '燥': 'ta3',
            # 顏色
            '紅': 'ang5', '白': 'peh8', '烏': 'oo1', '青': 'tshenn1', '黃': 'ng5',
            '綠': 'lik8', '藍': 'nam5', '紫': 'tsi2', '灰': 'hue1', '粉紅': 'hun2-ang5',
            # 家族與人際
            '阿爸': 'a1-pa1', '阿母': 'a1-bu2', '阿兄': 'a1-hiann1', '小妹': 'sio2-be7',
            '阿公': 'a1-kong1', '阿媽': 'a1-ma2', '囝': 'kiann2', '囝仔': 'gin2-a2',
            '翁': 'ang1', '某': 'boo2', '親情': 'tshin1-tsiann5', '厝邊': 'tshu3-pinn1',
            # 職業與場所
            '老師': 'lau7-su1', '醫生': 'i1-sing1', '店員': 'tiam3-uan5', '司機': 'su1-ki1',
            '學生': 'hak8-sing1', '公司': 'kong1-si1', '工廠': 'kang1-tsiunn2', '市場': 'tshi7-tiunn5',
            '醫院': 'i1-uan7', '銀行': 'gin5-hang5', '郵局': 'iu5-kiok8', '警察局': 'king2-tshat4-kiok8',
            # 交通工具
            '車': 'tshia1', '公車': 'kong1-tshia1', '火車': 'hue2-tshia1', '捷運': 'tsiap8-un7',
            '機車': 'ki1-tshia1', '跤踏車': 'kha1-tah8-tshia1', '飛機': 'pue1-ki1', '船': 'tsun5',
            # 方向與動作
            '行': 'kiann5', '走': 'tsau2', '飛': 'pue1', '跳': 'thiau3', '爬': 'pe5',
            '跑': 'tsau2', '徛': 'khia7', '踮': 'tiam7', '蹲': 'tsun5', '倒': 'to2',
            '開': 'khui1', '關': 'kuinn1', '推': 'tui1', '拉': 'lia2', '提': 'the5',
            # 品質與評價補充
            '毋錯': 'bu7-tshhuah4', '錯': 'tshhuah4', '爽': 'song2', '厚實': 'hoo7-tsiok8',
            '精': 'tsiann1', '粗': 'tshoo1', '細': 'se3', '鬆': 'song1', '硬': 'ng7',
            '軟': 'nn7', '滑': 'khuah4', '粗糙': 'tshoo1-tshau3', '光滑': 'kong1-khuah4',
            # 情緒與感受補充
            '驚': 'kiann1', '怕': 'phuann3', '擔心': 'tuan1-sim1', '放心': 'hong3-sim1',
            '安心': 'an1-sim1', '滿意': 'buan2-i3', '不滿': 'put4-buan2', '歡樂': 'huan1-lok8',
            '苦悶': 'khoo2-bun7', '無聊': 'bo5-lio5', '好笑': 'ho2-tshio3', '著惱': 'tiok8-lo2',
            # 時間與時序補充
            '遠早': 'hing7-tsa2', '日後': 'jit8-hoo7', '過後': 'kue3-hoo7', '下擺': 'e7-pue3',
            '頂擺': 'ting2-pue3', '這次': 'tse1-tshhuah4', '每擺': 'bue2-pue3',
            # 否定與限制補充
            '無': 'bo5', '毋': 'bu7', '不': 'put4', '絕對': 'tsiok8-tai3', '一定': 'tsi8t-tik4',
            '可能': 'khuann2-ling5', '無法': 'bo5-huat4', '袂使': 'be7-sai2', '毋使': 'bu7-sai2',
            # 強調與比較補充
            '較': 'khah4', '閣較': 'kik4-khah4', '卡': 'khuah4', '卡濟': 'khuah4-tse7',
            '最': 'tsue3', '上': 'tsiong7', '上古錐': 'tsiong7-koo2-tshue1',
            # 存在與所有補充
            '有': 'u7', '無': 'bo5', '有夠': 'u7-kau3', '有一工': 'u7-tsi8t-kang1',
            '著': 'tiok8', '在': 'ti7', '共': 'ka7', '予': 'hoo7',
            # 日光相關動詞補充
            '晒': 'tshuah4', '日光浴': 'jit8-kong1-io8k8', '曝光': 'pok8-kong1',
            '曠': 'khuiunn3', '掠光': 'lia8-kiunn1',
            # 常用副詞與狀態補充
            '都': 'long2', '全': 'tsuann5', '完': 'buan5', '攏': 'long2', '總': 'tsiong2',
            '嘛': 'maa7', '嘛是': 'maa7-si7', '彼': 'hit4', '這': 'tse1',
            # 補充動詞與完成式
            '了': 'a0', '做完': 'tso3-buan5', '去': 'khui3', '來': 'lai5', '轉來': 'tng2-lai5',
            '做好': 'tso3-ho2', '準備': 'tsin1-pue3', '準': 'tsin1',
            # 補充物質與環境
            '氣': 'khi3', '空氣': 'khang1-khi3', '新鮮': 'sin1-tshinn1', '乾淨': 'kan1-tsienn3',
            '清氣': 'tshing1-khi3', '污氣': 'bu5-khi3',
            # 強調語序
            '實在': 'tsiok8-tsai5', '誠': 'tsiann5', '真': 'tsin1', '上': 'tsiong7',
            '足': 'tsiok4', '靡': 'buan2', '無底': 'bo5-te2',
            # 補充常用介詞與連接詞
            '用': 'ting7', '以': 'i2', '將': 'tsiong1', '把': 'pa2',
            '同': 'kang5', '佮': 'kah4', '及': 'tsiok8', '及閣': 'tsiok8-kik4',
            # 娛樂與享受相關
            '享受': 'hiunn2-siok8', '快樂': 'khuai3-lok8', '玩': 'guan5', '玩樂': 'guan5-lok8',
            '戲': 'hi3', '看戲': 'khuann3-hi3', '唱卡啦OK': 'tshiunn3-khuah4-la1-o1-ke1',
            '光': 'kong1', '陽光': 'bing5-kong1', '日光': 'jit8-kong1', '月光': 'gu8h-kong1',
            '光線': 'kong1-tsuann3', '靚': 'tsiann2', '漂亮': 'phiau2-tsiann2',
            # 時間量詞補充
            '下': 'e7', '一下': 'tsi8t-e7', '一擺': 'tsi8t-pue3', '一陣': 'tsi8t-tsun7',
            '日': 'jit8', '工': 'kang1', '日工': 'jit8-kang1', '一工': 'tsi8t-kang1',
            # 條件與假設補充
            '若是': 'na7-si7', '若': 'na7', '或者': 'hik8-tsia2', '抑是': 'iah8-si7',
            # 享樂與活動補充
            '運動': 'un7-tong7', '散步': 'sann3-poo3', '踏青': 'tshoa8h-tshinn1', 
            '出遊': 'tshuat4-iu5', '旅遊': 'li2-iu5', '去遊': 'khui3-iu5',
        }

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
            print(f"⚠ 臺灣言語工具載入失敗，使用基本轉換: {e}")
            self.use_taiwan_tools = False
    
    def han_to_tlpa(self, text: str) -> str:
        """漢字轉台羅拼音"""
        if self.use_taiwan_tools:
            return self._advanced_convert(text)
        else:
            return self._basic_convert(text)
    
    def _advanced_convert(self, text: str) -> str:
        """使用han2tts進行轉換"""
        try:
            import han2tts
            dictionary = han2tts.build_dictionary()
            
            result = han2tts.han_to_tlpa_number(text, dictionary)
            return result
            
        except Exception as e:
            print(f"進階轉換失敗，使用基本轉換: {e}")
            return self._basic_convert(text)
    
    def _basic_convert(self, text: str) -> str:
        """基本字典對應轉換：在相鄰音節之間加入空白，標點獨立保留"""
        tokens: list[str] = []
        i = 0
        
        while i < len(text):
            # 嘗試最長匹配
            matched = False
            for length in range(min(4, len(text) - i), 0, -1):
                substr = text[i:i+length]
                if substr in self.basic_dict:
                    tokens.append(self.basic_dict[substr])
                    i += length
                    matched = True
                    break
            
            if not matched:
                char = text[i]
                if char.isspace():
                    # 將空白視為詞界，延後在組裝階段處理
                    tokens.append(' ')
                elif self._is_punctuation(char):
                    # 標點符號作為獨立 token
                    tokens.append(char)
                else:
                    # 未知字符，嘗試用華語拼音近似發音
                    pinyin_approx = self._chinese_to_pinyin_approx(char)
                    if pinyin_approx:
                        tokens.append(pinyin_approx)
                    # 如果無法轉換，直接跳過（不產生中括號）
                i += 1

        # 將 tokens 組裝成字串：
        # - 兩個非標點 token 之間加空白
        # - 標點前後由上層 process_text 以空白分隔（此處不再強制加空白）
        assembled: list[str] = []
        prev_was_word = False
        for tok in tokens:
            if tok == '':
                continue
            if len(tok) == 1 and self._is_punctuation(tok):
                # 標點直接附加，重置狀態
                assembled.append(tok)
                prev_was_word = False
            elif tok == ' ':
                # 明確詞界，轉為狀態，不立即輸出空白
                prev_was_word = False if not assembled else False
            else:
                # 一般音節/詞
                if assembled and not (len(assembled[-1]) == 1 and self._is_punctuation(assembled[-1])) and prev_was_word:
                    assembled.append(' ')
                assembled.append(tok)
                prev_was_word = True

        return ''.join(assembled).strip()
    
    def _is_punctuation(self, char: str) -> bool:
        """檢查是否為標點符號"""
        punct_chars = '，。！？；：、…()（）[]【】""' + "''" + '《》〈〉'
        return char in punct_chars
    
    def _chinese_to_pinyin_approx(self, char: str) -> str:
        """
        將中文字轉換為近似的台羅拼音
        使用華語拼音的聲母韻母對應到台語音
        """
        # 常用字的台語發音對照表（擴充版）
        common_chars = {
            # 問答相關
            '什': 'sim2', '麼': 'mih', '啥': 'sia2', '物': 'mih8',
            '可': 'kho2', '以': 'i2', '能': 'ling5', '會': 'e7',
            '幫': 'pang1', '助': 'tsioo7', '答': 'tap', '解': 'kai2',
            '問': 'bun7', '題': 'te5', '事': 'su7', '情': 'tsing5',
            
            # 動詞
            '使': 'sai2', '做': 'tso3', '講': 'kong2', '說': 'seh',
            '看': 'khuann3', '聽': 'thiann1', '食': 'tsia8h', '飲': 'lim1',
            '來': 'lai5', '去': 'khi3', '在': 'ti7', '有': 'u7',
            '知': 'tsai1', '道': 'to7', '想': 'siunn7', '要': 'beh4',
            
            # 形容詞
            '好': 'ho2', '美': 'bi2', '麗': 'le7', '大': 'tua7',
            '小': 'sio2', '新': 'sin1', '舊': 'ku7', '多': 'tse7',
            
            # 代詞
            '這': 'tsit', '那': 'hit', '啥': 'sia2', '誰': 'siang2',
            
            # 地點
            '裡': 'lai7', '邊': 'pinn1', '面': 'bin7', '內': 'lai7',
            
            # 其他常用
            '的': 'e5', '了': 'liau2', '嗎': 'ma0', '呢': 'ne0',
            '吧': 'pa0', '啊': 'a0', '喔': 'o0', '哦': 'o0',
            '無': 'bo5', '沒': 'bo5', '不': 'put', '別': 'pat',
        }
        
        if char in common_chars:
            return common_chars[char]
        
        # 如果不在常用字典中，返回空字符串（跳過）
        return ''

class TaiwaneseTextProcessor:
    """台語文字處理器 - 整合版本"""
    
    def __init__(self, enable_chinese_conversion: bool = True):
        self.converter = TaiwaneseConverter()
        self.punct_handler = PunctuationHandler()
        self.enable_chinese_conversion = enable_chinese_conversion
        
        # 初始化華文字轉台語漢字轉換器
        if enable_chinese_conversion:
            try:
                # 優先使用進階轉換器
                try:
                    from advanced_chinese_converter import AdvancedChineseToTaiwaneseConverter
                    self.chinese_converter = AdvancedChineseToTaiwaneseConverter()
                    self.converter_type = "advanced"
                    print("✓ 進階華文字轉台語漢字轉換器載入成功")
                except ImportError:
                    # 回退到基本轉換器
                    from chinese_to_taiwanese_converter import ChineseToTaiwaneseConverter
                    self.chinese_converter = ChineseToTaiwaneseConverter()
                    self.converter_type = "basic"
                    print("✓ 基本華文字轉台語漢字轉換器載入成功")
            except ImportError as e:
                print(f"⚠ 華文字轉換器載入失敗: {e}")
                self.chinese_converter = None
                self.converter_type = None
        else:
            self.chinese_converter = None
            self.converter_type = None
    
    def process_text(self, text: str, add_pauses: bool = True, convert_chinese: bool = True) -> str:
        """
        處理文字：華文字→台語漢字→台羅拼音並處理標點符號
        
        Args:
            text: 輸入文字
            add_pauses: 是否在標點符號處添加停頓
            convert_chinese: 是否進行華文字轉台語漢字預處理
            
        Returns:
            處理後的台羅拼音文字
        """
        
        # 0. 華文字轉台語漢字預處理
        if convert_chinese and self.chinese_converter:
            original_text = text
            text = self.chinese_converter.convert(text)
            if text != original_text:
                converter_name = "進階" if getattr(self, 'converter_type', '') == "advanced" else "基本"
                print(f"華文字轉換({converter_name}): {original_text} → {text}")
        
        # 1. 預處理：標準化標點符號
        text = self.punct_handler.normalize_punctuation(text)
        
        # 2. 分段處理：按標點符號分割
        segments = self._split_by_punctuation(text)
        
        processed_segments = []
        for segment, punct in segments:
            if segment.strip():
                # 轉換漢字部分
                tlpa = self.converter.han_to_tlpa(segment.strip())
                processed_segments.append(tlpa)
            
            # 添加標點符號
            if punct:
                processed_segments.append(punct)
        
        result = ' '.join(processed_segments)
        
        # 3. 後處理：添加停頓
        if add_pauses:
            result = self.punct_handler.add_pauses(result)
        
        # 4. 清理格式
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def _split_by_punctuation(self, text: str) -> List[Tuple[str, str]]:
        """按標點符號分割文字"""
        pattern = r'([,.!?;:，。！？；：、…])'
        parts = re.split(pattern, text)
        
        segments = []
        for i in range(0, len(parts), 2):
            content = parts[i] if i < len(parts) else ''
            punct = parts[i + 1] if i + 1 < len(parts) else ''
            segments.append((content, punct))
        
        return segments

class TaiwaneseTextToSpeech:
    """台語文字轉語音系統"""
    
    def __init__(self, tacotron_model: str = None, waveglow_model: str = None, enable_chinese_conversion: bool = True):
        self.text_processor = TaiwaneseTextProcessor(enable_chinese_conversion=enable_chinese_conversion)
        
        # 設定預設模型路徑
        if tacotron_model is None:
            tacotron_model = "tacotron2/model/checkpoint_100000"
        if waveglow_model is None:
            waveglow_model = "tacotron2/model/waveglow/waveglow_main.pt"
        
        self.tacotron_model = tacotron_model
        self.waveglow_model = waveglow_model
        self.synthesizer = None
        
        self._init_synthesizer()
    
    def _init_synthesizer(self):
        """初始化語音合成器"""
        try:
            import han2tts
            self.synthesizer = han2tts.Synthesizer(self.tacotron_model, self.waveglow_model)
            print("✓ TTS合成器初始化成功")
        except Exception as e:
            print(f"⚠ TTS合成器初始化失敗: {e}")
    
    def synthesize(self, text: str, output_path: str = None, convert_chinese: bool = True) -> Optional[str]:
        """
        文字轉語音
        
        Args:
            text: 輸入的華文字/台語漢字文字，或已轉換的台羅數字調文字
            output_path: 輸出音檔路徑
            convert_chinese: 是否進行華文字轉台語漢字預處理及台羅轉換（若 text 已是台羅則設為 False）
            
        Returns:
            輸出音檔路徑
        """
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f"wavs/{timestamp}.wav"
            os.makedirs("wavs", exist_ok=True)
        
        print("=" * 50)
        print("台語文字轉語音")
        print("=" * 50)
        print(f"輸入文字: {text}")
        
        # 處理文字：如果 convert_chinese=False 則直接使用輸入（已是台羅）
        if convert_chinese:
            tlpa_text = self.text_processor.process_text(text, convert_chinese=True)
            print(f"台羅轉換: {tlpa_text}")
        else:
            tlpa_text = text
            print(f"台羅文本（無需轉換）: {tlpa_text}")
        
        # 合成語音
        if self.synthesizer:
            try:
                self.synthesizer.tts(tlpa_text, output_path)
                print(f"✓ 音檔已生成: {output_path}")
                return output_path
            except Exception as e:
                print(f"✗ 語音合成失敗: {e}")
                return None
        else:
            print("✗ 無可用的語音合成器")
            return None

    def _apply_fade(self, pcm_bytes: bytes, params: wave._wave_params, fade_ms: float = 10.0) -> bytes:
        """對 16bit PCM 做首尾淡入淡出，降低拼接時的雜音。"""
        if params.sampwidth != 2 or not pcm_bytes:
            return pcm_bytes

        samples = array.array('h')
        samples.frombytes(pcm_bytes)
        fade_len = int(params.framerate * (fade_ms / 1000.0))
        if fade_len <= 0:
            return pcm_bytes
        fade_len = min(fade_len, len(samples) // params.nchannels)
        if fade_len <= 1:
            return pcm_bytes

        # 對每個聲道做線性淡入/淡出
        for ch in range(params.nchannels):
            # 淡入
            idx = ch
            for i in range(fade_len):
                factor = i / float(fade_len)
                samples[idx] = int(samples[idx] * factor)
                idx += params.nchannels
            # 淡出
            idx = len(samples) - params.nchannels + ch
            for i in range(fade_len):
                factor = (fade_len - i) / float(fade_len)
                samples[idx] = int(samples[idx] * factor)
                idx -= params.nchannels

        return samples.tobytes()

    def synthesize_segmented(self, text: str, output_path: str = None, segment_pause_sec: float = 0.18,
                              convert_chinese: bool = True) -> Optional[str]:
        """
        先完整轉台羅，再依標點切段合成並串接，保留原順序。

        Args:
            text: 原始輸入文字（華文或台文漢字）
            output_path: 合併後輸出音檔路徑
            segment_pause_sec: 標點後插入的靜音秒數
            convert_chinese: 是否啟用華文轉台文漢字預處理
        """
        if self.synthesizer is None:
            print("✗ 無可用的語音合成器")
            return None

        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f"wavs/{timestamp}.wav"
            os.makedirs("wavs", exist_ok=True)

        # 1) 先完成台羅轉換，保留原標點以便切段
        tlpa_text = self.text_processor.process_text(text, add_pauses=False, convert_chinese=convert_chinese)
        print(f"台羅拼音（分段前）: {tlpa_text}")

        # 2) 依標點切分，標點僅用來插入停頓，不再送入合成
        pattern = r'([,.!?;:])'
        parts = re.split(pattern, tlpa_text)
        segments: list[Tuple[str, str]] = []
        for i in range(0, len(parts), 2):
            content = parts[i] if i < len(parts) else ''
            punct = parts[i + 1] if i + 1 < len(parts) else ''
            segments.append((content.strip(), punct))

        params = None
        merged_frames: list[bytes] = []

        for content, punct in segments:
            if content:
                # 為每段生成臨時音檔後再合併
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_seg:
                    temp_seg_path = temp_seg.name
                try:
                    self.synthesizer.tts(content, temp_seg_path)
                    with wave.open(temp_seg_path, 'rb') as seg_wav:
                        seg_params = seg_wav.getparams()
                        seg_frames = seg_wav.readframes(seg_wav.getnframes())
                        seg_frames = self._apply_fade(seg_frames, seg_params)
                        if params is None:
                            params = seg_params
                        else:
                            if (seg_params.sampwidth != params.sampwidth or
                                    seg_params.nchannels != params.nchannels or
                                    seg_params.framerate != params.framerate):
                                raise RuntimeError("段落音檔參數不一致，無法合併")
                        merged_frames.append(seg_frames)
                finally:
                    if os.path.exists(temp_seg_path):
                        os.remove(temp_seg_path)

            # 標點後插入靜音以模擬停頓
            if punct and params and segment_pause_sec > 0:
                pause_frames = int(params.framerate * segment_pause_sec)
                merged_frames.append(b"\x00" * pause_frames * params.sampwidth * params.nchannels)

        if not merged_frames or params is None:
            print("✗ 無可合併的音訊段落")
            return None

        # 3) 合併並輸出
        with wave.open(output_path, 'wb') as out_wav:
            out_wav.setparams(params)
            for chunk in merged_frames:
                out_wav.writeframes(chunk)

        print(f"✓ 分段合併音檔已生成: {output_path}")
        return output_path
    
    def batch_synthesize(self, texts: List[str], output_dir: str = "wavs") -> List[str]:
        """批量處理"""
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, text in enumerate(texts):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"{timestamp}_{i:03d}.wav")
            result = self.synthesize(text, output_path)
            results.append(result)
            time.sleep(1)  # 避免檔名衝突
        
        return results
    
    def interactive_mode(self):
        """互動模式"""
        print("\n" + "=" * 50)
        print("台語TTS互動模式")
        print("=" * 50)
        print("輸入漢字文本，系統會轉換成台語語音")
        print("指令:")
        print("  quit, exit, 離開 - 離開程式")
        print("  test - 執行測試")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n請輸入文字: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '離開']:
                    print("再見！")
                    break
                elif user_input.lower() == 'test':
                    self._run_test()
                elif not user_input:
                    continue
                else:
                    self.synthesize(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n再見！")
                break
            except Exception as e:
                print(f"處理錯誤: {e}")
    
    def _run_test(self):
        """執行測試"""
        test_texts = [
            "大家好",
            "我是台語機器人", 
            "今天天氣真好！",
            "你會講台語嗎？",
            "謝謝你，再見。"
        ]
        
        print("\n執行測試...")
        for text in test_texts:
            print(f"\n測試文字: {text}")
            tlpa = self.text_processor.process_text(text)
            print(f"轉換結果: {tlpa}")

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='台語文字轉語音系統')
    parser.add_argument('text', nargs='*', help='要轉換的文本')
    parser.add_argument('--tacotron', help='Tacotron2模型路徑')
    parser.add_argument('--waveglow', help='WaveGlow模型路徑')
    parser.add_argument('--output', '-o', help='輸出音檔路徑')
    parser.add_argument('--interactive', '-i', action='store_true', help='啟動互動模式')
    parser.add_argument('--test', action='store_true', help='執行測試')
    parser.add_argument('--no-chinese-conversion', action='store_true', 
                       help='停用華文字轉台語漢字預處理')
    
    args = parser.parse_args()
    
    # 初始化TTS系統
    tts = TaiwaneseTextToSpeech(
        tacotron_model=args.tacotron,
        waveglow_model=args.waveglow,
        enable_chinese_conversion=not args.no_chinese_conversion
    )
    
    if args.test:
        tts._run_test()
    elif args.interactive:
        tts.interactive_mode()
    elif args.text:
        text = ' '.join(args.text)
        tts.synthesize(text, args.output)
    else:
        # 預設啟動互動模式
        tts.interactive_mode()

if __name__ == "__main__":
    main()