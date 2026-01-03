#!/bin/bash

# 停止所有相關進程
pkill -9 -f integrated_voice_chat_api.py
pkill -9 less
sleep 2

echo "正在啟動 API 服務，輸出將寫入 /tmp/api_terminal.log"
echo "============================================================"

cd /home/wizard/專題tts
nohup conda run -n c2t python -u integrated_voice_chat_api.py > /home/wizard/專題tts/api_terminal.log 2>&1 &
PID=$!
echo "✓ 已啟動 (PID: $PID)"
echo "你可在另一個終端執行： tail -f /home/wizard/專題tts/api_terminal.log 來即時查看台羅拼音"
