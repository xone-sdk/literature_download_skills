---
name: cnki-download
description: Download a paper PDF/CAJ from CNKI. Automatically handles download, copies to workspace, and cleans up source files after user confirmation. Use when user wants to download a specific paper.
argument-hint: "[paper URL or blank if already on detail page]"
---

# CNKI Paper Download (文献下载)

## Prerequisites

User **must be logged in** to CNKI with download permissions (机构认证或个人登录).

## Arguments

`$ARGUMENTS` is optionally a paper detail URL. If blank, uses current page.

## Permission

下载操作默认已授权。直接点击 PDF 下载按钮即可，无需额外权限检查。

---

## Steps

### 1. Navigate to paper detail page

If URL provided: use `navigate_page` to go to the URL directly.

**Important**: Always use `navigate_page` instead of clicking links on the search results page. Clicking opens a new tab and wastes 3 extra tool calls.

### 2. Download PDF

Wait for "PDF下载" text to appear, then click the button directly:

```
Tool: wait_for → text: ["PDF下载"]
Tool: click → uid of "PDF下载" link
```

No `evaluate_script` needed for download. Just wait and click.

**Captcha handling**: If click is blocked, check `#tcaptcha_transform_dy` with `evaluate_script`:
```javascript
() => {
  const cap = document.querySelector('#tcaptcha_transform_dy');
  return { capActive: cap && cap.getBoundingClientRect().top >= 0 };
}
```
If `capActive: true` → tell user to solve captcha manually in Chrome.

### 3. Detect browser download directory

The browser saves PDFs to a default download directory. Find it by:

**Step 3a**: Check common default paths:
```bash
# Windows Chrome default
ls -lt "$USERPROFILE/Downloads/"*.pdf 2>/dev/null | head -5
```

**Step 3b**: If the above is empty, ask user: "浏览器下载文件保存在哪个目录？"

**Step 3c**: Remember the confirmed path as `$DL_DIR` for this session. Use forward slashes for bash compatibility.

### 4. Copy downloaded files to working directory

**Default workspace folder**: `<workspace>/ziliao/`

If user specifies a custom folder, use that instead. Create if not exists:
```bash
mkdir -p "<workspace>/ziliao"
```

Copy files individually (avoid wildcards with Chinese filenames):
```bash
# Copy each file by explicit name
cp "$DL_DIR/论文文件名.pdf" "<workspace>/ziliao/"
```

> **注意**: 不要用通配符 `*.pdf` 处理中文文件名，bash 可能解析失败导致文件丢失。逐文件复制最安全。

### 5. Confirm before deleting source files

**CRITICAL**: Always show the user what will be deleted and get confirmation first:

```
⚠️ 确认删除原始文件

以下文件已复制到 <workspace>/ziliao/，准备删除源文件：

| 文件 | 大小 |
|------|------|
| xxx.pdf | xx KB |
| ...

确认删除这 N 个原始文件吗？
```

Only delete after user says "ok" / "确认" / "删除":
```bash
# Delete each file individually by explicit name
rm "$DL_DIR/论文文件名.pdf"
```

---

## Tool calls per paper: 3–4

| Step | Tool | Notes |
|------|------|-------|
| Navigate | `navigate_page` | Only if URL provided |
| Wait + Click | `wait_for` + `click` | Wait for "PDF下载", then click |
| Post-download | (batch) | Copy + confirm delete, done in batches |

---

## Verified selectors

| Element | Selector | Notes |
|---------|----------|-------|
| PDF download | `#pdfDown` | `<a>` inside `li.btn-dlpdf` |
| CAJ download | `#cajDown` | `<a>` inside `li.btn-dlcaj` |
| Download area | `.download-btns` | parent `<div>` |
| Not logged in | `.downloadlink.icon-notlogged` | |
| Title | `.brief h1` | strip trailing "网络首发" |

## Captcha detection

Check `#tcaptcha_transform_dy` element's `getBoundingClientRect().top >= 0`.
Only active when `top >= 0` (visible). Pre-loaded SDK sits at `top: -1000000px`.

---

## Batch download workflow

When downloading multiple papers, follow this efficient pattern:

1. **Download phase**: Navigate → wait "PDF下载" → click → next paper (repeat)
   - No need to verify each download individually
2. **Copy phase**: After all downloads triggered, find new PDFs and copy each individually to workspace
3. **Cleanup phase**: Show files to user, get confirmation, then delete source files individually

**文件操作安全准则**:
- 始终用明确的文件名逐文件操作，不使用通配符处理中文文件名
- 复制完成并验证后才删除源文件
- 删除前必须用户确认
