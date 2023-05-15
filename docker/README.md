
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
