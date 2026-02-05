# 🚀 Vercel + Render 5 分钟部署快速检查清单

## ✅ 部署前准备

- [ ] 有 GitHub 账号（没有去 https://github.com/signup 注册）
- [ ] 有 Vercel 账号（用 GitHub 登录 https://vercel.com）
- [ ] 有 Render 账号（用 GitHub 登录 https://render.com）

## 📤 第一步：上传代码到 GitHub

```bash
cd /Users/noizer/voice-changer

# 配置 Git
git config user.name "your-github-username"
git config user.email "your-email@example.com"

# 添加远程仓库（替换 your-username）
git remote add origin https://github.com/your-username/voice-changer.git

# 提交代码
git branch -M main
git commit -m "Initial commit: Voice Changer with 5 funny voices"
git push -u origin main
```

**检查** ✅：
- [ ] 代码已推送到 GitHub
- [ ] 访问 https://github.com/your-username/voice-changer 能看到代码

---

## 🌐 第二步：Vercel 前端部署（3 分钟）

### 步骤：
1. 访问 https://vercel.com/new
2. 点击 "Import Git Repository"
3. 选择 voice-changer 仓库
4. 配置：
   - **Framework**: Other
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/dist`
   - **Root Directory**: (留空)
5. 环境变量：
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://voice-changer.onrender.com` (暂时用这个)
6. 点击 "Deploy"

### 等待完成后：
- [ ] 部署成功（显示 "Ready"）
- [ ] 记下 Vercel 的应用 URL（类似 `https://voice-changer-abc123.vercel.app`）

---

## 🔌 第三步：Render 后端部署（10 分钟）

### 步骤：
1. 访问 https://render.com
2. 点击 "New" > "Web Service"
3. 选择 "Connect account" 授权 GitHub
4. 选择 voice-changer 仓库
5. 配置：
   - **Name**: `voice-changer`
   - **Environment**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: 
     ```
     gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
     ```
   - **Plan**: `Free`
6. 环境变量：
   - **Key**: `PYTHONUNBUFFERED`
   - **Value**: `1`
7. 点击 "Create Web Service"

### 等待完成后：
- [ ] 部署成功（显示 "Live"）
- [ ] 记下 Render 的应用 URL（类似 `https://voice-changer.onrender.com`）

---

## 🔄 第四步：更新 Vercel 环境变量

1. 回到 Vercel Dashboard
2. 选择 voice-changer 项目
3. Settings > Environment Variables
4. 编辑 `VITE_API_BASE_URL`：
   - 改为你的 Render URL
   - 例如：`https://voice-changer.onrender.com`
5. 保存
6. Deployments > 最新部署 > 三个点 > Redeploy

### 等待重新部署：
- [ ] Vercel 再次部署成功

---

## 🧪 第五步：验证部署成功

### 检查项：
- [ ] 打开 Vercel URL，页面能加载
- [ ] 页面上能看到 5 个搞怪音色
- [ ] 访问 `https://voice-changer.onrender.com/docs` 能看到 API 文档
- [ ] 尝试上传音频并转换，有输出

---

## 🎉 完成！

**现在你可以分享链接给朋友了！**

- 前端：`https://your-vercel-app.vercel.app`
- API：`https://voice-changer.onrender.com`

---

## ⚠️ 常见问题排查

| 问题 | 解决方案 |
|------|--------|
| Vercel 部署失败 | 检查 Build Log，通常是前端依赖或构建命令错误 |
| Render 一直 Building | 第一次部署会慢，等 10-15 分钟。之后很快 |
| API 返回 CORS 错误 | 确保 Vercel 的 `VITE_API_BASE_URL` 指向了正确的 Render URL |
| 上传文件超过限制 | 默认 100MB，可以在后端修改 `client_max_body_size` |
| 半小时无请求后应用停止 | 这是 Render 免费版特性。重新访问会自动重启（30 秒） |

---

## 📞 需要帮助？

查看完整文档：
- `cat /Users/noizer/voice-changer/VERCEL_RENDER_GUIDE.md`
- `cat /Users/noizer/voice-changer/FREE_DEPLOYMENT.md`

或查看官方文档：
- Vercel: https://vercel.com/docs
- Render: https://render.com/docs
