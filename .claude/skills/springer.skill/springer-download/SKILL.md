---
name: springer-download
description: Download paper PDF from Springer Link via library proxy. Uses direct content/pdf DOI link. Use when user wants to download a Springer paper.
argument-hint: "[Springer paper URL or DOI]"
---

# Springer Link Paper Download

通过图书馆IP认证直接下载Springer论文PDF，无需登录。

## Prerequisites

- 通过学校图书馆代理访问 Springer Link（自动IP认证）
- 浏览器：Chrome DevTools MCP

## Arguments

`$ARGUMENTS` 是 Springer 论文URL 或 DOI。

---

## Steps

### 1. Navigate to paper page

如果提供DOI，构造 Springer URL:
```
https://link.springer.com/article/DOI
```

如果提供完整URL（含图书馆代理前缀），直接 `navigate_page` 跳转。

### 2. Click PDF download

`wait_for` 页面加载后，找到并点击 "Download PDF" 按钮：

```
Tool: wait_for → text: ["Download PDF", "PDF"]
Tool: click → "Download PDF" 链接
```

或直接使用 PDF 直链:
```
navigate_page → https://link.springer.com/content/pdf/DOI.pdf
```

### 3. Post-download (与CNKI相同流程)

1. 检测浏览器下载目录
2. 逐文件复制PDF到 `<workspace>/ziliao/`
3. 向用户确认后删除源文件

**文件操作安全准则**:
- 逐文件用明确文件名操作，不用通配符
- 先复制后删除
- 删除前必须用户确认

---

## 直接下载模式（最优路径）

如果知道DOI，跳过论文页，直接:

```
navigate_page → https://link.springer.com/content/pdf/DOI.pdf
```

PDF 直接开始下载。

---

## 工具调用：1-3次

| 步骤 | 工具 | 说明 |
|------|------|------|
| 导航到论文页 | `navigate_page` | 仅当需要找下载链接时 |
| 点击下载 | `wait_for` + `click` | 或直接跳转PDF直链 |
| 后续处理 | Bash | 复制+确认删除 |

---

## 选择器速查

| 元素 | Selector |
|------|----------|
| PDF下载按钮 | `a[href*="/content/pdf/"]` 或 `.c-pdf-download__link` |
| 标题 | `h1.c-article-title` |
| DOI | `meta[name="citation_doi"]` |
