#!/bin/bash

# Run the fastapi app
uvicorn app.main:server --host 0.0.0.0 --port 8000
