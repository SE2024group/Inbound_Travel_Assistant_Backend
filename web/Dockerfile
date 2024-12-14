# 使用官方 Python 基础镜像
FROM python:3.10.12

# 设置工作目录
WORKDIR /app

# 设置环境变量，防止 Python 生成 .pyc 文件并开启缓冲
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# 复制依赖文件并安装，使用国内镜像源
COPY requirements.txt /app/


# 替换 apt 源为腾讯云镜像源
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.tencent.com/debian/ bookworm main contrib non-free\n\
    deb-src https://mirrors.tencent.com/debian/ bookworm-updates main contrib non-free" > /etc/apt/sources.list


RUN cat /etc/apt/sources.list

# 更新包列表并安装 ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


# 复制项目代码
COPY . /app/

# 运行数据库迁移和收集静态文件（如果需要）
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 启动 Gunicorn 服务器
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]

