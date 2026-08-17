"""Modelos Pydantic para las respuestas de la API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Institucion(BaseModel):
    """Registro completo de una institución tal como aparece en el catálogo."""

    clave_casfim: str = Field(..., examples=["40002"], description="Clave CASFIM (sin guion).")
    nombre_corto: str = Field(..., examples=["BANAMEX"], description="Nombre corto.")
    estatus: str = Field(..., examples=["En Operación"], description="Estatus actual.")
    fecha_actualizacion: str | None = Field(
        None, examples=["06/06/2005"], description="Fecha de actualización (dd/mm/aaaa)."
    )
    sector: int = Field(..., examples=[40], description="Número de sector.")
    sector_nombre: str = Field(
        ..., examples=["Instituciones de Banca Múltiple"], description="Nombre del sector."
    )


class InstitucionEnOperacion(BaseModel):
    """Vista reducida para el endpoint principal (sólo clave y nombre corto)."""

    clave_casfim: str = Field(..., examples=["40002"])
    nombre_corto: str = Field(..., examples=["BANAMEX"])


class SectorInfo(BaseModel):
    """Metadatos de un sector."""

    sector: int
    nombre: str
    pdf_url: str | None = None
    total_instituciones: int | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    sectores: list[int]


class RefreshResponse(BaseModel):
    status: str
    sectores_cargados: list[int]
    total_instituciones: int
    errores: dict[int, str] = Field(default_factory=dict)


class Sofomer(BaseModel):
    """SOFOMER con indicador de si consolida o no con bancos."""

    clave_casfim: str = Field(..., examples=["68003"])
    nombre: str = Field(..., examples=["Financiera Ayudamos"])
    grupo: str = Field(
        ..., examples=["Consolidan con Bancos"], description="Grupo de consolidación."
    )


class SofomerRefreshResponse(BaseModel):
    status: str
    consolidan: int
    no_consolidan: int
