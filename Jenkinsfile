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
            when { branch 'main' }
            steps {
                sh '''
                    docker network inspect lee-net >/dev/null 2>&1 || docker network create lee-net
                    docker network inspect lee-net-1 >/dev/null 2>&1 || docker network create lee-net-1
                    ./scripts/compose.sh up -d --remove-orphans
                    docker image prune -f
                '''
            }
        }
        stage('Verify') {
            when { branch 'main' }
            steps { sh 'wget -qO- http://127.0.0.1:5000/health | grep -q healthy' }
        }
    }
}
