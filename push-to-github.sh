#!/bin/bash

# 🚀 一键推送代码到 GitHub

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           📤 Voice Changer GitHub 一键推送脚本               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 检查是否在正确的目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误：请在 voice-changer 目录运行此脚本"
    exit 1
fi

# 询问用户信息
echo "📋 请输入你的 GitHub 信息："
echo ""

read -p "👤 GitHub 用户名 (例如: john-doe): " github_username
read -p "✉️  GitHub 邮箱 (例如: john@example.com): " github_email

if [ -z "$github_username" ] || [ -z "$github_email" ]; then
    echo "❌ 错误：用户名和邮箱不能为空"
    exit 1
fi

echo ""
echo "📝 将使用以下信息："
echo "   用户名: $github_username"
echo "   邮箱: $github_email"
echo ""

# 配置 Git
git config user.name "$github_username"
git config user.email "$github_email"

# 检查是否有远程仓库配置
if ! git remote get-url origin 2>/dev/null; then
    echo "⚙️  配置远程仓库..."
    read -p "🔗 GitHub 仓库 URL (https://github.com/your-username/voice-changer.git): " repo_url
    
    if [ -z "$repo_url" ]; then
        echo "❌ 错误：仓库 URL 不能为空"
        exit 1
    fi
    
    git remote add origin "$repo_url"
fi

# 显示当前远程
echo ""
echo "✅ 远程仓库已配置:"
git remote -v
echo ""

# 提交代码
echo "📦 准备提交代码..."
git add .
git branch -M main

if git diff --cached --quiet; then
    echo "ℹ️  没有新文件需要提交"
else
    git commit -m "🚀 Initial commit: Voice Changer with 5 funny voices (Anime Uncle, UwU Anime, Gender Swap, Mamba, Nerd Bro)"
fi

# 推送代码
echo ""
echo "🚀 推送代码到 GitHub..."
git push -u origin main

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ 推送完成！                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 后续步骤："
echo ""
echo "【第二步】部署前端到 Vercel"
echo "   1. 访问 https://vercel.com/new"
echo "   2. 用 GitHub 账号登录"
echo "   3. 点击 Import Git Repository"
echo "   4. 选择 voice-changer 仓库"
echo "   5. 配置："
echo "      - Build Command: cd frontend && npm run build"
echo "      - Output Directory: frontend/dist"
echo "      - Environment: VITE_API_BASE_URL=https://voice-changer.onrender.com"
echo "   6. 点击 Deploy"
echo ""
echo "【第三步】部署后端到 Render"
echo "   1. 访问 https://render.com"
echo "   2. 点击 New > Web Service"
echo "   3. 连接 GitHub 仓库"
echo "   4. 选择 voice-changer"
echo "   5. 配置："
echo "      - Environment: Python 3.11"
echo "      - Build: pip install -r requirements.txt"
echo "      - Start: gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app"
echo "   6. 点击 Create Web Service"
echo ""
echo "【第四步】更新 Vercel 环境变量"
echo "   1. Vercel Dashboard > Settings > Environment Variables"
echo "   2. 将 VITE_API_BASE_URL 改为你的 Render URL"
echo "   3. Redeploy"
echo ""
echo "✨ 详细文档："
echo "   cat /Users/noizer/voice-changer/DEPLOY_CHECKLIST.md"
echo ""
