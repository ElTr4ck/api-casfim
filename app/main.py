"""API CASFIM - FastAPI.

Expone el catálogo del Sistema Financiero Mexicano (sectores 37, 40 y 68) a
partir del scraping de los PDF publicados por la SHCP.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse

from . import __version__, config
from .models import (
    HealthResponse,
    Institucion,
    InstitucionEnOperacion,
    RefreshResponse,
    SectorInfo,
    Sofomer,
    SofomerRefreshResponse,
)
from .service import service
from .powerbi import sofomer_service

app = FastAPI(
    title="API CASFIM",
    version=__version__,
    description=(
        "Catálogo del Sistema Financiero Mexicano (SHCP). Hace scraping de los "
        "PDF de los sectores 37 (Banca de Desarrollo), 40 (Banca Múltiple) y 68 "
        "(SOFOM E.R.) y expone su contenido como JSON.\n\n"
        "Endpoint principal: **GET /instituciones/en-operacion**."
    ),
)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health():
    """Estado del servicio."""
    return HealthResponse(version=__version__, sectores=sorted(config.SECTORES))


# --------------------------------------------------------------------------
# Endpoint OBLIGATORIO
# --------------------------------------------------------------------------
@app.get(
    "/instituciones/en-operacion",
    response_model=list[InstitucionEnOperacion],
    tags=["instituciones"],
    summary="Instituciones 'En Operación' (clave + nombre largo + nombre corto)",
)
def instituciones_en_operacion():
    """Devuelve, en un solo JSON y para los tres sectores, la **clave CASFIM**, el
    **nombre largo** (razón social) y el **nombre corto** de todas las
    instituciones cuyo estatus es *En Operación*.
    """
    try:
        return service.en_operacion()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error al cargar catálogo: {exc}")


# --------------------------------------------------------------------------
# Endpoints adicionales
# --------------------------------------------------------------------------
@app.get(
    "/instituciones",
    response_model=list[Institucion],
    tags=["instituciones"],
    summary="Todas las instituciones (con filtros opcionales)",
)
def listar_instituciones(
    sector: int | None = Query(
        None, description="Filtra por sector (37, 40 o 68).", examples=[40]
    ),
    estatus: str | None = Query(
        None,
        description="Filtra por estatus exacto (sin distinguir acentos/mayúsculas).",
        examples=["En Operación"],
    ),
):
    """Catálogo completo. Acepta filtros por `sector` y/o `estatus`."""
    if sector is not None and sector not in config.SECTORES:
        raise HTTPException(
            status_code=404,
            detail=f"Sector {sector} no soportado. Use uno de {sorted(config.SECTORES)}.",
        )
    try:
        return service.todas(sector=sector, estatus=estatus)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error al cargar catálogo: {exc}")


@app.get(
    "/instituciones/{clave}",
    response_model=Institucion,
    tags=["instituciones"],
    summary="Detalle de una institución por clave CASFIM",
)
def obtener_institucion(clave: str):
    """Detalle completo de una institución dada su clave (p. ej. `40-002`)."""
    inst = service.por_clave(clave)
    if inst is None:
        raise HTTPException(status_code=404, detail=f"Clave '{clave}' no encontrada.")
    return inst


@app.get("/sectores", response_model=list[SectorInfo], tags=["sectores"])
def listar_sectores():
    """Sectores soportados con su URL de PDF y total de instituciones."""
    return service.info_sectores()


@app.get(
    "/sectores/{sector}/instituciones",
    response_model=list[Institucion],
    tags=["sectores"],
    summary="Instituciones de un sector",
)
def instituciones_por_sector(sector: int):
    if sector not in config.SECTORES:
        raise HTTPException(
            status_code=404,
            detail=f"Sector {sector} no soportado. Use uno de {sorted(config.SECTORES)}.",
        )
    return service.todas(sector=sector)


@app.get("/estatus", tags=["meta"], summary="Estatus disponibles y su conteo")
def listar_estatus():
    """Distribución de instituciones por estatus (útil para descubrir valores)."""
    return service.estatus_disponibles()


@app.post("/refresh", response_model=RefreshResponse, tags=["meta"])
def refrescar():
    """Fuerza la re-descarga y re-parseo de los PDF (ignora el caché)."""
    resumen = service.recargar()
    return RefreshResponse(status="ok", **resumen)


# --------------------------------------------------------------------------
# SOFOMERs — consolidan / no consolidan con bancos (fuente: PowerBI SHCP)
# --------------------------------------------------------------------------

def _sofomer_o_503(fn):
    """Ejecuta fn() y convierte errores de configuración/red en HTTP 503."""
    try:
        return fn()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error al consultar PowerBI: {exc}")


@app.get(
    "/sofomers/consolidan",
    response_model=list[Sofomer],
    tags=["sofomers"],
    summary="SOFOMERs que consolidan con bancos",
)
def sofomers_consolidan():
    """SOFOMERs reguladas (sector 68) que **consolidan** con bancos,
    según el reporte PowerBI de la SHCP."""
    return _sofomer_o_503(sofomer_service.consolidan)


@app.get(
    "/sofomers/no-consolidan",
    response_model=list[Sofomer],
    tags=["sofomers"],
    summary="SOFOMERs que NO consolidan con bancos",
)
def sofomers_no_consolidan():
    """SOFOMERs reguladas (sector 68) que **no consolidan** con bancos,
    según el reporte PowerBI de la SHCP."""
    return _sofomer_o_503(sofomer_service.no_consolidan)


@app.get(
    "/sofomers",
    response_model=list[Sofomer],
    tags=["sofomers"],
    summary="Todas las SOFOMERs con indicador de consolidación",
)
def sofomers_todas():
    """Devuelve las SOFOMERs de ambos grupos en un solo JSON.
    El campo `grupo` indica si consolidan o no con bancos."""
    return _sofomer_o_503(sofomer_service.todas)


@app.post("/sofomers/refresh", response_model=SofomerRefreshResponse, tags=["sofomers"])
def refrescar_sofomers():
    """Fuerza la re-consulta a PowerBI (ignora el caché)."""
    resumen = _sofomer_o_503(sofomer_service.recargar)
    return SofomerRefreshResponse(status="ok", **resumen)
