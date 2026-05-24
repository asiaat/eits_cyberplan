mkdir -p zap-reports

TS=$(date +"%Y%m%d_%H%M%S")

docker run --rm --network=host \
  -v "$(pwd)/zap-reports:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
  -t http://localhost:5173 \
  -r "zap-portal-${TS}.html"