#!/usr/bin/env bash
set -m

source $1

echo "This will wipe ALL local Sempo data."
echo "Persist Ganache? (y/N)"
read ganachePersistInput

if [ -z ${MASTER_WALLET_PK+x} ]
then
echo "\$MASTER_WALLET_PK is empty"
exit 0
else
echo "\$MASTER_WALLET_PK is NOT empty"
fi

set +e

echo ~~~~Resetting readis
redis-server &
redis-cli FLUSHALL

echo ~~~~Resetting Ganache
cd ../
kill $(ps aux | grep '[g]anache-cli' | awk '{print $2}')
rm -R ./ganacheDB

if [ $ganachePersistInput != y ]
then
  ganache-cli -l 80000000 -i 42 --account="${MASTER_WALLET_PK},10000000000000000000000000" &
else
  mkdir ganacheDB
  ganache-cli -l 80000000 -i 42 --account="${MASTER_WALLET_PK},10000000000000000000000000" --db './ganacheDB' &
fi

