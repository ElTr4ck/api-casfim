"""Parseo de los catálogos en PDF de la SHCP.

Los PDF no tienen una tabla con bordes reales: son texto posicionado por
coordenadas. Cada institución es un registro de 5 columnas:

    Clave | Razón Social | Nombre Corto | Estatus | Fecha de Actualización

Complicaciones que resuelve este parser:

1. La posición X de cada columna **cambia entre sectores** (y el sector 37 usa
   el encabezado "Status" en vez de "Estatus"). Por eso los límites de columna
   se derivan dinámicamente de la fila de encabezado de cada página.
2. La "Razón Social" suele ocupar varias líneas, lo que provoca que la "Clave"
   quede en una línea intermedia y que el "Estatus" se parta en varias líneas
   (p. ej. "Extinción por Escisión"). Se agrupa por registro asignando cada
   línea al ancla (línea con Clave) verticalmente más cercana.
3. Los encabezados y el pie de página ("N de M") se repiten en cada página y se
   filtran para no contaminar los datos.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

import pdfplumber

# Una clave CASFIM luce como "40-002", "37-000", "68-1234"...
_CLAVE_RE = re.compile(r"^\d{2}-\d{2,4}$")
# Pie de página tipo "1 de 6".
_FOOTER_RE = re.compile(r"^\d+\s+de\s+\d+$")
# Título de sector: "Sector 40: Instituciones de Banca Múltiple".
_TITULO_RE = re.compile(r"Sector\s+(\d+)\s*:\s*(.+)", re.IGNORECASE)


# Margen (puntos) a la izquierda del encabezado "Nombre" para separar la Razón
# Social (ancha y desalineada) de la columna Nombre Corto.
_NOMBRE_MARGEN = 6.0

# Margen (puntos) a la izquierda del encabezado "Estatus" para separar el Nombre
# Corto (que puede ser ancho, p. ej. "FUNDACIÓN DONDÉ") del Estatus, cuyo texto a
# veces empieza ligeramente a la izquierda de su encabezado.
_ESTATUS_MARGEN = 25.0


@dataclass
class _Boundaries:
    """Límites en X (puntos PDF) que separan las columnas de la derecha.

    La columna Clave NO se delimita por X: la clave es siempre la primera palabra
    de la línea-ancla. Todo lo que quede a la izquierda de ``razon_nombre`` se
    considera Razón Social y se ignora (no se pide en la API).
    """

    razon_nombre: float
    nombre_estatus: float
    estatus_fecha: float

    def column_of(self, x0: float) -> str:
        if x0 < self.razon_nombre:
            return "razon"
        if x0 < self.nombre_estatus:
            return "nombre"
        if x0 < self.estatus_fecha:
            return "estatus"
        return "fecha"


def _group_lines(words: list[dict]) -> dict[int, list[dict]]:
    """Agrupa palabras en líneas usando la coordenada vertical (`top`)."""
    lines: dict[int, list[dict]] = {}
    for w in words:
        lines.setdefault(round(w["top"]), []).append(w)
    for top in lines:
        lines[top].sort(key=lambda w: w["x0"])
    return lines


def _is_header(words: list[dict]) -> bool:
    texts = [w["text"] for w in words]
    joined = " ".join(texts)
    if joined.startswith("Sector "):
        return True
    if "Clave" in texts and ("Social" in texts or "Razón" in joined):
        return True
    if _FOOTER_RE.match(joined.strip()):
        return True
    return False


def _boundaries_from_header(words: list[dict]) -> _Boundaries | None:
    """Calcula los límites de columna a partir de una fila de encabezado.

    Usa la coordenada X de inicio de los encabezados Nombre, Estatus/Status y
    Fecha (las tres columnas que la API necesita separar).
    """
    pos: dict[str, float] = {}
    for w in words:
        t = w["text"]
        if t == "Nombre" and "nombre" not in pos:
            pos["nombre"] = w["x0"]
        elif t in ("Estatus", "Status") and "estatus" not in pos:
            pos["estatus"] = w["x0"]
        elif t == "Fecha" and "fecha" not in pos:
            pos["fecha"] = w["x0"]

    if not {"nombre", "estatus", "fecha"} <= pos.keys():
        return None

    return _Boundaries(
        # La Razón Social puede extenderse casi hasta el encabezado "Nombre";
        # por eso el límite se ancla al borde izquierdo de "Nombre", no al punto
        # medio con "Razón".
        razon_nombre=pos["nombre"] - _NOMBRE_MARGEN,
        nombre_estatus=pos["estatus"] - _ESTATUS_MARGEN,
        estatus_fecha=(pos["estatus"] + pos["fecha"]) / 2,
    )


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_sector_pdf(pdf_bytes: bytes) -> tuple[int | None, str | None, list[dict]]:
    """Parsea el PDF de un sector.

    Devuelve ``(numero_sector, nombre_sector, registros)`` donde cada registro es
    un dict con: ``clave_casfim``, ``nombre_corto``, ``estatus``,
    ``fecha_actualizacion``.
    """
    sector_num: int | None = None
    sector_nombre: str | None = None
    registros: list[dict] = []
    boundaries: _Boundaries | None = None

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            if not words:
                continue
            lines = _group_lines(words)

            # Título del sector (sólo en la primera página).
            if sector_num is None:
                for top in sorted(lines):
                    m = _TITULO_RE.search(" ".join(w["text"] for w in lines[top]))
                    if m:
                        sector_num = int(m.group(1))
                        sector_nombre = _clean(m.group(2))
                        break

            # Actualiza los límites de columna con el encabezado de esta página.
            for top in sorted(lines):
                b = _boundaries_from_header(lines[top])
                if b is not None:
                    boundaries = b
                    break
            if boundaries is None:
                continue

            # Líneas de datos (sin encabezados/pie).
            data_tops = [t for t in sorted(lines) if not _is_header(lines[t])]
            anchors = [
                t for t in data_tops if _CLAVE_RE.match(lines[t][0]["text"])
            ]
            if not anchors:
                continue

            # Asigna cada línea de datos al ancla (Clave) vertical más cercana.
            assigned: dict[int, list[int]] = {a: [] for a in anchors}
            for t in data_tops:
                nearest = min(anchors, key=lambda a: abs(a - t))
                assigned[nearest].append(t)

            for a in anchors:
                # La clave es siempre la primera palabra de la línea-ancla.
                clave = lines[a][0]["text"]
                if not _CLAVE_RE.match(clave):
                    continue

                cols: dict[str, list[str]] = {
                    "nombre": [],
                    "estatus": [],
                    "fecha": [],
                }
                for t in sorted(assigned[a]):
                    for w in lines[t]:
                        c = boundaries.column_of(w["x0"])
                        if c in cols:
                            cols[c].append(w["text"])

                registros.append(
                    {
                        # Clave sin el guion separador: "40-012" -> "40012".
                        "clave_casfim": clave.replace("-", ""),
                        "nombre_corto": _clean(" ".join(cols["nombre"])),
                        "estatus": _clean(" ".join(cols["estatus"])),
                        "fecha_actualizacion": _clean(" ".join(cols["fecha"])) or None,
                    }
                )

    return sector_num, sector_nombre, registros
