# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=${TZ:-Asia/Seoul}

WORKDIR /app

# 필요 최소 빌드 툴 (확장 시에만 증가)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

# 의존성 먼저 복사 → 설치 (캐시 활용)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# 소스 (개발에선 compose 볼륨이 덮어씁니다)
COPY . /app

EXPOSE 8000

# 기본 실행(개발에선 compose의 command가 이걸 덮습니다)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
