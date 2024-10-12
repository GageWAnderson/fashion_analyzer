from minio import Minio
from pydantic import BaseModel

from crawler.config.config import config


class MinioResponse(BaseModel):
    bucket_name: str
    file_name: str
    url: str


def get_minio_client():
    minio_url = f"{config.minio_host}:{config.minio_port}"
    return Minio(
        endpoint=minio_url,
        access_key=config.minio_backend_user,
        secret_key=config.minio_backend_password,
        secure=True,
    )
