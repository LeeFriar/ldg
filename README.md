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

For the `dev` branch, use `LDG_CONTAINER_NAME=dev-ldg LDG_DATA_VOLUME=dev-ldg-data` when running the Compose wrapper. Jenkins handles naming and storage automatically: `dev` deploys as `dev-ldg` with `dev-ldg-data`, while `main` deploys as `ldg` with `ldg-data`. Both containers can run simultaneously because neither publishes port 5000 on the host. The development service is reachable from a shared Docker network at `http://dev-ldg:5000`.

## Gallery and customer feedback

The private admin page is available at `/admin`. Set `ADMIN_USERNAME` and a strong `ADMIN_PASSWORD` in Jenkins; if either is missing, admin access is disabled. Set `PUBLIC_BASE_URL` to the public address for the deployed branch so generated customer links use the correct hostname.

Admins can upload JPEG, PNG or WebP work photos up to 12 MB. The application strips image metadata, creates a small WebP thumbnail for the gallery, and serves the larger detail image only after a visitor selects a photo. Gallery images and feedback are stored in the branch-specific Docker volume.

For each completed job, the admin can generate a single-use customer feedback link. Links expire after seven days. The form does not ask for a name or email address. Submitted feedback is private until an admin approves it for display. Only a hash of the link token is stored in the database.

Admin and feedback forms use HMAC-protected CSRF tokens. Admin authentication is rate limited per client: five failed attempts trigger a one-minute lockout shared across application workers. User text is normalized, length-limited and rendered only through auto-escaped templates or browser `textContent`.

## Deployment

`Jenkinsfile` runs static checks, builds and smoke-tests the image, then deploys both `dev` and `main` directly with Docker. Health checks run inside each container, so deployment does not require a host port. Direct container replacement avoids the `ContainerConfig` recreation bug in legacy Docker Compose 1.29 while still attaching both required networks. The included Compose wrapper remains available for local operation and supports both the modern `docker compose` plugin and legacy `docker-compose`. Configure the GitHub repository webhook to point to:

```text
https://YOUR-JENKINS-HOST/github-webhook/
```

The Jenkins worker needs Docker and Docker Compose access. Configure `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `PUBLIC_BASE_URL` as Jenkins environment variables or credentials. Both deployed containers join `lee-net` and `lee-net-1`.
