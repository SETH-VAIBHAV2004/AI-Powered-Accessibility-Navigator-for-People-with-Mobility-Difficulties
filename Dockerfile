FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini wsgi.py ./
RUN mkdir -p /app/instance && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["sh", "-c", "flask --app wsgi:app db upgrade && exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 60 --access-logfile - wsgi:app"]
