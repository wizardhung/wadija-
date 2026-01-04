# -*- coding: utf-8 -*-
import os, sys, json, threading, time, audioop, math, array, wave
import requests, websocket, pyaudio
from websocket._exceptions import WebSocketConnectionClosedException

API_KEY  = os.getenv("YATING_API_KEY") or "e0b11545ab32fd588ef18437591ea9ffbc68445f"
PIPELINE = "asr-zh-en-std"
TOKEN_URL = "https://asr.api.yating.tw/v1/token"
WS_URL    = "wss://asr.api.yating.tw/ws/v1/"

TARGET_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
FRAMES_PER_BUFFER = 1000  # 以 "樣本數" 為單位（16k 時約 62.5ms）

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
            name = info.get("name","")
            rate = int(info.get("defaultSampleRate",0))
            print(f"  index={i:2d} | name={name} | defaultRate={rate}Hz")
    s = input("請輸入要使用的 index（直接 Enter 用系統預設）: ").strip()
    if s == "": return None
    try:
        return int(s)
    except:
        return None

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
    try:
        st = pa.open(format=FORMAT, channels=CHANNELS, rate=TARGET_RATE, input=True,
                     frames_per_buffer=FRAMES_PER_BUFFER,
                     input_device_index=wanted_index if wanted_index is not None else None)
        return st, TARGET_RATE
    except Exception:
        pass
    rates = []
    if wanted_index is not None:
        try:
            info = pa.get_device_info_by_index(wanted_index)
            rates.append(int(info.get("defaultSampleRate",0)) or 48000)
        except Exception:
            pass
    rates += [48000, 44100]
    for r in rates:
        try:
            st = pa.open(format=FORMAT, channels=CHANNELS, rate=r, input=True,
                         frames_per_buffer=FRAMES_PER_BUFFER,
                         input_device_index=wanted_index if wanted_index is not None else None)
            return st, r
        except Exception:
            continue
    raise RuntimeError("無法開啟麥克風（請確認權限/裝置未被佔用/選對 index）")

def to_16k(data: bytes, in_rate: int, in_sampwidth: int = 2, in_channels: int = 1) -> bytes:
    # 轉 16-bit
    if in_sampwidth != 2:
        data = audioop.lin2lin(data, in_sampwidth, 2)
    # 轉 mono
    if in_channels != 1:
        data = audioop.tomono(data, 2, 0.5, 0.5)
    # 重採樣
    if in_rate != TARGET_RATE:
        data, _ = audioop.ratecv(data, 2, 1, in_rate, TARGET_RATE, None)
    return data

# ✅ 台語關鍵詞偵測（只有顯示用途）
def detect_language(text: str) -> str:
    taiwanese_keywords = [
        "欲","敢會","有影無","煞","無啥物","食飯","咱","啊你","汝","攏","恁","嘛會",
        "歹勢","共款","輸贏","講","麥","哩","毋是","食飽","食未"
    ]
    text_lower = text.lower()
    if any(word in text_lower for word in ["the","and","you","hello","name","is"]):
        return "英文"
    elif any(tw in text for tw in taiwanese_keywords):
        return "台語"
    elif any('\u4e00' <= ch <= '\u9fff' for ch in text):
        return "台語"
    else:
        return "無法判斷"

def flush_final(ws, wait_sec: float = 4.0):
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
                    if text:
                        lang = detect_language(text)
                        print(f"📝 辨識結果: {text}")
                        print(f"📊 信心度: N/A")
                        print(f"🌐 偵測語言：{lang}")
                        return
        except websocket.WebSocketTimeoutException:
            pass
        except WebSocketConnectionClosedException:
            print("[debug] 連線已關閉（可能同時讀寫或網路中斷）")
            return
    if not got_any:
        print("[debug] 沒收到伺服器回傳（可能網路/防火牆/等候太短）")

# ---------- 檔案模式：把 WAV 串流送到 Yating ----------
def stream_wav_file_to_ws(ws, wav_path: str):
    if not os.path.isfile(wav_path):
        raise FileNotFoundError(f"WAV 檔不存在：{wav_path}")
    with wave.open(wav_path, 'rb') as wf:
        in_rate = wf.getframerate()
        in_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()  # bytes per sample

        # 每次讀多少「來源取樣數」：估一個對應 16k 時的 FRAMES_PER_BUFFER
        # 讓上傳節奏接近即時
        read_frames = max(1, int(FRAMES_PER_BUFFER * (in_rate / float(TARGET_RATE))))

        while True:
            raw = wf.readframes(read_frames)
            if not raw:
                break
            payload = to_16k(raw, in_rate, sampwidth, in_channels)
            ws.send(payload, opcode=websocket.ABNF.OPCODE_BINARY)
            # 控制節奏，避免一次送太快
            time.sleep(read_frames / float(in_rate))

    # 送兩個空段表示結束，並等待最終結果
    ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)
    time.sleep(0.1)
    ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)
    flush_final(ws, wait_sec=4.0)

def main():
    # 若帶入 WAV 路徑則走「檔案模式」
    if len(sys.argv) >= 2 and sys.argv[1].lower().endswith(".wav"):
        wav_path = sys.argv[1]
        print(f"📥 檔案模式：使用 {wav_path} 送交 Yating 辨識")
        token = get_token()
        ws = websocket.create_connection(f"{WS_URL}?token={token}")
        ws.settimeout(2.0)
        try:
            stream_wav_file_to_ws(ws, wav_path)
        finally:
            try: ws.close()
            except Exception: pass
        return

    # ---------- 即時麥克風模式（原本流程） ----------
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
                        ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)
                        time.sleep(0.1)
                        ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)
                        flush_final(ws, wait_sec=4.0)
                break
            if recording.is_set():
                recording.clear()
                print("🔴 結束錄音")
                with ws_lock:
                    ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)
                    time.sleep(0.1)
                    ws.send(b"", opcode=websocket.ABNF.OPCODE_BINARY)
                    flush_final(ws, wait_sec=4.0)
            else:
                recording.set()
                print("🟢 開始錄音")

    threading.Thread(target=input_worker, daemon=True).start()

    last_vu = 0.0
    try:
        while not quitting.is_set():
            data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
            if time.time() - last_vu > 0.5:
                print(f"[mic] {dBFS(data):.1f} dBFS")
                last_vu = time.time()
            if recording.is_set():
                payload = to_16k(data, in_rate, 2, 1)
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
