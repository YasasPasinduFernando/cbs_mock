FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY mock_t24_cbs.py /app/mock_t24_cbs.py
COPY mock_config.json /app/mock_config.json

EXPOSE 8780

CMD ["python", "/app/mock_t24_cbs.py", "--config", "/app/mock_config.json", "--host", "0.0.0.0", "--port", "8780"]
