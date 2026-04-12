import json
import os
from functools import lru_cache
from typing import Any


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_service_account_key() -> dict[str, Any] | None:
    key_json = os.environ.get("GEE_PRIVATE_KEY_JSON")
    if key_json:
        return json.loads(key_json)

    key_path = os.environ.get("GEE_PRIVATE_KEY_PATH")
    if key_path and os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as file:
            return json.load(file)

    return None


@lru_cache(maxsize=1)
def get_ee_client() -> tuple[Any | None, str]:
    if _as_bool(os.environ.get("DISABLE_GEE"), default=False):
        return None, "GEE desabilitado por ambiente"

    try:
        import ee
    except Exception:
        return None, "earthengine-api não instalado"

    project_id = os.environ.get("GEE_PROJECT_ID")
    enable_default_auth = _as_bool(os.environ.get("ENABLE_GEE_DEFAULT_AUTH"), default=False)

    try:
        service_account = os.environ.get("GEE_SERVICE_ACCOUNT")
        key_data = _load_service_account_key()
        if service_account and key_data:
            credentials = ee.ServiceAccountCredentials(service_account, key_data=json.dumps(key_data))
            if project_id:
                ee.Initialize(credentials=credentials, project=project_id)
            else:
                ee.Initialize(credentials=credentials)
            return ee, "service_account"

        application_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if application_credentials:
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            return ee, "application_default_credentials"

        if enable_default_auth:
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            return ee, "default_credentials"

        return None, "credenciais do GEE nao configuradas"
    except Exception as error:
        return None, f"falha_gee_init: {error}"


def to_ee_polygon(ee: Any, geometry: dict[str, Any]) -> Any:
    if geometry.get("type") != "Polygon":
        raise ValueError("GEE suporta apenas Polygon neste MVP.")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("Geometria Polygon inválida.")
    return ee.Geometry.Polygon(coordinates)
