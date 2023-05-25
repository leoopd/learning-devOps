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
