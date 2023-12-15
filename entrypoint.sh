#!/bin/bash

# Run the filebeat logging agent
filebeat -e -c /etc/filebeat/filebeat.yml &

# Run the fastapi app
uvicorn app.main:server --host 0.0.0.0 --port 8000
