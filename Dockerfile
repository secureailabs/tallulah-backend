FROM python:3.12.3

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

COPY filebeat-8.11.1-amd64.deb /filebeat-8.11.1-amd64.deb
RUN dpkg -i filebeat-8.11.1-amd64.deb
COPY filebeat.yml /etc/filebeat/filebeat.yml
RUN chmod go-w /etc/filebeat/filebeat.yml

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
