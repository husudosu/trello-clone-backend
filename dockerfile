FROM python:3.10-bullseye
LABEL maintainer="Ferenc Nánási <husudosu94@gmail.com>"

ENV FLASK_APP=run.py \
    FLASK_ENV=production \
    TZ="Europe/Budapest"

RUN apt update && \
    apt upgrade -y && \
    apt install \
    libpq-dev \
    python3-dev \
    nginx \
    build-essential \
    supervisor -y

WORKDIR /root
COPY REQUIREMENTS.txt ./
RUN pip install -r REQUIREMENTS.txt

COPY run.py \
    config.py \
    boot.sh \ 
    configs/supervisord.conf \ 
    configs/nginx/nginx.conf \
    ./

COPY api api
COPY migrations migrations
COPY frontend/dist dist
COPY ./configs/nginx/http /etc/nginx/sites-enabled/default
COPY ./configs/nginx/nginx.conf /etc/nginx/nginx.conf

# Self-signed cert
COPY ./configs/nginx/nginx-selfsigned.key /etc/ssl/private/nginx-selfsigned.key
COPY ./configs/nginx/nginx-selfsigned.crt /etc/ssl/certs/nginx-selfsigned.crt
COPY ./configs/nginx/snippets/self-signed.conf /etc/nginx/snippets/self-signed.conf
COPY ./configs/nginx/dhparam.pem /etc/nginx/dhparam.pem

RUN chmod 777 boot.sh

EXPOSE 80
EXPOSE 443
