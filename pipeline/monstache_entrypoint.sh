#!/bin/sh

export MONSTACHE_MONGO_URL="$MONGO_URL"\&tlscertificatekeyFile=/mnt/certificates/mongo-certificate

/bin/monstache -f /etc/monstache/monstache.toml

# don't kill the container
tail -f /dev/null
