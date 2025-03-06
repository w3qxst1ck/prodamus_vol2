FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements_build.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./server /app/server
COPY ./database /app/database

CMD ["uvicorn", "./server/main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]