FROM ubuntu:20.04

ENV TZ=America/Toronto
LABEL authors="prawal@secureailabs.com"
USER root

# Set time zone data
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install dependencies
RUN apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y \
  nginx \
  wget \
  curl \
  sudo \
  git \
  build-essential \
  python3-pip \
  jq

# Install mongodb
RUN wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
RUN echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list

RUN apt-get update && \
  apt-get install -y \
  mongodb-org

RUN rm -rf /var/lib/apt/lists/*

RUN mkdir -p /srv/mongodb/db0 && chown -R mongodb:mongodb /srv/mongodb/db0
RUN mongod --port 27017 --dbpath /srv/mongodb/db0 --replSet rs0 --bind_ip localhost --fork --logpath /var/log/mongod.log

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/Entrypoint.sh /Entrypoint.sh
RUN chmod +x /Entrypoint.sh

COPY app /app

ENTRYPOINT [ "/Entrypoint.sh" ]
