---
name: ieee-download
description: Download paper PDF from IEEE Xplore via library proxy. Extracts article number and uses direct PDF link. Use when user wants to download an IEEE paper.
argument-hint: "[IEEE paper URL or DOI]"
---

# IEEE Xplore Paper Download

通过图书馆IP认证直接下载IEEE论文PDF，无需登录。

## Prerequisites

- 通过学校图书馆代理访问 IEEE Xplore（自动IP认证）
- 浏览器：Chrome DevTools MCP

## Arguments

`$ARGUMENTS` 是 IEEE 论文URL 或 DOI。

---

## Steps

### 1. Navigate to paper page

**如果提供的是DOI**: 先用图书馆统一检索定位，或构造 IEEE URL:
```
https://ieeexplore.ieee.org/document/ARTICLE_NUMBER
```

**如果提供的是IEEE URL**: 直接 `navigate_page` 跳转。

确保URL中包含图书馆代理前缀（如适用）。

### 2. Extract article number and download

`wait_for` 页面加载后，提取 `arnumber` 并直接导航到 PDF 直链：

```javascript
() => {
  // Extract article number from URL or meta
  const url = window.location.href;
  const arnumberMatch = url.match(/document\/(\d+)/) || url.match(/arnumber=(\d+)/);
  const arnumber = arnumberMatch ? arnumberMatch[1] : '';

  // Also try meta tag
  const metaArnumber = document.querySelector('meta[name="citation_ieee_article_number"]')?.getAttribute('content') || '';

  // Get title
  const title = document.querySelector('h1.document-title, h1.title, meta[name="citation_title"]')?.getAttribute('content')
    || document.querySelector('h1')?.innerText?.trim() || '';

  return {
    arnumber: arnumber || metaArnumber,
    title: title,
    pdfUrl: arnumber ? `https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=${arnumber || metaArnumber}` : null
  };
}
```

### 3. Navigate to PDF URL

```bash
# 使用提取的 arnumber
navigate_page → https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=NUMBER
```

**两种情况**：
- **小文件 (<2MB)**: PDF 自动下载，30秒内完成
- **大文件/超时**: PDF 以 inline 方式显示在浏览器中 → 告知用户手动 `Ctrl+S` 保存

### 4. Post-download (与CNKI相同流程)

1. 检测浏览器下载目录
2. 逐文件复制PDF到 `<workspace>/ziliao/`
3. 向用户确认后删除源文件

**文件操作安全准则**:
- 逐文件用明确文件名操作，不用通配符
- 先复制后删除
- 删除前必须用户确认

---

## 直接下载模式（最优路径）

如果知道 `arnumber`，跳过步骤1-2，直接：

```
navigate_page → https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=NUMBER
```

PDF 直接开始下载。

---

## 工具调用：2-3次

| 步骤 | 工具 | 说明 |
|------|------|------|
| 导航到论文页 | `navigate_page` | 仅当需要提取arnumber时 |
| 提取arnumber | `evaluate_script` | 只需1次 |
| 下载PDF | `navigate_page` | 直接跳转PDF直链 |
| 后续处理 | Bash | 复制+确认删除 |

---

## 选择器速查

| 元素 | Selector |
|------|----------|
| 标题 | `h1.document-title` 或 `meta[name="citation_title"]` |
| Article Number | `meta[name="citation_ieee_article_number"]` |
| DOI | `meta[name="citation_doi"]` |
| PDF链接 | `.pdf-btn` 或 `a[href*="stampPDF"]` |
