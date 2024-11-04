FROM rwynn/monstache:latest

COPY pipeline/monstache.toml /etc/monstache/monstache.toml

# COPY arin-test-kv-mongo-connection-certificate-20241028.pem arin-test-kv-mongo-connection-certificate-20241028.pem

COPY pipeline/monstache_entrypoint.sh /monstache_entrypoint.sh
RUN chmod +x /monstache_entrypoint.sh

ENTRYPOINT ["/monstache_entrypoint.sh"]
