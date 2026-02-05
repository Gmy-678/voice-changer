# Voice Changer 部署指南

## 📋 部署方案对比

| 方案 | 成本 | 难度 | 适用场景 |
|------|------|------|--------|
| Docker + VPS | 💵 低-中 | 中 | 自主完全控制、长期运营 |
| Vercel (前) + Railway (后) | 💵 低 | 低 | 快速上线、少用户 |
| Heroku | 💵 中 | 低 | 简单部署、需付费 |
| AWS/阿里云 | 💵 高 | 高 | 大规模、企业级 |

---

## 🚀 方案一：Docker + VPS（推荐）

### 步骤 1：本地构建 Docker 镜像

```bash
# 构建镜像
docker build -t voice-changer:latest .

# 测试运行
docker run -p 8000:8000 voice-changer:latest
```

### 步骤 2：部署到 VPS（以 Ubuntu 为例）

**购买 VPS**：推荐使用 DigitalOcean、Vultr、Linode（$3-5/月起）

**SSH 连接到 VPS**
```bash
ssh root@your_vps_ip
```

**安装 Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**克隆代码**
```bash
cd /home
git clone https://github.com/your-username/voice-changer.git
cd voice-changer
```

**启动服务**
```bash
docker-compose up -d
```

**配置域名**（可选）
```bash
# 在阿里云/腾讯云等 DNS 管理中
# 添加 A 记录：yourdomain.com -> your_vps_ip
```

**配置 HTTPS（使用 Certbot）**
```bash
sudo apt update && sudo apt install certbot python3-certbot-nginx -y

# 停止 nginx
docker-compose down

# 生成证书
sudo certbot certonly --standalone -d yourdomain.com

# 修改 nginx.conf 添加 SSL 配置
# 重新启动
docker-compose up -d
```

---

## 🟦 方案二：Vercel（前端）+ Railway（后端）

### 前端部署到 Vercel

**步骤 1**：登录 [Vercel](https://vercel.com)，导入 GitHub 仓库

**步骤 2**：配置构建设置
- Framework: Vue
- Build Command: `npm run build`
- Output Directory: `frontend/dist`
- Root Directory: `frontend`

**步骤 3**：环境变量（Settings > Environment Variables）
```
VITE_API_BASE_URL=https://your-railway-app.up.railway.app
```

### 后端部署到 Railway

**步骤 1**：登录 [Railway](https://railway.app)

**步骤 2**：New Project > GitHub Repo，选择你的代码库

**步骤 3**：添加服务
- 选择 Python
- 配置文件会自动检测

**步骤 4**：环境变量
```
PYTHONUNBUFFERED=1
```

**步骤 5**：Procfile（项目根目录创建）
```
web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT app.main:app
```

**步骤 6**：获取 Railway 应用 URL，在 Vercel 前端环境变量中配置

---

## 🌥️ 方案三：使用宝塔面板（VPS）

**最简单的方式**（适合不熟悉 CLI 的用户）

**步骤 1**：购买 VPS，安装宝塔面板
```bash
curl http://download.bt.cn/install/install_6.0.sh | bash
```

**步骤 2**：登录宝塔后台，创建 Node.js + Python 网站

**步骤 3**：上传项目文件

**步骤 4**：配置反向代理指向后端

---

## 📱 前端 API 配置修改

编辑 `frontend/src/api/` 中的 API 配置，改为使用环境变量：

```typescript
// frontend/src/api/index.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
})
```

---

## 🔧 部署后常见问题

### 1. **CORS 错误**
后端 `app/main.py` 添加 CORS 配置：
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. **文件上传大小限制**
```python
# app/main.py
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com"]
)

# 在路由中设置
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(status_code=413, detail="File too large")
```

### 3. **磁盘空间问题**
定期清理 `runs/` 和 `tmp/` 目录：
```bash
# 定时任务（crontab）
0 2 * * * find /app/runs -type f -mtime +7 -delete
```

---

## ✅ 推荐部署流程

1. **本地测试** ✓
2. **建立 GitHub 仓库** `git push`
3. **Docker 本地测试** `docker build && docker run`
4. **选择部署方案**
   - 个人项目：Vercel + Railway（最快）
   - 需要完全控制：Docker + VPS
5. **配置域名和 HTTPS**
6. **监控和日志**

---

## 💡 生产环境检查清单

- [ ] 关闭 FastAPI reload 模式（生产用 gunicorn）
- [ ] 设置环境变量（不要硬编码）
- [ ] 配置 HTTPS/SSL
- [ ] 设置合理的文件上传限制
- [ ] 定期备份数据
- [ ] 配置错误日志和监控
- [ ] 设置自动重启机制
- [ ] 配置 CORS 白名单

