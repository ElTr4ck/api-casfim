"""Configuración de la API CASFIM."""

from __future__ import annotations

# Página índice del catálogo (la usamos para descubrir las URLs vigentes de los PDF).
CATALOGO_URL = (
    "https://www.gob.mx/shcp/documentos/catalogo-del-sistema-financiero-mexicano"
)

# Sectores que maneja la API: número -> nombre oficial.
SECTORES: dict[int, str] = {
    37: "Instituciones de Banca de Desarrollo",
    40: "Instituciones de Banca Múltiple",
    68: "Sociedades Financieras de Objeto Múltiple, Entidades Reguladas",
}

# URLs conocidas (fallback) por si el scraping del índice es bloqueado por el
# challenge anti-bot de gob.mx. El nombre del archivo (`sectorNN.pdf`) codifica el
# sector, por lo que el scraper, cuando funciona, sólo necesita leer estos enlaces.
FALLBACK_PDF_URLS: dict[int, str] = {
    37: "https://www.gob.mx/cms/uploads/attachment/file/839073/sector37.pdf",
    40: "https://www.gob.mx/cms/uploads/attachment/file/1065660/sector40.pdf",
    68: "https://www.gob.mx/cms/uploads/attachment/file/1076836/sector68.pdf",
}

# Estatus que se considera "activo" para el endpoint principal.
ESTATUS_EN_OPERACION = "En Operación"

# Tiempo de vida del caché en segundos (por defecto 6 horas). El catálogo se
# actualiza con poca frecuencia, así que no tiene sentido re-descargar en cada
# request.
CACHE_TTL_SECONDS = 6 * 60 * 60

# Cabeceras para las peticiones HTTP (gob.mx rechaza User-Agents vacíos).
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
}

HTTP_TIMEOUT = 30

# ---------------------------------------------------------------------------
# PowerBI - SOFOMERS que consolidan / no consolidan con bancos
# ---------------------------------------------------------------------------
POWERBI_URL = (
    "https://wabi-south-central-us-c-primary-api.analysis.windows.net/"
    "public/reports/querydata?synchronous=true"
)

POWERBI_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "X-PowerBI-ResourceKey": "aee1f30a-a7dc-41e1-84a2-26358696aedc",
}

# Valores del filtro "Grupo" en el payload de PowerBI.
GRUPO_CONSOLIDAN = "Sofomers que consolidan con bancos"
GRUPO_NO_CONSOLIDAN = "Sofomers que no consolidan con bancos"

# TTL del caché PowerBI (mismo que el catálogo PDF).
POWERBI_CACHE_TTL_SECONDS = CACHE_TTL_SECONDS
