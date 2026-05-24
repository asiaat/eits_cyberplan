#!/usr/bin/env bash
set -u

TARGET="${ZAP_TARGET:-http://localhost:9000}"
OUT_DIR="zap-reports"
TS=$(date +"%Y%m%d_%H%M%S")

HTML_REPORT="zap-minio-${TS}.html"
JSON_REPORT="zap-minio-${TS}.json"
MD_REPORT="zap-minio-${TS}.md"

mkdir -p "$OUT_DIR"

echo "Running ZAP baseline scan against: $TARGET"
echo "Reports will be saved in: $OUT_DIR"
echo

docker run --rm --network=host \
  -v "$(pwd)/${OUT_DIR}:/zap/wrk/:rw" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
  -t "$TARGET" \
  -m 2 \
  -r "$HTML_REPORT" \
  -J "$JSON_REPORT" \
  -w "$MD_REPORT"

ZAP_EXIT_CODE=$?

echo
echo "ZAP finished with exit code: $ZAP_EXIT_CODE"
echo "HTML report: $OUT_DIR/$HTML_REPORT"
echo "JSON report: $OUT_DIR/$JSON_REPORT"
echo "Markdown report: $OUT_DIR/$MD_REPORT"

exit "$ZAP_EXIT_CODE"