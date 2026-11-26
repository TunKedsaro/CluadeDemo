#!/bin/sh
# Generate js/config.js from API_BASE_URL at container start.
set -e
API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api}"
# Allow only a plain URL so the value cannot break out of the JS string.
case "$API_BASE_URL" in
    *[\"\\\ \;\`\$]*) echo "invalid API_BASE_URL" >&2; exit 1 ;;
esac
cat > /usr/share/nginx/html/js/config.js <<JS
// Generated at container start from API_BASE_URL. Do not edit.
export const API_BASE_URL = "${API_BASE_URL}";
JS
echo "config.js: API_BASE_URL=${API_BASE_URL}"
