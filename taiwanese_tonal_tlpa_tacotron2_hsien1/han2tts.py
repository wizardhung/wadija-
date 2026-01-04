# han2tts.py
# -*- coding: utf-8 -*-
import io
import logging
import os
import sys
import time
import warnings
from typing import List

warnings.filterwarnings("ignore")
os.environ['KMP_WARNINGS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.disable(logging.WARNING)

# ========= 專案路徑 =========
# Use repository-relative defaults and allow overrides via environment variables.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(REPO_ROOT, "tacotron2")
DEFAULT_MODEL_DIR = os.path.join(PROJECT_DIR, "model")
# Allow user to override via environment variables if they want to point to external checkpoints
TACOTRON_CKPT = os.environ.get("TACOTRON_CKPT", os.path.join(DEFAULT_MODEL_DIR, "checkpoint_100000"))
WAVEGLOW_CKPT = os.environ.get("WAVEGLOW_CKPT", os.path.join(DEFAULT_MODEL_DIR, "waveglow", "waveglow_main.pt"))
OUT_DIR = os.environ.get("OUT_DIR", os.path.join(REPO_ROOT, "wavs"))

# Ensure project paths are on sys.path so imports work when running the script
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
waveglow_path = os.path.join(PROJECT_DIR, "waveglow")
if waveglow_path not in sys.path:
    sys.path.insert(0, waveglow_path)
# ========= TTS =========
import numpy as np
import torch
from tacotron2.waveglow.denoiser import Denoiser
from tacotron2.waveglow.glow import WaveGlow
from tacotron2.hparams import create_hparams
from tacotron2.model import Tacotron2
from scipy.io.wavfile import write as wavwrite
from tacotron2.text import text_to_sequence

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_grad_enabled(False)

# —— TTS ——（保持原樣）
class Synthesizer:
    def __init__(self, tacotron_ckpt: str, waveglow_ckpt: str):
        self.hparams = create_hparams()
        self.hparams.sampling_rate = 22050
        self.hparams.max_decoder_steps = 3000
        self.hparams.fp16_run = False

        # Resolve checkpoint paths robustly: expand, abspath, realpath; if missing, search repo for basename
        def _resolve_ckpt(path):
            # Normalize backslashes to forward slashes to handle Windows/WSL UNC paths
            orig = path
            if isinstance(path, str):
                path_norm = path.replace('\\', '/').replace('\\\\', '/')
            else:
                path_norm = path

            # If the normalized path contains a POSIX /home/ segment (WSL UNC), prefer that substring
            if isinstance(path_norm, str) and '/home/' in path_norm:
                idx = path_norm.find('/home/')
                path_norm = path_norm[idx:]

            p = os.path.expanduser(path_norm)
            # If still not absolute, interpret relative to repo root
            if not os.path.isabs(p):
                p = os.path.join(REPO_ROOT, p)
            p = os.path.realpath(p)
            if os.path.exists(p):
                return p

            # search repo for matching basename as a fallback
            basename = os.path.basename(orig)
            for root, dirs, files in os.walk(REPO_ROOT):
                if basename in files:
                    candidate = os.path.join(root, basename)
                    return os.path.realpath(candidate)

            return p

        tacotron_ckpt_path = _resolve_ckpt(tacotron_ckpt)
        if not os.path.exists(tacotron_ckpt_path):
            raise FileNotFoundError(f"Tacotron checkpoint not found: tried {tacotron_ckpt_path}\n" \
                                    f"Set TACOTRON_CKPT env or place the file under {os.path.join(REPO_ROOT, 'tacotron2','model')}")

        self.tacotron = Tacotron2(self.hparams)
        try:
            self.tacotron.load_state_dict(torch.load(tacotron_ckpt_path, map_location=device)['state_dict'])
        except Exception as e:
            raise RuntimeError(f"Failed loading tacotron checkpoint from {tacotron_ckpt_path}: {e}")
        self.tacotron = self.tacotron.to(device).eval()

        waveglow_ckpt_path = _resolve_ckpt(waveglow_ckpt)
        if not os.path.exists(waveglow_ckpt_path):
            raise FileNotFoundError(f"WaveGlow checkpoint not found: tried {waveglow_ckpt_path}\n" \
                                    f"Set WAVEGLOW_CKPT env or place the file under {os.path.join(REPO_ROOT, 'tacotron2','model','waveglow')}")
        try:
            self.waveglow: WaveGlow = torch.load(waveglow_ckpt_path, map_location=device)['model']
        except Exception as e:
            raise RuntimeError(f"Failed loading WaveGlow checkpoint from {waveglow_ckpt_path}: {e}")
        try:
            from glow import remove_weightnorm as _rm
            self.waveglow = _rm(self.waveglow)
        except Exception:
            import torch.nn.utils as _nnutils
            for m in self.waveglow.modules():
                try: _nnutils.remove_weight_norm(m)
                except Exception: pass
        self.waveglow = self.waveglow.to(device).eval()
        for k in getattr(self.waveglow, 'convinv', []):
            try: k.float()
            except Exception: pass
        self.denoiser = Denoiser(self.waveglow, device=device)

    def tts(self, text: str, out_path: str) -> str:
        import gc
        seq = np.array(text_to_sequence(text, ['basic_cleaners']))[None, :]
        seq = torch.from_numpy(seq).to(device=device, dtype=torch.int64)
        # Ensure sequence length is at least encoder kernel size to avoid conv kernel > input errors
        try:
            min_len = int(self.hparams.encoder_kernel_size)
        except Exception:
            min_len = 5
        cur_len = seq.size(1)
        if cur_len < min_len:
            pad_amount = min_len - cur_len
            pad_tensor = torch.zeros((1, pad_amount), dtype=seq.dtype, device=seq.device)
            seq = torch.cat([seq, pad_tensor], dim=1)
        
        with torch.no_grad():
            try:
                _, mel, _, _ = self.tacotron.inference(seq)
                # 確保 mel 幀數足夠，避免 WaveGlow/降噪在極短音訊時出現張量拼接錯誤
                # WaveGlow 產生音訊長度約為 mel_frames * 256；為了讓 STFT(1024)正常，至少需要 ~4 幀
                min_mel_frames = 4
                if mel.size(-1) < min_mel_frames:
                    pad_frames = min_mel_frames - int(mel.size(-1))
                    last = mel[:, :, -1:].repeat(1, 1, pad_frames)
                    mel = torch.cat([mel, last], dim=-1)
                # 另外盡量讓時間軸對齊到 8 的倍數（對 n_group=8 較穩定），不足則複製最後一幀補齊
                n_group = 8
                rem = int(mel.size(-1)) % n_group
                if rem != 0:
                    add = n_group - rem
                    last = mel[:, :, -1:].repeat(1, 1, add)
                    mel = torch.cat([mel, last], dim=-1)
                gc.collect()  # Clear memory between steps
                
                audio = self.waveglow.infer(mel, sigma=0.666)
                gc.collect()
                
                # 對極短音訊，降噪可能失敗；失敗則退回未降噪音訊
                try:
                    audio = self.denoiser(audio, strength=0.01)[:, 0]
                except Exception:
                    audio = audio[:, 0]
                audio = audio[0].data.cpu().numpy()
                gc.collect()
                
                audio *= 32767 / max(0.01, float(np.max(np.abs(audio))))
            finally:
                # Ensure cleanup even if error occurs
                try:
                    del seq, mel
                except:
                    pass
                gc.collect()
        
        wavwrite(out_path, self.hparams.sampling_rate, audio.astype(np.int16))
        return out_path

# —— 輔助：產生輸出檔名（保留原寫法） ——
def next_out_path() -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUT_DIR, f"{stamp}.wav")

def main():
    if len(sys.argv) < 2:
        print("用法：python han2tts.py <要唸的文字>", file=sys.stderr)
        sys.exit(2)

    # 直接把 CLI 的文字當成要合成的內容（不再做 Han→TLPA）
    input_text = " ".join(sys.argv[1:]).strip()
    if not input_text:
        print("錯誤：輸入文字為空", file=sys.stderr)
        sys.exit(2)

    synth = Synthesizer(TACOTRON_CKPT, WAVEGLOW_CKPT)
    out_path = next_out_path()
    synth.tts(input_text, out_path)

    print(f"[TEXT] {input_text}")
    print(f"[WAV]  {out_path}")

if __name__ == "__main__":
    main()
