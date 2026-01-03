import logging
import os

# 啟用 CUDA 以使用 GPU
# 移除 CUDA 禁用設定，讓 PyTorch 使用 GPU
# os.environ['CUDA_VISIBLE_DEVICES'] = ''  # 註解掉此行以啟用 GPU
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import traceback
import sys
import base64
import tempfile

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from unidecode import unidecode

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 假設開發環境已安裝 subword-nmt，直接修改 BPE.__init__ 以提供 UTF-8 解碼後的 StringIO
def apply_encoding_patch():
    """Patch subword_nmt.apply_bpe.BPE.__init__ to feed UTF-8-decoded StringIO for codes.

    This simplified implementation assumes the dependency is present in the environment
    (as in your conda list). It keeps the robust binary->UTF-8 decode strategy but
    removes extra defensive try/except blocks for readability.
    """
    from subword_nmt.apply_bpe import BPE as original_bpe_class
    original_init = original_bpe_class.__init__

    def patched_init(self, codes, *args, **kwargs):
        import io as _io

        if isinstance(codes, str):
            with open(codes, 'rb') as _f:
                raw = _f.read()
            text = raw.decode('utf-8', errors='replace')
            codes = _io.StringIO(text)
        elif hasattr(codes, 'read'):
            if hasattr(codes, 'buffer'):
                raw = codes.buffer.read()
                text = raw.decode('utf-8', errors='replace')
                codes = _io.StringIO(text)
            else:
                pos = None
                try:
                    pos = codes.tell()
                except Exception:
                    pos = None
                content = codes.read()
                if isinstance(content, bytes):
                    text = content.decode('utf-8', errors='replace')
                    codes = _io.StringIO(text)
                elif isinstance(content, str):
                    codes = _io.StringIO(content)
                else:
                    if hasattr(codes, 'name') and isinstance(codes.name, str) and os.path.exists(codes.name):
                        with open(codes.name, 'rb') as _f:
                            raw = _f.read()
                        text = raw.decode('utf-8', errors='replace')
                        codes = _io.StringIO(text)
                try:
                    if pos is not None and hasattr(codes, 'seek'):
                        codes.seek(0)
                except Exception:
                    pass

        return original_init(self, codes, *args, **kwargs)

    original_bpe_class.__init__ = patched_init
    logging.info('Encoding Patch 成功應用：強制 subword_nmt 使用 UTF-8。')
# 服務啟動前即刻執行修補（若可用）
apply_encoding_patch()
# --- END 核心修正 ---


# --- Flask 應用程式設定 ---
app = Flask(__name__)
CORS(app) 
app.config['Chinese2TLPA'] = None
app.config['TTS_Synthesizer'] = None

# --- TTS 模型載入 ---
def load_tts_model():
    """載入 TTS Synthesizer 模型（嘗試 GPU，失敗則放棄）。
    
    注意：此函數在首次 TTS 請求時調用（延遲載入），
    以避免在 WSL 環境下 CUDA 庫問題導致啟動崩潰。
    """
    try:
        # 檢查 GPU 可用性（但不強制要求）
        import torch
        gpu_available = False
        try:
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                logging.info('檢測到 GPU: %s', torch.cuda.get_device_name(0))
                logging.info('CUDA 版本: %s', torch.version.cuda)
            else:
                logging.warning('未檢測到 GPU')
        except Exception as gpu_err:
            logging.warning('GPU 檢測失敗: %s', str(gpu_err)[:100])
        
        # 設定TTS模型路徑
        tts_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_dir = os.path.join(tts_repo_root, "taiwanese_tonal_tlpa_tacotron2_hsien1")
        
        logging.info('TTS 模型路徑尋找: %s', project_dir)
        
        if not os.path.exists(project_dir):
            logging.error("TTS 專案目錄不存在: '%s'。TTS 功能將不可用。", project_dir)
            return
        
        # 加入路徑以便匯入 han2tts
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
            logging.info('已加入 sys.path: %s', project_dir)
        
        tacotron_ckpt = os.path.join(project_dir, "tacotron2", "model", "checkpoint_100000")
        waveglow_ckpt = os.path.join(project_dir, "tacotron2", "model", "waveglow", "waveglow_main.pt")
        
        # 檢查模型檔案是否存在
        if not os.path.exists(tacotron_ckpt):
            logging.error("Tacotron 檢查點不存在: '%s'。TTS 功能將不可用。", tacotron_ckpt)
            return
        if not os.path.exists(waveglow_ckpt):
            logging.error("WaveGlow 檔案不存在: '%s'。TTS 功能將不可用。", waveglow_ckpt)
            return
        
        logging.info('Tacotron2 檔案確認存在 (%.1f MB)', os.path.getsize(tacotron_ckpt) / 1024 / 1024)
        logging.info('WaveGlow 檔案確認存在 (%.1f MB)', os.path.getsize(waveglow_ckpt) / 1024 / 1024)
        
        logging.info('嘗試匯入 han2tts 模組...')
        import han2tts
        logging.info('han2tts 模組匯入成功')
        
        logging.info('正在載入 TTS Synthesizer 模型（可能需要 30-60 秒）...')
        synthesizer = han2tts.Synthesizer(tacotron_ckpt, waveglow_ckpt)
        app.config['TTS_Synthesizer'] = synthesizer
        
        device = 'GPU' if gpu_available else 'CPU'
        logging.info('✓ TTS Synthesizer 載入成功（運行在 %s）。', device)
        
    except ImportError as e:
        logging.error('無法匯入 han2tts 模組: %s', str(e)[:200])
        logging.info('TTS 功能將使用音調合成備選方案')
    except RuntimeError as e:
        error_msg = str(e)
        if 'CUDA' in error_msg or 'cuda' in error_msg:
            logging.error('CUDA 運行時錯誤: %s', error_msg[:300])
            logging.info('WSL 環境 CUDA 庫不可用，TTS 將使用音調合成備選方案')
        else:
            logging.error('TTS 模型載入運行時錯誤: %s', error_msg[:300])
    except Exception as e:
        logging.error('TTS Synthesizer 載入失敗: %s', str(e)[:300])
        logging.error('完整錯誤:\n%s', traceback.format_exc()[:1000])

# --- 華語文字分詞輔助函式 ---
def _is_chinese_char(cp):
    """Checks whether CP is the codepoint of a CJK character."""
    if ((cp >= 0x4E00 and cp <= 0x9FFF) or
            (cp >= 0x3400 and cp <= 0x4DBF) or
            (cp >= 0x20000 and cp <= 0x2A6DF) or
            (cp >= 0x2A700 and cp <= 0x2B73F) or
            (cp >= 0x2B740 and cp <= 0x2B81F) or
            (cp >= 0x2B820 and cp <= 0x2CEAF) or
            (cp >= 0xF900 and cp <= 0xFAFF) or
            (cp >= 0x2F800 and cp <= 0x2FA1F)):
        return True
    return False

def tokenize_chinese_chars(text):
    """在 CJK 字元周圍加入空白，並對非 CJK 使用 unidecode。

    回傳值：經過空格分隔與 ASCII 化的字串。
    """
    output = []
    for char in text:
        cp = ord(char)
        if _is_chinese_char(cp):
            output.append(' ')
            output.append(char)
            output.append(' ')
        else:
            output.append(unidecode(char))
    return ''.join(output).replace('  ', ' ').strip()

# --- 模型載入 ---

def load_model():
    """禁用 Fairseq 模型載入，使用演示字典。
    
    Fairseq 在 CPU 環境下會導致程序崩潰 (memory corruption)。
    /translate 端點已修改為使用內置演示字典，無需載入 Fairseq。
    """
    logging.info('Fairseq 模型載入已禁用 (CPU環境不支持)')
    logging.info('使用演示字典模式處理翻譯請求。')
    # 保持 app.config['Chinese2TLPA'] = None（預設值）
    return

# --- 台語詞彙庫 ---

def get_taiwanese_dictionary():
    """返回華語到台語數字調的詞彙映射字典（包含常見詞彙和字符）。"""
    return {
        # 常用問候語
        '你好': 'li2 hoo2',
        '謝謝': 'tsieh3 tsieh3',
        '再見': 'tsai5 kinn7',
        '早安': 'tsua5 uan1',
        
        # 代詞
        '我': 'gua2',
        '你': 'li2',
        '他': 'thoo1',
        '她': 'tsia1',
        '我們': 'guan2',
        '你們': 'lian2',
        
        # 常用動詞
        '好': 'hoo2',
        '謝': 'tsieh3',
        '愛': 'tshua3',
        '錢': 'tshinn5',
        '去': 'tsi2',
        '來': 'lai5',
        '做': 'tsueh3',
        '有': 'uu2',
        '沒': 'bue5',
        '買': 'bue2',
        '食': 'tsiok4',
        '睡': 'tsue5',
        '起': 'khi2',
        '看': 'khuann3',
        
        # 形容詞和副詞
        '好': 'hoo2',
        '大': 'tsuai7',
        '小': 'tsiok4',
        '新': 'tsin1',
        '舊': 'kuu7',
        '真': 'tin1',
        '歡喜': 'huan1 hue2',
        
        # 地名
        '台灣': 'tsiann5 uan5',
        '台北': 'tsiann5 pak4',
        '台南': 'tsiann5 lam5',
        '高雄': 'ko5 hiong5',
        
        # 語言相關
        '台語': 'tsiann5 gio5',
        '華語': 'hua5 gio5',
        '日語': 'lit4 gio5',
        '英語': 'ing1 gio5',
        
        # 日期和時間
        '今天': 'kim1 tshinn5',
        '昨天': 'tsiok4 tshinn5',
        '明天': 'bing5 tshinn5',
        '今年': 'kim1 tsue5',
        '去年': 'tshi7 tsue5',
        
        # 其他常用詞
        '因為': 'in1 huai7',
        '所以': 'tsoo2 i2',
        '但是': 'punn7 tsiok4',
        '如果': 'ju2 hue2',
        '問題': 'bun7 tshue5',
        '解決': 'kue2 kuat4',
        '電腦': 'tsuann5 noo2',
        '手機': 'tshiu2 ki1',
        '電話': 'tsuann5 ue7',
        '矣': 'ah4',
        
        # 單字組合
        '日': 'lit4',
        '月': 'guat4',
        '年': 'tsue5',
        '天': 'tshinn5',
        '時': 'tshi5',
        '分': 'hun1',
    }

# --- 詞彙分割函數 ---

def segment_and_translate_demo(text, demo_dict):
    """使用貪心分詞法將輸入文本分割，並逐詞查詢字典進行翻譯。
    
    策略：
    1. 優先匹配最長的詞彙（貪心法）
    2. 如果沒有完全匹配，逐字查詢
    3. 未找到的字符保持原樣
    """
    result = []
    i = 0
    
    while i < len(text):
        found = False
        
        # 嘗試從最長的詞開始匹配（貪心法）
        for length in range(min(10, len(text) - i), 0, -1):
            substring = text[i:i+length]
            
            if substring in demo_dict:
                result.append(demo_dict[substring])
                i += length
                found = True
                break
        
        if not found:
            # 未找到任何匹配，直接使用該字符
            char = text[i]
            if char in demo_dict:
                result.append(demo_dict[char])
            else:
                # 保持原字符（不翻譯）
                result.append(char)
            i += 1
    
    return ' '.join(result)

# --- 台語羅馬字到數字調轉換 ---

def convert_tlpa_to_tonal_number(tlpa_text):
    """將 TLPA 羅馬字轉換為數字調表示。
    
    例如: 'li2 hoo2' -> 'li2 hoo2'（已經是數字調）
          'li hoo' -> 'li2 hoo2'（如果只有羅馬字則添加調號）
    """
    # 羅馬字到台語聲調的映射（簡化版本）
    # 台語有 8 個聲調（實際上 7 個，第 8 調較少用）
    # 這裡使用常見詞彙映射
    
    tonal_map = {
        '你': 'li2',
        '好': 'hoo2',
        '謝': 'tsieh3',
        '台': 'tsiann5',
        '灣': 'uan5',
        '語': 'gio5',
        '我': 'gua2',
        '愛': 'tshua3',
        '錢': 'tshinn5',
        '今': 'kim1',
        '天': 'tshinn1',
        '真': 'tin1',
        '歡': 'huan1',
        '喜': 'hue2',
        '因': 'in1',
        '為': 'hui7',
        '的': 'e5',
        '電': 'tsuann5',
        '腦': 'noo2',
        '問': 'bun7',
        '題': 'tshue5',
        '解': 'kue2',
        '決': 'kuat4',
        '矣': 'ah4'
    }
    
    # 如果輸入已包含數字，直接返回
    if any(char.isdigit() for char in tlpa_text):
        return tlpa_text
    
    # 否則嘗試用映射轉換
    words = tlpa_text.split()
    result = []
    
    for word in words:
        if word in tonal_map:
            result.append(tonal_map[word])
        else:
            # 如果沒有映射，假設是標準 TLPA，添加預設聲調 2（常見的聲調）
            result.append(word + '2' if word else word)
    
    return ' '.join(result)

# --- API 端點 ---

@app.route('/', methods=['GET'])
def index():
    """提供 index.html 前端頁面。"""
    index_path = os.path.join(os.path.dirname(__file__), 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return jsonify({"error": "index.html not found"}), 404

@app.route('/translate', methods=['POST'])
def translate_text():
    """接收華語文本，返回臺語羅馬字翻譯結果（包含數字調版本）。"""
    
    try:
        data = request.get_json()
        chinese_text = data.get('text')
        
        if not chinese_text:
            return jsonify({"error": "Missing 'text' parameter in request body."}), 400
        
        logging.info("華語翻譯請求: '%s'", chinese_text)
        
        # 嘗試使用真實模型
        model = app.config.get('Chinese2TLPA')
        
        if model is not None:
            try:
                # 有模型就用真實模型翻譯
                tokenized_text = tokenize_chinese_chars(chinese_text)
                tlpa_result = model.translate(tokenized_text)
                tonal_number_result = convert_tlpa_to_tonal_number(tlpa_result)
                logging.info("翻譯結果: '%s' -> '%s'", tlpa_result, tonal_number_result)
                
                return jsonify({
                    "original_text": chinese_text,
                    "tlpa_result": tlpa_result,
                    "tonal_number_result": tonal_number_result,
                    "mode": "real"
                })
            except Exception as e:
                logging.warning("真實模型翻譯失敗，使用示範: %s", str(e)[:100])
        
        # 模型未載入或失敗，使用演示字典進行分詞翻譯
        demo_dict = get_taiwanese_dictionary()
        tonal_number_result = segment_and_translate_demo(chinese_text, demo_dict)
        tlpa_result = tonal_number_result  # Demo 已是數字調
        logging.info("[DEMO] 翻譯結果: '%s'", tonal_number_result)
        
        return jsonify({
            "original_text": chinese_text,
            "tlpa_result": tonal_number_result,
            "tonal_number_result": tonal_number_result,
            "mode": "demo",
            "note": "演示模式 - 返回常用詞彙翻譯（數字調格式）"
        })
        
    except Exception as e:
        logging.error('翻譯處理時發生內部錯誤: %s', traceback.format_exc())
        return jsonify({"error": "Internal server error."}), 500

@app.route('/synthesize_tonal_number', methods=['POST'])
def synthesize_tonal_number():
    """接收台語數字調文本，返回生成的語音檔案（base64編碼）。
    
    使用真實的 Tacotron2 + WaveGlow TTS 模型（GPU加速）。
    """
    
    try:
        data = request.get_json()
        tonal_number_text = data.get('text')
        
        if not tonal_number_text:
            return jsonify({"error": "Missing 'text' parameter in request body."}), 400
        
        # 清理輸入文本（移除多餘空白）
        tonal_number_text = tonal_number_text.strip()
        
        logging.info("台語數字調合成請求: '%s'", tonal_number_text)
        
        # 檢查 TTS 模型是否已載入
        synthesizer = app.config.get('TTS_Synthesizer')
        
        if synthesizer is None:
            # 首次使用時載入模型
            logging.info("TTS 模型未載入，正在載入...")
            load_tts_model()
            synthesizer = app.config.get('TTS_Synthesizer')
        
        if synthesizer is None:
            # 模型載入失敗，使用備選方案
            logging.warning("TTS 模型載入失敗，使用聲調合成備選方案")
            wav_file = generate_tonal_audio(tonal_number_text)
            audio_base64 = base64.b64encode(wav_file).decode('utf-8')
            
            return jsonify({
                "tonal_number_text": tonal_number_text,
                "audio": audio_base64,
                "status": "success",
                "mode": "tonal_synthesis_fallback",
                "note": "備選方案：聲調合成（TTS模型不可用）"
            })
        
        try:
            # 使用真實 TTS 模型合成
            logging.info("使用真實 Tacotron2 + WaveGlow 模型合成（GPU）...")
            
            # 建立臨時輸出檔案
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_wav_path = tmp_file.name
            
            # 呼叫 TTS 合成
            output_path = synthesizer.tts(tonal_number_text, temp_wav_path)
            
            # 讀取生成的 WAV 檔案
            with open(output_path, 'rb') as f:
                wav_data = f.read()
            
            # 清理臨時檔案
            try:
                os.remove(output_path)
            except:
                pass
            
            logging.info(f'GPU TTS 合成成功，音訊大小: {len(wav_data)} bytes')
            
            # Base64 編碼
            audio_base64 = base64.b64encode(wav_data).decode('utf-8')
            
            return jsonify({
                "tonal_number_text": tonal_number_text,
                "audio": audio_base64,
                "status": "success",
                "mode": "real_tts_gpu",
                "note": "真實 Tacotron2 + WaveGlow GPU 加速語音合成"
            })
        
        except Exception as e:
            logging.error(f'GPU TTS 合成失敗: {str(e)[:200]}')
            logging.error(traceback.format_exc())
            
            # 回退到聲調合成
            logging.info("回退到聲調合成備選方案...")
            wav_file = generate_tonal_audio(tonal_number_text)
            audio_base64 = base64.b64encode(wav_file).decode('utf-8')
            
            return jsonify({
                "tonal_number_text": tonal_number_text,
                "audio": audio_base64,
                "status": "success",
                "mode": "tonal_synthesis_fallback",
                "note": "備選方案：聲調合成（TTS執行失敗）"
            })
    
    except Exception as e:
        logging.error('合成處理時發生內部錯誤:\n%s', traceback.format_exc())
        return jsonify({"error": "Internal server error."}), 500

def generate_tonal_audio(text):
    """根據台語數字調文本生成高質量模擬音訊。
    
    台語有 8 個聲調（實際上 7 個），根據調號生成不同的音頻模式：
    1. 高平調 - 高頻
    2. 上升調 - 從中低升至高
    3. 低降調 - 從高降至低
    4. 低停調 - 中低平調
    5. 上升調（長） - 從低升至高（較長）
    6. 高降調 - 從高降至中
    7. 低停調（長） - 低平調（較長）
    8. 高停調 - 高平調（停頓）
    """
    try:
        import struct
        import math
        
        sample_rate = 22050
        duration = 1  # 總時長 1 秒
        num_samples = sample_rate * duration
        
        audio_data = bytearray()
        amplitude = int(32767 * 0.4)
        
        # 解析台語數字調
        words = text.split()
        samples_per_word = num_samples // max(len(words), 1)
        
        total_sample_index = 0
        
        for word in words:
            # 提取最後一個數字作為聲調
            tone = None
            for char in reversed(word):
                if char.isdigit():
                    tone = int(char)
                    break
            
            if tone is None:
                tone = 2  # 預設為第 2 聲
            
            # 根據聲調生成音頻
            tone_samples = int(samples_per_word * 0.8)  # 80% 為音調部分
            pause_samples = int(samples_per_word * 0.2)  # 20% 為停頓
            
            # 聲調頻率曲線
            if tone == 1:  # 高平調
                freq_fn = lambda t: 350
            elif tone == 2:  # 上升調
                freq_fn = lambda t: 250 + (t / tone_samples) * 150
            elif tone == 3:  # 低降調
                freq_fn = lambda t: 400 - (t / tone_samples) * 150
            elif tone == 4:  # 低停調
                freq_fn = lambda t: 200
            elif tone == 5:  # 上升調（長）
                freq_fn = lambda t: 200 + (t / tone_samples) * 200
            elif tone == 6:  # 高降調
                freq_fn = lambda t: 380 - (t / tone_samples) * 100
            elif tone == 7:  # 低停調（長）
                freq_fn = lambda t: 180
            elif tone == 8:  # 高停調
                freq_fn = lambda t: 360
            else:
                freq_fn = lambda t: 300
            
            # 生成聲調樣本
            for i in range(tone_samples):
                frequency = freq_fn(i)
                # 添加淡入效果
                envelope = min(1.0, i / 100)  # 前 100 個樣本淡入
                sample = amplitude * envelope * math.sin(2 * math.pi * frequency * i / sample_rate)
                sample_int = int(sample) & 0xFFFF
                audio_data.extend(struct.pack('<h', sample_int - 65536 if sample_int > 32767 else sample_int))
                total_sample_index += 1
            
            # 生成停頓（靜音）
            for i in range(pause_samples):
                audio_data.extend(struct.pack('<h', 0))
                total_sample_index += 1
        
        # 確保達到預期的總樣本數
        while total_sample_index < num_samples:
            audio_data.extend(struct.pack('<h', 0))
            total_sample_index += 1
        
        # 限制音訊長度為預期值
        if len(audio_data) > num_samples * 2:
            audio_data = audio_data[:num_samples * 2]
        
        # 構建WAV檔案頭
        wav_header = bytearray()
        wav_header.extend(b'RIFF')
        
        file_size = 36 + len(audio_data)
        wav_header.extend(struct.pack('<I', file_size))
        wav_header.extend(b'WAVE')
        
        # fmt子塊
        wav_header.extend(b'fmt ')
        wav_header.extend(struct.pack('<I', 16))  # Subchunk1Size
        wav_header.extend(struct.pack('<H', 1))   # AudioFormat (PCM)
        wav_header.extend(struct.pack('<H', 1))   # NumChannels (mono)
        wav_header.extend(struct.pack('<I', sample_rate))
        wav_header.extend(struct.pack('<I', sample_rate * 2))  # ByteRate
        wav_header.extend(struct.pack('<H', 2))   # BlockAlign
        wav_header.extend(struct.pack('<H', 16))  # BitsPerSample
        
        # data子塊
        wav_header.extend(b'data')
        wav_header.extend(struct.pack('<I', len(audio_data)))
        
        wav_file = wav_header + audio_data
        
        logging.info('台語聲調音頻生成完成，大小: %d bytes', len(wav_file))
        
        return wav_file
    
    except Exception as e:
        logging.error('台語聲調音頻生成失敗: %s', str(e))
        raise

# 載入模型
if __name__ == '__main__':
    load_model()
    # TTS 模型延遲載入（首次請求時載入，避免啟動時崩潰）
    logging.info('應用啟動，TTS 模型將在首次請求時載入（GPU模式）...')
    # 讓 Flask 伺服器監聽所有介面的 5000 Port
    app.run(host='0.0.0.0', port=5000, debug=False)