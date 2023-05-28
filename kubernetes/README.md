Will contain the kubernetes specific parts of hosting my scs_ai repo with docker/kubernetes

#### 22.05.23

1. the plan is to create a kubernetes cluster by hosting three vms for one master and two worker machines
    - trying to setup the environment with kvm
    - configuring the bridge network caused problems with the server connection

#### 23.05.23

1. trying to restore the connection by booting in repair mode
    - tried to restore original network config
    - server still not reachable

2. initializing restore to clean state

#### 24.05.23

1. setting up kvm
2. setting up a vm without gui support
    - ```
        virt-install \
        --name master01 \
        --ram 4096 \
        --disk path=/var/kvm/images/master01.img,size=20 \
        --vcpus 2 \
        --os-variant ubuntu22.04 \
        --network bridge=virbr0 \
        --graphics none \
        --console pty,target_type=serial \
        --location /home/ubuntu-22.04.2-live-server-amd64.iso,kernel=casper/vmlinuz,initrd=casper/initrd \
        --extra-args 'console=ttyS0,115200n8'
      ```
    - set up works but vm has no internet connection

#### 25.05.23

1. fixing internet connection of vms
    - issue seems to be the same as before, adding the vm interface to the bridge gives internet connection
    - docker containers created on the vms have internet access by default and the networking works properly

2. setting up 1 master and 2 worker nodes
    ```
    subnet      192.168.122.0/24
    virbr0      192.168.122.1
    master01    192.168.122.200
    worker01    192.168.122.201
    worker02    192.168.122.202
    ```
    - installed docker and kubernetes on all nodes
    - set the master on worker nodes /etc/hosts `192.168.122.200 kube-master`
    - created snapshots of vms with `virsh snapshot-create-as <vm> initial --description "<vm> docker and k8s"`
     - to revert to snapshots:
     `virsh snapshot-revert master01 initial`
     `virsh snapshot-revert master01 --current`

#### 26.05.23

1. setting up kubernetes cluster on master node 
    - `sudo kubeadm init --control-plane-endpoint kube-master:6443 --pod-network-cidr 192.168.122.0/23`
    - correction: 25.05: all nodes need to set /etc/hosts `192.168.122.200 kube-master` not just worker nodes
    - set up works after correcting that mistake
2. setting up network
    - using calico E `curl https://raw.githubusercontent.com/projectcalico/calico/v3.25.1/manifests/calico.yaml -O`
    - setting CALICO_IPV4POOL_CIDR to 192.168.122.0/24

#### 27.05.23

1. finishing the network setup
    - kubectl cannot reach localhost
2. fixing the localhost error
    - ports are open, still doesn't work
    - firewall enabled/disabled doesn't work
    - other subnet configs (ie calico default) doesn't work

#### 28.05.23

1. still working on localhost error
    - kubectl can reach localhost but only after initializing, after like a minute it stops working
    - TZ synced, still doesn't work

2. resetting the whole set up
    - creating snapshots after each installation+configuration to debug
    - testing different network plugins, subnets, installing components one by one according to k8s documentation, different host vms, etc.

3. cluster stable after doing the following
    - disable swap `sudo swapoff -a`
    - disable swap in /etc/fstab `sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab`
    - delete swap files `cat /proc/swaps`
    - install docker `sudo apt-get install docker.io`
    - install cri-dockerd: https://github.com/Mirantis/cri-dockerd
    - install kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
    - install kubeadm: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/#installing-runtime
    - initialize a cluster:
    - ```
      sudo kubeadm init --control-plane-endpoint=192.168.122.200 \
      --pod-network-cidr=192.168.122.0/24 \
      --apiserver-advertise-address=192.168.122.200 \
      --cri-socket=unix:///var/run/cri-dockerd.sock
      ```
    - set user-variables to use kubectl
    - download the network-plugin (flannel) yaml: https://github.com/flannel-io/flannel/blob/master/Documentation/kube-flannel.yml
    - change network under `net-conf.json` to the correct pod-network-cidr used
    - apply network-plugin `kubectl apply -f kube-flannel.yml`
 `kubectl get nodes --all-namespaces` shows components starting, after all components are up `kubectl get nodes` shows the cluster is ready
