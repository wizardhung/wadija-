import json
import os

# --- 設定路徑 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(BASE_DIR, 'dictionaries')

def load_json(filename):
    """通用 JSON 讀取函式"""
    try:
        path = os.path.join(DICT_DIR, filename)
        if not os.path.exists(path):
            # 為了避免找不到檔案報錯，如果不在 dictionaries 裡，試試看根目錄 (給 profile_db 用)
            path = os.path.join(BASE_DIR, filename)
            
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: 無法讀取 {filename}: {e}")
        return {}

def determine_accent(location):
    """
    根據地點判斷腔調
    這是一個簡單的規則庫，您可以根據需求持續擴充
    """
    location = location or ""
    
    if any(x in location for x in ["鹿港", "台西", "金門", "淡水", "新竹"]):
        return "quanzhou"
    elif any(x in location for x in ["宜蘭", "員山", "板橋"]): # 宜蘭腔代表
        return "zhangzhou"
    else:
        # 預設為通行混合腔 (台南、高雄、台中多數地區)
        return "mixed"

def build_system_prompt(profile_data):
    if not profile_data:
        return "你是使用道地台語聊天的孝順子女。"

    # 1. 載入長輩基本資料
    info = profile_data.get("basic_info", {})
    health = profile_data.get("health_condition", {})
    
    # 2. 判斷腔調
    accent_key = determine_accent(info.get("location", ""))
    
    # 3. 載入所有字典
    common_rules = load_json("common_rules.json")
    japanese_loan = load_json("japanese_loan.json")
    accents_data = load_json("accents.json")
    
    # 取得該長輩對應的腔調字典
    target_accent = accents_data.get(accent_key, accents_data.get("mixed"))

    # 4. 動態組裝 Prompt (最關鍵的一步)
    
    # A. 處理日語借詞字串
    jp_dict_str = "\n".join([f"- {k} -> **{v}**" for k, v in japanese_loan.get("vocabulary", {}).items()])
    
    # B. 處理腔調特殊用詞字串
    accent_vocab_str = "\n".join([f"- {k} -> **{v}**" for k, v in target_accent.get("vocab", {}).items()])

    # C. 處理通用規範字串
    common_rules_str = "\n".join(common_rules.get("negatives", {}).get("rules", []))
    
    
    rag_prompt = f"""
    你是一個孝順、貼心的子女，正在用道地的台語跟父母聊天。
    對話對象是：{info.get('name')}，住在{info.get('location')}。
    因此，你說話必須帶有 **[{target_accent.get('name')}]** 的特色。

    【個人資訊】
    - 身體：{', '.join(health.get('chronic_diseases', []))}
    - 備註：{health.get('physical_state')}

    =============== 語言核心規範 (請嚴格遵守) ===============

    1. **基礎通用規範**：
    {common_rules_str}

    2. **日語借詞 (台灣長輩習慣用語，請優先使用)**：
    {jp_dict_str}

    3. **在地腔調用詞 ({target_accent.get('name')})**：
    {accent_vocab_str}

    =======================================================

    【回答原則】
    - 必須使用對應的台閩漢字。
    - 語氣簡短、溫暖。
    - 若遇到日語借詞表中的詞彙（如機車、醫生），請務必使用表中的講法（歐兜邁、先生）。
    """
    return rag_prompt.strip()

def load_elder_profile(filename="profile_db.json"):
    return load_json(filename)