#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系統配置檢查腳本
檢查所有必要的依賴和配置是否正確設置
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """打印標題"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_check(name, passed, message=""):
    """打印檢查結果"""
    status = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {name}")
    if message:
        print(f"  → {message}")

def check_python_version():
    """檢查 Python 版本"""
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 8
    print_check(
        "Python 版本",
        passed,
        f"當前版本: {version.major}.{version.minor}.{version.micro}" + 
        ("" if passed else " (需要 3.8+)")
    )
    return passed

def check_package(package_name, import_name=None):
    """檢查套件是否安裝"""
    if import_name is None:
        import_name = package_name.replace("-", "_")
    
    try:
        __import__(import_name)
        print_check(f"套件: {package_name}", True)
        return True
    except ImportError:
        print_check(f"套件: {package_name}", False, f"請執行: pip install {package_name}")
        return False

def check_file(filepath, description):
    """檢查文件是否存在"""
    exists = os.path.exists(filepath)
    print_check(
        description,
        exists,
        filepath if exists else f"找不到: {filepath}"
    )
    return exists

def check_env_variable(var_name, filepath=None):
    """檢查環境變數"""
    if filepath and os.path.exists(filepath):
        # 從文件讀取
        with open(filepath, 'r') as f:
            content = f.read()
            has_var = var_name in content
            print_check(
                f"環境變數: {var_name}",
                has_var,
                f"在 {filepath} 中" + ("找到" if has_var else "未找到")
            )
            return has_var
    else:
        # 從系統環境變數讀取
        has_var = var_name in os.environ
        print_check(
            f"環境變數: {var_name}",
            has_var,
            "已設置" if has_var else "未設置"
        )
        return has_var

def main():
    """主函數"""
    print_header("台語 AI 語音對話系統 - 配置檢查")
    
    BASE_DIR = Path(__file__).parent
    
    # 計分
    total_checks = 0
    passed_checks = 0
    
    # 1. 檢查 Python 版本
    print_header("1. Python 環境")
    total_checks += 1
    if check_python_version():
        passed_checks += 1
    
    # 2. 檢查必要套件
    print_header("2. Python 套件")
    packages = [
        ("flask", "flask"),
        ("flask-cors", "flask_cors"),
        ("google-cloud-speech", "google.cloud.speech"),
        ("openai", "openai"),
        ("python-dotenv", "dotenv"),
        ("numpy", "numpy"),
    ]
    
    for package_name, import_name in packages:
        total_checks += 1
        if check_package(package_name, import_name):
            passed_checks += 1
    
    # 3. 檢查文件結構
    print_header("3. 文件結構")
    files_to_check = [
        (BASE_DIR / "integrated_voice_chat_api.py", "後端 API 文件"),
        (BASE_DIR / "voice_chat_interface.html", "前端介面文件"),
        (BASE_DIR / "yating1" / "main_corrector.py", "STT 模組"),
        (BASE_DIR / "wadija_llm" / "main.py", "LLM 模組"),
        (BASE_DIR / "wadija_llm" / "rag_tools_v2.py", "RAG 工具"),
        (BASE_DIR / "wadija_llm" / "profile_db.json", "長輩資料檔"),
        (BASE_DIR / "taiwanese_tonal_tlpa_tacotron2_hsien1" / "taiwanese_tts_v2.py", "TTS 模組"),
    ]
    
    for filepath, description in files_to_check:
        total_checks += 1
        if check_file(str(filepath), description):
            passed_checks += 1
    
    # 4. 檢查配置
    print_header("4. 服務配置")
    
    # Google Cloud 認證
    google_creds = BASE_DIR / "yating1" / "newproject0901-470807-038aaaad5572.json"
    total_checks += 1
    if check_file(str(google_creds), "Google Cloud 認證金鑰"):
        passed_checks += 1
    
    # OpenAI API Key
    env_file = BASE_DIR / "wadija_llm" / ".env"
    total_checks += 1
    if check_env_variable("OPENAI_API_KEY", str(env_file)):
        passed_checks += 1
    
    # 5. 總結
    print_header("檢查完成")
    print(f"\n通過: {passed_checks}/{total_checks}")
    
    percentage = (passed_checks / total_checks) * 100
    
    if percentage == 100:
        print("\n✅ 所有檢查通過！系統已準備就緒。")
        print("   執行 ./start_voice_chat.sh 啟動系統")
    elif percentage >= 80:
        print("\n⚠️  大部分檢查通過，但有些問題需要處理。")
        print("   請檢查上方標記為 ✗ 的項目")
    else:
        print("\n❌ 有多個問題需要解決才能運行系統。")
        print("   請按照上方的提示進行配置")
    
    print("\n詳細說明請參考: VOICE_CHAT_README.md")
    print("快速開始請參考: QUICK_START_VOICE_CHAT.md\n")
    
    return 0 if percentage == 100 else 1

if __name__ == "__main__":
    sys.exit(main())
