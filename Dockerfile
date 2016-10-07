FROM python:2-alpine
RUN apk update && apk add git openssh

RUN pip install --upgrade tower-companion

RUN echo "[general]" > ~/.tower_cli.cfg
RUN echo "reckless_mode = yes" >> ~/.tower_cli.cfg
