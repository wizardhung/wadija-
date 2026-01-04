import os
from openai import OpenAI
from dotenv import load_dotenv

# 1. 載入 .env
load_dotenv()

# 2. 建立 OpenAI 客戶端
try:
    client = OpenAI()

    # --- 微調模型 ID ---
    YOUR_CORRECT_MODEL_ID = "ft:gpt-4o-mini-2024-07-18:wadija:wadija-v1:CfpAz39B" 

    # 3. 呼叫 API
    chat_response = client.chat.completions.create(
        model=YOUR_CORRECT_MODEL_ID,
    # --- 參數調整區 ---
        
        # 1. 創意度：保持 0.8，有溫度但不發瘋
        temperature=0.8, 
        
        # 2. 長度限制：限制回覆長度，確保「簡短」
        # 設定 100 tokens 大約是 50-70 個中文字，足夠講2句話，避免長篇大論
        max_tokens=100,
        
        # 3. 重複懲罰：稍微給一點懲罰，避免它一直重複「你要小心、你要小心」
        # 設定 0.3 很安全，不會破壞台語的語助詞習慣
        frequency_penalty=0.3,
        
        # 4. 話題新鮮度：稍微鼓勵它講點新的，不要一直鬼打牆
        presence_penalty=0.3,

        messages=[
            {
                "role": "system", 
                "content": "你是使用道地台語聊天的孝順子女，對話對象是年長的父母，回應要簡短、溫暖且生活化。"
            },
            {
                "role": "user",
                "content": "應該是這幾天變冷了吧",
            },
        ]
    )

    # 4. 顯示結果
    print("AI: " + chat_response.choices[0].message.content)

except Exception as e:
    print(f"測試失敗，發生錯誤：{e}")