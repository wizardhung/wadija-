#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STT 路由測試腳本（檔案模式）
測試語音輸入文件或 WAV 數據
根據信心度自動在 Google STT 和 Yating STT 之間切換
"""

import os
import sys
import requests
import json
import wave
import base64
from pathlib import Path

# 設置 Yating API Key（若需要）
if "YATING_API_KEY" not in os.environ:
    os.environ["YATING_API_KEY"] = "e0b11545ab32fd588ef18437591ea9ffbc68445f"

API_BASE = "http://localhost:5000"

def load_wav_file(audio_path: str) -> tuple:
    """讀取 WAV 檔案，返回 (PCM 數據, 取樣率)"""
    with wave.open(audio_path, 'rb') as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        
        print(f"   📊 Channels: {channels}")
        print(f"   📊 Sample Rate: {rate} Hz")
        print(f"   📊 Bit Depth: {sample_width * 8} bits")
        print(f"   📊 Duration: {len(frames) / (channels * sample_width * rate):.2f} sec")
        
        return frames, rate

def test_stt_api(audio_bytes: bytes, sample_rate: int = 16000):
    """呼叫 STT API，展示信心度路由"""
    
    print("\n" + "=" * 70)
    print("📤 發送到 STT API...")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/stt",
            json={
                "audio": base64.b64encode(audio_bytes).decode('utf-8'),
                "sample_rate": sample_rate
            },
            timeout=120
        )
        
        result = response.json()
        
        if result.get("success"):
            print(f"\n✅ STT 成功")
            print(f"📌 提供者: {result.get('provider', 'unknown')}")
            print(f"📝 轉寫結果: {result.get('transcript', '')}")
            
            conf = result.get('confidence')
            if conf is not None:
                print(f"📊 信心度: {conf:.2%}")
            else:
                print(f"📊 信心度: N/A (Yating 無提供)")
            
            google_conf = result.get('google_confidence')
            if google_conf is not None:
                print(f"🔹 Google 信心度: {google_conf:.2%}")
            
            print("\n" + "=" * 70)
            print("🔍 路由說明：")
            print("=" * 70)
            provider = result.get('provider', '')
            if provider == "google":
                print("✅ 使用 Google STT（信心度 ≥ 80%）")
                print("   適合: 通用中文/台語/英文")
            elif provider == "yating":
                print("✅ 使用 Yating STT（Google 信心度 < 80%，切換台語專用）")
                print("   適合: 純台語或口音明顯的台語")
            elif provider == "google_low_conf":
                print("⚠️  Google 低信心但 Yating 失敗，返回 Google 結果")
                print("   建議: 重新錄音或調整麥克風")
            
        else:
            print(f"❌ STT 失敗: {result.get('error', 'unknown')}")
            
    except requests.exceptions.Timeout:
        print("❌ 請求超時（可能正在処理較長的音頻）")
    except Exception as e:
        print(f"❌ 錯誤: {e}")

def test_with_file(audio_path: str):
    """使用 WAV 檔案進行測試"""
    if not os.path.exists(audio_path):
        print(f"❌ 檔案不存在: {audio_path}")
        return
    
    print(f"📁 使用檔案: {audio_path}")
    try:
        audio_bytes, rate = load_wav_file(audio_path)
        test_stt_api(audio_bytes, sample_rate=rate)
    except Exception as e:
        print(f"❌ 無法讀取 WAV 檔案: {e}")

def main():
    print("=" * 70)
    print("🎙️  STT 自動路由測試工具（檔案模式）")
    print("=" * 70)
    print("\n說明:")
    print("1. 【讀取 WAV 檔案】：支援任何 WAV 格式")
    print("2. 【Google STT 優先】：檢查信心度")
    print("3. 【信心度 < 80%】：自動切換到 Yating 台語 STT")
    print("4. 【自動選擇】：選擇最可能正確的結果")
    print("\n" + "=" * 70)
    
    # 檢查 API
    try:
        health = requests.get(f"{API_BASE}/api/health", timeout=5).json()
        if health.get("status") == "ok":
            print("✅ API 服務已啟動")
            services = health.get("services", {})
            print(f"   STT: {'✅' if services.get('stt') else '❌'}")
            print(f"   LLM: {'✅' if services.get('llm') else '❌'}")
            print(f"   TTS: {'✅' if services.get('tts') else '❌'}")
        else:
            print("❌ API 服務異常")
            return
    except Exception as e:
        print(f"❌ 無法連接到 API: {e}")
        print(f"   請先啟動: cd /home/wizard/專題tts && conda run -n c2t python3 integrated_voice_chat_api.py")
        return
    
    print("\n" + "=" * 70)
    print("可用測試檔案：")
    print("=" * 70)
    
    # 列舉可用 WAV 檔案
    candidates = [
        "/home/wizard/專題tts/yating1/recorded.wav",
        "/home/wizard/專題tts/yating1/test_440hz.wav",
        "/tmp/stt_test_audio.wav"
    ]
    
    for i, path in enumerate(candidates, 1):
        if os.path.exists(path):
            print(f"{i}. {path}")
    
    # 優先使用第一個可用檔案（支持 CI/自動化）
    for path in candidates:
        if os.path.exists(path):
            print(f"\n✅ 使用檔案: {path}\n")
            test_with_file(path)
            break
    else:
        print("\n❌ 沒有可用的 WAV 檔案")
        print("提示: 你可以使用 yating1/ 資料夾中的腳本錄製音頻")

if __name__ == "__main__":
    main()
