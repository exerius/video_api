FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git

RUN pip install poetry==2.2.1
WORKDIR /app
RUN git clone https://github.com/exerius/video_api.git .

RUN poetry install --no-interaction --no-ansi --no-root

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "log_config.yaml"]