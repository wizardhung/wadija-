import pdfplumber
import json
import os

# ETL for Table-based PDF to JSON conversion
# =================設定區=================
# 請確認您的 PDF 檔名正確
INPUT_PDF_FILENAME = "700word.pdf" 

# 輸出的 JSON 檔名
OUTPUT_JSON_FILENAME = "common_words.json"
# =======================================

def convert_table_pdf_to_json(pdf_path, output_name):
    vocab_dict = {}
    print(f"正在讀取表格型 PDF: {pdf_path} ...")
    
    if not os.path.exists(pdf_path):
        print(f"❌ 錯誤：找不到檔案 '{pdf_path}'")
        return

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"檔案共有 {total_pages} 頁，開始解析表格...")

            for i, page in enumerate(pdf.pages):
                # ★★★ 關鍵修改：使用 extract_tables() ★★★
                # 這會回傳一個大列表，裡面每一項都是一個 row (列)
                tables = page.extract_tables()

                for table in tables:
                    for row in table:
                        # 檢查：這一列是否有足夠的欄位？(圖片中有7欄)
                        # 我們至少需要讀到第5欄(Index 4)
                        if not row or len(row) < 5:
                            continue

                        # 圖片結構分析：
                        # row[1] = 建議用字 (台語) -> 例如 "按呢"
                        # row[4] = 對應華語 (國語) -> 例如 "這樣、如此"
                        
                        taiwanese_word = row[1]
                        mandarin_content = row[4]

                        # 1. 過濾空值 (None)
                        if not taiwanese_word or not mandarin_content:
                            continue
                            
                        # 2. 清理換行符號 (\n) 和空白
                        taiwanese_word = taiwanese_word.replace('\n', '').strip()
                        mandarin_content = mandarin_content.replace('\n', '').strip()

                        # 3. 過濾標題列 (不要抓到 "建議用字" 這種字)
                        if "建議用字" in taiwanese_word or "對應華語" in mandarin_content:
                            continue

                        # 4. 處理「一對多」的情況
                        # 例如國語是："這樣、如此" (中間有頓號)
                        # 我們要把 "這樣" -> "按呢", "如此" -> "按呢" 都存進去
                        
                        # 把頓號替換成統一分隔符，有些表格可能會用逗號或斜線
                        separators = ['、', '，', ',', '/', '或']
                        for sep in separators:
                            mandarin_content = mandarin_content.replace(sep, '|')
                        
                        mandarin_list = mandarin_content.split('|')

                        for m_word in mandarin_list:
                            clean_m_word = m_word.strip()
                            if clean_m_word:
                                # 寫入字典： Key=國語, Value=台語
                                vocab_dict[clean_m_word] = taiwanese_word

                # 顯示進度
                if (i + 1) % 5 == 0:
                    print(f"已處理 {i + 1}/{total_pages} 頁...")

        # 儲存結果
        output_dir = "dictionaries"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_path = os.path.join(output_dir, output_name)
        
        final_data = {
            "description": "教育部700字表匯入 (表格模式)",
            "vocabulary": vocab_dict
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 表格轉檔完成！")
        print(f"共擷取了 {len(vocab_dict)} 個對應詞彙。")
        print(f"範例資料： '這樣' -> '{vocab_dict.get('這樣', '未找到')}'")
        print(f"範例資料： '舅媽' -> '{vocab_dict.get('舅媽', '未找到')}'")

    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    convert_table_pdf_to_json(INPUT_PDF_FILENAME, OUTPUT_JSON_FILENAME)