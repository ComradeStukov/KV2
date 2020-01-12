#!/bin/bash

JUDICATOR_CORE='judicator-core'
JUDICATOR='judicator'
EXECUTOR='executor'
GATEWAY='gateway'

COOL_DOWN_TIME="25"

if [[ $# != 4 ]]; then
    echo "USAGE: $0 judicator-core-number judicator-number gateway-number executor-number"
    exit 1
fi

echo "================================="
echo "Creating following services:"
echo "$JUDICATOR_CORE : $1"
echo "$JUDICATOR : $2"
echo "$GATEWAY : $3"
echo "$EXECUTOR : $4"
echo "================================="
echo ""

echo "================================="
echo "Creating service $JUDICATOR_CORE."
echo "================================="
echo ""

docker service create \
--stop-grace-period=30s \
--replicas $1 \
--mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
--network khala \
--name $JUDICATOR_CORE khala:v0.1 judicator \
--docker-sock=unix:///var/run/docker.sock \
--boot-print-log \
--etcd-print-log \
--mongodb-print-log \
--main-print-log \
--etcd-cluster-init-independent \
--etcd-advertise-address=DOCKER \
--mongodb-advertise-address=DOCKER \
--main-advertise-address=DOCKER

read -ra service_id <<< `docker service ps -q $JUDICATOR_CORE`
service_id=${service_id[0]}
container_id=`docker inspect $service_id --format '{{.Status.ContainerStatus.ContainerID}}'`;
container_name=`docker inspect $container_id --format '{{.Name}}'`
judicator_core_name=${container_name#*/}

echo ""
echo "$JUDICATOR_CORE name detected: $judicator_core_name."

echo ""
echo "================================="
echo "Creating service $JUDICATOR."
echo "================================="
echo ""

docker service create \
--stop-grace-period=30s \
--replicas $2 \
--mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
--network khala \
--name $JUDICATOR khala:v0.1 judicator \
--docker-sock=unix:///var/run/docker.sock \
--boot-print-log \
--etcd-print-log \
--mongodb-print-log \
--main-print-log \
--etcd-cluster-join-member-client=http://$judicator_core_name:2001 \
--etcd-advertise-address=DOCKER \
--mongodb-advertise-address=DOCKER \
--main-advertise-address=DOCKER

echo ""
echo "================================="
echo "Creating service $GATEWAY."
echo "================================="
echo ""

docker service create \
--stop-grace-period=30s \
--replicas $3 \
--mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
--network khala -p 7000:7000 \
--name $GATEWAY khala:v0.1 gateway \
--docker-sock=unix:///var/run/docker.sock \
--boot-print-log \
--etcd-print-log \
--uwsgi-print-log \
--etcd-cluster-join-member-client=http://$judicator_core_name:2001

echo ""
echo "================================="
echo "Creating service $EXECUTOR."
echo "================================="
echo ""

docker service create \
--stop-grace-period=30s \
--replicas $4 \
--mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
--network khala \
--name $EXECUTOR khala:v0.1 executor \
--docker-sock=unix:///var/run/docker.sock \
--boot-print-log \
--etcd-print-log \
--main-print-log \
--etcd-cluster-join-member-client=http://$judicator_core_name:2001

echo ""
echo "Wait for $COOL_DOWN_TIME seconds."
sleep $COOL_DOWN_TIME

echo ""
echo "================================="
echo "All Service successfully created."
echo "================================="
echo ""
