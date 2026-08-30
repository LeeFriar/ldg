#!/bin/sh
set -eu

test -f app.py
test -f requirements.txt
test -f templates/admin.html
test -f templates/feedback.html
test -f public/index.html
test -f public/styles.css
test -f public/brand/favicon.ico
test -f public/privacy.html
test -f public/cookies.html
test -x scripts/compose.sh || chmod +x scripts/compose.sh
grep -q 'Lloyd Garland' public/index.html
grep -q 'lloyd@ldg-electrical.co.uk' public/index.html
grep -q 'tel:+447587869215' public/index.html
! grep -R -q '07342 832300\|+447342832300' public
grep -q 'https://www.ldg-electrical.co.uk/' public/index.html
grep -q '<span><b>NVQ</b> Level 3</span><span><b>ECS</b> Gold Card</span><span><b>18th</b> Edition</span>' public/index.html
grep -q 'id="work"' public/index.html
grep -q 'id="feedback"' public/index.html
grep -q "loading = 'lazy'" public/script.js
grep -q '/api/gallery' app.py
grep -q '/feedback/<token>' app.py
grep -q 'Information Commissioner' public/privacy.html
grep -q 'OVHcloud' public/privacy.html
grep -q 'UK.*adequacy regulations' public/privacy.html
grep -q 'does not set cookies' public/cookies.html
! grep -q 'fonts.googleapis.com' public/index.html
grep -q 'deploy_container=dev-ldg' Jenkinsfile
grep -q 'deploy_container=ldg' Jenkinsfile
grep -q 'data_volume=dev-ldg-data' Jenkinsfile
grep -q 'container_name: ${LDG_CONTAINER_NAME:-ldg}' compose.yaml
grep -q 'expose:' compose.yaml
! grep -q -- '-p 5000:5000' Jenkinsfile
! grep -q '5000:5000' compose.yaml
echo "Static checks passed."
