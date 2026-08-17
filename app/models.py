"""Modelos Pydantic para las respuestas de la API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Institucion(BaseModel):
    """Registro completo de una institución tal como aparece en el catálogo."""

    clave_casfim: str = Field(..., examples=["40002"], description="Clave CASFIM (sin guion).")
    nombre_largo: str = Field(
        ..., examples=["BANCO NACIONAL DE MÉXICO, S.A."], description="Razón social."
    )
    nombre_corto: str = Field(..., examples=["BANAMEX"], description="Nombre corto.")
    estatus: str = Field(..., examples=["En Operación"], description="Estatus actual.")
    fecha_actualizacion: str | None = Field(
        None, examples=["06/06/2005"], description="Fecha de actualización (dd/mm/aaaa)."
    )
    sector: int = Field(..., examples=[40], description="Número de sector.")
    sector_nombre: str = Field(
        ..., examples=["Instituciones de Banca Múltiple"], description="Nombre del sector."
    )
    sector_actualizado_al: str | None = Field(
        None,
        examples=["10/08/2026"],
        description="Fecha en que SHCP generó el PDF de este sector (dd/mm/aaaa).",
    )


class InstitucionEnOperacion(BaseModel):
    """Vista reducida para el endpoint principal (clave, nombre largo y nombre corto)."""

    clave_casfim: str = Field(..., examples=["40002"])
    nombre_largo: str = Field(..., examples=["BANCO NACIONAL DE MÉXICO, S.A."])
    nombre_corto: str = Field(..., examples=["BANAMEX"])
    sector_actualizado_al: str | None = Field(None, examples=["10/08/2026"])


class SectorInfo(BaseModel):
    """Metadatos de un sector."""

    sector: int
    nombre: str
    pdf_url: str | None = None
    total_instituciones: int | None = None
    actualizado_al: str | None = Field(
        None,
        examples=["10/08/2026"],
        description="Fecha en que SHCP generó el PDF de este sector (dd/mm/aaaa).",
    )


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
