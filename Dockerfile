# 使用官方 Python 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，防止 Python 生成 .pyc 文件并开启缓冲
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 复制依赖文件并安装，使用国内镜像源
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码
COPY . /app/

# 运行数据库迁移和收集静态文件（如果需要）
RUN python manage.py migrate && \
    python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 启动 Gunicorn 服务器
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]
