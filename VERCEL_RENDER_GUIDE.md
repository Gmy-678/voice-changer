#!/bin/bash

# ✨ Vercel + Render 5 分钟部署指南

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         🚀 Vercel + Render 5 分钟快速部署指南                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📍 当前状态：
  ✅ 代码已准备好
  ⏳ 需要连接到 GitHub
  ⏳ 需要部署到 Vercel + Render

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【第一步】上传代码到 GitHub（如果还没有）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 访问 https://github.com/new 创建新仓库
   - 仓库名：voice-changer
   - 选择 Public（这样 Vercel 和 Render 才能看到）
   - 创建后会显示仓库 URL

2. 本地提交代码：
EOF

echo ""
echo "执行以下命令："
echo ""
cat << 'EOF'
   cd /Users/noizer/voice-changer
   git config user.name "your-github-username"
   git config user.email "your-email@example.com"
   git remote add origin https://github.com/your-username/voice-changer.git
   git branch -M main
   git commit -m "Initial commit: Voice Changer with 5 funny voices"
   git push -u origin main

   ⚠️  将上面的 your-username 和 your-email 替换为你的真实信息！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【第二步】前端部署到 Vercel（3 分钟）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 访问：https://vercel.com/new
   👉 用 GitHub 账号登录

2. 点击 "Import Git Repository"
   - 选择你刚才推送的 voice-changer 仓库
   - 点击 "Import"

3. 配置构建设置：
   ├─ Framework: Other
   ├─ Build Command: cd frontend && npm run build
   ├─ Output Directory: frontend/dist
   └─ Root Directory: . (留空)

4. 添加环境变量（重要！）：
   ├─ Key: VITE_API_BASE_URL
   └─ Value: https://voice-changer.onrender.com
      （稍后会改成你的 Render 应用 URL）

5. 点击 "Deploy"
   ⏳ 等待 2-3 分钟...
   ✅ 完成！你会得到一个 Vercel URL，类似：
      https://voice-changer-xxx.vercel.app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【第三步】后端部署到 Render（2 分钟）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 访问：https://render.com/register
   👉 用 GitHub 账号登录

2. 点击 "New" > "Web Service"

3. 连接 GitHub：
   - 点击 "Connect account"
   - 授权 Render 访问你的 GitHub
   - 选择 voice-changer 仓库

4. 配置 Web Service：
   ├─ Name: voice-changer
   ├─ Environment: Python 3.11
   ├─ Build Command: pip install -r requirements.txt
   ├─ Start Command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
   └─ Plan: Free（选择免费版）

5. 添加环境变量：
   ├─ Key: PYTHONUNBUFFERED
   └─ Value: 1

6. 点击 "Create Web Service"
   ⏳ 等待 5-10 分钟（第一次会慢一点）...
   ✅ 完成！你会得到一个 Render URL，类似：
      https://voice-changer.onrender.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【第四步】更新 Vercel 环境变量
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 回到 Vercel Dashboard
2. 找到你的 voice-changer 项目
3. 点击 "Settings" > "Environment Variables"
4. 修改 VITE_API_BASE_URL：
   - 改为你的 Render 应用 URL
   - 例如：https://voice-changer.onrender.com
5. 点击保存
6. 点击 "Deployments"，重新部署最新版本（点击三个点 > Redeploy）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【第五步】验证部署成功！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 打开前端应用：https://your-vercel-app.vercel.app
✅ 检查后端 API：https://voice-changer.onrender.com/docs
✅ 尝试转换一段音频

🎉 完成！现在你可以把链接分享给朋友了！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  常见问题

Q: 后端总是显示"Building"怎么办？
A: Render 首次构建需要 10-15 分钟，请耐心等待。之后会很快。

Q: 上传大文件时说超过大小限制？
A: Render 默认 100MB，如果太大可以在后端添加限制处理。

Q: 半小时没有请求，应用停止了？
A: 这是 Render 免费版的自动休眠机制。访问时会自动重启（30 秒内）。
   可以用 UptimeRobot 定时 ping 来保活。

Q: 如何添加自己的域名？
A: 在 Vercel/Render Dashboard 的 Domains 中添加自定义域名。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 需要帮助？

查看完整文档：
  cat /Users/noizer/voice-changer/FREE_DEPLOYMENT.md
  cat /Users/noizer/voice-changer/DEPLOYMENT.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
