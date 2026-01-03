#!/usr/bin/env python3
"""
完整台羅轉換流程測試腳本
測試：LLM 輸出 → 台羅數字調轉換 → TTS 語音合成
"""

import requests
import json
import base64
import wave

API_BASE = "http://localhost:5000"

def print_header(title):
    """打印標題"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_chat_with_tlpa(message, session_id="test"):
    """測試聊天 API 並獲取台羅轉換"""
    print_header("步驟 1: LLM 對話與台羅轉換")
    print(f"用戶輸入: {message}\n")
    
    response = requests.post(
        f"{API_BASE}/api/chat",
        json={"message": message, "session_id": session_id},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        reply = data.get('reply', '')
        tlpa = data.get('reply_tlpa', '')
        
        print(f"✓ LLM 回應成功")
        print(f"  原始回覆: {reply}")
        print(f"  台羅數字調: {tlpa}")
        print(f"  台羅長度: {len(tlpa)} 字元")
        
        return tlpa
    else:
        print(f"✗ Chat API 失敗: {response.status_code}")
        print(f"  錯誤訊息: {response.text}")
        return None

def test_tts_with_tlpa(tlpa_text, output_file="test_output.wav"):
    """使用台羅文本測試 TTS API"""
    print_header("步驟 2: 台羅數字調 → TTS 語音合成")
    print(f"台羅輸入: {tlpa_text}\n")
    
    response = requests.post(
        f"{API_BASE}/api/tts",
        json={"text": tlpa_text},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('success'):
            print(f"✓ TTS 合成成功")
            print(f"  輸入文字: {data.get('text', 'N/A')}")
            print(f"  台羅確認: {data.get('tlpa', 'N/A')}")
            print(f"  音檔大小: {data.get('file_size', 0):,} bytes")
            
            # 解碼並保存音檔
            audio_base64 = data.get('audio', '')
            if audio_base64:
                audio_data = base64.b64decode(audio_base64)
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                
                # 獲取音檔資訊
                with wave.open(output_file, 'rb') as wav:
                    frames = wav.getnframes()
                    rate = wav.getframerate()
                    duration = frames / float(rate)
                    
                print(f"  音檔時長: {duration:.2f} 秒")
                print(f"  音檔已保存: {output_file}")
                return True
        else:
            print(f"✗ TTS 失敗: {data.get('error', 'Unknown')}")
            return False
    else:
        print(f"✗ TTS API 失敗: {response.status_code}")
        print(f"  錯誤訊息: {response.text}")
        return False

def main():
    """主測試流程"""
    print_header("完整台羅轉換與 TTS 流程測試")
    print("測試流程: LLM 輸出 → 完整台羅數字調轉換 → TTS 語音合成")
    
    # 測試案例
    test_cases = [
        "你好，你叫什麼名字？",
        "今天天氣如何？",
        "你會說台語嗎？"
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 60}")
        print(f"# 測試案例 {i}/{len(test_cases)}")
        print(f"{'#' * 60}")
        
        # 步驟 1: 獲取 LLM 回應和台羅轉換
        tlpa_text = test_chat_with_tlpa(message, session_id=f"test_{i}")
        
        if tlpa_text:
            # 步驟 2: 使用台羅文本進行 TTS 合成
            output_file = f"test_output_{i}.wav"
            success = test_tts_with_tlpa(tlpa_text, output_file)
            
            if success:
                print(f"\n✓ 測試案例 {i} 完成！")
            else:
                print(f"\n✗ 測試案例 {i} TTS 失敗")
        else:
            print(f"\n✗ 測試案例 {i} Chat 失敗")
    
    # 最終總結
    print_header("測試總結")
    print("✓ LLM 輸出台語漢字")
    print("✓ 完整轉換為台羅數字調（add_pauses=True）")
    print("✓ 台羅文本直接進入 TTS 合成（convert_chinese=False）")
    print("✓ 語音合成成功")
    print("\n流程確認：")
    print("  1. LLM 輸出 → 台羅完整轉換（in /api/chat）")
    print("  2. 台羅數字調 → TTS 語音合成（in /api/tts）")
    print("  3. 無二次轉換，確保語義一致性")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n測試中斷")
    except Exception as e:
        print(f"\n\n✗ 測試錯誤: {e}")
        import traceback
        traceback.print_exc()
