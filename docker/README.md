
Will contain the docker specific parts of hosting my scs_ai repo with docker/kubernetes

### Progress
#### 13.05.23
set up docker on hostmachine, created and configured docker-compose.yml to make the webui availabe on port 8443
 - not yet reachable via compose, issue seems to lie in the network that is used
   - works via CLI
     ```bash
     docker run -d \
     --name=code-server \
     --network=host \
     -e PUID=1000 \
     -e PGID=1000 \
     -e TZ=Europe/London \
     -e PASSWORD=example \
     -e DEFAULT_WORKSPACE=/example \
     -v /example:/example \
     --restart unless-stopped \
     lscr.io/linuxserver/code-server:latest
     ```

#### 14.05.23
1. docker-compose.yml is reachable 
- if `network_mode: host` is added on code-server-config level

2. ~~trying to make the password via file work~~
   - ~~normal file can't be found by code-server~~
   - ~~seems like the password has to be input via swarm secret, postponed for now~~

3. preparing the env to run the scs_ai flaskapp
   - added the venv, installed required modules and `pip freeze >> requirements.txt`
    - app runs fine

4. added requirements for building the image to docker/scs_ai
   - includes webapp functionality and Dockerfile
   - building the Dockerfile is not working yet, fails on `RUN pip install requirements.txt`
    - the problem seems to be the deafult bridge network, the host network works

#### 15.05.23

_1. added requirements for building the image to docker/scs_ai_
   - _includes webapp functionality and Dockerfile_
   - _building the Dockerfile is not working yet, fails on `RUN pip install requirements.txt`_
   - the problem seems to be the deafult bridge network, the host network works

2. trying to make the app run inside the container
  - issue seems to be the missing env var for the openai key
  - adding the aikey to a file in a different dir allows to set it without exposing the key `docker run -d -p 8000:5000 --env-file ~/env_file.txt --name scsai-test scs-ai:dnsset`

#### 16.05.23

1. containers still without internet connection
 - issue seems to be the docker0 network thats DOWN (`ip link show docker0`)
 - ```
   15: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN mode DEFAULT group default
   link/ether 02:42:46:f1:b5:80 brd ff:ff:ff:ff:ff:ff
   ```
 - `networkctl` looks weird too
 - ```
   IDX LINK            TYPE     OPERATIONAL SETUP
   1 lo              loopback carrier     configured
   2 eno2            ether    no-carrier  configuring
   3 eno1            ether    routable    configured
   15 docker0         bridge   no-carrier  configuring
   18 br-ba1fce2699d3 bridge   no-carrier  configuring
   26 veth6db1def     ether    degraded    configuring
   ```
 - /etc/resolv.conf looks fine
 - testing with different networks with different gateways/subents did not help
 - testing with different dns did not help `docker run dns=8.8.8.8 <img>`, setting resolv.conf inside the container
 - deleting docker0 and restarting docker did not help
 - testing different images, containers etc did not help
 - etc.

#### 17.05.23

1. still testing container internet connection
  - new interfaces do not get added to docker0
  - custom bridge networks did not change anything
  - initialized a reinstall to see if the problem persists

2. setting up docker according to official doc
  - connection problems persist

#### 18.05.23

1. `cat /etc/resolv.conf` inside a container shows some issue
   ```
   search stratoserver.net
   nameserver 127.0.0.11
   options edns0 trust-ad ndots:0
   ```
  - setting the dns by editing daemon () does not work
  - setting dns by adding it to run command does not work
  - if container is inside host network, the dns is set just fine
    ```
    search stratoserver.net
    nameserver 10.1.2.3
    nameserver 8.8.8.8
    options edns0 trust-ad
    ```
