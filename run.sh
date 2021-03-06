#! /bin/bash

docker-compose up -d
docker-compose stop proxy
echo 'Waiting 50 seconds before restarting traefik'
sleep 40
docker-compose up -d proxy
echo "traefik restarted"
echo "marathon is accessible at marathon.localhost"
echo "chronos is accessible at chronos.localhost"
echo "traefik is accessible at traefik.localhost"
echo "maracker is accessible at localhost:8000"
