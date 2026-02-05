# 免费部署方案完全指南

## 🆓 零成本部署方案对比

| 方案 | 前端 | 后端 | 难度 | 限制 |
|------|------|------|------|------|
| **Vercel + Render** | ✅ | ✅ | 低 | Render 5 分钟自动休眠 |
| **Netlify + Railway** | ✅ | ✅ | 低 | Railway $5/月额度 |
| **Hugging Face Spaces** | ✅ | ✅ | 中 | 需改造为 Streamlit/Gradio |
| **Replit** | ✅ | ✅ | 低 | 社区版有限制 |
| **Oracle Cloud** | ✅ | ✅ | 中 | 永久免费 VM（最强） |
| **本地 + 内网穿透** | ✅ | ✅ | 低 | 需要本地电脑常开 |

---

## 🥇 最推荐：Vercel + Render（5 分钟上线）

### 前端部署到 Vercel（完全免费）

**Step 1**: 上传到 GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

**Step 2**: 登录 [Vercel](https://vercel.com)，用 GitHub 账号登录

**Step 3**: 点击 "New Project" > 选择你的仓库

**Step 4**: 配置构建设置
```
Framework: Other (Vite)
Build Command: cd frontend && npm run build
Output Directory: frontend/dist
Root Directory: . (或留空)
```

**Step 5**: 添加环境变量
```
VITE_API_BASE_URL = https://your-render-app.onrender.com
```

点击 "Deploy"，**2 分钟自动上线** ✅

---

### 后端部署到 Render（有免费额度）

**Step 1**: 登录 [Render](https://render.com)

**Step 2**: 点击 "New" > "Web Service"

**Step 3**: 连接 GitHub 仓库

**Step 4**: 配置
```
Name: voice-changer
Environment: Python 3.11
Build Command: pip install -r requirements.txt
Start Command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
```

**Step 5**: 环境变量
```
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
PYTHONUNBUFFERED=1
```

**Step 6**: Plan 选择 "Free"，点击 "Create Web Service"

**等待 5 分钟部署完成** ✅

---

## 🦅 最强：Oracle Cloud（永久免费 VM）

**完全免费**，不会自动休眠，最适合长期运营！

### 步骤：

**Step 1**: 注册 [Oracle Cloud](https://www.oracle.com/cloud/free/) 账户（需要信用卡验证，但不会扣费）

**Step 2**: 创建虚拟机
- Region: 选择离你最近的区域
- Image: Ubuntu 22.04
- Shape: Ampere A1（永久免费）
- Public IP: 勾选

**Step 3**: SSH 连接
```bash
chmod 600 ~/your-key.key
ssh ubuntu@your-oracle-ip -i ~/your-key.key
```

**Step 4**: 安装 Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Step 5**: 部署应用
```bash
git clone https://github.com/your-username/voice-changer.git
cd voice-changer
docker-compose up -d
```

**Step 6**: 配置防火墙（Oracle Cloud Console）
- 进入 Instance Details
- VNIC: 编辑
- 安全列表: 添加 Ingress Rule
  - Protocol: TCP
  - Destination Port Range: 8000, 80, 443

**访问**: `http://your-oracle-ip:8000`

---

## 🤗 Hugging Face Spaces（改造方案）

适合想要完全免费且不需要休眠的

**改造成 Gradio 应用**（比较复杂，需要改代码）：

```python
# app_gradio.py
import gradio as gr
from app.services.providers.funny_voice import FunnyVoiceProvider
import tempfile
import os

provider = FunnyVoiceProvider()

def convert_voice(audio, voice_id):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio)
        tmp_path = tmp.name
    
    try:
        result = provider.convert(
            voice_id=voice_id,
            audio_path=tmp_path,
            output_format="wav"
        )
        
        output_path = "output.wav"
        with open(output_path, "wb") as f:
            f.write(result.audio_bytes)
        
        return output_path
    finally:
        os.unlink(tmp_path)

interface = gr.Interface(
    fn=convert_voice,
    inputs=[
        gr.Audio(type="filepath", label="Upload Audio"),
        gr.Dropdown(
            choices=['anime_uncle', 'uwu_anime', 'gender_swap', 'mamba', 'nerd_bro'],
            label="Voice Style"
        )
    ],
    outputs=gr.Audio(label="Converted Audio"),
    title="Voice Changer 🎤",
)

if __name__ == "__main__":
    interface.launch()
```

上传到 GitHub，然后在 Hugging Face Spaces 创建新应用，连接仓库即可！

---

## 🏠 本地 + 内网穿透（极简方案）

**不需要任何服务器**，在家电脑就能做网站！

### 使用 Cloudflare Tunnel（完全免费）

**Step 1**: 安装 Cloudflare
```bash
# macOS
brew install cloudflare/cloudflare-go/cloudflared

# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
```

**Step 2**: 启动隧道
```bash
# 后端隧道
cloudflared tunnel --url http://localhost:8000

# 记下显示的 URL，类似: https://abc123.trycloudflare.com
```

**Step 3**: 前端配置环境变量
```
VITE_API_BASE_URL=https://abc123.trycloudflare.com
```

**Step 4**: 启动前端
```bash
npm run dev
```

**就这么简单！** 别人可以通过 `https://abc123.trycloudflare.com` 访问你的应用了！

---

## 💡 免费方案快速对比总结

### 🥇 **第一选择：Vercel + Render**
- ✅ 完全免费（Render 有自动休眠）
- ✅ 部署简单
- ✅ 网络快
- ⚠️ 5-10 分钟无请求自动休眠

### 🥈 **第二选择：Oracle Cloud**
- ✅ 永久免费，不休眠
- ✅ 可完全控制
- ⚠️ 设置相对复杂

### 🥉 **第三选择：本地 + Cloudflare Tunnel**
- ✅ 最简单快速
- ✅ 完全免费
- ⚠️ 需要电脑常开

---

## 🚀 立即行动清单

**方案 A（推荐，5 分钟）**
- [ ] 代码推到 GitHub
- [ ] Vercel 连接仓库自动部署前端
- [ ] Render 连接仓库部署后端
- [ ] Vercel 环境变量配置 API 地址
- [ ] 访问链接分享给朋友

**方案 B（最强，30 分钟）**
- [ ] Oracle Cloud 注册
- [ ] 创建免费 VM
- [ ] SSH 连接，安装 Docker
- [ ] 运行 `docker-compose up -d`
- [ ] 配置防火墙开放端口
- [ ] 访问 `ip:8000` 分享给朋友

**方案 C（最快，2 分钟）**
- [ ] 本地启动前后端服务
- [ ] 运行 `cloudflared tunnel --url http://localhost:8000`
- [ ] 复制生成的 URL 分享给朋友

---

## ⚠️ 注意事项

1. **Render 免费版限制**
   - 自动休眠：30 分钟无请求则关闭
   - 重启需要 30 秒
   - 解决方案：用 UptimeRobot 定时 ping 保活

2. **文件上传大小**
   - Vercel：100MB
   - Render：默认无限
   - 建议限制在 50MB

3. **Oracle Cloud 永久免费条件**
   - 每月至少登录一次
   - 实际使用资源不超过限额
   - 超过限额会警告，不会直接扣费

---

## 🔗 快速链接

- [Vercel 官网](https://vercel.com)
- [Render 官网](https://render.com)
- [Oracle Cloud 官网](https://www.oracle.com/cloud/free/)
- [Cloudflare Tunnel 文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Hugging Face Spaces](https://huggingface.co/spaces)

