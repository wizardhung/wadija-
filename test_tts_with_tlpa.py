import requests
import json

API_BASE = "http://localhost:5000/api"

test_text = "你好，我是台語助手。"

print("=" * 60)
print("🧪 測試 TTS 台羅拼音顯示")
print("=" * 60)
print(f"測試句子: {test_text}\n")

try:
    response = requests.post(
        f"{API_BASE}/tts",
        json={"text": test_text},
        timeout=30
    )
    
    if response.ok:
        data = response.json()
        print(f"✅ API 回應成功")
        print(f"   文字: {data.get('text', 'N/A')}")
        print(f"   台羅: {data.get('tlpa', 'N/A')}")
        print(f"   音檔大小: {data.get('file_size', 'N/A')} bytes")
        print(f"   成功: {data.get('success', False)}")
        
        # 驗證 audio 欄位存在且不為空
        if 'audio' in data and data['audio']:
            audio_len = len(data['audio'])
            print(f"   Base64 音檔長度: {audio_len} characters")
            print(f"\n✅ 台羅拼音將顯示在網頁上:")
            print(f"   🔊 台羅拼音: {data.get('tlpa', 'N/A')}")
        else:
            print("❌ 音檔數據缺失")
    else:
        print(f"❌ API 錯誤: {response.status_code}")
        print(f"   {response.text}")
        
except Exception as e:
    print(f"❌ 錯誤: {e}")

print("\n" + "=" * 60)
