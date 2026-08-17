# API CASFIM

API en **Python + FastAPI** que hace *scraping* del
[Catálogo del Sistema Financiero Mexicano](https://www.gob.mx/shcp/documentos/catalogo-del-sistema-financiero-mexicano)
publicado por la SHCP y expone su contenido como JSON.

Procesa los PDF de tres sectores:

| Sector | Descripción |
|-------:|-------------|
| **37** | Instituciones de Banca de Desarrollo |
| **40** | Instituciones de Banca Múltiple |
| **68** | Sociedades Financieras de Objeto Múltiple, Entidades Reguladas |

De cada institución se extrae: **clave CASFIM**, **nombre corto**, **estatus** y
**fecha de actualización**.

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

- Documentación interactiva (Swagger): http://127.0.0.1:8000/docs
- La raíz `/` redirige a `/docs`.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | **`/instituciones/en-operacion`** | **(Obligatorio)** Clave CASFIM + nombre corto de todas las instituciones *En Operación* de los 3 sectores, en un solo JSON. |
| `GET` | `/instituciones` | Catálogo completo. Filtros opcionales: `?sector=40` y `?estatus=En Operación`. |
| `GET` | `/instituciones/{clave}` | Detalle de una institución por su clave (p. ej. `40-002`). |
| `GET` | `/sectores` | Sectores soportados, su URL de PDF y total de instituciones. |
| `GET` | `/sectores/{sector}/instituciones` | Instituciones de un sector (37, 40 o 68). |
| `GET` | `/estatus` | Estatus existentes y su conteo. |
| `GET` | `/health` | Estado del servicio. |
| `POST` | `/refresh` | Fuerza la re-descarga y re-parseo de los PDF (ignora el caché). |

### Ejemplo — endpoint principal

```bash
curl http://127.0.0.1:8000/instituciones/en-operacion
```

```json
[
  { "clave_casfim": "37-006", "nombre_corto": "Bancomext" },
  { "clave_casfim": "40-002", "nombre_corto": "BANAMEX" },
  { "clave_casfim": "68-002", "nombre_corto": "AYF BANORTE" }
]
```

> El filtro por `estatus` ignora acentos y mayúsculas, así que
> `?estatus=en operacion` también funciona.

## Cómo funciona

1. **Descubrimiento de URLs** (`app/scraper.py`): intenta leer la página índice
   del catálogo y detectar los enlaces `sectorNN.pdf` (el número de sector va en
   el nombre del archivo). La página índice está protegida por un *challenge*
   anti-bot, por lo que si el *scraping* falla se usan las URLs conocidas de
   respaldo en `app/config.py`. Los PDF de `/cms/uploads/` sí se descargan
   directamente.
2. **Parseo** (`app/parser.py`): los PDF son texto posicionado (sin tabla con
   bordes). El parser:
   - deriva los límites de columna **dinámicamente** del encabezado de cada
     página (la posición de las columnas cambia entre sectores; el sector 37 usa
     "Status" en vez de "Estatus");
   - agrupa cada institución por su *clave* aunque la *Razón Social* ocupe varias
     líneas y parta el *Estatus* (p. ej. "Extinción por Escisión");
   - filtra encabezados y pies de página repetidos.
3. **Servicio + caché** (`app/service.py`): mantiene el resultado en memoria con
   un TTL (6 h por defecto). `POST /refresh` lo invalida.

## Estructura

```
app/
  config.py    # sectores, URLs de respaldo, TTL del caché
  models.py    # modelos Pydantic de respuesta
  scraper.py   # descubre URLs y descarga PDFs
  parser.py    # extrae instituciones de cada PDF
  service.py   # orquestación + caché + consultas
  main.py      # FastAPI: endpoints
requirements.txt
```

## Notas

- El catálogo se actualiza con poca frecuencia; el caché evita descargar los PDF
  en cada petición. Usa `POST /refresh` para forzar la actualización.
- Si la SHCP republica los PDF con un nuevo `file id`, el *scraper* lo detecta
  automáticamente cuando la página índice es accesible; de lo contrario, basta
  con actualizar `FALLBACK_PDF_URLS` en `app/config.py`.
