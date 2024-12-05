# FROM python:3.12.3
FROM python:3.12.3-alpine3.19

RUN apk add --no-cache git
# this is a fix for: https://github.com/giampaolo/psutil/issues/2192#issuecomment-1396079848
RUN apk --no-cache add gcc musl-dev linux-headers python3-dev ffmpeg

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --target /dd_tracer/python/ ddtrace
RUN pip install ddtrace
ENV DD_SERVICE=tallulah-backend
ENV DD_VERSION=1

COPY app /app
COPY VERSION /VERSION

COPY --from=datadog/serverless-init:1-alpine /datadog-init /app/datadog-init

ENTRYPOINT ["/app/datadog-init"]
CMD [ "/dd_tracer/python/bin/ddtrace-run", "uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000" ]
