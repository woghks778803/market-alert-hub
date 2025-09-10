FROM python:3.11-slim
WORKDIR /app

# 시스템 타임존(옵션)
ENV TZ=${TZ:-Asia/Seoul}

# 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스
COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
