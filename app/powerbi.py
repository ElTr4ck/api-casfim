"""Cliente PowerBI para obtener SOFOMERs que consolidan / no consolidan con bancos.

La respuesta del API de PowerBI usa el formato DSR (Delta-compressed Semantic
Result). Para este reporte, los datos relevantes están en `ValueDicts`:
  - D0: lista de claves CASFIM (ej. ['068003', '068004', ...])
  - D1: lista de nombres de institución (paralela a D0)
  - D2: nombre del grupo (1 elemento, igual para toda la consulta)

Los índices en las filas (PH) coinciden posicionalmente con D0/D1, por lo que
basta con hacer zip de ambas listas.
"""

from __future__ import annotations

import copy
import threading
import time
import urllib.error
import urllib.request
import json

from . import config


def _payload_configurado() -> dict:
    """Devuelve el PAYLOAD base. Lanza error claro si no fue configurado."""
    try:
        from .powerbi_payload import PAYLOAD
    except ImportError:
        raise RuntimeError("No se encontró app/powerbi_payload.py.")

    if not PAYLOAD:
        raise RuntimeError(
            "El PAYLOAD de PowerBI está vacío. "
            "Pega el JSON del request en app/powerbi_payload.py."
        )
    return PAYLOAD


def _set_grupo(payload: dict, grupo: str) -> dict:
    """Clona el payload y sobreescribe el filtro de Grupo."""
    p = copy.deepcopy(payload)
    where = (
        p["queries"][0]["Query"]["Commands"][0]
        ["SemanticQueryDataShapeCommand"]["Query"]["Where"]
    )
    # El primer filtro del Where corresponde al campo Grupo.
    where[0]["Condition"]["In"]["Values"] = [
        [{"Literal": {"Value": f"'{grupo}'"}}]
    ]
    return p


def _parse_response(resp_json: dict) -> list[dict]:
    """Extrae lista de {clave_casfim, nombre} desde la respuesta DSR de PowerBI."""
    ds = resp_json["results"][0]["result"]["data"]["dsr"]["DS"][0]
    vd = ds["ValueDicts"]
    claves: list[str] = vd["D0"]
    nombres: list[str] = vd["D1"]
    grupo: str = vd["D2"][0]
    return [
        {"clave_casfim": clave, "nombre": nombre, "grupo": grupo}
        for clave, nombre in zip(claves, nombres)
    ]


def _query_powerbi(grupo: str) -> list[dict]:
    payload = _set_grupo(_payload_configurado(), grupo)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        config.POWERBI_URL,
        data=body,
        headers=config.POWERBI_HEADERS,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=config.HTTP_TIMEOUT) as resp:
        return _parse_response(json.loads(resp.read().decode("utf-8")))


# ---------------------------------------------------------------------------
# Caché en memoria
# ---------------------------------------------------------------------------
class SofomerService:
    """Consulta PowerBI y cachea los resultados."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._consolidan: list[dict] = []
        self._no_consolidan: list[dict] = []
        self._loaded_at: float | None = None
        self._error: str | None = None

    def _cache_valido(self) -> bool:
        return (
            self._loaded_at is not None
            and (time.time() - self._loaded_at) < config.POWERBI_CACHE_TTL_SECONDS
            and (bool(self._consolidan) or bool(self._no_consolidan))
        )

    def _recargar(self) -> None:
        self._error = None
        try:
            self._consolidan = _query_powerbi(config.GRUPO_CONSOLIDAN)
            self._no_consolidan = _query_powerbi(config.GRUPO_NO_CONSOLIDAN)
            self._loaded_at = time.time()
        except Exception as exc:
            self._error = str(exc)
            raise

    def asegurar_cargado(self) -> None:
        if self._cache_valido():
            return
        with self._lock:
            if self._cache_valido():
                return
            self._recargar()

    def recargar(self) -> dict:
        with self._lock:
            self._recargar()
        return {
            "consolidan": len(self._consolidan),
            "no_consolidan": len(self._no_consolidan),
        }

    def consolidan(self) -> list[dict]:
        self.asegurar_cargado()
        return self._consolidan

    def no_consolidan(self) -> list[dict]:
        self.asegurar_cargado()
        return self._no_consolidan

    def todas(self) -> list[dict]:
        self.asegurar_cargado()
        return self._consolidan + self._no_consolidan


sofomer_service = SofomerService()
