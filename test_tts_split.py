#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試分句 TTS"""

import requests
import json

API_BASE = "http://localhost:5000/api"

def split_text_by_sentence(text):
    """根據標點符號分句"""
    import re
    sentences = re.split(r'([。！？；.!?;]+)', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    result = []
    for i in range(len(sentences)):
        if re.match(r'^[。！？；.!?;]+$', sentences[i]):
            if result:
                result[-1] += sentences[i]
        else:
            result.append(sentences[i])
    
    # 過濾掉純標點
    return [s for s in result if re.search(r'[\u4e00-\u9fa5a-zA-Z0-9]', s)]

def test_tts(text):
    """測試 TTS"""
    print(f"\n{'='*60}")
    print(f"測試文字: {text}")
    print(f"{'='*60}")
    
    sentences = split_text_by_sentence(text)
    print(f"分成 {len(sentences)} 個句子:")
    for i, s in enumerate(sentences, 1):
        print(f"  {i}. [{s}]")
    
    print(f"\n開始請求 TTS...")
    for i, sentence in enumerate(sentences, 1):
        print(f"\n第 {i} 句: {sentence}")
        try:
            response = requests.post(
                f"{API_BASE}/tts",
                json={"text": sentence},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"  ✓ 成功 ({len(response.content)} bytes)")
            else:
                print(f"  ✗ 失敗 ({response.status_code})")
                print(f"  錯誤: {response.text}")
        except Exception as e:
            print(f"  ✗ 異常: {e}")

if __name__ == "__main__":
    # 測試案例
    test_cases = [
        "你好",
        "你好，今天天氣很好。",
        "台灣是個美麗的地方！我很喜歡這裡。",
        "測試，帶有，多個，逗號。"
    ]
    
    for test_text in test_cases:
        test_tts(test_text)
