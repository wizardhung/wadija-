import pyaudio
pa = pyaudio.PyAudio()
print("=== Input devices ===")
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if int(info.get("maxInputChannels", 0)) > 0:
        print(f"index={i:2d} | name={info['name']} | defaultRate={int(info.get('defaultSampleRate',0))}")
print("=====================")

# 試著打開每個裝置，先用16k，失敗就用裝置預設速率
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if int(info.get("maxInputChannels", 0)) <= 0: 
        continue
    for rate in (16000, int(info.get("defaultSampleRate", 0)) or 44100, 48000):
        try:
            s = pa.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True,
                        frames_per_buffer=1024, input_device_index=i)
            s.close()
            print(f"[OK] index={i} 可用, rate={rate}")
            break
        except Exception as e:
            print(f"[NG] index={i} rate={rate} -> {e}")
pa.terminate()
