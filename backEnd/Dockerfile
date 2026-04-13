# 使用 Python 3.12 轻量级基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制依赖列表并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY main.py .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
