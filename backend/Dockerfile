FROM python:3.11-slim

  WORKDIR /app/backend

  # 安装系统依赖
  RUN apt-get update && apt-get install -y \
      gcc \
      && rm -rf /var/lib/apt/lists/*

  # 复制requirements.txt
  COPY requirements.txt .

  # 使用清华镜像源加速安装
  RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
      pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

  # 复制代码
  COPY . .

  CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
