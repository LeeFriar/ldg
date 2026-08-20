#!/bin/sh
set -eu

test -f public/index.html
test -f public/styles.css
test -f public/brand/favicon.ico
grep -q 'Lloyd Garland' public/index.html
grep -q 'lloyd@ldg-electrical.co.uk' public/index.html
grep -q 'tel:+447342832300' public/index.html
grep -q 'https://www.ldg-electrical.co.uk/' public/index.html
grep -q 'listen 5000' nginx.conf
echo "Static checks passed."
