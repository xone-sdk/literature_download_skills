# Literature Download Skills

文献检索、下载、整理与自动提取的一站式工具集，适配 Claude Code 环境。

## 快速开始

### 一键安装
```bash
bash <(curl -sL https://raw.githubusercontent.com/xone-sdk/literature_download_skills/main/install.sh)
```

### 手动安装
```bash
git clone git@github.com:xone-sdk/literature_download_skills.git
cp -r literature_download_skills/.claude/skills/cnki.skill/* ~/.claude/skills/
cp -r literature_download_skills/.claude/skills/ieee.skill/* ~/.claude/skills/
cp -r literature_download_skills/.claude/skills/springer.skill/* ~/.claude/skills/
cp literature_download_skills/.claude/skills/文献检索下载工作流.md ~/.claude/skills/
```

---

## 工具一览

| 文件 | 功能 | 类型 |
|------|------|------|
| `文献检索下载工作流.md` | Claude Code Skill：检索→下载→命名→分类→Zotero导入 | 工作流 |
| `cnki.skill/` | CNKI（知网）全套工具：搜索、下载、导出、期刊查询 | Skill套件 |
| `ieee.skill/` | IEEE Xplore 论文下载工具 | Skill套件 |
| `springer.skill/` | Springer Link 论文下载工具 | Skill套件 |
| `extracted.py` | 多模态文献批量提取：PDF / Word / HTML / 图片 → JSON | 脚本 |
| `install.sh` | 一键安装 Skill 到 `~/.claude/skills/` | 安装 |

---

## extracted.py — 文献批量提取

支持 PDF、DOCX、DOC、HTML、JPG/PNG 的全文提取，自动识别扫描件并启 OCR，同时提取文中图表和表格。

### 安装依赖
```bash
pip install pdfplumber pymupdf python-docx pywin32 beautifulsoup4 pytesseract pillow
# OCR 中文识别需额外安装 tesseract-ocr 及中文语言包
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
```

### 用法
```bash
python extracted.py <存放文件的路径>
```

**示例：**
```bash
python extracted.py ./ziliao
```

脚本会递归扫描指定目录下所有子文件夹中的文件，按格式自动选择提取器：

| 格式 | 提取方式 |
|------|----------|
| `.pdf` | pdfplumber 文本提取 + 扫描件OCR回退 + 图表/表格截图 |
| `.docx` | python-docx 段落提取 |
| `.doc` | win32com 调用 Word 应用提取 |
| `.html` | Beautiful Soup 内容解析 |
| `.jpg / .png` | pytesseract OCR 识别 |

### 输出

所有结果输出到 `./output/` 目录：

```
output/
├── extracted_data.json    ← 汇总JSON（含状态、统计、全文）
├── 论文A/                 ← 每篇论文的图表截图
│   ├── 第1页_图片1.png
│   ├── 第1页_表格1.png
│   └── ...
└── 论文B/
    └── ...
```

**JSON 结构：**
```json
{
  "status": "success",
  "generated_at": "2026-06-02T12:00:00",
  "input_dir": "<workspace>/ziliao",
  "summary": {
    "total_processed": 20,
    "success": 18,
    "failed": 1,
    "skipped": 1
  },
  "documents": [
    {
      "file_name": "论文A.pdf",
      "file_type": "pdf",
      "status": "success",
      "key_information": "全文内容..."
    },
    {
      "file_name": "论文B.pdf",
      "file_type": "pdf",
      "status": "failed",
      "error": "未提取到任何文字内容"
    }
  ]
}
```

- `status` 顶层：全部成功 `"success"`，有失败 `"partial"`
- 每篇文档 `status`：`"success"` / `"failed"` / `"skipped"`
- 失败和跳过的文档会附带 `error` 字段说明原因

---

## 文献检索下载工作流 Skill

在 Claude Code 中输入 `/文献检索下载工作流` 启动，覆盖完整流程：

1. **检索** — Google Scholar / Web 关键词搜索
2. **下载** — CNKI / IEEE / Elsevier / Springer / MDPI / Wiley
3. **命名** — `分区_数据库_标题_第一作者.pdf`
4. **分类** — 按模块归档到子目录
5. **导入** — Zotero MCP 自动导入 + 附件关联

---

## 环境依赖

| 依赖 | 用途 | 必需 |
|------|------|------|
| Claude Code | 运行 Skill | ✅ |
| Zotero + MCP HTTP 端点 (`127.0.0.1:23120`) | 文献管理 | ✅ |
| Chrome DevTools MCP | 浏览器自动化下载 | ✅ |
| Python 3.8+ | 批量提取 / Zotero 导入 | ✅ |
| Tesseract OCR + 中文包 | 扫描件 / 图片文字识别 | ❌ |

---

## 注意事项

- Zotero 需保持运行，MCP 端点 `http://127.0.0.1:23120/mcp` 可访问
- Windows 下 Python 默认 stdout 编码 cp1252，脚本已内置 UTF-8 修复
- ScienceDirect / Elsevier 部分论文需手动下载（反爬限制）
- 本仓库为通用工具框架，不含具体研究内容
