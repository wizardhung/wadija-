from gradio_client import Client, handle_file

client = Client("http://140.113.30.139:5003/")

# 上傳本地檔案
prompt_wav_upload = handle_file(r'D:\\Users\\User\\Desktop\\project\\0912\\taiwanese_tonal_tlpa_tacotron2\\child_nan.wav')
prompt_wav_record = handle_file(r'D:\\Users\\User\\Desktop\\project\\0912\\taiwanese_tonal_tlpa_tacotron2\\child_nan.wav')

result = client.predict(
    tts_text="ai3 tsu3-i3 an1-tsuan5--ooh4,a1-kong1 tshue1 tian7-hong1,li2 u7 oh8--khi2-lai5 a2-bo5",
    mode_checkbox_group="3s極速覆刻",
    prompt_text="lan2 tsit4 kai2 tio7 beh4 tui3 tam7-tsui2-ho5 khau2 jip8--khi3,lai5 tsau2-tshue7 pat4-li2 kap4 tam7-tsui2 tsi1-kan1 e5 siang1-siann5 koo3-su7",
    prompt_wav_upload=prompt_wav_upload,
    prompt_wav_record=prompt_wav_record,
    instruct_text="Speak very fast",
    seed=0,
    stream=False,
    speed=1,
    enable_translation=False,
    api_name="/generate_audio"
)

print(result)
