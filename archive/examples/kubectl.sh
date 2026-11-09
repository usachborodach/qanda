# kubeproxy настраиваиет iptables
minikube start

kubectl get nodes
kubectl get nodes -o wide

учитывать что скейлинг применяется к поду

kubectl create - создаёт заново
kubectl apply - обновляет

kubectl get namespaces

kubectl get pods -n kube-system
kubectl get pods -A

kubectl create -f pod_app.yaml
kubectl apply -f pod_app.yaml

kubectl logs -f app -c server

kubectl describe pod
kubectl describe node
kubectl describe replicaset

# sa=serviceaccount
kubectl get sa logshipper-sa -n default

kubectl get rolebindings -n default -o json | \
  jq -r '.items[] | select(.subjects[]? | .kind=="ServiceAccount" and .name=="logshipper-sa") | .metadata.name'

kubectl get clusterrolebindings -o json | \
  jq -r '.items[] | select(.subjects[]? | .kind=="ServiceAccount" and .name=="logshipper-sa" and .namespace=="default") | .metadata.name'


kubectl get limitrange -n default -o yaml
kubectl edit limitranges default