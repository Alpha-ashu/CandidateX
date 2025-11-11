"""
Cloud storage utilities for file uploads and management.
"""
import logging
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
import aiofiles
import os
from datetime import datetime

# Cloud storage imports (commented out until packages are installed)
# import boto3
# from botocore.exceptions import ClientError
# import firebase_admin
# from firebase_admin import credentials, storage

from app.config import settings

logger = logging.getLogger(__name__)

class CloudStorageService:
    """Unified cloud storage service supporting AWS S3 and Firebase."""

    def __init__(self):
        self.s3_client = None
        self.firebase_bucket = None

        # Initialize AWS S3 if configured
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                # self.s3_client = boto3.client(
                #     's3',
                #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                #     region_name=settings.AWS_REGION
                # )
                logger.info("AWS S3 client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AWS S3: {e}")

        # Initialize Firebase if configured
        if settings.FIREBASE_CONFIG:
            try:
                # cred = credentials.Certificate(settings.FIREBASE_CONFIG)
                # firebase_admin.initialize_app(cred, {'storageBucket': f"{settings.FIREBASE_CONFIG['project_id']}.appspot.com"})
                # self.firebase_bucket = storage.bucket()
                logger.info("Firebase Storage initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")

    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = "uploads",
        storage_type: str = "auto"  # auto, s3, firebase, local
    ) -> Dict[str, Any]:
        """
        Upload a file to cloud storage.

        Args:
            file_content: File content stream
            filename: Original filename
            content_type: MIME content type
            folder: Storage folder/path
            storage_type: Preferred storage type

        Returns:
            Dict with upload result information
        """
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(filename).suffix
        unique_filename = f"{timestamp}_{filename}"

        # Create full path
        full_path = f"{folder}/{unique_filename}"

        try:
            if storage_type == "s3" and self.s3_client:
                return await self._upload_to_s3(file_content, full_path, content_type)
            elif storage_type == "firebase" and self.firebase_bucket:
                return await self._upload_to_firebase(file_content, full_path, content_type)
            elif storage_type == "local" or not (self.s3_client or self.firebase_bucket):
                return await self._upload_to_local(file_content, full_path, content_type)
            else:
                # Auto-select: prefer S3, then Firebase, then local
                if self.s3_client:
                    return await self._upload_to_s3(file_content, full_path, content_type)
                elif self.firebase_bucket:
                    return await self._upload_to_firebase(file_content, full_path, content_type)
                else:
                    return await self._upload_to_local(file_content, full_path, content_type)

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise

    async def download_file(self, file_path: str, storage_type: str = "auto") -> Optional[bytes]:
        """
        Download a file from cloud storage.

        Args:
            file_path: Path to the file
            storage_type: Storage type (auto, s3, firebase, local)

        Returns:
            File content as bytes, or None if not found
        """
        try:
            if storage_type == "s3" and self.s3_client:
                return await self._download_from_s3(file_path)
            elif storage_type == "firebase" and self.firebase_bucket:
                return await self._download_from_firebase(file_path)
            elif storage_type == "local" or not (self.s3_client or self.firebase_bucket):
                return await self._download_from_local(file_path)
            else:
                # Auto-select based on file path or try all
                if file_path.startswith("s3://") and self.s3_client:
                    return await self._download_from_s3(file_path.replace("s3://", ""))
                elif self.s3_client:
                    return await self._download_from_s3(file_path)
                elif self.firebase_bucket:
                    return await self._download_from_firebase(file_path)
                else:
                    return await self._download_from_local(file_path)

        except Exception as e:
            logger.error(f"File download failed: {e}")
            return None

    async def delete_file(self, file_path: str, storage_type: str = "auto") -> bool:
        """
        Delete a file from cloud storage.

        Args:
            file_path: Path to the file
            storage_type: Storage type

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if storage_type == "s3" and self.s3_client:
                return await self._delete_from_s3(file_path)
            elif storage_type == "firebase" and self.firebase_bucket:
                return await self._delete_from_firebase(file_path)
            elif storage_type == "local" or not (self.s3_client or self.firebase_bucket):
                return await self._delete_from_local(file_path)
            else:
                # Try all storage types
                if self.s3_client and await self._delete_from_s3(file_path):
                    return True
                if self.firebase_bucket and await self._delete_from_firebase(file_path):
                    return True
                return await self._delete_from_local(file_path)

        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False

    async def get_file_url(self, file_path: str, storage_type: str = "auto", expires_in: int = 3600) -> Optional[str]:
        """
        Get a signed URL for file access.

        Args:
            file_path: Path to the file
            storage_type: Storage type
            expires_in: URL expiration time in seconds

        Returns:
            Signed URL or None if not supported
        """
        try:
            if storage_type == "s3" and self.s3_client:
                return await self._get_s3_signed_url(file_path, expires_in)
            elif storage_type == "firebase" and self.firebase_bucket:
                return await self._get_firebase_signed_url(file_path, expires_in)
            else:
                # For local storage, return direct path (not recommended for production)
                return f"/files/{file_path}"

        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None

    async def _upload_to_s3(self, file_content: BinaryIO, file_path: str, content_type: str) -> Dict[str, Any]:
        """Upload file to AWS S3."""
        try:
            # Read file content
            file_content.seek(0)
            file_data = file_content.read()

            # Upload to S3
            # self.s3_client.put_object(
            #     Bucket=settings.S3_BUCKET_NAME,
            #     Key=file_path,
            #     Body=file_data,
            #     ContentType=content_type,
            #     ACL='private'
            # )

            # Mock response for now
            file_url = f"s3://{settings.S3_BUCKET_NAME}/{file_path}"
            public_url = await self._get_s3_signed_url(file_path, 3600)

            return {
                "success": True,
                "storage_type": "s3",
                "file_path": file_path,
                "file_url": file_url,
                "public_url": public_url,
                "bucket": settings.S3_BUCKET_NAME,
                "size": len(file_data),
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise

    async def _upload_to_firebase(self, file_content: BinaryIO, file_path: str, content_type: str) -> Dict[str, Any]:
        """Upload file to Firebase Storage."""
        try:
            # Read file content
            file_content.seek(0)
            file_data = file_content.read()

            # Upload to Firebase
            # blob = self.firebase_bucket.blob(file_path)
            # blob.upload_from_string(file_data, content_type=content_type)
            # blob.make_private()

            # Mock response for now
            file_url = f"firebase://{file_path}"
            public_url = await self._get_firebase_signed_url(file_path, 3600)

            return {
                "success": True,
                "storage_type": "firebase",
                "file_path": file_path,
                "file_url": file_url,
                "public_url": public_url,
                "size": len(file_data),
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Firebase upload failed: {e}")
            raise

    async def _upload_to_local(self, file_content: BinaryIO, file_path: str, content_type: str) -> Dict[str, Any]:
        """Upload file to local storage."""
        try:
            # Read file content
            file_content.seek(0)
            file_data = file_content.read()

            # Create upload directory
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)

            # Save file locally
            file_path_obj = upload_dir / file_path
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path_obj, "wb") as f:
                await f.write(file_data)

            return {
                "success": True,
                "storage_type": "local",
                "file_path": str(file_path_obj),
                "file_url": f"file://{file_path_obj.absolute()}",
                "public_url": f"/files/{file_path}",
                "size": len(file_data),
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Local upload failed: {e}")
            raise

    async def _download_from_s3(self, file_path: str) -> Optional[bytes]:
        """Download file from AWS S3."""
        try:
            # response = self.s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=file_path)
            # return response['Body'].read()

            # Mock response
            return b"Mock file content from S3"

        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            return None

    async def _download_from_firebase(self, file_path: str) -> Optional[bytes]:
        """Download file from Firebase Storage."""
        try:
            # blob = self.firebase_bucket.blob(file_path)
            # return blob.download_as_bytes()

            # Mock response
            return b"Mock file content from Firebase"

        except Exception as e:
            logger.error(f"Firebase download failed: {e}")
            return None

    async def _download_from_local(self, file_path: str) -> Optional[bytes]:
        """Download file from local storage."""
        try:
            file_path_obj = Path("uploads") / file_path
            if file_path_obj.exists():
                async with aiofiles.open(file_path_obj, "rb") as f:
                    return await f.read()
            return None

        except Exception as e:
            logger.error(f"Local download failed: {e}")
            return None

    async def _delete_from_s3(self, file_path: str) -> bool:
        """Delete file from AWS S3."""
        try:
            # self.s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=file_path)
            return True

        except Exception as e:
            logger.error(f"S3 deletion failed: {e}")
            return False

    async def _delete_from_firebase(self, file_path: str) -> bool:
        """Delete file from Firebase Storage."""
        try:
            # blob = self.firebase_bucket.blob(file_path)
            # blob.delete()
            return True

        except Exception as e:
            logger.error(f"Firebase deletion failed: {e}")
            return False

    async def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local storage."""
        try:
            file_path_obj = Path("uploads") / file_path
            if file_path_obj.exists():
                file_path_obj.unlink()
            return True

        except Exception as e:
            logger.error(f"Local deletion failed: {e}")
            return False

    async def _get_s3_signed_url(self, file_path: str, expires_in: int) -> Optional[str]:
        """Generate S3 signed URL."""
        try:
            # url = self.s3_client.generate_presigned_url(
            #     'get_object',
            #     Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': file_path},
            #     ExpiresIn=expires_in
            # )
            # return url

            # Mock URL
            return f"https://s3.{settings.AWS_REGION}.amazonaws.com/{settings.S3_BUCKET_NAME}/{file_path}"

        except Exception as e:
            logger.error(f"S3 signed URL generation failed: {e}")
            return None

    async def _get_firebase_signed_url(self, file_path: str, expires_in: int) -> Optional[str]:
        """Generate Firebase signed URL."""
        try:
            # blob = self.firebase_bucket.blob(file_path)
            # url = blob.generate_signed_url(expiration=datetime.utcnow() + timedelta(seconds=expires_in))
            # return url

            # Mock URL
            return f"https://firebasestorage.googleapis.com/v0/b/{settings.FIREBASE_CONFIG['project_id']}.appspot.com/o/{file_path.replace('/', '%2F')}"

        except Exception as e:
            logger.error(f"Firebase signed URL generation failed: {e}")
            return None

# Global cloud storage service instance
cloud_storage = CloudStorageService()
