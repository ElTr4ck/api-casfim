"""Descubrimiento y descarga de los PDF del catálogo SHCP.

La página índice de gob.mx está protegida por un challenge anti-bot, por lo que
el scraping del HTML puede fallar. La estrategia es:

1. Intentar scrapear el índice para descubrir las URLs vigentes de cada sector
   (los archivos se llaman ``sectorNN.pdf``, así que el número de sector se
   deduce del nombre del archivo).
2. Si el índice está bloqueado, usar las URLs conocidas en ``config.FALLBACK_PDF_URLS``.

Los PDF en ``/cms/uploads/`` sí son descargables directamente.
"""

from __future__ import annotations

import re
import urllib.request

from . import config

# Enlaces tipo .../file/123456/sector40.pdf
_PDF_LINK_RE = re.compile(
    r"https://www\.gob\.mx/cms/uploads/attachment/file/\d+/sector(\d+)\.pdf",
    re.IGNORECASE,
)


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=config.HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=config.HTTP_TIMEOUT) as resp:
        return resp.read()


def descubrir_urls() -> dict[int, str]:
    """Devuelve un mapa sector -> URL del PDF.

    Intenta scrapear el índice; si falla o no encuentra los sectores deseados,
    completa con las URLs de respaldo.
    """
    urls: dict[int, str] = {}
    try:
        html = _http_get(config.CATALOGO_URL).decode("utf-8", "ignore")
        for match in _PDF_LINK_RE.finditer(html):
            sector = int(match.group(1))
            if sector in config.SECTORES:
                urls[sector] = match.group(0)
    except Exception:
        # El índice está bloqueado o caído; se usará el fallback.
        pass

    # Completa cualquier sector faltante con la URL conocida.
    for sector, url in config.FALLBACK_PDF_URLS.items():
        urls.setdefault(sector, url)

    return urls


def descargar_pdf(url: str) -> bytes:
    """Descarga el PDF y valida que efectivamente sea un PDF."""
    data = _http_get(url)
    if not data.startswith(b"%PDF"):
        raise ValueError(f"El recurso en {url} no es un PDF (posible challenge anti-bot).")
    return data
