"""Connexion Snowflake utilisée par RetailPulse 360."""

from __future__ import annotations

from typing import Any

import snowflake.connector
from snowflake.connector import SnowflakeConnection

from ingestion.common.settings import get_settings


def connection_parameters(
    include_context: bool = True,
) -> dict[str, Any]:
    """Construire les paramètres de connexion Snowflake."""

    settings = get_settings()

    if not settings.snowflake_account:
        raise ValueError(
            "SNOWFLAKE_ACCOUNT n'est pas configuré."
        )

    if not settings.snowflake_user:
        raise ValueError(
            "SNOWFLAKE_USER n'est pas configuré."
        )

    if (
        settings.snowflake_authenticator == "snowflake"
        and not settings.snowflake_password
    ):
        raise ValueError(
            "SNOWFLAKE_PASSWORD n'est pas configuré."
        )

    parameters: dict[str, Any] = {
        "account": settings.snowflake_account,
        "user": settings.snowflake_user,
        "role": settings.snowflake_role,
        "authenticator": settings.snowflake_authenticator,
        "session_parameters": {
            "QUERY_TAG": "retailpulse-360",
        },
    }

    if settings.snowflake_password:
        parameters["password"] = (
            settings.snowflake_password
        )

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
        **connection_parameters(
            include_context=include_context
        )
    )
