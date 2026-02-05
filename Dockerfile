FROM python:3.11-slim

# 安装系统依赖（ffmpeg 用于音频处理）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制后端代码
COPY app/ ./app/

# 创建数据目录
RUN mkdir -p /app/runs /app/tmp

# 暴露端口
EXPOSE 8000

# 启动命令（Render 会通过环境变量 PORT 指定监听端口）
CMD ["sh", "-c", "gunicorn -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} app.main:app"]
