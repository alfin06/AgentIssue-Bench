FROM python:3.11

# 配置系统代理环境变量
ENV HTTP_PROXY=http://127.0.0.1:7890
ENV HTTPS_PROXY=http://127.0.0.1:7890
ENV NO_PROXY=localhost,127.0.0.1


# 可选：更新 pip，或者安装一些常用工具
RUN pip install --upgrade pip

# 默认进入 bash
CMD ["bash"]