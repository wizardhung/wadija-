# Tacotron2

base on https://github.com/yfliao/taiwanese_tonal_tlpa_tacotron2

## Pre-requisites
NVIDIA GPU + CUDA cuDNN

## 安裝Anaconda虛擬環境
Anaconda官網
https://www.anaconda.com/products/individual

1. 安裝

`wget https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh --no-check-certificate`

`bash Anaconda3-2021.05-Linux-x86_64.sh` #conda init的地方選擇yes

`echo 'export PATH="~/anaconda3/bin:$PATH"' >> ~/.bashrc`

`source ~/.bashrc`

2. 建立虛擬環境

`conda create -n tacotron2 python=3.8 -y`

3. 進入虛擬環境

`conda deactivate`

`conda activate tacotron2`

## 準備訓練環境
1. 安裝tensorflow-gpu

`pip install tensorflow-gpu==2.4.1`

2. 安裝pytorch

cudatoolkit版本要一致

`conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch -y`

3. 安裝apex

`git clone https://github.com/NVIDIA/apex`

`cd apex`

`pip install -v --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" ./`

4. 安裝必要套件

`cd tacotron2`

`pip install -r requirements.txt`

## 訓練語音合成模型
單張GPU，可先測試GPU記憶體會不會爆

`python train.py --o='model' --l='logs'`

即時查看GPU使用情形

`watch -n 1 nvidia-smi`

多張GPU訓練，n_gpus調整GPU數量，後臺訓練

`nohup python -m multiproc train.py --o='model' --l='logs' --n_gpus='10' >& M1.log &`

即時查看終端輸出

`tail -f M1.log`

## 語音合成
在tacotron2資料夾內安裝waveglow

`git clone https://github.com/NVIDIA/waveglow.git`

下載官方的waveglow模型，waveglow_256channels_universal_v5.pt

https://drive.google.com/file/d/1rpK8CzAAirq9sWZhe9nlfvxMF1dRgFbF/view

也可以下載廖元甫老師訓練的waveglow模型，waveglow_main.pt

https://drive.google.com/file/d/1reQLND1vmhjF-2gF9Bx2AFy9zpgDPrJh/view?usp=sharing

將waveglow模型放到model/waveglow資料夾裡面

合成用的台羅拼音文本位置在txt/taiwanese.txt，可自行更改

編輯synthesizer.py，更改要合成語音的模型路徑

tacotron_model='tacotron2/model/checkpoint_XXXXXX'

執行synthesizer.py

`python synthesizer.py`

合成音檔位置在wavs


