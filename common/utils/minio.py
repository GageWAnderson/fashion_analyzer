from datetime import timedelta
from io import BytesIO
import uuid

from common.db.minio import get_minio_client, MinioResponse
from crawler.config.config import config


def minio_presigned_get_object(bucket_name: str, object_name: str) -> str:
    minio_client = get_minio_client()
    return minio_client.presigned_get_object(
        bucket_name,
        object_name,
        expires=timedelta(days=config.minio_presigned_url_expiry_days),
    )


def minio_put_object(file_data: BytesIO, content_type: str) -> MinioResponse:
    """
    Uploads a file to Minio and returns a presigned URL to the file.
    """
    minio_client = get_minio_client()
    file_id = str(uuid.uuid4())
    minio_client.put_object(
        bucket_name=config.minio_bucket,
        object_name=file_id,
        data=file_data,
        length=file_data.getbuffer().nbytes,
        content_type=content_type,
    )
    return MinioResponse(
        bucket_name=config.minio_bucket,
        file_name=file_id,
        url=minio_presigned_get_object(config.minio_bucket, file_id),
    )
