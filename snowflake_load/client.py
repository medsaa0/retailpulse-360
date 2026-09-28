"""Connexion Snowflake utilisée par RetailPulse 360."""

from __future__ import annotations

from typing import Any

import snowflake.connector
from cryptography.hazmat.primitives import serialization
from snowflake.connector import SnowflakeConnection

from ingestion.common.settings import get_settings


def load_private_key_der(path: str) -> bytes:
    """Charger la clé privée RSA et la convertir au format attendu par Snowflake."""

    with open(path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )

    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def connection_parameters(
    include_context: bool = True,
) -> dict[str, Any]:
    """Construire les paramètres de connexion Snowflake."""

    settings = get_settings()

    if not settings.snowflake_account:
        raise ValueError("SNOWFLAKE_ACCOUNT n'est pas configuré.")

    if not settings.snowflake_user:
        raise ValueError("SNOWFLAKE_USER n'est pas configuré.")

    using_key_pair = bool(settings.snowflake_private_key_path)

    if (
        settings.snowflake_authenticator == "snowflake"
        and not settings.snowflake_password
        and not using_key_pair
    ):
        raise ValueError(
            "SNOWFLAKE_PASSWORD ou SNOWFLAKE_PRIVATE_KEY_PATH doit être configuré."
        )

    parameters: dict[str, Any] = {
        "account": settings.snowflake_account,
        "user": settings.snowflake_user,
        "role": settings.snowflake_role,
        "session_parameters": {
            "QUERY_TAG": "retailpulse-360",
        },
    }

    if using_key_pair:
        parameters["private_key"] = load_private_key_der(
            settings.snowflake_private_key_path
        )
    else:
        parameters["authenticator"] = settings.snowflake_authenticator

        if settings.snowflake_password:
            parameters["password"] = settings.snowflake_password

    if include_context:
        parameters.update(
            {
                "warehouse": settings.snowflake_warehouse,
                "database": settings.snowflake_database,
                "schema": settings.snowflake_schema,
            }
        )

    return parameters


def get_connection(
    include_context: bool = True,
) -> SnowflakeConnection:
    """Ouvrir une connexion Snowflake."""

    return snowflake.connector.connect(
        **connection_parameters(include_context=include_context)
    )