#!/bin/bash
# 一键安装文献检索技能到 Claude Code
# 用法: bash install.sh

SKILLS_DIR="${HOME}/.claude/skills"
REPO="https://github.com/xone-sdk/literature_download_skills.git"
TMPDIR="/tmp/literature_skills_$$"

echo "==> 下载技能仓库..."
git clone --depth 1 "$REPO" "$TMPDIR" 2>/dev/null || {
    echo "Git clone failed, trying direct download..."
    curl -sL "${REPO%.git}/archive/refs/heads/main.tar.gz" | tar xz -C /tmp
    TMPDIR="/tmp/literature_download_skills-main"
}

mkdir -p "$SKILLS_DIR"

echo "==> 安装技能文件..."
cp "$TMPDIR/.claude/skills/"* "$SKILLS_DIR/" 2>/dev/null

rm -rf "$TMPDIR"

echo "==> 完成！"
echo "已安装到: $SKILLS_DIR"
ls "$SKILLS_DIR"
