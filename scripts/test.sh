#!/bin/sh
set -eu

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
grep -q 'Information Commissioner' public/privacy.html
grep -q 'OVHcloud' public/privacy.html
grep -q 'UK.*adequacy regulations' public/privacy.html
grep -q 'does not set cookies' public/cookies.html
! grep -q 'fonts.googleapis.com' public/index.html
grep -q 'listen 5000' nginx.conf
echo "Static checks passed."
