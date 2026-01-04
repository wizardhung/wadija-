"""
Wadi+ Main Application
台語長輩陪伴系統 - 主程式

功能：
- 整合 OpenAI API 與 RAG Tools
- 維護對話歷史 (Context Window)
- 處理使用者輸入/輸出
- 錯誤處理與日誌記錄

作者: Wadi+ Team
更新日期: 2025-12-01
"""

import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# 匯入 RAG 工具模組
from rag_tools_v2 import load_elder_profile, build_system_prompt

# ============================================================================
# 初始設定 (Initialization)
# ============================================================================

load_dotenv()
client = OpenAI()

# 微調模型 ID (請替換成你的模型 ID)
FINE_TUNED_MODEL = "gpt-4o-mini-2024-07-18:wadija:wadija-v2:CpEQBZHS"

# 對話參數設定
DEFAULT_TEMPERATURE = 0.8      # 人性化程度 (0-2)
DEFAULT_MAX_TOKENS = 50       # 單次回應長度限制
DEFAULT_PRESENCE_PENALTY = 0.4  # 鼓勵多樣性 

# ============================================================================
# 主程式邏輯 (Main Logic)
# ============================================================================

def main():
    """
    主對話迴圈
    
    工作流程:
    1. 載入長輩個資 (Retrieve)
    2. 組裝 RAG-enhanced System Prompt (Augment)
    3. 進入對話迴圈 (Generate)
    4. 維護對話歷史 (Memory Management)
    """
    print("=" * 60)
    print("  Wadi+ 台語長輩陪伴系統 v2.0")
    print("=" * 60)
    print()
    
    # ========================================================================
    # RAG 步驟 A: 檢索資料 (Retrieve)
    # ========================================================================
    
    print("[系統] 正在載入長輩資料...")
    profile_data = load_elder_profile("profile_db.json")
    
    if not profile_data:
        print("[錯誤] 無法載入個資，程式終止。")
        print("[提示] 請確認 profile_db.json 存在且格式正確。")
        sys.exit(1)
    
    elder_name = profile_data.get('basic_info', {}).get('name', '長輩')
    print(f"\n[系統] 歡迎！準備與 {elder_name} 開始對話")
    print("[提示] 輸入 '離開' 或 'exit' 結束對話\n")
    print("=" * 60)
    
    # ========================================================================
    # RAG 步驟 B: 增強提示詞 (Augment)
    # ========================================================================
    
    # 初始化時不傳入 user_input，使用基礎 Prompt
    system_prompt_with_rag = build_system_prompt(profile_data)
    
    # 建立對話歷史 (Memory)
    messages = [
        {"role": "system", "content": system_prompt_with_rag}
    ]
    
    print("\n[系統] RAG 初始化完成，開始對話\n")

    # ========================================================================
    # RAG 步驟 C: 對話迴圈 (Generate)
    # ========================================================================
    
    conversation_count = 0  # 對話輪數計數器
    
    while True:
        try:
            # 接收使用者輸入
            user_input = input(f"\n{elder_name} 說: ").strip()
            
            # 檢查離開指令
            if user_input.lower() in ["離開", "exit", "quit", "bye"]:
                print(f"\n[系統] 感謝使用 Wadi+，祝 {elder_name} 身體健康！")
                break
            
            # 忽略空白輸入
            if not user_input:
                print("[提示] 請輸入內容")
                continue
            
            conversation_count += 1
            
            # 加入使用者訊息到歷史
            messages.append({"role": "user", "content": user_input})
            
            # ★ 動態更新 System Prompt (根據當前對話內容)
            if conversation_count % 5 == 1:  # 每 5 輪重新檢索一次
                print("[RAG] 動態更新知識庫...")
                updated_prompt = build_system_prompt(profile_data, user_input)
                messages[0] = {"role": "system", "content": updated_prompt}

            # 呼叫 OpenAI API
            response = client.chat.completions.create(
                model=FINE_TUNED_MODEL,
                messages=messages,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS,
                presence_penalty=DEFAULT_PRESENCE_PENALTY
            )

            # 提取 AI 回應
            ai_reply = response.choices[0].message.content.strip()
            
            # Token 使用統計 (可選)
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'
            
            print(f"\n{elder_name} 的子女回: {ai_reply}")
            print(f"[Debug] Tokens: {tokens_used}")

            # 加入 AI 回應到歷史紀錄
            messages.append({"role": "assistant", "content": ai_reply})
            
            # 記憶體管理：限制對話歷史長度 (避免 Token 超限)
            MAX_HISTORY_LENGTH = 20  # 保留最近 20 輪對話
            if len(messages) > MAX_HISTORY_LENGTH:
                # 保留 System Prompt + 最近的對話
                messages = [messages[0]] + messages[-(MAX_HISTORY_LENGTH-1):]
                print("[系統] 已清理舊對話記錄")

        except KeyboardInterrupt:
            print(f"\n\n[系統] 偵測到中斷信號，準備結束對話...")
            print(f"[系統] 感謝使用 Wadi+，祝 {elder_name} 身體健康！")
            break
            
        except Exception as e:
            print(f"\n[錯誤] 發生未預期錯誤: {e}")
            print("[提示] 請檢查網路連線或 API 設定")
            
            # 詢問是否繼續
            retry = input("\n是否繼續對話？(Y/n): ").strip().lower()
            if retry in ['n', 'no', '否']:
                break

# ============================================================================
# 程式進入點 (Entry Point)
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[嚴重錯誤] 程式異常終止: {e}")
        print("[提示] 請聯繫技術支援或查看日誌檔案")
        sys.exit(1)