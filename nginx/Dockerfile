# nginx/Dockerfile

# 使用官方 Nginx 镜像
FROM nginx:stable-alpine

# 复制自定义的 Nginx 配置文件
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露 HTTP 端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
