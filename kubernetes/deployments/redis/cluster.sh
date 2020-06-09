NAMESPACE=$1
kubectl -n $NAMESPACE exec -it redis-cluster-0 -- redis-cli --cluster create --cluster-replicas 1 $(kubectl -n $NAMESPACE get pods -l app=redis-cluster -o jsonpath='{range.items[*]}{.status.podIP}:6379 ')
kubectl -n $NAMESPACE exec -it redis-cluster-0 -- redis-cli cluster info
for x in $(seq 0 5); do echo "redis-cluster-$x"; kubectl -n $NAMESPACE exec redis-cluster-$x -- redis-cli role; echo; done