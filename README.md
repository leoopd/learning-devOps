# This is for documentation purposes


# Deploying Apps in Kubernetes

### Introduction

The goal of the project is to host a previously developed app [scsai](https://github.com/leoopd/scs_ai) as well as a code-server instance as a deployment in a Kubernetes cluster. The apps should be reachable from https://www.ler0y.com/scsai and https://www.ler0y.com/code respectively. The code-server has an integrated login functionality, the scsai app will use basic auth.  

### Table of contents
 - [Docker](#docker)  
    * [Installing the latest Docker Engine](#installing-the-latest-docker-engine)
    * [Prerequisites](#prerequisites)
    * [Dockerfile](#dockerfile)
    * [Building the image](#building-the-image)
    * [Running the container](#running-the-container)
    * [Docker compose](#docker-compose)
    * [Publishing the image on Docker Hub](#publishing-the-image-on-docker-hub) 
 - [Kubernetes](#kubernetes)  
    * [Setting up VMs](#setting-up-vms)
    * [Installing Kubernetes](#installing-kubernetes)
    * [Setting up the cluster](#setting-up-the-cluster)
    * [Creating a deployment](#creating-a-deployment)
    * [Exposing the deployment](#exposing-the-deployment)
    * [Reverse proxy and basic auth](#reverse-proxy-and-basic-auth)
    * [SSL cert](#ssl-cert)

## Challenges

### Network bridge-interfaces

By default, interfaces like veth's created for containers don't get added to their respective bridges like *docker0* that handles forwarding traffic from containers in Dockers default network *bridge*.  
To work around this issue, interfaces can be manually added to their bridge with `brctl addif <bridge> <interface>`.  
The bridge will start, but not get an IPv4 address. To fix this and give containers internet access, assign the gateway IP, for example the gateway IP of Docker's *bridge* network to the bridge *docker0* with  
`sudo ip addr add <ip>/<cidr> dev <bridge>`

## Docker

The container runtime of choice in this case is docker. Resulting images will be available on Docker Hub to be used by the Kubernetes deployment later on.

### Installing the latest Docker Engine

**Prerequisites**  
Create a user with sudo access and switch to it
  ```console
  sudo adduser <username>
  usermod -aG sudo <username>
  su - <username>
  ```
\
Delete conflicting packages
```console
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done
```
\
Usual workflow of updating the machine prior to installing new software
```console
sudo apt-get update && sudo apt-get upgrade
```
\
Allow the usage of repositories over HTTPS
```console
sudo apt-get install ca-certificates curl gnupg
```
\
Add Docker's official GPG key
```console
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```
\
Set up the repository
```console
echo \
"deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
"$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
\
**Install and test Docker Engine**
```console
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run hello-world
```
\
**Post installation**  
Create Docker group and add the current user to it to run docker commands without sudo
```console
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
``` 
\
Enable Docker
```console
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

### Prerequisites

**Build environment for the Dockerfile**  
Create a file containing the openai api-key as an env variable
```console
cd ~
nano env-file.txt
```
Add your key in the format `OPENAI_API_KEY="<key>"`  
  
Create a directory containing the code necessary to run the app and create a venv  
*I am using my previously developed scsai app as mentioned in the beginning, so I'm simply forking the repo*
```console
mkdir <project-name>
cd <project-name>

sudo apt-get update
sudo apt install pip

pip install virtualenv
python -m venv <venv-name>
```
  
Install everything needed to run your app  
Freeze setup in requirements.txt
```console
python -m pip freeze >> requirements.txt
```

### Dockerfile

The Dockerfile contains all the steps necessary to set up the container environment.  
  
Set the base image
```console
# syntax=docker/dockerfile:1
FROM python:3.10.6
```
  
Create a workdir, copy over requirements and install them
```console
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
```
  
Copy the context and run the app
```console
COPY . .
CMD ["python3", "-m", "flaskapp"]
```

### Building the image

Since we're only building the image to debug the app and upload it to Docker Hub, we don't need to worry about proper networking at this point.  
We will use the `--network=host` tag to use the host's network.
  
Make sure you're in the same directory as the Dockerfile and run  
`docker build --network=host --tag=scsai .`  
This creates an image *scsai:latest* and sets the openai api-key from the txt created previously

### Running the container

We're making sure that the app runs as expected. Get a container up and running and connect to it. The container will forward to a port on the host, since we're using its network.\
`docker run -dit --name=test1 --network=host --env-file=~/env-file.txt scsai:latest`  
  
Connect to the app on port 5000 either with a browser or curl `curl http:<host-ip>:5000`  
Reference the containers logs for errors `docker logs <container>`

### Docker compose

When the app works as intended, we can optionally create a docker-compose.yml for the whole setup, including a code-server instance as a base for the kubernetes deployment later on.  
  
Create a *.env* file at the root of the directory you work in (don't forget to also create a *gitignore* file if you plan on publishing your project on GitHub) and add your openai api-key as well as the password used to log into code-server to it in the format
```console
OPENAI_API_KEY="<key>"
PASSWORD="<password>"
```
  
Create a file called docker-compose.yml and add the following contents
```console
---
version: "2.1"
services:
  code-server:
    image: lscr.io/linuxserver/code-server:latest
    container_name: code-server
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/London
      - PASSWORD=${PASSWORD}
    volumes:
      - <volume-path>
    ports:
      - 8443:8443
    network_mode: host
    restart: unless-stopped
  scsai:
    image: scs-ai:latest
    container_name: scsai-server
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - <volume-path>
    ports:
      - 8000:5000
    network_mode: host
    restart: unless-stopped
```
Don't forget to set *volume-path* accordingly to your setup if you want to use volumes.  
Docker will reference the password for code-server and the api-key for scsai from the *.env* file we created earlier.
  
### Publishing the image on Docker Hub

After making sure that the app works as intended, we can publish our image on Docker Hub to import it into our Kubernetes cluster later on.  
  
By convention, we add our username in front of the image and push it to Docker Hub
```console
docker tag scsai:latest ler0y/scsai:latest
docker image push ler0y/scsai:latest
```

## Kubernetes

### Setting up VMs

To set up our three VMs, we need to virtualize our server, plan our cluster and initialize it.  
We will use KVM ato virtualize the machine, virt-install to run the VMs and virsh to manage them.
```console
sudo apt-get update && sudo apt-get upgrade
sudo apt install qemu-kvm libvirt-daemon-system virtinst libvirt-clients bridge-utils
```
  
Enable libvirt
```console
sudo systemctl enable libvirtd
sudo systemctl start libvirtd
sudo systemctl status libvirtd
```
  
Add the current user to the kvm and the libvirt group to run respective commands
```console
sudo usermod -aG kvm $USER
sudo usermod -aG libvirt $USER
```
Log out and back in to the user to apply changes.  
  
We will now set up the three VMs needed to run the Kubnetes cluster. The VMs will use the default bridge *virbr0* and get assigned a static IP.  
| Name     | CPU | RAM  | DISK | IP              |
|----------|-----|------|------|-----------------|
| master01 | 2   | 4096 | 40   | 192.168.122.200 |
| worker01 | 2   | 4096 | 40   | 192.168.122.201 |
| worker02 | 2   | 4096 | 40   | 192.168.122.202 |

```console
virt-install \
--name master01 \
--ram 4096 \
--disk path=/var/kvm/images/master01.img,size=40 \
--vcpus 2 \
--os-variant ubuntu22.04 \
--network bridge=virbr0 \
--graphics none \
--console pty,target_type=serial \
--location /home/ubuntu-22.04.2-live-server-amd64.iso,kernel=casper/vmlinuz,initrd=casper/initrd \
--extra-args 'console=ttyS0,115200n8'
```
After initializing and installing is done, we can start preparing the VMs for kubernetes.

### Installing Kubernetes

Installing Kubernetes comes with a few pitfalls. If we want to use docker as our container runtime, we will have to also install cri-dockerd. Besides thatwe will have to disable swap and make sure our VMs have internet access by adding them to their bridge.  
  
We will start by disabling swap, preparing the VM for new software and installing docker.
```console
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# delete any swapfiles that may be present
cat /proc/swaps

sudo apt-get update && sudo apt-get upgrade
sudo apt-get install docker.io
```
  
After that we need to install cri-dockerd to make sure that our container runtime works as intended
```console
git clone https://github.com/Mirantis/cri-dockerd.git

wget https://storage.googleapis.com/golang/getgo/installer_linux
chmod +x ./installer_linux
./installer_linux
source ~/.bash_profile

cd cri-dockerd
mkdir bin
go build -o bin/cri-dockerd
mkdir -p /usr/local/bin
sudo install -o root -g root -m 0755 bin/cri-dockerd /usr/local/bin/cri-dockerd
sudo cp -a packaging/systemd/* /etc/systemd/system
sudo sed -i -e 's,/usr/bin/cri-dockerd,/usr/local/bin/cri-dockerd,' /etc/systemd/system/cri-docker.service

sudo daemon-reload
sudo enable cri-docker.service
sudo enable --now cri-docker.socket
```
  
The prerequisites are now installed and we can install kubectl to manage the cluster later on and interact with it's resources.
```console
sudo apt-get update
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```
  
After that we are ready to install kubeadm
```console
# Prerequisites
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl

curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
| sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-archive-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" \
| sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```
We marked kubelet, kubeadm and kubectl with hold since updating them requires additional care.

### Setting up the cluster

After that lengthy installation we're finally ready to initialize our cluster.  
I like to pull the config images prior to running `sudo kubeadm init`
```console
kubeadm config images pull

sudo kubeadm init --control-plane-endpoint=192.168.122.200 \
--pod-network-cidr=10.244.0.0/16 \
--apiserver-advertise-address=192.168.122.200 \
--cri-socket=unix:///var/run/cri-dockerd.sock
```

 - **control-plane** sets the first control-plane node, we can add more later on if we need to
 - **pod-network-cidr** sets the subnet that kubernetes assigns to worker nodes (/24 blocks at a time by default)
 - **apiserver-advertise-address** advertises the api-address
 - **cri-socket** specifies the cri socket we are using
  
After succesfully initializing the cluster, Kubernetes will print some instructions on how to proceed.  
It will give us the functionality to interact with the cluster, join control-plane nodes and join worker nodes.
```console
# To start using your cluster, you need to run the following as a regular user:
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Alternatively, if you are the root user, you can run:
export KUBECONFIG=/etc/kubernetes/admin.conf

# You should now deploy a pod network to the cluster.
kubectl apply -f [podnetwork].yaml

# You can now join any number of control-plane nodes by copying certificate authorities
# and service account keys on each node and then running the following as root:
  kubeadm join 192.168.122.200:6443 --token <token> \
        --discovery-token-ca-cert-hash sha256:<hash> \
        --control-plane

# Then you can join any number of worker nodes by running the following on each as root:
kubeadm join 192.168.122.200:6443 --token <token> \
        --discovery-token-ca-cert-hash sha256:<hash> \
	--cri-socket=unix:///var/run/cri-dockerd.sock
```
  
As Kubernetes suggested, we should proceed by applying a pod network. We will use flannel, other options work too.
```console
https://github.com/flannel-io/flannel/blob/master/Documentation/kube-flannel.yml
kubectl apply -f kube-flannel.yml
```
  
We can now log into our worker nodes and join them to our cluster. Once all pods are started and `kubectl get nodes` shows that our nodes are ready, we can proceed.
```console
kubeadm join 192.168.122.200:6443 --token <token> \
        --discovery-token-ca-cert-hash sha256:<hash> \
	--cri-socket=unix:///var/run/cri-dockerd.sock

kubectl get pods -o wide --all-namespaces
kubetl get nodes
```

### Creating a deployment

When all nodes are ready, we can create our deployments for the scsai app and a code-server instance. We previously used a *.env* file in combination with *.gitignore* to store the env vars needed. Kubernetes gives us the ability to store those in secrets and reference them in the deployment yml.  
We create deployments for the scsai-app and code-sercer instance, we could combine them but seperate files are fine for now.  
  
scsai-deployment.yml
```console
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scsai-deployment
  labels:
    app: scsai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scsai
  template:
    metadata:
      labels:
        app: scsai
    spec:
      containers:
      - name: scsai
        env:
          - name: OPENAI_API_KEY
            valueFrom:
              secretKeyRef:
                key: api-key
                name: api-key
        image: ler0y/scsai:latest
        ports:
        - containerPort: 5000
```
  
code-deployment.yml
```console
apiVersion: apps/v1
kind: Deployment
metadata:
  name: code-server-deployment
  labels:
    app: code-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: code-server
  template:
    metadata:
      labels:
        app: code-server
    spec:
      containers:
      - name: code-server
        env:
          - name: PASSWORD
            valueFrom:
              secretKeyRef:
                key: pw
                name: code-pw
          - name: PUID
            value: "1000"
          - name: PGID
            value: "1000"
          - name: TZ
            value: "Europe/London"
        image: lscr.io/linuxserver/code-server:latest
        ports:
        - containerPort: 8443
```
We could set the secrets as optional, but since the api-key is required and we want to manage access to code-server, we want the secrets anyways. 
```console
kubectl create secret generic api-key --from-literal=api-key="<key>"
kubectl create secret generic code-pw --from-literal=pw="<password>"
```
  
Applying the deployments creates 2 pods running the scsai app and 1 pod running code-server.
```console
kubectl apply -f scsai-deployment.yml
kubectl apply -f code-deployment.yml
```
  
Verify that the pods are running and working as intended. The starting process can take a moment, so maybe check again after a short while.
```console
kubectl get deployments
kubectl get pods -o wide --all-namespaces
kubectl logs <pod-name>
```

### Exposing the deployment

Right now, our services are only available on their respective cluster-ip from inside the cluster. To forward it to our host machine, we need a NodePort service that exposes them on the worker and master nodes.
```console
kubectl expose deployment scsai-deployment --type=NodePort --port=5000
kubectl expose deployment code-server-deployment --type=NodePort --port=8443
```
  
We can check resulting ports with `kubectl get service -o wide`   
Header PORT(S) shows the ports in the format *internal-port:external-port* . We can now reach our deployment from the host machine with
```console
curl http:192.168.122.200:8443
curl http:192.168.122.200:5000
```

### Reverse proxy and basic auth

To reach the internal services from the internet, we need to set up a reverse-proxy that routes connections correctly.   
We will use nginx since it's widely used and easy to set up.
```console
sudo apt-get update
sudo apt-get install nginx
```
  
Disable the default virtual host
```console
sudo unlink /etc/nginx/sites-enabled/default
```
  
Since we want to use basic_auth to manage access to our scsai app, we need to create a password file and reference it in nginx.
```console
# Install  apache2-utils
sudo apt-get update
sudo apt-get install apache2-utils

# create the password file
sudo htpasswd -c /etc/apache2/.htpasswd <username>

# create additional credential pairs
sudo htpasswd /etc/apache2/.htpasswd <username>
```
  
Move to sites-available and create a config for your domain in the format *example-domain.com.conf*
```console
server {
    server_name ler0y.com www.ler0y.com;

    location /code/ {
        auth_basic "Code-Server";
        auth_basic_user_file /etc/apache2/.htpasswd;
        proxy_pass http://192.168.122.200:30781/;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection upgrade;
        proxy_set_header Accept-Encoding gzip;
    }

    location /scsai/ {
        auth_basic "SCS AI APP";
        auth_basic_user_file /etc/apache2/.htpasswd;
        proxy_pass http://192.168.122.200:30335/;
        proxy_redirect off;
        include proxy_params;
    }
}
```
Link the new config, test it and restart nginx to complete the setup.
```console
sudo ln -s /etc/nginx/sites-available/reverse-proxy.conf /etc/nginx/sites-enabled/reverse-proxy.conf

sudo nginx -t
sudo systemctl restart nginx
```
  
Our services are now available on our domain with their respective paths http://example.com/scsai and http://example.com/code

### SSL cert

The last step is to set up an SSL cert so enable HTTPS. We will use a free Let's-Encrypt certificate and automate refreshing it with a cronjob
```console
apt-get update
sudo apt-get install certbot
apt-get install python3-certbot-nginx

sudo certbot --nginx -d example.com -d www.example.com
```
Don't forget to add your domain to the certbot command.  
To automatically refresh the certificate that expires after 90 days, create a cronjob
```console
crontab -e
```
Add `0 12 * * * /usr/bin/certbot renew --quiet` and save the file.  
  
Our services are now available on https://example.com/scsai and https://example.com/code.
