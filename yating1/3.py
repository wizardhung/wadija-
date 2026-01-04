# -*- coding: utf-8 -*-
import os, sys, threading, time, wave, pyaudio
from google.cloud import speech

# ===== 錄音參數 =====
RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024
MAX_SECONDS = 55
WAV_PATH = os.path.abspath("recorded.wav")

# ===== Google STT 呼叫 =====
def stt_google_linear16(audio_bytes: bytes, rate: int = RATE):
    """nan-TW / zh-TW / en-US 三語提示，回傳 (transcript, confidence)"""
    max_frames = MAX_SECONDS * rate
    max_bytes = max_frames * 2  # int16 -> 2 bytes/sample
    audio_bytes = audio_bytes[:max_bytes]

    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=rate,
        language_code="nan-TW",                        # 主語言：台語
        alternative_language_codes=["zh-TW", "en-US"], # 允許中文/英文
        enable_automatic_punctuation=True,
    )
    resp = client.recognize(config=config, audio=audio)
    if not resp.results:
        return "", 0.0
    alt = resp.results[0].alternatives[0]
    return (alt.transcript or "").strip(), float(alt.confidence or 0.0)

def save_wav(frames, path=WAV_PATH):
    """將 frames 儲存為 16k/mono/16-bit WAV"""
    pa = pyaudio.PyAudio()
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pa.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
    pa.terminate()
    return path

# ===== 錄音 + Enter 控制 =====
def main():
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("⚠️ 請先設定 GOOGLE_APPLICATION_CREDENTIALS 為你的 JSON 金鑰路徑")
        return

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

    print("（按 Enter 開始/停止錄音；輸入 q + Enter 離開）")

    recording = threading.Event()
    quitting = threading.Event()
    frames = []
    last_vu = time.time()

    def input_worker():
        while not quitting.is_set():
            s = input()
            if s.strip().lower() == "q":
                if recording.is_set():
                    recording.clear()
                quitting.set()
                break
            if recording.is_set():
                recording.clear()
                print("🔴 結束錄音，處理中…")
            else:
                frames.clear()
                recording.set()
                print("🟢 開始錄音")

    threading.Thread(target=input_worker, daemon=True).start()

    try:
        while not quitting.is_set():
            data = stream.read(CHUNK, exception_on_overflow=False)
            if recording.is_set():
                frames.append(data)

            # 簡單音量表
            if time.time() - last_vu >= 0.5:
                import audioop, math
                try:
                    rms = audioop.rms(data, 2) / 32768.0
                    db = 20 * math.log10(rms) if rms > 0 else -120.0
                except Exception:
                    db = -120.0
                print(f"[mic] {db:.1f} dBFS")
                last_vu = time.time()

            # 偵測剛停止錄音
            if (not recording.is_set()) and frames:
                audio_bytes = b"".join(frames)
                frames.clear()

                # 先存 WAV（之後要傳給 1.py 用）
                save_wav([audio_bytes], WAV_PATH)

                # 丟 Google STT
                text, conf = stt_google_linear16(audio_bytes, RATE)
                print(f"📝 辨識結果: {text}")
                print(f"📊 信心度: {conf:.2f}")

                # 信心度不足 → 交給 1.py + 帶上剛剛的 wav 路徑
                if conf < 0.80:
                    print(f"⚠️ 信心度 {conf:.2f} < 0.80，yating（使用同一段錄音）…")
                    try:
                        stream.stop_stream(); stream.close()
                    except Exception:
                        pass
                    try:
                        p.terminate()
                    except Exception:
                        pass
                    os.execv(sys.executable, [sys.executable, "1.py", WAV_PATH])
                else:
                    print("✅ 信心度足夠，保留本次結果。")

    finally:
        try:
            stream.stop_stream(); stream.close()
        except Exception:
            pass
        p.terminate()
        print("👋 已關閉麥克風。")

if __name__ == "__main__":
    main()
