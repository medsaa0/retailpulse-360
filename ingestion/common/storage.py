"""Client S3 compatible utilisé pour MinIO."""

from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from ingestion.common.settings import get_settings


class ObjectStorage:
    """Accéder au bucket RAW via l'API S3."""

    def __init__(self) -> None:
        settings = get_settings()

        self.bucket = settings.minio_bucket

        self.client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name="us-east-1",
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path",
                },
            ),
        )

    def ensure_bucket(self) -> None:
        """Créer le bucket lorsqu'il n'existe pas."""

        response = self.client.list_buckets()

        bucket_names = {
            bucket["Name"]
            for bucket in response.get(
                "Buckets",
                [],
            )
        }

        if self.bucket not in bucket_names:
            self.client.create_bucket(Bucket=self.bucket)

    def put_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Envoyer des octets vers MinIO."""

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata=metadata or {},
        )

    def get_bytes(
        self,
        key: str,
    ) -> bytes:
        """Télécharger un objet."""

        response = self.client.get_object(
            Bucket=self.bucket,
            Key=key,
        )

        return response["Body"].read()

    def put_json(
        self,
        key: str,
        payload: dict[str, Any],
    ) -> None:
        """Enregistrer un document JSON."""

        content = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")

        self.put_bytes(
            key=key,
            data=content,
            content_type="application/json",
        )

    def get_json(
        self,
        key: str,
        default: dict[str, Any],
    ) -> dict[str, Any]:
        """Lire un document JSON ou retourner une valeur par défaut."""

        try:
            data = self.get_bytes(key)

        except ClientError as error:
            error_code = str(
                error.response.get(
                    "Error",
                    {},
                ).get(
                    "Code",
                    "",
                )
            )

            if error_code in {
                "NoSuchKey",
                "NoSuchObject",
                "404",
            }:
                return default

            raise

        result = json.loads(data.decode("utf-8"))

        if not isinstance(result, dict):
            raise ValueError(f"L'objet {key} ne contient pas un dictionnaire JSON.")

        return result

    def list_keys(
        self,
        prefix: str = "",
    ) -> list[str]:
        """Lister les objets du bucket."""

        keys: list[str] = []

        continuation_token: str | None = None

        while True:
            parameters: dict[str, Any] = {
                "Bucket": self.bucket,
                "Prefix": prefix,
            }

            if continuation_token is not None:
                parameters["ContinuationToken"] = continuation_token

            response = self.client.list_objects_v2(**parameters)

            keys.extend(
                item["Key"]
                for item in response.get(
                    "Contents",
                    [],
                )
            )

            if not response.get(
                "IsTruncated",
                False,
            ):
                break

            continuation_token = response["NextContinuationToken"]

        return keys
