export KUBECONFIG=.kubernetes/admin-kubeconfig.conf 

curl https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0/aio/deploy/recommended.yaml > dashboard.yaml
kubectl --kubeconfig=.kubernetes/admin-kubeconfig.conf apply -f .kubernetes/dashboard.yaml
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep admin-user | awk '{print $1}')
kubectl proxy
open http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

curl https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/baremetal/deploy.yaml > .kubernetes/ingress-nginx.yaml
kubectl get pods --all-namespaces -l app.kubernetes.io/name=ingress-nginx --watch

https://rook.io/docs/rook/v1.3/ceph-quickstart.html#storage
https://rook.io/docs/rook/v1.3/ceph-filesystem.html
kubectl -n rook-ceph get pod -l app=rook-ceph-mds