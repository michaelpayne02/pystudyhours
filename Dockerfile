FROM python:3.12.0rc1-alpine3.18
RUN apk update && \
    apk add --no-cache tzdata

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py /etc/periodic/hourly/pystudyhours.py
RUN chmod +x /etc/periodic/hourly/pystudyhours.py

CMD ["crond", "-f", "-d", "8"]
