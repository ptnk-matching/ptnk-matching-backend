"""AWS S3 service for file storage."""
import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import uuid
from datetime import datetime


class S3Service:
    """Service for uploading files to AWS S3."""
    
    def __init__(self):
        """Initialize S3 service."""
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            raise ValueError(
                "AWS credentials not configured. "
                "Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_S3_BUCKET_NAME"
            )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        file_type: str
    ) -> tuple[str, str]:
        """
        Upload file to S3.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            user_id: User ID who uploaded
            file_type: File extension (pdf, docx, etc.)
        
        Returns:
            Tuple of (s3_url, s3_key)
        """
        # Generate unique key
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        s3_key = f"test/{user_id}/{timestamp}_{unique_id}_{filename}"
        
        # Determine content type
        content_type_map = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'txt': 'text/plain'
        }
        content_type = content_type_map.get(file_type.lower(), 'application/octet-stream')
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'user_id': user_id,
                    'uploaded_at': timestamp
                }
            )
            
            # Generate URL
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            
            return s3_url, s3_key
        
        except ClientError as e:
            raise Exception(f"Error uploading file to S3: {str(e)}")
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            print(f"Error deleting file from S3: {str(e)}")
            return False
    
    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for file access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")

