FROM python:2-alpine
RUN apk update && apk add git openssh

RUN git config --global http.sslVerify false

RUN mkdir ~/.ssh
RUN echo "Host gitbub.com" > ~/.ssh/config
RUN echo "    StrictHostKeyChecking no" >> ~/.ssh/config

RUN echo "[general]" > ~/.tower_cli.cfg
RUN echo "reckless_mode = yes" >> ~/.tower_cli.cfg

RUN chmod 700 ~/.ssh
RUN chmod 400 ~/.ssh/config

RUN git clone https://github.com/gerva/tower-companion.git

WORKDIR ./tower-companion
RUN git checkout docker
RUN pip install --upgrade .
