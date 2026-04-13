# 使用 Python 3.12 轻量级基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制前端代码
COPY app.py .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 设置环境变量防止 Streamlit 启动时弹出邮箱收集框
ENV STREAMLIT_SERVER_GATHER_USAGE_STATS=false

# 启动命令
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
