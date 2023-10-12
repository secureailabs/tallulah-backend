FROM python:3.8

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

# Install mongodump
RUN apt-get update && apt-get install -y wget
RUN wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-x86_64-100.8.0.deb
RUN dpkg -i mongodb-database-tools-ubuntu2204-x86_64-100.8.0.deb

ENTRYPOINT [ "uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000" ]
