# -*- coding: utf-8 -*-
"""
整合台語TTS系統
結合原有的 han2tts.py 和新的 taiwanese_text_processor.py
提供簡單易用的漢字轉語音介面
"""

import argparse
import os
import sys
import time
from typing import Dict, List, Optional

# 導入現有的 TTS 組件
try:
    from taiwanese_text_processor import (TaiwaneseTextProcessor,
                                          TaiwaneseTextToSpeech)
    TEXT_PROCESSOR_AVAILABLE = True
except ImportError:
    TEXT_PROCESSOR_AVAILABLE = False
    print("警告：無法導入 taiwanese_text_processor")

# 導入原有的 han2tts 組件
try:
    import han2tts
    HAN2TTS_AVAILABLE = True
except ImportError:
    HAN2TTS_AVAILABLE = False
    print("警告：無法導入 han2tts")


class IntegratedTaiwaneTTS:
    """整合的台語TTS系統"""
    
    def __init__(self, 
                 tacotron_model: str = None,
                 waveglow_model: str = None,
                 use_advanced_processor: bool = True):
        """
        初始化整合TTS系統
        
        Args:
            tacotron_model: Tacotron2模型路徑
            waveglow_model: WaveGlow模型路徑  
            use_advanced_processor: 是否使用進階文字處理器
        """
        
        # 設定預設模型路徑
        if tacotron_model is None:
            tacotron_model = r"D:\Users\User\Desktop\project\0912\taiwanese_tonal_tlpa_tacotron2\tacotron2\model\checkpoint_100000"
        if waveglow_model is None:
            waveglow_model = r"D:\Users\User\Desktop\project\0912\taiwanese_tonal_tlpa_tacotron2\tacotron2\model\waveglow\waveglow_main.pt"
            
        self.tacotron_model = tacotron_model
        self.waveglow_model = waveglow_model
        
        # 初始化文字處理器
        if TEXT_PROCESSOR_AVAILABLE and use_advanced_processor:
            print("使用進階文字處理器")
            self.text_processor = TaiwaneseTextProcessor(use_advanced_tools=True)
            self.use_advanced = True
        else:
            print("使用基本文字處理器")
            self.text_processor = None
            self.use_advanced = False
        
        # 初始化TTS合成器
        if HAN2TTS_AVAILABLE:
            self.synthesizer = han2tts.Synthesizer(tacotron_model, waveglow_model)
            print("TTS合成器初始化完成")
            print(f"Tacotron模型: {tacotron_model}")
            print(f"WaveGlow模型: {waveglow_model}")
        else:
            self.synthesizer = None
            print("警告：無法初始化TTS合成器")
    
    def text_to_speech(self, 
                      han_text: str, 
                      output_path: Optional[str] = None,
                      method: str = "auto") -> Optional[str]:
        """
        漢字文本轉語音
        
        Args:
            han_text: 輸入的漢字文本
            output_path: 輸出音檔路徑（None則自動生成）
            method: 轉換方法 ("auto", "advanced", "basic")
            
        Returns:
            輸出音檔的路徑
        """
        
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f"wavs/{timestamp}.wav"
            os.makedirs("wavs", exist_ok=True)
        
        print("\n=== 台語TTS轉換 ===")
        print(f"輸入文本: {han_text}")
        
        # 選擇轉換方法
        if method == "auto":
            method = "advanced" if self.use_advanced else "basic"
        
        if method == "advanced" and self.text_processor:
            tlpa_text = self._advanced_convert(han_text)
        else:
            tlpa_text = self._basic_convert(han_text)
        
        print(f"台羅拼音: {tlpa_text}")
        
        # 合成語音
        if self.synthesizer:
            try:
                self.synthesizer.tts(tlpa_text, output_path)
                print(f"音檔已生成: {output_path}")
                return output_path
            except Exception as e:
                print(f"語音合成失敗: {e}")
                return None
        else:
            print("無可用的語音合成器")
            return None
    
    def _advanced_convert(self, han_text: str) -> str:
        """使用進階文字處理器轉換"""
        try:
            return self.text_processor.preprocess_for_tacotron2(han_text)
        except Exception as e:
            print(f"進階轉換失敗，使用基本轉換: {e}")
            return self._basic_convert(han_text)
    
    def _basic_convert(self, han_text: str) -> str:
        """使用基本方法轉換（調用原有han2tts邏輯）"""
        if HAN2TTS_AVAILABLE:
            try:
                # 使用han2tts的轉換邏輯
                phrases = han2tts.load_phrases(han2tts.PHRASES_TSV)
                endings = han2tts.load_endings(han2tts.END_TSV) 
                dictionary = han2tts.build_dictionary()
                
                return han2tts.han2tlpa(han_text, dictionary, endings, phrases)
            except Exception as e:
                print(f"基本轉換失敗: {e}")
                return han_text  # fallback
        else:
            return han_text
    
    def batch_convert(self, texts: List[str], output_dir: str = "wavs") -> List[str]:
        """批量轉換多個文本"""
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, text in enumerate(texts):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"{timestamp}_{i:03d}.wav")
            result = self.text_to_speech(text, output_path)
            results.append(result)
            time.sleep(1)  # 避免檔名衝突
        
        return results
    
    def interactive_mode(self):
        """互動模式"""
        print("\n=== 台語TTS互動模式 ===")
        print("輸入漢字文本，系統會轉換成台語語音")
        print("輸入 'quit' 或 'exit' 離開")
        print("輸入 'help' 查看幫助")
        
        while True:
            try:
                user_input = input("\n請輸入文本: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '離開']:
                    print("再見！")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                elif not user_input:
                    continue
                else:
                    self.text_to_speech(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n再見！")
                break
            except Exception as e:
                print(f"處理錯誤: {e}")
    
    def _show_help(self):
        """顯示幫助資訊"""
        print("\n=== 幫助資訊 ===")
        print("功能說明:")
        print("- 輸入漢字文本，自動轉換為台語語音")
        print("- 支援數字調號和符號調號")
        print("- 支援進階語言處理（需要臺灣言語工具）")
        print("\n指令:")
        print("- 'help': 顯示此幫助")
        print("- 'quit' 或 'exit': 離開程式")
        print("\n範例文本:")
        print("- 大家好")
        print("- 我是台語機器人")
        print("- 今天天氣真好")


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='台語文字轉語音系統')
    parser.add_argument('text', nargs='*', help='要轉換的文本')
    parser.add_argument('--tacotron', help='Tacotron2模型路徑')
    parser.add_argument('--waveglow', help='WaveGlow模型路徑')
    parser.add_argument('--output', '-o', help='輸出音檔路徑')
    parser.add_argument('--method', choices=['auto', 'advanced', 'basic'], 
                       default='auto', help='轉換方法')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='啟動互動模式')
    parser.add_argument('--batch', help='批量處理文本檔案')
    
    args = parser.parse_args()
    
    # 初始化TTS系統
    tts = IntegratedTaiwaneTTS(
        tacotron_model=args.tacotron,
        waveglow_model=args.waveglow
    )
    
    if args.interactive:
        # 互動模式
        tts.interactive_mode()
    elif args.batch:
        # 批量處理
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                texts = [line.strip() for line in f if line.strip()]
            results = tts.batch_convert(texts)
            print(f"批量處理完成，共生成 {len(results)} 個音檔")
        except Exception as e:
            print(f"批量處理失敗: {e}")
    elif args.text:
        # 單一文本轉換
        han_text = ' '.join(args.text)
        tts.text_to_speech(han_text, args.output, args.method)
    else:
        # 沒有指定文本，顯示幫助並啟動互動模式
        parser.print_help()
        print("\n啟動互動模式...")
        tts.interactive_mode()


if __name__ == "__main__":
    main()