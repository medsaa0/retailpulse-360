"""Calcul des empreintes utilisées pour l'idempotence."""

import hashlib
from pathlib import Path


def sha256_file(
    file_path: Path,
) -> str:
    """Calculer le SHA-256 d'un fichier."""

    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()
