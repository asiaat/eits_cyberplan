#!/usr/bin/env python3
"""Backfill file_size and mime_type for existing evidence records from MinIO.

Usage:
    PYTHONPATH=. python scripts/backfill_evidence_stats.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from botocore.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.evidence import Evidence

settings = get_settings()
engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
db = Session()

s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
    config=Config(signature_version="s3"),
    region_name="us-east-1",
)

records = db.query(Evidence).filter(
    Evidence.storage_uri.isnot(None),
    Evidence.file_size.is_(None),
).all()

print(f"Found {len(records)} evidence records to backfill")

for ev in records:
    try:
        resp = s3.head_object(Bucket=settings.MINIO_BUCKET, Key=ev.storage_uri)
        ev.file_size = resp.get("ContentLength")
        ev.mime_type = resp.get("ContentType", "application/octet-stream")
        print(f"  {ev.id}: {ev.file_size} bytes, {ev.mime_type}")
    except Exception as e:
        print(f"  {ev.id}: SKIPPED ({e})")

db.commit()
db.close()
print("Done")
