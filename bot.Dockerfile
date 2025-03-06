FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements_bot.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./database /app/database
COPY ./routers /app/routers
COPY ./services /app/services
COPY apsched.py /app
COPY main.py /app
COPY settings.py /app
