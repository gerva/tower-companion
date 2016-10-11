FROM python:2-alpine
RUN apk update && apk add git openssh

RUN pip install --upgrade tower-companion
