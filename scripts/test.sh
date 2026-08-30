#!/bin/sh
set -eu

test -f app.py
test -f requirements.txt
test -f templates/admin.html
test -f templates/feedback.html
test -f public/work/thumb/kitchen-electrical-accessories.webp
test -f public/work/detail/kitchen-electrical-accessories.webp
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
grep -q '/work/thumb/kitchen-electrical-accessories.webp' public/index.html
grep -q 'data-gallery-detail' public/index.html
grep -q 'id="gallery-previous"' public/index.html
grep -q 'id="gallery-next"' public/index.html
grep -q 'grid-auto-columns:calc((100% - 42px)/4)' public/styles.css
! grep -q 'id="feedback"' public/index.html
! grep -q 'feedback-grid' public/index.html
! grep -q 'loadFeedback' public/script.js
grep -q "loading = 'lazy'" public/script.js
grep -q '/api/gallery' app.py
grep -q 'STATIC_GALLERY' app.py
grep -q 'mimetype="image/webp"' app.py
grep -q '/feedback/<token>' app.py
grep -q 'FEEDBACK_LINK_LIFETIME = timedelta(days=7)' app.py
grep -q 'AUTH_FAILURE_LIMIT = 5' app.py
grep -q 'AUTH_LOCK_SECONDS = 60' app.py
grep -q 'feedback_csrf_token' app.py
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
