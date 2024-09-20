# FROM python:3.12.3
FROM python:3.12.3-alpine3.19

RUN apk add --no-cache git
# this is a fix for: https://github.com/giampaolo/psutil/issues/2192#issuecomment-1396079848
RUN apk --no-cache add gcc musl-dev linux-headers python3-dev ffmpeg

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

ENTRYPOINT [ "uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000" ]
