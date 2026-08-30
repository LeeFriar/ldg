pipeline {
    agent any
    options { disableConcurrentBuilds(); timestamps() }
    triggers { githubPush() }
    stages {
        stage('Test') {
            steps { sh 'chmod +x scripts/test.sh && ./scripts/test.sh' }
        }
        stage('Build') {
            steps { sh 'chmod +x scripts/compose.sh && ./scripts/compose.sh build --pull' }
        }
        stage('Container test') {
            steps {
                sh '''
                    docker rm -f ldg-test 2>/dev/null || true
                    docker run -d --name ldg-test -p 15000:5000 ldg:latest
                    for i in $(seq 1 15); do
                      wget -qO- http://127.0.0.1:15000/health | grep -q healthy && exit 0
                      sleep 1
                    done
                    exit 1
                '''
            }
            post { always { sh 'docker rm -f ldg-test 2>/dev/null || true' } }
        }
        stage('Deploy') {
            when { anyOf { branch 'main'; branch 'dev' } }
            steps {
                sh '''
                    case "$BRANCH_NAME" in
                      main)
                        deploy_container=ldg
                        other_container=dev-ldg
                        ;;
                      dev)
                        deploy_container=dev-ldg
                        other_container=ldg
                        ;;
                      *)
                        echo "Deployment is not configured for branch: $BRANCH_NAME" >&2
                        exit 1
                        ;;
                    esac

                    docker network inspect lee-net >/dev/null 2>&1 || docker network create lee-net
                    docker network inspect lee-net-1 >/dev/null 2>&1 || docker network create lee-net-1

                    # docker-compose 1.29 cannot recreate images produced by
                    # newer Docker engines (KeyError: ContainerConfig). This
                    # stateless service is replaced directly and predictably.
                    # Only one branch can own host port 5000 at a time.
                    docker rm -f "$deploy_container" 2>/dev/null || true
                    docker rm -f "$other_container" 2>/dev/null || true
                    stale_ids=$(docker ps -aq --filter label=com.docker.compose.service=ldg)
                    if [ -n "$stale_ids" ]; then
                      docker rm -f $stale_ids
                    fi

                    docker run -d \
                      --name "$deploy_container" \
                      --restart unless-stopped \
                      --network lee-net \
                      -p 5000:5000 \
                      ldg:latest
                    docker network connect lee-net-1 "$deploy_container"
                    docker image prune -f
                '''
            }
        }
        stage('Verify') {
            when { anyOf { branch 'main'; branch 'dev' } }
            steps { sh 'wget -qO- http://127.0.0.1:5000/health | grep -q healthy' }
        }
    }
}
