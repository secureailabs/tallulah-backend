FROM docker.elastic.co/logstash/logstash:8.11.1

RUN rm -f /usr/share/logstash/pipeline/logstash.conf

COPY pipeline/logstash.conf /usr/share/logstash/pipeline/logstash.conf

# COPY config/ /usr/share/logstash/config/

