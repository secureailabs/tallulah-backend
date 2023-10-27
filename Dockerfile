FROM python:3.11

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

ENTRYPOINT [ "uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000" ]
