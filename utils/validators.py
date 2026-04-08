from __future__ import annotations

from pathlib import Path
from typing import Any

from config import MAX_UPLOAD_SIZE_MB



def get_extension(name: str) -> str:
    return Path(name).suffix.lower().lstrip(".")



def validate_extension(file_name: str, allowed_extensions: set[str]) -> None:
    extension = get_extension(file_name)
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise ValueError(f"Arquivo inválido. Use um dos formatos aceitos: {allowed}.")



def validate_upload_size(file_obj: Any) -> None:
    size_bytes = getattr(file_obj, "size", None)
    if size_bytes is None:
        return
    limit_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > limit_bytes:
        raise ValueError(
            f"O arquivo excede o limite recomendado de {MAX_UPLOAD_SIZE_MB} MB para o app."
        )
