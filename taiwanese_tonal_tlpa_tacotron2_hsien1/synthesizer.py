import warnings

warnings.filterwarnings("ignore")

try:
    from tensorflow.python.util import deprecation
    deprecation._PRINT_DEPRECATION_WARNINGS = False
except Exception:
    deprecation = None

class HParams:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def parse(self, hparams_string):
        if not hparams_string:
            return self
        for pair in hparams_string.split(','):
            pair = pair.strip()
            if not pair:
                continue
            name, value = pair.split('=')
            name, value = name.strip(), value.strip()
            if hasattr(self, name):
                cur = getattr(self, name)
                if isinstance(cur, bool):
                    value = value.lower() in ('true', '1', 'yes', 'y')
                elif isinstance(cur, int):
                    value = int(value)
                elif isinstance(cur, float):
                    value = float(value)
            setattr(self, name, value)
        return self

# tf.get_logger().setLevel('INFO')

import logging
import os

os.environ['KMP_WARNINGS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.disable(logging.WARNING)

import argparse
import io
import json
import sys
import time
from os.path import join
from pathlib import Path

import numpy as np
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

from scipy.io.wavfile import write

project_name = 'tacotron2'
sys.path.append(project_name)
sys.path.append(join(project_name, 'waveglow/'))

from denoiser import Denoiser
from glow import WaveGlow
from hparams import create_hparams
from model import Tacotron2
from text import text_to_sequence

# import sox

# setting
torch.set_grad_enabled(False)

tacotron_model = r"D:\Users\User\Desktop\project\0912\taiwanese_tonal_tlpa_tacotron2\tacotron2\model\checkpoint_100000"
waveglow_model = r"D:\Users\User\Desktop\project\0912\taiwanese_tonal_tlpa_tacotron2\tacotron2\model\waveglow\waveglow_main.pt"

print('Use ' + tacotron_model)

class Synthesizer:

    def load(self, tacotron_model, waveglow_model):
        # setting
        self.project_name = 'tacotron2'
        sys.path.append(self.project_name)
        sys.path.append(join(self.project_name, 'waveglow/'))

        # initialize Tacotron2
        self.hparams = create_hparams()
        self.hparams.sampling_rate = 22050
        self.hparams.max_decoder_steps = 3000
        self.hparams.fp16_run = False


        self.tacotron = Tacotron2(self.hparams)
        self.tacotron.load_state_dict(torch.load(tacotron_model, map_location=device)['state_dict'])
        _ = self.tacotron.to(device).eval()

        self.waveglow = torch.load(waveglow_model, map_location=device)['model']

        # 有些版本沒有 remove_weightnorm；能用就用，不能用就嘗試逐層移除或直接略過
        try:
            from glow import remove_weightnorm as _rm
            self.waveglow = _rm(self.waveglow)
        except Exception:
            import torch.nn.utils as _nnutils
            for module in self.waveglow.modules():
                try:
                    _nnutils.remove_weight_norm(module)
                except Exception:
                    pass  # 沒有套 weight_norm 的層會丟例外，直接略過即可

        _ = self.waveglow.to(device).eval()

        # 有些版本可能沒有 convinv，避免屬性不存在
        for k in getattr(self.waveglow, 'convinv', []):
            k.float()

        self.denoiser = Denoiser(self.waveglow, device=device)



    def __init__(self, tacotron, waveglow, text):
        self.tacotron = tacotron
        self.waveglow = waveglow
        self.text = text

    def read_text(self):
        with open(self.text, 'r') as rf:
            return rf.readlines()

    def run(self):
        self.load(self.tacotron, self.waveglow)
        for i, text in enumerate(self.read_text(),start=1):
            self.synthesize(text, i)

    def synthesize(self, text, i):

        sequence = np.array(text_to_sequence(text, ['basic_cleaners']))[None, :]
        sequence = torch.from_numpy(sequence).to(device=device, dtype=torch.int64)


        with torch.no_grad():
            _, mel, _, _ = self.tacotron.inference(sequence)
            audio = self.waveglow.infer(mel, sigma=0.666)
            audio = self.denoiser(audio, strength=0.01)[:, 0]
            audio = audio[0].data.cpu().numpy()
            audio *= 32767 / max(0.01, np.max(np.abs(audio)))

        self.out = io.BytesIO()
        write('wavs/%02d.wav' %i, self.hparams.sampling_rate, audio.astype(np.int16))
        print('%02d.wav' %i)

        return self.out.getvalue()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--tacotron', default=tacotron_model, help='Full path to tacotron model')
    parser.add_argument('--waveglow', default=waveglow_model, help='Full path to waveglow model')
    parser.add_argument('--port', type=int, default=80)
    parser.add_argument('--hparams', default='tacotron2/hparams.py',
                        help='Hyperparameter overrides as a comma-separated list of name=value pairs')
    args = parser.parse_args()

    os.environ['KMP_WARNINGS'] = '0'
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.makedirs('wavs', exist_ok=True)  

    synthesizer = Synthesizer(
        args.tacotron,
        args.waveglow,
        r"D:\Users\User\Desktop\project\0912\taiwanese_tonal_tlpa_tacotron2\txt\taiwanese.txt"
    )
    synthesizer.run()
