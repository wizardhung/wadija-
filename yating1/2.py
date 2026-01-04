# -*- coding: utf-8 -*-
import os, json, threading, time, audioop, math, array, wave
import requests, websocket, pyaudio
from websocket._exceptions import WebSocketConnectionClosedException
from google.cloud import speech

# ===== Yating 設定 =====
API_KEY  = os.getenv("YATING_API_KEY") or "e0b11545ab32fd588ef18437591ea9ffbc68445f"
PIPELINE = "asr-zh-en-std"
TOKEN_URL = "https://asr.api.yating.tw/v1/token"
WS_URL    = "wss://asr.api.yating.tw/ws/v1/"

TARGET_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
FRAMES_PER_BUFFER = 1000
WAVE_OUTPUT_FILENAME = "recorded.wav"

# 收集已轉成 16 kHz 的音訊片段
frames = []

def dBFS(data: bytes) -> float:
    if not data: return -120.0
    a = array.array('h', data)
    if not a: return -120.0
    mean_sq = sum(x*x for x in a)/len(a)
    if mean_sq <= 1: return -120.0
    rms = math.sqrt(mean_sq)/32768.0
    return 20*math.log10(rms)

def choose_input_device(pa: pyaudio.PyAudio) -> int | None:
    print("🔎 可用輸入裝置：")
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if int(info.get("maxInputChannels", 0)) > 0:
            print(f"  index={i:2d} | name={info.get('name','')} | defaultRate={int(info.get('defaultSampleRate',0))}Hz")
    s = input("請輸入要使用的 index（直接 Enter 用系統預設）: ").strip()
    if s == "": return None
    try: return int(s)
    except: return None

def get_token() -> str:
    r = requests.post(
        TOKEN_URL,
        headers={"key": API_KEY, "Content-Type": "application/json"},
        json={"pipeline": PIPELINE},
        timeout=10
    )
    r.raise_for_status()
    token = r.json().get("auth_token")
    if not token:
        raise RuntimeError("No auth_token in response.")
    return token

def open_stream(pa: pyaudio.PyAudio, wanted_index: int | None):
    """優先 16k 開啟；失敗則拋錯（我們已做重取樣，所以裝置不必支援 16k）"""
    try:
        st = pa.open(format=FORMAT, channels=CHANNELS, rate=TARGET_RATE, input=True,
                     frames_per_buffer=FRAMES_PER_BUFFER,
                     input_device_index=wanted_index if wanted_index is not None else None)
        return st, TARGET_RATE
    except Exception:
        # 若你的裝置不吃 16k，可改為裝置預設率，然後我們再重取樣
        info = pa.get_device_info_by_index(wanted_index) if wanted_index is not None else pa.get_default_input_device_info()
        fallback_rate = int(info.get("defaultSampleRate", 44100)) or 44100
        st = pa.open(format=FORMAT, channels=CHANNELS, rate=fallback_rate, input=True,
                     frames_per_buffer=FRAMES_PER_BUFFER,
                     input_device_index=wanted_index if wanted_index is not None else None)
        return st, fallback_rate

def to_16k(data: bytes, in_rate: int) -> bytes:
    if in_rate == TARGET_RATE:
        return data
    out, _ = audioop.ratecv(data, 2, 1, in_rate, TARGET_RATE, None)
    return out

def flush_final(ws, wait_sec: float = 4.0) -> str:
    """
    只負責把 Yating 的 final 句子拿回來並回傳文字。
    不在這裡做 Google STT。
    """
    deadline = time.time() + wait_sec
    got_any = False
    while time.time() < deadline:
        try:
            frame = ws.recv_frame()
            if frame and frame.opcode == websocket.ABNF.OPCODE_TEXT:
                payload = json.loads(frame.data.decode("utf-8"))
                got_any = True
                pipe = payload.get("pipe", {})
                if payload.get("error") or pipe.get("error"):
                    print("[server][error]", payload)
                if pipe.get("asr_final"):
                    text = pipe.get("asr_sentence") or ""
                    return text
        except websocket.WebSocketTimeoutException:
            pass
        except WebSocketConnectionClosedException:
            print("[debug] 連線已關閉（可能同時讀寫或網路中斷）")
            return ""
    if not got_any:
        print("[debug] 沒收到伺服器回傳（可能網路/防火牆/等候太短）")
    return ""

def save_wave(frames_list, rate=TARGET_RATE):
    """frames_list 內是 16k 的原始 PCM；這裡一律用 TARGET_RATE 存檔"""
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    pa = pyaudio.PyAudio()
    try:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pa.get_sample_size(FORMAT))
        wf.setframerate(TARGET_RATE)
        wf.writeframes(b''.join(frames_list))
    finally:
        wf.close()
        pa.terminate()

def run_google_stt(filename) -> str:
    """
    讀取 WAV，取前 55 秒的原始 PCM 送到 Google STT。
    回傳中文/台語/英文/無法判斷。
    """
    MAX_SEC = 55

    # 讀 WAV 取得原始 PCM（去掉 WAV header）
    import wave
    with wave.open(filename, "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        nframes = wf.getnframes()

        # 取最多 MAX_SEC 秒
        max_frames = min(nframes, int(MAX_SEC * rate))
        pcm_bytes = wf.readframes(max_frames)

    # 準備 Google STT
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=pcm_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # 我們存的是 16-bit PCM
        sample_rate_hertz=rate,                                     # 用檔案實際取樣率
        language_code="zh-TW",
        alternative_language_codes=["en-US", "nan-TW"],
        enable_automatic_punctuation=True,
    )

    try:
        response = client.recognize(config=config, audio=audio)
    except Exception as e:
        print(f"🌐 Google語言偵測發生錯誤：{e}")
        return "無法判斷"

    if not response.results:
        return "無法判斷"

    transcript = response.results[0].alternatives[0].transcript.strip()

    # 粗略語言判斷（可按需加強）
    if any(w in transcript.lower() for w in ["the", "is", "my", "name", "you", "hello"]):
        return "英文"
    if any(t in transcript for t in ["欲", "咱", "恁", "汝", "嘛會", "敢會", "食飯", "講", "無啥物"]):
        return "台語"
    if any('\u4e00' <= ch <= '\u9fff' for ch in transcript):
        return "中文"
    return "無法判斷"


def main():
    token = get_token()
    ws = websocket.create_connection(f"{WS_URL}?token={token}")
    ws.settimeout(2.0)

    pa = pyaudio.PyAudio()
    idx = choose_input_device(pa)
    stream, in_rate = open_stream(pa, idx)

    recording = threading.Event()
    quitting  = threading.Event()
    ws_lock = threading.Lock()

    def input_worker():
        print("（按 Enter 開始/停止錄音；輸入 q + Enter 結束）")
        while not quitting.is_set():
            s = input()
            if s.strip().lower() == "q":
                quitting.set()
                if recording.is_set():
                    with ws_lock:
                        ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)  # EOS 1
                        time.sleep(0.1)
                        ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)  # EOS 2
                break

            if recording.is_set():
                # 停止
                recording.clear()
                print("🔴 結束錄音，處理中...")

                # 送 EOS，先把 frames 存檔，再取 final，再跑 Google
                with ws_lock:
                    ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)
                    time.sleep(0.1)
                    ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)

                # 重要！先存檔（frames 是 16k）
                save_wave(frames, TARGET_RATE)

                # 再拿 Yating 的 final
                text = flush_final(ws, wait_sec=4.0) or ""

                # 用 Google 判語言
                lang = run_google_stt(WAVE_OUTPUT_FILENAME)

                # 依你要的格式輸出
                print(f"📝 辨識結果: {text}")
                print(f"📊 信心度: N/A")
                print(f"🌐 偵測語言：{lang}")

            else:
                # 開始
                frames.clear()
                recording.set()
                print("🟢 開始錄音")

    threading.Thread(target=input_worker, daemon=True).start()

    last_vu = 0.0
    try:
        while not quitting.is_set():
            data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)

            # 顯示音量
            if time.time() - last_vu > 0.5:
                print(f"[mic] {dBFS(data):.1f} dBFS")
                last_vu = time.time()

            # 錄音中就重取樣→推給 Yating，同時寫入 frames
            if recording.is_set():
                payload = to_16k(data, in_rate)
                frames.append(payload)
                with ws_lock:
                    try:
                        ws.send(payload, opcode=websocket.ABNF.OPCODE_BINARY)
                    except WebSocketConnectionClosedException:
                        print("[debug] 連線已關閉（傳送時）")
                        quitting.set()
                        break

    finally:
        try:
            with ws_lock:
                ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)
        except Exception:
            pass
        try: ws.close()
        except Exception:
            pass
        try: stream.stop_stream(); stream.close(); pa.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    main()
