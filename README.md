# LDG Electrical

Responsive business website for [www.ldg-electrical.co.uk](https://www.ldg-electrical.co.uk).

## Run locally

The two Docker networks are external and must exist before starting the service:

```sh
docker network create lee-net
docker network create lee-net-1
./scripts/compose.sh up -d --build
```

The site runs in a container named `ldg` at [http://localhost:5000](http://localhost:5000). Its health endpoint is `/health`.

## Deployment

`Jenkinsfile` runs static checks, builds and smoke-tests the image, then deploys `main` directly with Docker. Direct container replacement avoids the `ContainerConfig` recreation bug in legacy Docker Compose 1.29 while still attaching both required networks. The included Compose wrapper remains available for local operation and supports both the modern `docker compose` plugin and legacy `docker-compose`. Configure the GitHub repository webhook to point to:

```text
https://YOUR-JENKINS-HOST/github-webhook/
```

The Jenkins worker needs Docker and Docker Compose access. The production container joins both `lee-net` and `lee-net-1`.
