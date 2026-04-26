FROM python:3.12-slim

WORKDIR /app

COPY common/requirements.txt .
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# COPY ./worker /app
# RUN chmod +x /app/entrypoint.sh
# ENTRYPOINT ["/app/entrypoint.sh"]