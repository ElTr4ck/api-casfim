"""Capa de servicio: orquesta scraping + parseo y mantiene un caché en memoria."""

from __future__ import annotations

import threading
import time
import unicodedata

from . import config, scraper
from .parser import parse_sector_pdf


def _normaliza(texto: str) -> str:
    """minúsculas + sin acentos, para comparaciones tolerantes."""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.casefold().strip()


class CatalogoService:
    """Carga, cachea y consulta el catálogo de las tres secciones."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._instituciones: list[dict] = []
        self._pdf_urls: dict[int, str] = {}
        self._errores: dict[int, str] = {}
        self._loaded_at: float | None = None

    # -- carga --------------------------------------------------------------
    def _cache_valido(self) -> bool:
        return (
            self._loaded_at is not None
            and (time.time() - self._loaded_at) < config.CACHE_TTL_SECONDS
            and bool(self._instituciones)
        )

    def asegurar_cargado(self) -> None:
        """Carga el catálogo si el caché expiró o está vacío."""
        if self._cache_valido():
            return
        with self._lock:
            if self._cache_valido():
                return
            self._recargar()

    def recargar(self) -> dict:
        """Fuerza una recarga (ignora el caché). Devuelve un resumen."""
        with self._lock:
            self._recargar()
        return {
            "sectores_cargados": sorted(
                {i["sector"] for i in self._instituciones}
            ),
            "total_instituciones": len(self._instituciones),
            "errores": dict(self._errores),
        }

    def _recargar(self) -> None:
        urls = scraper.descubrir_urls()
        instituciones: list[dict] = []
        errores: dict[int, str] = {}

        for sector in sorted(config.SECTORES):
            url = urls.get(sector)
            if not url:
                errores[sector] = "No se encontró URL del PDF."
                continue
            try:
                pdf_bytes = scraper.descargar_pdf(url)
                num, nombre, registros = parse_sector_pdf(pdf_bytes)
                num = num or sector
                nombre = nombre or config.SECTORES[sector]
                for r in registros:
                    instituciones.append(
                        {
                            **r,
                            "sector": num,
                            "sector_nombre": nombre,
                        }
                    )
            except Exception as exc:  # noqa: BLE001 - se reporta al cliente
                errores[sector] = f"{type(exc).__name__}: {exc}"

        self._instituciones = instituciones
        self._pdf_urls = urls
        self._errores = errores
        self._loaded_at = time.time()

    # -- consultas ----------------------------------------------------------
    def todas(self, sector: int | None = None, estatus: str | None = None) -> list[dict]:
        self.asegurar_cargado()
        data = self._instituciones
        if sector is not None:
            data = [i for i in data if i["sector"] == sector]
        if estatus is not None:
            objetivo = _normaliza(estatus)
            data = [i for i in data if _normaliza(i["estatus"]) == objetivo]
        return data

    def en_operacion(self) -> list[dict]:
        """Sólo instituciones 'En Operación', vista reducida (clave + nombre)."""
        objetivo = _normaliza(config.ESTATUS_EN_OPERACION)
        return [
            {"clave_casfim": i["clave_casfim"], "nombre_corto": i["nombre_corto"]}
            for i in self.todas()
            if _normaliza(i["estatus"]) == objetivo
        ]

    def por_clave(self, clave: str) -> dict | None:
        # Acepta la clave con o sin guion: "40-012" o "40012".
        clave = clave.strip().replace("-", "")
        for i in self.todas():
            if i["clave_casfim"] == clave:
                return i
        return None

    def estatus_disponibles(self) -> dict[str, int]:
        from collections import Counter

        c = Counter(i["estatus"] for i in self.todas())
        return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))

    def info_sectores(self) -> list[dict]:
        self.asegurar_cargado()
        out = []
        for sector, nombre in sorted(config.SECTORES.items()):
            total = sum(1 for i in self._instituciones if i["sector"] == sector)
            out.append(
                {
                    "sector": sector,
                    "nombre": nombre,
                    "pdf_url": self._pdf_urls.get(sector),
                    "total_instituciones": total,
                    "error": self._errores.get(sector),
                }
            )
        return out


# Instancia única usada por la app.
service = CatalogoService()
