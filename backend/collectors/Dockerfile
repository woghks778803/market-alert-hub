FROM python:3.11-slim
WORKDIR /app
ENV TZ=${TZ:-Asia/Seoul}
RUN pip install --no-cache-dir redis
COPY . .
CMD ["python", "-c", "import time,sys; print('collectors up'); sys.stdout.flush(); \
[time.sleep(60) for _ in iter(int,1)]"]
