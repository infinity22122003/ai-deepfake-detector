
FROM python:3.11-slim
WORKDIR /worker
COPY . .
RUN pip install celery
CMD celery -A tasks worker --loglevel=info
