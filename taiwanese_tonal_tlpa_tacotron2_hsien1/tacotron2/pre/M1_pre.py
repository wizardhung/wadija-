import os
import json
import re
import string
from zhon.hanzi import punctuation
import sox
from sklearn.model_selection import train_test_split

# files = 檔案名稱 (ex. M1_1-1.json)
# full_paths = path + files (ex. M1/json/M1_1-1.json)

path_json = '/nfs/TS-1635AX/Corpora/HAN/TAT-TTS/M1/M1_new_json_TTS'
path_wav = '/nfs/TS-1635AX/Corpora/HAN/TAT-TTS/M1/wav22050'

f1 = open('text.txt', 'w')
f2 = open('wav.txt', 'w')
f3 = open('WRONG.txt', 'w')
f4 = open('ori_text.txt', 'w')
f5 = open('ori_zh.txt', 'w')
f6 = open('ori_hl.txt', 'w')

chinese = re.compile('([\u4e00-\u9fa5]+)+?') #判斷是否含有中文
ABC = re.compile('([A-Z]+)+?') #判斷是否含有大寫英文字母
Zhuyin = re.compile('([\u3105-\u3129]+)+?') #判斷是否含有注音符號
#3105到3129→ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦㄧㄨㄩ

# half = string.punctuation
#半形→!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
half = '''"#$%&'()*+/<=>@[\]^_`{|}~''' #保留六種標點符號和dash→,.:;!?-

full = punctuation
#全形→＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､　、〃〈〉《》「」『』【】〔〕〖〗 〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏﹑﹔·！？｡。

special = '─―'

for files in sorted(os.listdir(path_json)):
    full_paths = os.path.join(path_json, files)
    with open(full_paths, 'r') as f:
        output = json.load(f)
        a = output['台羅數字調']
        b = output['中文']
        c = output['漢羅台文']
        f4.write(files.replace('.json', '.wav') + '|' + a + '\n')
        f5.write(files.replace('.json', '.wav') + '|' + b + '\n')
        f6.write(files.replace('.json', '.wav') + '|' + c + '\n')
        CH = chinese.findall(str(a)) #正則表達獲取中文
        A = ABC.findall(str(a)) #正則表達獲取大寫英文字母
        ZY = Zhuyin.findall(str(a)) #正則表達獲取注音符號
        if CH or A or ZY:
            f3.write(files.replace('.json', '') + '|' + a + '\n')
        else:
            for i in half:
                a = a.replace(i, ' ')
            for i in full:
                a = a.replace(i, ' ')
            for i in special:
                a = a.replace(i, ' ')
            a = ' '.join(filter(lambda x: x, a.split(' '))) #把重複的空格合併成一個空格
            a = a.replace('...', '.').replace(' .', '.').replace('. ', '.').replace(' ,', ',').replace(', ', ',')\
                .replace(' ;', ';').replace('; ', ';').replace(' :', ':').replace(': ', ':')\
                .replace(' ?', '?').replace('? ', '?').replace(' !', '!').replace('! ', '!') + '\n'
            a = a.replace('1\n', '1.\n').replace('2\n', '2.\n').replace('3\n', '3.\n').replace('4\n', '4.\n')\
                .replace('5\n', '5.\n').replace('7\n', '7.\n').replace('8\n', '8.\n').replace('9\n', '9.\n')\
                .replace('1,\n', '1.\n').replace('2,\n', '2.\n').replace('3,\n', '3.\n').replace('4,\n', '4.\n')\
                .replace('5,\n', '5.\n').replace('7,\n', '7.\n').replace('8,\n', '8.\n').replace('9,\n', '9.\n')\
                .replace('1:\n', '1.\n').replace('2:\n', '2.\n').replace('3:\n', '3.\n').replace('4:\n', '4.\n')\
                .replace('5:\n', '5.\n').replace('7:\n', '7.\n').replace('8:\n', '8.\n').replace('9:\n', '9.\n')\
                .replace('1;\n', '1.\n').replace('2;\n', '2.\n').replace('3;\n', '3.\n').replace('4;\n', '4.\n')\
                .replace('5;\n', '5.\n').replace('7;\n', '7.\n').replace('8;\n', '8.\n').replace('9;\n', '9.\n')
            a = a.replace('à', 'a').replace('á', 'a').replace('â', 'a').replace('ā', 'a').replace('a̍', 'a').replace('ă', 'a')\
                .replace('è', 'e').replace('é', 'e').replace('ê', 'e').replace('ē', 'e').replace('e̍', 'e').replace('ĕ', 'e')\
                .replace('ì', 'i').replace('í', 'i').replace('î', 'i').replace('ī', 'i').replace('i̍', 'i').replace('ĭ', 'i')\
                .replace('ò', 'o').replace('ó', 'o').replace('ô', 'o').replace('ō', 'o').replace('o̍', 'o').replace('ŏ', 'o')\
                .replace('ù', 'u').replace('ú', 'u').replace('û', 'u').replace('ū', 'u').replace('u̍', 'u').replace('ŭ', 'u')
            f1.write(files.replace('.json', '.wav') + '|' + a)
            f2.write(files.replace('.json', '.wav') + '\n')
        f.close()
f1.close()
f2.close()
f3.close()
f4.close()
f5.close()


# 過濾掉高於指定秒數的資料
second = '25'

list1 = []
with open('text.txt') as file:
    for line in file:
        line = line.strip()
        list1.append(line)
list2 = []
with open('wav.txt') as file:
    for line in file:
        line = line.strip()
        list2.append(line)
list = []
for i, item in enumerate(list2):
    audio = sox.file_info.num_samples(path_wav + '/' + list2[i])
    if audio <= 22050 * int(second): #sampling_rate=22050
        print(list2[i])
        list.append(path_wav + '/' + list1[i])
with open('filelist.txt', 'w') as filelist:
    for line in list:
        filelist.write(''.join(line) + '\n')
filelist.close()
print('prepare filelist DONE!')


#train:eval=9:1
H = []
with open('filelist.txt') as file:
    for line in file:
        line = line.strip()
        H.append(line)
train_H, test_H = train_test_split(H, test_size = 0.1, random_state = 0)
#生成訓練集和測試集
with open('train-filelist_under%ss.txt'%second, 'w') as a1, open('eval-filelist_under%ss.txt'%second, 'w') as a2:
    for line in train_H:
        a1.write(''.join(line) + '\n')
    for line in test_H:
        a2.write(''.join(line) + '\n')
print('train:eval=9:1 DONE!')
