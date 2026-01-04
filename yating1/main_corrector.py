# -*- coding: utf-8 -*-
import os, sys, threading, time, wave
import pyaudio
from google.cloud import speech
from difflib import SequenceMatcher
import importlib

# =========================
#  1) 載入 pycorrector.corrector（子模組）
# =========================
try:
    _pyc_corrector = importlib.import_module("pycorrector.corrector")
    getattr(_pyc_corrector, "correct")  # 確認 API 存在
    _HAS_PYCORRECTOR = True
except Exception as e:
    _HAS_PYCORRECTOR = False
    print(f"⚠️ 無法載入 pycorrector.corrector（將略過更正文與改動密度訊號）：{e}")

# =========================
#  2) 載入語言流暢度工具：jieba + wordfreq
# =========================
try:
    import jieba
    from wordfreq import zipf_frequency
    _HAS_WORDFREQ = True
except Exception as e:
    _HAS_WORDFREQ = False
    print(f"⚠️ 無法載入 jieba/wordfreq（將以中性流暢度評分替代）：{e}")

# =========================
#  3) 錄音 / STT 參數
# =========================
RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024
MAX_SECONDS = 55
WAV_PATH = os.path.abspath("recorded.wav")

CONF_MIN = 0.80  # Google STT 信心度門檻
LOGIC_MIN = 0.4  # 語意合理度門檻（可依需求調整 0.85~0.90）

# =========================
#  4) 語意合理度評分（流暢度 + 改動密度 + 相似度）
# =========================
def _zipf(token: str) -> float:
    if not _HAS_WORDFREQ:
        return 0.0
    try:
        return zipf_frequency(token, "zh")
    except Exception:
        return 0.0

def _bigram_zipf_avg(text: str) -> float:
    if not _HAS_WORDFREQ:
        return 0.0
    toks = [t for t in jieba.cut(text) if t.strip()]
    if len(toks) < 2:
        return _zipf(text)
    zs, n = 0.0, 0
    for a, b in zip(toks, toks[1:]):
        zs += _zipf(a + b)  # 相鄰雙詞頻率
        n += 1
    return zs / max(1, n)

def _char_zipf_avg(text: str) -> float:
    if not _HAS_WORDFREQ:
        return 0.0
    chars = [c for c in text if c.strip()]
    if not chars:
        return 0.0
    return sum(_zipf(c) for c in chars) / len(chars)

def _squash_zipf(z: float) -> float:
    # 將 zipf 值線性壓到 0~1：3.0(偏罕見)->0、6.0(很常見)->1
    return max(0.0, min(1.0, (z - 3.0) / 3.0))

def logic_score_zh(text: str):
    """
    回傳 (score, corrected, changes)
      - score: 0~1，越高越合理
      - corrected: pycorrector 的修正句
      - changes: 修正點數
    """
    text = (text or "").strip()
    if not text:
        return 1.0, "", 0

    # A) pycorrector 訊號（改動密度）
    corrected, details, changes = text, [], 0
    if _HAS_PYCORRECTOR:
        try:
            corrected, details = _pyc_corrector.correct(text)
            changes = len(details)
        except Exception:
            pass  # 若 pycorrector 內部出錯，略過

    # B) 語言流暢度（需要 jieba + wordfreq）
    if _HAS_WORDFREQ:
        bigram_z = _bigram_zipf_avg(text)     # 搭配是否常見
        char_z   = _char_zipf_avg(text)       # 單字是否常見
        fluency = 0.7 * _squash_zipf(bigram_z) + 0.3 * _squash_zipf(char_z)
    else:
        fluency = 0.5  # 中性分

    # C) 改動密度懲罰（改越多越不合理）
    density = changes / max(1, len(text))
    penalty = min(1.0, density * 5)

    # D) 與修正文的相似度（避免「全改」也高分）
    sim = SequenceMatcher(None, text, corrected).ratio()

    # E) 綜合分數
    score = (0.75 * fluency) + (0.15 * sim) + (0.10 * (1 - penalty))
    score = max(0.0, min(1.0, score))
    return score, corrected, changes

# =========================
#  5) Google STT
# =========================
def stt_google_linear16(audio_bytes: bytes, rate: int = RATE):
    """nan-TW / zh-TW / en-US 三語提示，回傳 (transcript, confidence)"""
    max_frames = MAX_SECONDS * rate
    audio_bytes = audio_bytes[: max_frames * 2]  # int16 * 2 bytes

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

# =========================
#  6) 工具：存 WAV
# =========================
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

# =========================
#  7) 主程式：錄音 + 判斷 + Fallback
# =========================
def main():
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("⚠️ 請先設定 GOOGLE_APPLICATION_CREDENTIALS 為你的 JSON 金鑰路徑")
        return

    pa = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
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

            # 簡單音量表（Python 3.11 可用）
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

                # 存 WAV 以便 fallback 給 1.py 用
                save_wav([audio_bytes], WAV_PATH)

                # Google STT
                text, conf = stt_google_linear16(audio_bytes, RATE)
                print(f"📝 辨識結果: {text}")
                print(f"📊 信心度: {conf:.2f}")

                # 語意合理度
                logic = 1.0
                if text:
                    logic, corrected, changes = logic_score_zh(text)
                    print(f"🧠 合理度(pycorrector+流暢度): {logic:.2f}（更動 {changes} 處）")
                    # 想看修正文可開：
                    # print(f"🔧 修正建議: {corrected}")

                # 任一門檻未達 → fallback 到 1.py
                if (conf < CONF_MIN) or (logic < LOGIC_MIN):
                    reasons = []
                    if conf < CONF_MIN:   reasons.append(f"信心度 {conf:.2f} < {CONF_MIN}")
                    if logic < LOGIC_MIN: reasons.append(f"合理度 {logic:.2f} < {LOGIC_MIN}")
                    print(f"⚠️ {'、'.join(reasons)}，改跑 1.py（使用同一段錄音）…")
                    try:
                        stream.stop_stream(); stream.close()
                    except Exception:
                        pass
                    try:
                        pa.terminate()
                    except Exception:
                        pass
                    os.execv(sys.executable, [sys.executable, "1.py", WAV_PATH])
                else:
                    print("✅ 通過：信心度與合理度皆達標。")

    finally:
        try:
            stream.stop_stream(); stream.close()
        except Exception:
            pass
        pa.terminate()
        print("👋 已關閉麥克風。")

if __name__ == "__main__":
    main()
