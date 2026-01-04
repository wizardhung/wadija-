import json

import requests

BASE = "http://tts001.bronci.com.tw:8802"

def detect_fn_index():
    cfg = requests.get(f"{BASE}/config").json()
    for d in cfg.get("dependencies", []):
        if d.get("api_name") == "/predict":
            return d.get("fn_index", 0)
    return 0

def translate(text):
    display_only = "taigi_zh_tw_py：中文 → 漢羅台文 → 台羅拼音數字調"
    mode = "taigi_zh_tw_py"
    payload = {"data": [display_only, text, mode], "fn_index": detect_fn_index()}
    j = requests.post(f"{BASE}/api/predict", json=payload).json()
    return j["data"][0] if "data" in j else json.dumps(j, ensure_ascii=False)

if __name__ == "__main__":
    text = input("請輸入要翻譯的中文：")
    print(translate(text))
