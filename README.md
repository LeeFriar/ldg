# LDG Electrical

Responsive business website for [www.ldg-electrical.co.uk](https://www.ldg-electrical.co.uk).

## Run locally

The two Docker networks are external and must exist before starting the service:

```sh
docker network create lee-net
docker network create lee-net-1
./scripts/compose.sh up -d --build
```

The container listens on port 5000 only inside Docker. No host port is published. Other containers on `lee-net` or `lee-net-1`, such as a reverse proxy, can reach the production service at `http://ldg:5000`.

For the `dev` branch, use `LDG_CONTAINER_NAME=dev-ldg` when running the Compose wrapper. Jenkins handles naming automatically: `dev` deploys as `dev-ldg`, while `main` deploys as `ldg`. Both containers can run simultaneously because neither publishes port 5000 on the host. The development service is reachable from a shared Docker network at `http://dev-ldg:5000`.

## Deployment

`Jenkinsfile` runs static checks, builds and smoke-tests the image, then deploys both `dev` and `main` directly with Docker. Health checks run inside each container, so deployment does not require a host port. Direct container replacement avoids the `ContainerConfig` recreation bug in legacy Docker Compose 1.29 while still attaching both required networks. The included Compose wrapper remains available for local operation and supports both the modern `docker compose` plugin and legacy `docker-compose`. Configure the GitHub repository webhook to point to:

```text
https://YOUR-JENKINS-HOST/github-webhook/
```

The Jenkins worker needs Docker and Docker Compose access. Both deployed containers join `lee-net` and `lee-net-1`.
