# FROM python:3.12.3
FROM python:3.12.3-alpine3.19

RUN apk add --no-cache git
RUN apk --no-cache add gcc musl-dev
COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY app /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "sh", "/entrypoint.sh" ]
