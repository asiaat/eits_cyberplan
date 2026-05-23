mkdir -p zap-reports

docker run --rm --network=host \
  -v "$(pwd)/zap-reports:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
  -t http://localhost:5173 \
  -r zap-portal-20260523_223800.html