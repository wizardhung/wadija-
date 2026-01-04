#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI wrapper for main_corrector.py 
Allows passing WAV file as command-line argument for automated testing
"""
import os, sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() != "--help":
        # Process WAV file passed as argument
        wav_path = sys.argv[1]
        
        # Import the main module components
        from main_corrector import stt_google_linear16, logic_score_zh, CONF_MIN, LOGIC_MIN, WAV_PATH, RATE
        import shutil
        
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🎯 檔案模式 (CLI)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if not os.path.exists(_CREDS_PATH := os.path.join(os.path.dirname(__file__), 
                                                          "newproject0901-470807-038aaaad5572.json")):
            print(f"❌ 找不到 Google 金鑰檔：{_CREDS_PATH}")
            sys.exit(1)
        
        if not os.path.exists(wav_path):
            print(f"❌ 找不到檔案：{wav_path}")
            sys.exit(1)
        
        # 讀取 WAV 檔案
        try:
            with open(wav_path, 'rb') as f:
                f.read(44)  # Skip WAV header
                audio_bytes = f.read()
        except Exception as e:
            print(f"❌ 讀取檔案失敗：{e}")
            sys.exit(1)
        
        print(f"📤 處理 {os.path.getsize(wav_path)} bytes…")
        
        # Google STT
        text, conf = stt_google_linear16(audio_bytes, RATE)
        print(f"📝 辨識結果: {text}")
        print(f"📊 信心度: {conf:.2f}")
        
        # 語意合理度
        logic = 1.0
        if text:
            logic, corrected, changes = logic_score_zh(text)
            print(f"🧠 合理度: {logic:.2f}（更動 {changes} 處）")
        
        # 判斷是否通過門檻
        if (conf < CONF_MIN) or (logic < LOGIC_MIN):
            reasons = []
            if conf < CONF_MIN:   reasons.append(f"信心度 {conf:.2f} < {CONF_MIN}")
            if logic < LOGIC_MIN: reasons.append(f"合理度 {logic:.2f} < {LOGIC_MIN}")
            print(f"⚠️ {'、'.join(reasons)}，改跑 1.py…")
            try:
                shutil.copy(wav_path, WAV_PATH)
            except Exception:
                pass
            os.execv(sys.executable, [sys.executable, "1.py", wav_path])
        else:
            print("✅ 通過：信心度與合理度皆達標。")
            sys.exit(0)
    else:
        # Interactive mode
        from main_corrector import main
        main()
