# LDG Electrical

Responsive business website for [www.ldg-electrical.co.uk](https://www.ldg-electrical.co.uk).

## Run locally

The two Docker networks are external and must exist before starting the service:

```sh
docker network create lee-net
docker network create lee-net-1
./scripts/compose.sh up -d --build
```

The site runs at [http://localhost:5000](http://localhost:5000). Its health endpoint is `/health`.

For the `dev` branch, use `LDG_CONTAINER_NAME=dev-ldg` when running the Compose wrapper. Jenkins handles naming automatically: `dev` deploys as `dev-ldg`, while `main` deploys as `ldg`. Because both publish host port 5000, deploying one branch replaces the other branch's running container.

## Deployment

`Jenkinsfile` runs static checks, builds and smoke-tests the image, then deploys both `dev` and `main` directly with Docker. Direct container replacement avoids the `ContainerConfig` recreation bug in legacy Docker Compose 1.29 while still attaching both required networks. The included Compose wrapper remains available for local operation and supports both the modern `docker compose` plugin and legacy `docker-compose`. Configure the GitHub repository webhook to point to:

```text
https://YOUR-JENKINS-HOST/github-webhook/
```

The Jenkins worker needs Docker and Docker Compose access. The deployed container joins both `lee-net` and `lee-net-1`.
