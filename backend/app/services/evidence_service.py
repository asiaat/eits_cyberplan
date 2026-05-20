"""Evidence Service - File handling with MinIO storage and duplicate detection."""
import hashlib
import uuid
from datetime import datetime
from typing import Optional, Tuple
from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.evidence import Evidence

settings = get_settings()


class EvidenceService:
    """Service for handling evidence file uploads to MinIO."""

    def __init__(self):
        self.s3_client = None
        self._init_s3_client()

    def _init_s3_client(self):
        """Initialize MinIO/S3 client."""
        config = Config(signature_version='s3')
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=config,
            region_name='us-east-1'
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=settings.MINIO_BUCKET)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=settings.MINIO_BUCKET)
            except Exception:
                pass

    def compute_file_hash(self, file_content: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    def check_duplicate(self, db: Session, file_hash: str, tenant_id: uuid.UUID) -> Optional[Evidence]:
        """Check if file with same hash already exists for this tenant."""
        return db.query(Evidence).filter(
            Evidence.file_hash == file_hash,
            Evidence.tenant_id == tenant_id
        ).first()

    def upload_file(
        self,
        db: Session,
        file_content: bytes,
        filename: str,
        content_type: str,
        title: str,
        evidence_type: str,
        tenant_id: uuid.UUID,
        owner_user_id: Optional[uuid.UUID] = None
    ) -> tuple[Evidence, bool]:
        """
        Upload file to MinIO and create evidence record.

        Returns (evidence, is_new) where is_new indicates if file was new upload
        or duplicate found in system.
        """
        file_hash = self.compute_file_hash(file_content)

        existing = self.check_duplicate(db, file_hash, tenant_id)
        if existing:
            return existing, False

        file_id = str(uuid.uuid4())
        storage_key = f"evidence/{tenant_id}/{file_id}/{filename}"

        try:
            self.s3_client.put_object(
                Bucket=settings.MINIO_BUCKET,
                Key=storage_key,
                Body=file_content,
                ContentType=content_type,
            )
        except Exception as e:
            raise Exception(f"Failed to upload to storage: {str(e)}")

        evidence = Evidence(
            tenant_id=tenant_id,
            title=title,
            evidence_type=evidence_type,
            storage_uri=storage_key,
            file_hash=file_hash,
            owner_user_id=owner_user_id,
            version="1.0",
        )
        db.add(evidence)
        db.flush()

        return evidence, True

    def get_presigned_url(self, storage_uri: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for file download."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.MINIO_BUCKET,
                    'Key': storage_uri
                },
                ExpiresIn=expiration
            )
            return url
        except Exception:
            return None

    def delete_file(self, storage_uri: str) -> bool:
        """Delete file from MinIO storage."""
        try:
            self.s3_client.delete_object(
                Bucket=settings.MINIO_BUCKET,
                Key=storage_uri
            )
            return True
        except Exception:
            return False

    def list_files(self, tenant_id: uuid.UUID) -> list[str]:
        """List all files for a tenant in MinIO."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=settings.MINIO_BUCKET,
                Prefix=f"evidence/{tenant_id}/"
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception:
            return []


def get_evidence_service() -> EvidenceService:
    """Get evidence service instance."""
    return EvidenceService()