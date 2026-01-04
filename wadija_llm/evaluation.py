import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# 您的微調模型 ID
FINE_TUNED_MODEL = "ft:gpt-4o-mini-2024-07-18:wadija:wadija-v1:CfpAz39B"

# 測試題目 (模擬長輩說的話)
test_cases = [
    "今天菜市場人擠人。",
    "那個隔壁老王真的很吵。",
    "我腳指甲剪不到。",
    "孫子很久沒打電話回來了。",
    "最近一直下雨，心情很差。"
]

def evaluate_model():
    print(f"正在評估模型: {FINE_TUNED_MODEL}...\n")
    
    for user_input in test_cases:
        # 1. 取得微調模型的回覆
        response = client.chat.completions.create(
            model=FINE_TUNED_MODEL,
            temperature=0.8,
            messages=[
                {"role": "system", "content": "你是使用道地台語聊天的孝順子女，對話對象是年長的父母，回應在10個字內，並且要簡短、溫暖且生活化。"},
                {"role": "user", "content": user_input}
            ]
        )
        ai_reply = response.choices[0].message.content

        # 2. 請 GPT-4o 當評審老師 (LLM-as-a-Judge)
        judge_prompt = f"""
        請你擔任台語對話的評審。
        
        【情境】長輩說："{user_input}"
        【模型回覆】"{ai_reply}"

        請針對【模型回覆】進行評分（1-10分）並簡短評論，評分標準如下：
        1. 台語用字是否道地？(是否使用了正確的台語漢字，如：食、毋通、歇睏)
        2. 語氣是否像晚輩對長輩？(有無溫度，是否過於說教)
        3. 是否簡短？(是否像真人對話)

        請直接輸出 JSON 格式：
        {{
            "score": 分數,
            "comment": "簡短評語"
        }}
        """

        judge_response = client.chat.completions.create(
            model="gpt-4o", # 使用最強的模型來評分
            messages=[{"role": "user", "content": judge_prompt}],
            response_format={"type": "json_object"}
        )
        
        evaluation = json.loads(judge_response.choices[0].message.content)
        
        # 3. 顯示結果
        print(f"長輩: {user_input}")
        print(f"AI回: {ai_reply}")
        print(f"評分: {evaluation['score']} / 10")
        print(f"評語: {evaluation['comment']}")
        print("-" * 30)

if __name__ == "__main__":
    evaluate_model()