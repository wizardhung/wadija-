#!/bin/bash

# ============================================================================
# 台語 AI 語音對話系統 - 啟動腳本
# ============================================================================

echo "=================================="
echo "  台語 AI 語音對話系統"
echo "=================================="
echo ""

# 檢查 conda 環境
if ! command -v conda &> /dev/null; then
    echo "❌ 錯誤: 找不到 conda"
    echo "請先安裝 Anaconda 或 Miniconda"
    exit 1
fi

# 啟動 conda 環境
echo "🔧 正在啟動 conda 環境 (c2t)..."
eval "$(conda shell.bash hook)"
conda activate c2t

if [ $? -ne 0 ]; then
    echo "❌ 錯誤: 無法啟動 c2t 環境"
    echo "請先創建環境: conda create -n c2t python=3.8"
    exit 1
fi

echo "✓ conda 環境已啟動"
echo ""

# 檢查必要的套件
echo "🔍 檢查必要套件..."

REQUIRED_PACKAGES=(
    "flask"
    "flask-cors"
    "google-cloud-speech"
    "openai"
    "python-dotenv"
)

MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    python -c "import ${package//-/_}" 2>/dev/null
    if [ $? -ne 0 ]; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo "⚠️  發現缺少的套件: ${MISSING_PACKAGES[*]}"
    echo "正在安裝..."
    pip install "${MISSING_PACKAGES[@]}"
fi

echo "✓ 所有套件已就緒"
echo ""

# 檢查環境變數
echo "🔍 檢查配置..."

if [ ! -f "wadija_llm/.env" ]; then
    echo "⚠️  警告: 找不到 wadija_llm/.env 文件"
    echo "請確保已設置 OPENAI_API_KEY"
fi

if [ ! -f "yating1/newproject0901-470807-038aaaad5572.json" ]; then
    echo "⚠️  警告: 找不到 Google Cloud 認證金鑰"
    echo "STT 功能可能無法使用"
fi

echo ""

# 啟動後端服務
echo "🚀 啟動後端 API 服務..."
echo "   服務地址: http://localhost:5000"
echo ""
echo "=================================="
echo "  按 Ctrl+C 停止服務"
echo "=================================="
echo ""

# 運行 Flask 應用
cd /home/wizard/專題tts
python -u integrated_voice_chat_api.py
