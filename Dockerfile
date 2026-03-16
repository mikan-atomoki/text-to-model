FROM python:3.11-slim

WORKDIR /app
COPY TextToModel/ ./TextToModel/
COPY docker/ ./docker/

EXPOSE 13405

CMD ["python", "docker/stdio_server.py"]
