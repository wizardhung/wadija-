# -*- coding: utf-8 -*-
"""
整合語音對話 API
整合 STT (yating1) + LLM (wadija_llm) + TTS (taiwanese_tonal_tlpa_tacotron2_hsien1)
提供完整的語音對話功能

端點:
- POST /api/stt - 語音轉文字
- POST /api/chat - 發送訊息給 LLM 並獲得回應
- POST /api/tts - 文字轉台語語音
- GET /api/health - 健康檢查
"""

import os
import sys
import tempfile
import time
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import base64
import wave
import requests
from websocket import create_connection, ABNF
import audioop

# 添加模組路徑
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "yating1"))
sys.path.insert(0, str(BASE_DIR / "wadija_llm"))
sys.path.insert(0, str(BASE_DIR / "taiwanese_tonal_tlpa_tacotron2_hsien1"))

# ============================================================================
# 初始化 Flask 應用
# ============================================================================
app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 將訊息同時輸出到終端與工作目錄的日誌檔
LOG_FILE_PATH = Path('/home/wizard/專題tts/api_terminal.log')

def log_terminal(msg: str):
    try:
        print(msg)
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE_PATH.open('a', encoding='utf-8') as f:
            f.write(msg + "\n")
    except Exception:
        # 若寫檔失敗，至少保留終端輸出
        pass

# ============================================================================
# 導入各模組
# ============================================================================
# ============================================================================
# 導入各模組
# ============================================================================
try:
    # STT 模組
    from google.cloud import speech
    print("✓ Google Cloud Speech 模組載入成功")
except Exception as e:
    print(f"⚠️ STT 模組載入失敗: {e}")
    speech = None

# Yating STT 設定（台語優先）
YATING_API_KEY = os.getenv("YATING_API_KEY") or ""
YATING_PIPELINE = "asr-zh-en-nan"
YATING_TOKEN_URL = "https://asr.api.yating.tw/v1/token"
YATING_WS_URL = "wss://asr.api.yating.tw/ws/v1/"

# STT 信心度門檻（Google 低於此值才切到 Yating 台語 STT）
GOOGLE_CONF_MIN = 0.80

# 設定 Google Cloud 認證
CREDS_PATH = str(BASE_DIR / "yating1" / "newproject0901-470807-038aaaad5572.json")
if os.path.exists(CREDS_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDS_PATH
    print(f"✓ Google Cloud 認證已設置")
else:
    print(f"⚠️ 找不到 Google Cloud 認證: {CREDS_PATH}")

try:
    # LLM 模組
    from openai import OpenAI
    from dotenv import load_dotenv
    
    # 載入環境變數
    env_path = BASE_DIR / "wadija_llm" / ".env"
    if os.path.exists(env_path):
        load_dotenv(str(env_path))
    
    llm_client = OpenAI()
    
    # 載入 RAG 工具
    wadija_path = str(BASE_DIR / "wadija_llm")
    if wadija_path not in sys.path:
        sys.path.insert(0, wadija_path)
    
    try:
        from rag_tools_v2 import load_elder_profile, build_system_prompt
        
        # 載入長輩資料
        profile_path = BASE_DIR / "wadija_llm" / "profile_db.json"
        if profile_path.exists():
            profile_data = load_elder_profile(str(profile_path))
        else:
            print(f"⚠️ 找不到長輩資料: {profile_path}，使用預設")
            profile_data = None
    except ImportError as e:
        print(f"⚠️ RAG 工具載入失敗: {e}，使用簡化模式")
        build_system_prompt = None
        profile_data = None
    
    # 微調模型 ID
    FINE_TUNED_MODEL = "ft:gpt-4o-mini-2024-07-18:wadija:wadija-v1:CfpAz39B"
    
    print("✓ LLM 模組載入成功")
except Exception as e:
    print(f"⚠️ LLM 模組載入失敗: {e}")
    llm_client = None
    profile_data = None
    build_system_prompt = None

try:
    # TTS 模組
    from taiwanese_tts_v2 import TaiwaneseTextToSpeech
    
    # 初始化 TTS 系統
    tts_system = TaiwaneseTextToSpeech(
        enable_chinese_conversion=True
    )
    
    print("✓ TTS 模組載入成功")
except Exception as e:
    print(f"⚠️ TTS 模組載入失敗: {e}")
    tts_system = None

# ============================================================================
# 對話歷史管理
# ============================================================================
# 使用字典儲存每個會話的對話歷史
conversation_sessions = {}

def get_or_create_session(session_id):
    """獲取或創建會話"""
    if session_id not in conversation_sessions:
        # 初始化新會話
        if llm_client and profile_data and build_system_prompt:
            try:
                system_prompt = build_system_prompt(profile_data)
            except Exception as e:
                print(f"⚠️ 無法生成系統提示詞: {e}")
                system_prompt = "你是一個友善的台灣台語 AI 助手。請用台語（台羅漢字或台灣台語漢字）直接回答用戶的問題。"
            
            conversation_sessions[session_id] = {
                "messages": [{"role": "system", "content": system_prompt}],
                "created_at": time.time()
            }
        else:
            conversation_sessions[session_id] = {
                "messages": [{"role": "system", "content": "你是一個友善的台灣台語 AI 助手。請用台語（台羅漢字或台灣台語漢字）直接回答用戶的問題。"}],
                "created_at": time.time()
            }
    
    return conversation_sessions[session_id]

# =========================================================================
# STT 工具：Google / Yating（自動落地切換）
# =========================================================================

def google_stt_linear16(audio_bytes: bytes, rate: int = 16000, max_seconds: int = 55):
    """使用 Google STT（nan-TW 為主）回傳 (text, confidence)。"""
    if speech is None:
        return "", 0.0

    max_frames = max_seconds * rate
    audio_bytes = audio_bytes[: max_frames * 2]  # int16 * 2 bytes

    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=rate,
        language_code="nan-TW",
        alternative_language_codes=["zh-TW", "en-US"],
        enable_automatic_punctuation=True,
    )

    response = client.recognize(config=config, audio=audio)
    if not response.results:
        return "", 0.0
    alt = response.results[0].alternatives[0]
    return (alt.transcript or "").strip(), float(alt.confidence or 0.0)


def _yating_get_token():
    if not YATING_API_KEY:
        raise RuntimeError("缺少 YATING_API_KEY")
    r = requests.post(
        YATING_TOKEN_URL,
        headers={"key": YATING_API_KEY, "Content-Type": "application/json"},
        json={"pipeline": YATING_PIPELINE},
        timeout=10,
    )
    r.raise_for_status()
    token = r.json().get("auth_token")
    if not token:
        raise RuntimeError("Yating 無 auth_token 回應")
    return token


def _to_16k_mono(audio_bytes: bytes, rate: int) -> bytes:
    data = audio_bytes
    # 假設 int16/mono，如果取樣率不同則重採樣
    if rate != 16000:
        data, _ = audioop.ratecv(data, 2, 1, rate, 16000, None)
    return data


def yating_stt_linear16(audio_bytes: bytes, rate: int = 16000, chunk_samples: int = 1000):
    """呼叫 Yating WS STT，返回台語轉寫（不提供信心度）。"""
    token = _yating_get_token()
    ws = create_connection(f"{YATING_WS_URL}?token={token}")
    ws.settimeout(6.0)

    try:
        payload = _to_16k_mono(audio_bytes, rate)
        chunk_bytes = max(1, chunk_samples * 2)
        for i in range(0, len(payload), chunk_bytes):
            ws.send(payload[i:i+chunk_bytes], opcode=ABNF.OPCODE_BINARY)
            time.sleep(chunk_bytes / 2 / 16000.0)

        # EOS x2
        ws.send(b"", opcode=ABNF.OPCODE_BINARY)
        time.sleep(0.1)
        ws.send(b"", opcode=ABNF.OPCODE_BINARY)

        # 等待最終 asr_final
        deadline = time.time() + 6.0
        text = ""
        while time.time() < deadline:
            try:
                frame = ws.recv_frame()
                if frame and frame.opcode == ABNF.OPCODE_TEXT:
                    payload_json = json.loads(frame.data.decode("utf-8"))
                    pipe = payload_json.get("pipe", {})
                    if pipe.get("asr_final"):
                        text = pipe.get("asr_sentence") or ""
                        break
            except Exception:
                break
        return text.strip()
    finally:
        try:
            ws.close()
        except Exception:
            pass

# ============================================================================
# API 端點
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康檢查"""
    return jsonify({
        "status": "ok",
        "services": {
            "stt": speech is not None,
            "llm": llm_client is not None,
            "tts": tts_system is not None
        }
    })

@app.route('/api/stt', methods=['POST'])
def speech_to_text():
    """
    語音轉文字
    接收音頻數據，返回識別的文字
    """
    try:
        if (speech is None) and (not YATING_API_KEY):
            return jsonify({
                "success": False,
                "error": "STT 未初始化，缺少 Google 或 Yating 配置"
            }), 503

        # 取得音訊資料（可接受 multipart 或 base64 JSON），預設 16k/mono/16-bit
        sample_rate = 16000
        if 'audio' not in request.files:
            data = request.get_json() or {}
            if 'audio' not in data:
                return jsonify({"error": "未提供音頻數據"}), 400
            audio_data = base64.b64decode(data['audio'])
            sample_rate = int(data.get('sample_rate', 16000) or 16000)
        else:
            audio_file = request.files['audio']
            audio_data = audio_file.read()
            sample_rate = int(request.form.get('sample_rate', 16000) or 16000)

        google_text, google_conf = "", 0.0
        if speech is not None:
            try:
                google_text, google_conf = google_stt_linear16(audio_data, rate=sample_rate)
            except Exception as e:
                print(f"STT Google 錯誤: {e}")

        # 信心度高 → 直接用 Google (中文/台語雙模)
        if google_text and google_conf >= GOOGLE_CONF_MIN:
            return jsonify({
                "success": True,
                "provider": "google",
                "transcript": google_text,
                "confidence": google_conf
            })

        # 低信心 → 切 Yating 台語 STT
        yating_text = ""
        try:
            yating_text = yating_stt_linear16(audio_data, rate=sample_rate)
        except Exception as e:
            print(f"STT Yating 錯誤: {e}")

        if yating_text:
            return jsonify({
                "success": True,
                "provider": "yating",
                "transcript": yating_text,
                "confidence": None,
                "google_confidence": google_conf
            })

        # 若 Yating 失敗但 Google 有文字，回傳 Google 低信心結果
        if google_text:
            return jsonify({
                "success": True,
                "provider": "google_low_conf",
                "transcript": google_text,
                "confidence": google_conf
            })

        return jsonify({
            "success": False,
            "error": "無法識別語音"
        }), 400

    except Exception as e:
        print(f"STT 錯誤: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    LLM 對話
    接收用戶訊息，返回 AI 回應
    """
    try:
        if not llm_client:
            return jsonify({"error": "LLM 服務未初始化"}), 500
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({"error": "訊息不能為空"}), 400
        
        # 獲取會話
        session = get_or_create_session(session_id)
        messages = session["messages"]
        
        # 添加用戶訊息
        messages.append({"role": "user", "content": user_message})
        
        # 呼叫 OpenAI API
        response = llm_client.chat.completions.create(
            model=FINE_TUNED_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=150,
            presence_penalty=0.4
        )
        
        # 提取 AI 回應
        ai_reply = response.choices[0].message.content.strip()
        
        # 完整轉換為台羅數字調（add_pauses=True 確保生成可直接合成的完整台羅文本）
        tlpa_text = tts_system.text_processor.process_text(ai_reply, add_pauses=True, convert_chinese=True) if tts_system else ai_reply
        log_terminal(f"\n[台羅轉換] 原文: {ai_reply}")
        log_terminal(f"[台羅轉換] 台羅: {tlpa_text}\n")
        
        # 添加到對話歷史
        messages.append({"role": "assistant", "content": ai_reply})
        
        # 記憶體管理：限制對話歷史長度
        MAX_HISTORY = 20
        if len(messages) > MAX_HISTORY:
            messages = [messages[0]] + messages[-(MAX_HISTORY-1):]
        
        return jsonify({
            "success": True,
            "reply": ai_reply,
            "reply_tlpa": tlpa_text,
            "session_id": session_id
        })
        
    except Exception as e:
        print(f"Chat 錯誤: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    文字轉語音
    接收文字，返回音頻文件
    """
    try:
        if not tts_system:
            return jsonify({"error": "TTS 服務未初始化"}), 500
        
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "文字不能為空"}), 400
        
        # 過濾純標點符號（至少要有中文字、英文字或數字）
        import re
        if not re.search(r'[\u4e00-\u9fa5a-zA-Z0-9]', text):
            log_terminal(f"⚠️ 跳過純標點句子: {text}")
            return jsonify({"error": "句子必須包含有意義的文字"}), 400
        
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_path = temp_file.name
        
        # 合成語音 - 顯示詳細處理過程
        log_terminal("\n" + "="*60)
        log_terminal(f"📝 TTS 請求")
        log_terminal("="*60)
        log_terminal(f"輸入文字: {text}")
        
        # 檢測是否已經是台羅數字調格式（包含數字 0-9）
        is_tlpa = bool(re.search(r'[0-9]', text))
        
        if is_tlpa:
            # 已經是台羅格式，直接使用
            tlpa_text = text
            log_terminal(f"✓ 檢測到台羅數字調格式，直接使用")
        else:
            # 需要轉換為台羅
            tlpa_text = tts_system.text_processor.process_text(text, add_pauses=True, convert_chinese=True)
            log_terminal(f"原始文字: {text}")
            log_terminal(f"轉換台羅: {tlpa_text}")
        
        # 使用台羅文本進行合成（convert_chinese=False 因為已經是台羅）
        result = tts_system.synthesize(tlpa_text, output_path, convert_chinese=False)
        
        if result and os.path.exists(output_path):
            # 檢查檔案大小（太小可能是合成失敗）
            file_size = os.path.getsize(output_path)
            if file_size < 1000:  # 小於 1KB 可能有問題
                log_terminal(f"⚠️ 音檔過小 ({file_size} bytes)，可能合成失敗")
                log_terminal("="*60 + "\n")
                os.remove(output_path)
                return jsonify({"error": "語音合成失敗（音檔過小）"}), 500
            
            log_terminal(f"✓ 音檔已生成: {file_size} bytes")
            log_terminal("="*60 + "\n")
            
            # 讀取音檔並轉為 base64（以便在一個 JSON 回應中同時傳回台羅拼音與音檔）
            with open(output_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 清理臨時文件
            os.remove(output_path)
            
            # 返回 JSON 包含台羅拼音與音檔
            return jsonify({
                "success": True,
                "text": text,
                "tlpa": tlpa_text,
                "audio": audio_data,
                "file_size": file_size
            })
        else:
            log_terminal(f"✗ 語音合成失敗，未生成檔案")
            return jsonify({"error": "語音合成失敗"}), 500
            
    except Exception as e:
        import traceback
        log_terminal(f"TTS 錯誤: {e}")
        log_terminal(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"語音合成失敗: {str(e)}"
        }), 500

@app.route('/api/reset_session', methods=['POST'])
def reset_session():
    """重置會話"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]
        
        return jsonify({
            "success": True,
            "message": "會話已重置"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================================
# 主程式
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  整合語音對話系統 API")
    print("="*60)
    print("\n可用端點:")
    print("  - GET  /api/health        - 健康檢查")
    print("  - POST /api/stt           - 語音轉文字")
    print("  - POST /api/chat          - LLM 對話")
    print("  - POST /api/tts           - 文字轉語音")
    print("  - POST /api/reset_session - 重置會話")
    print("\n正在啟動服務...")
    print("="*60 + "\n")
    
    # 啟動 Flask 服務
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False  # 生產環境不要用 debug=True
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print("\n❌ 錯誤: Port 5000 已被佔用")
            print("嘗試用另一個端口啟動...")
            app.run(
                host='0.0.0.0',
                port=5001,
                debug=False
            )
        else:
            raise
