
Will contain the docker specific parts of hosting my scs_ai repo with docker/kubernetes

### Progress
#### 13.05.23
set up docker on hostmachine, created and configured docker-compose.yml to make the webui availabe on port 8443
 - not yet reachable, not sure why
 - - works via CLI (details removed), issue seems to be fixed when using --network=host
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
