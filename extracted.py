import os
import sys
import io
import json
import pdfplumber
import fitz  # PyMuPDF
import docx
import win32com.client
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
from datetime import datetime

# 屏蔽底层排版报错
fitz.TOOLS.mupdf_display_errors(False)

# ================= 配置区 =================
# 用法: python extracted.py [存放文件的路径]
# 示例: python extracted.py ./04_ziliao
OUTPUT_DIR = './output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'extracted_data.json')
# ==========================================

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def merge_rects(rects, tolerance=40):
    """保留的防碎图机制：将距离相近的图片框智能合并成一个大框"""
    merged = list(rects)
    changed = True
    while changed:
        changed = False
        new_merged = []
        while merged:
            current = merged.pop(0)
            merged_with_something = False
            for i, m in enumerate(new_merged):
                m_exp = fitz.Rect(m.x0 - tolerance, m.y0 - tolerance, m.x1 + tolerance, m.y1 + tolerance)
                if current.intersects(m_exp):
                    new_merged[i] = m | current
                    changed = True
                    merged_with_something = True
                    break
            if not merged_with_something:
                new_merged.append(current)
        merged = new_merged
    return merged

def extract_all_figures_and_tables(file_path, out_dir):
    """推土机模式：提取所有图片和所有表格，不加任何过滤条件"""
    try:
        doc = fitz.open(file_path)
        with pdfplumber.open(file_path) as pdf:
            for page_num in range(len(doc)):
                fitz_page = doc.load_page(page_num)
                plumber_page = pdf.pages[page_num]
                
                # ================= 1. 提取本页所有图片 =================
                img_info_list = fitz_page.get_image_info()
                # 仅过滤极其微小的噪点（宽或高小于 20 像素的细线或纯色块），其余全留
                raw_img_rects = [fitz.Rect(img["bbox"]) for img in img_info_list if fitz.Rect(img["bbox"]).width > 20 and fitz.Rect(img["bbox"]).height > 20]
                
                if raw_img_rects:
                    # 拼合碎图
                    merged_img_rects = merge_rects(raw_img_rects, tolerance=40)
                    
                    for img_idx, target_rect in enumerate(merged_img_rects):
                        # 加点内边距
                        pad = 10
                        target_rect = fitz.Rect(target_rect.x0 - pad, target_rect.y0 - pad, 
                                                target_rect.x1 + pad, target_rect.y1 + pad)
                        target_rect = target_rect.intersect(fitz_page.rect)
                        
                        # 高清截图
                        mat = fitz.Matrix(4.0, 4.0)
                        pix = fitz_page.get_pixmap(matrix=mat, clip=target_rect)
                        img_path = os.path.join(out_dir, f"第{page_num+1}页_图片{img_idx+1}.png")
                        pix.save(img_path)

                # ================= 2. 提取本页所有表格 =================
                tables = plumber_page.find_tables()
                for table_idx, table in enumerate(tables):
                    bbox = table.bbox 
                    cropped_page = plumber_page.crop(bbox)
                    img_obj = cropped_page.to_image(resolution=300)
                    tab_path = os.path.join(out_dir, f"第{page_num+1}页_表格{table_idx+1}.png")
                    img_obj.original.save(tab_path, format="PNG")

        doc.close()
    except Exception as e:
        print(f"   ⚠️ 提取图表失败: {e}")

# --- 各种格式的全量解析函数 ---

def parse_pdf(file_path, base_filename):
    text_content = []
    
    paper_out_dir = os.path.join(OUTPUT_DIR, base_filename)
    ensure_dir(paper_out_dir)
    
    # 提取所有图表
    extract_all_figures_and_tables(file_path, paper_out_dir)
    
    try:
        is_scanned = True
        total_text_length = 0
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    total_text_length += len(page_text.strip())
                    # 取消了关键字过滤，直接存入每一行文字
                    text_content.append(page_text.strip())
                            
        # 如果是纯图片构成的 PDF，启动 OCR 硬扫
        if total_text_length > 50:
            is_scanned = False
            
        if is_scanned:
            print(f"   ⚠️ 检测到纯图片 PDF，正在启动 OCR 逐页全量扫描 (请耐心等待)...")
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                zoom = 2.0 
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                extracted_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                text_content.append(extracted_text.strip())
            doc.close()
            
    except Exception as e:
        print(f"❌ 读取 PDF 出错 {file_path}: {e}")
    return "\n".join(text_content)

def parse_docx(file_path):
    text_content = []
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                text_content.append(para.text.strip())
    except Exception as e:
        print(f"❌ 读取 Word 出错 {file_path}: {e}")
    return "\n".join(text_content)

def parse_old_doc(file_path):
    text_content = []
    abs_path = os.path.abspath(file_path)
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(abs_path)
        
        for i in range(1, doc.Paragraphs.Count + 1):
            text = doc.Paragraphs(i).Range.Text.strip()
            if text:
                text_content.append(text)
                
        doc.Close()
        word.Quit()
    except Exception as e:
        print(f"❌ 读取老版 Word (.doc) 出错 {file_path}: {e}")
        try:
            word.Quit()
        except:
            pass
    return "\n".join(text_content)

def parse_html(file_path):
    text_content = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: 
            soup = BeautifulSoup(f, 'lxml')
            paragraphs = soup.find_all(['p', 'div', 'span', 'article', 'section']) 
            for para in paragraphs:
                text = para.get_text(strip=True)
                if text:
                    text_content.append(text)
    except Exception as e:
        print(f"❌ 读取 HTML 出错 {file_path}: {e}")
    return "\n".join(text_content)

def parse_jpg(file_path):
    text_content = []
    try:
        image = Image.open(file_path)
        extracted_text = pytesseract.image_to_string(image, lang='chi_sim+eng') 
        text_content.append(extracted_text.strip())
    except Exception as e:
        print(f"❌ 读取 JPG 出错 {file_path}: {e}")
    return "\n".join(text_content)

# --- 主控制流 ---
def main(input_dir=None):
    # 修复Windows cp1252编码导致中文print崩溃的问题
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (AttributeError, OSError):
        pass

    if input_dir is None:
        if len(sys.argv) > 1:
            input_dir = sys.argv[1]
        else:
            print("用法: python extracted.py <存放文件的路径>")
            print("示例: python extracted.py ./04_ziliao")
            sys.exit(1)

    ensure_dir(input_dir)
    ensure_dir(OUTPUT_DIR)

    results = []
    success_count = 0
    fail_count = 0
    skip_count = 0
    print("🚀 开始多模态全量无过滤提取...")

    # 递归遍历所有子目录
    all_files = []
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            all_files.append((root, filename))

    for root, filename in all_files:
        file_path = os.path.join(root, filename)

        ext = os.path.splitext(filename)[1].lower().strip()
        base_filename = os.path.splitext(filename)[0]
        extracted_text = ""

        # 显示相对路径
        rel_path = os.path.relpath(file_path, input_dir)
        print(f"正在处理: {rel_path}")

        doc_data = {
            "file_name": filename,
            "file_type": ext.replace('.', ''),
        }

        if ext == '.pdf':
            extracted_text = parse_pdf(file_path, base_filename)
        elif ext == '.docx':
            extracted_text = parse_docx(file_path)
        elif ext == '.doc':
            extracted_text = parse_old_doc(file_path)
        elif ext in ['.html', '.htm', '.xhtml', '.shtml']:
            extracted_text = parse_html(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
            extracted_text = parse_jpg(file_path)
        else:
            print(f"   ⚠️ 跳过不支持的格式 ({ext}): {filename}")
            doc_data["status"] = "skipped"
            doc_data["error"] = f"不支持的格式: {ext}"
            results.append(doc_data)
            skip_count += 1
            continue

        if extracted_text:
            doc_data["status"] = "success"
            doc_data["key_information"] = extracted_text
            results.append(doc_data)
            success_count += 1
            print(f"   ✅ 全文及全量图片/表格提取完毕！")
        else:
            doc_data["status"] = "failed"
            doc_data["error"] = "未提取到任何文字内容"
            results.append(doc_data)
            fail_count += 1
            print("   ❌ 未提取到任何文字内容。")

    # 汇总JSON
    total = success_count + fail_count + skip_count
    summary_data = {
        "status": "success" if fail_count == 0 else "partial",
        "generated_at": datetime.now().isoformat(),
        "input_dir": os.path.abspath(input_dir),
        "summary": {
            "total_processed": total,
            "success": success_count,
            "failed": fail_count,
            "skipped": skip_count
        },
        "documents": results
    }

    if results:
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=4)
            print("\n🎉 处理完成！")
            print(f"   ✅ 成功: {success_count} 篇")
            if fail_count > 0:
                print(f"   ❌ 失败: {fail_count} 篇")
            if skip_count > 0:
                print(f"   ⚠️ 跳过: {skip_count} 篇")
            print(f"📁 汇总数据已保存至: {OUTPUT_FILE}")
        except Exception as e:
            print(f"❌ 保存 JSON 失败: {e}")
    else:
        print("\n⚠️ 扫描完毕，未提取到任何数据。")

    return summary_data

if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else None
    main(input_dir)