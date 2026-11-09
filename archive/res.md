user@user-pc:~/Downloads$ minikube start --driver=docker --memory=5000 --cpus=2
😄  minikube v1.39.0 on Ubuntu 22.04
✨  Using the docker driver based on user configuration
📌  Using Docker driver with root privileges
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.51 ...
💾  Downloading Kubernetes v1.37.0 preload ...
    > preloaded-images-k8s-v18-v1...:  347.58 MiB / 347.58 MiB  100.00% 3.88 Mi
    > gcr.io/k8s-minikube/kicbase:  507.60 MiB / 507.61 MiB  100.00% 5.39 MiB p
🔥  Creating docker container (CPUs=2, Memory=5000MB) ...
❗  Local proxy ignored: not passing HTTP_PROXY=http://127.0.0.1:10809/ to docker env.
❗  Local proxy ignored: not passing HTTPS_PROXY=http://127.0.0.1:10809/ to docker env.
❗  Local proxy ignored: not passing HTTP_PROXY=http://127.0.0.1:10809/ to docker env.
❗  Local proxy ignored: not passing HTTPS_PROXY=http://127.0.0.1:10809/ to docker env.
🌐  Found network options:
    ▪ HTTP_PROXY=http://127.0.0.1:10809/
❗  You appear to be using a proxy, but your NO_PROXY environment does not include the minikube IP (192.168.49.2).
📘  Please see https://minikube.sigs.k8s.io/docs/handbook/vpn_and_proxy/ for more details
    ▪ HTTPS_PROXY=http://127.0.0.1:10809/
    ▪ NO_PROXY=localhost,127.0.0.0/8,::1
    ▪ HTTP_PROXY=http://127.0.0.1:10809/
    ▪ HTTPS_PROXY=http://127.0.0.1:10809/
    ▪ NO_PROXY=localhost,127.0.0.0/8,::1
❗  Failing to connect to https://registry.k8s.io/ from inside the minikube container
💡  To pull new external images, you may need to configure a proxy: https://minikube.sigs.k8s.io/docs/reference/networking/proxy/
📦  Preparing Kubernetes v1.37.0 on containerd 2.3.4 ...
    ▪ env NO_PROXY=localhost,127.0.0.0/8,::1
🔗  Configuring CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
