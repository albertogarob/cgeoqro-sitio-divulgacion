---
name: auditoria-licencias
description: Audita las licencias de los papers PDF de la carpeta de Google Drive de CentroGeo Querétaro para determinar de cuáles se pueden reutilizar figuras/fotos/mapas en el sitio de divulgación. Úsalo cuando el usuario pida "revisar/auditar licencias", "de qué papers se pueden usar las figuras", "qué artículos permiten reutilización", o cuando se agreguen papers nuevos al Drive y haya que reclasificarlos. Encapsula el acceso a Drive vía Composio, la extracción de la declaración de licencia con pdftotext, la clasificación conservadora, y el volcado a docs/licencias-papers.md.
---

# Auditar licencias de los papers del Drive

Determina, de forma reproducible, **de qué papers se pueden reutilizar figuras** en el
sitio, según su licencia. Es el complemento operativo de la política de derechos de autor
de [CLAUDE.md](../../../CLAUDE.md) (leerla primero) y alimenta el documento de referencia
[docs/licencias-papers.md](../../../docs/licencias-papers.md).

## Regla de decisión (conservadora)

- **Usable** (figuras reutilizables con atribución): el PDF declara una licencia Creative
  Commons que autoriza redistribución: **CC BY, CC BY-SA, CC BY-NC, CC0**. Anota las
  condiciones: `-NC` = solo no comercial (este sitio califica), `-SA` = compartir igual,
  `-ND` = sin derivados (no recortar/editar la figura, solo reproducirla íntegra).
- **No usable**: "all rights reserved" / "todos los derechos reservados" / "DR ©";
  editoriales de suscripción sin aviso CC (Elsevier, Springer, Taylor & Francis/Informa,
  Wiley); o **sin ninguna declaración de licencia** (reservado por defecto, no asumir
  libre).
- **"Acceso abierto" no es licencia de reuso.** Gratis de leer no da permiso sobre las
  imágenes (ej. Research in Computing Science del IPN prohíbe reproducir imágenes pese a
  ser de lectura abierta). Exige una licencia CC explícita.
- **Licencia usable no implica figura usable**: revisar **figura por figura** (ver Paso 4).

## Paso 1. Enumerar los PDFs del Drive (vía Composio)

Carpeta raíz: `173mm3nHDzPU8Cjhz7HAjSxi_GzUXaCcM`, subcarpetas por investigador; algunas
tienen sub-subcarpetas (ej. "Revistas", "Congresos"). Conexión: `agarcia@centrogeo.edu.mx`.

1. `COMPOSIO_SEARCH_TOOLS` con "list files in a Google Drive folder" y "download a file
   from Google Drive". Guarda el `session_id`.
2. Lista la raíz con `GOOGLEDRIVE_FIND_FILE` (`folder_id`, `fields: "files(id,name,mimeType)"`).
   Recorre cada subcarpeta y baja un nivel más en las que tengan subcarpetas
   (`mimeType == application/vnd.google-apps.folder`). Reúne todos los `application/pdf`
   (id + nombre + investigador). Nota las carpetas vacías.

## Paso 2. Descargar y extraer texto

1. `GOOGLEDRIVE_DOWNLOAD_FILE` por `fileId` (se pueden lotear muchos en un
   `COMPOSIO_MULTI_EXECUTE_TOOL`). Devuelve `downloaded_file_content.s3url` (enlace
   temporal ~1h; consumir pronto).
2. En bash, en `/tmp` (nunca en el repo): `curl` cada s3url a un PDF y `pdftotext` a `.txt`.
   La declaración de licencia casi siempre está en el pie de la página 1 o en la última
   página, así que basta procesar primeras 2 + últimas 2 páginas si el texto completo es
   pesado.

## Paso 3. Clasificar la licencia

Señal más fiable: la URL `creativecommons.org/licenses/<variante>` en el texto. Si no está,
busca la frase de licencia ("distributed under the terms of...", "This is an open access
article...", "licensee MDPI", "all rights reserved", "DR ©", "© <año> <editorial>").

```bash
# por cada N.txt:
grep -iohm1 "creativecommons.org/licenses/[a-z-]*" N.txt      # -> CC BY / by-nc-sa / ...
grep -iohm1 "all rights reserved\|derechos reservados\|dr ©"  N.txt
grep -iohm1 "licensee mdpi\|open access article distributed\|distributed under the terms" N.txt
grep -iohm1 "elsevier\|springer\|taylor & francis\|informa\|wiley" N.txt   # suscripción -> reservado
```

Heurísticas de editorial: MDPI = CC BY; PLOS/Frontiers/Copernicus = CC BY; Elsevier /
Springer / Taylor & Francis (Informa) / Wiley por defecto = reservado salvo aviso CC
explícito de "gold open access". Ante duda, confirma con `WebFetch` a la página del DOI o
del editor, pero **si no hay licencia CC explícita, clasifícalo como reservado**.

### Errores comunes (aprendidos en producción)

- **Falsos positivos de "CC BY" o "Open Access"**: una mención suelta puede venir de una
  barra lateral ("Most Read Open Access ...") o de una referencia, no del artículo. Confía
  en la URL `creativecommons.org/licenses/...` o en la frase "This ... article is
  distributed under ... Creative Commons ..." que precede a la cita del propio artículo.
- **"© <editorial>" sin "all rights reserved"** sigue siendo reservado (Elsevier a veces
  escribe "All rights are reserved, including those for text and data mining...").
- **Regex pesados sobre pdftotext de decenas de PDFs se cuelgan**: convierte a `.txt`
  primero y usa greps de cadena simple.
- **Espaciado roto de pdftotext**: la frase de licencia puede salir con espacios raros
  ("creativecommons.org/ licenses/ by/"); normaliza espacios antes de casar patrones.

## Paso 4. Advertir la revisión figura por figura

Para los papers marcados "usable", recuerda que la licencia del artículo cubre lo propio
"salvo que se indique lo contrario". Antes de publicar una figura, revisa su pie: si dice
"Fuente: [tercero]" o "reproducida con permiso", esa figura NO está bajo la licencia del
artículo y queda fuera. Precedente: el paper de Utopías (Geopauta) es CC BY pero sus tres
fotos están atribuidas a obras previas de las autoras, así que no son reutilizables sin
permiso. Para extraer e inspeccionar figuras: `pdfimages -list paper.pdf` (ignora el logo
de la revista que se repite en cada página) y `pdfimages -f P -l P -j paper.pdf fig`,
luego lee el pie con `pdftotext -f P-1 -l P+1 paper.pdf -`.

## Paso 5. Volcar el resultado

Actualiza [docs/licencias-papers.md](../../../docs/licencias-papers.md): la fecha de
auditoría, la tabla de papers usables (investigador, artículo, editorial, licencia,
condiciones), el caso especial "licencia sí / figuras no" si aplica, la tabla de no
usables con el motivo, y las carpetas vacías. Mantén el formato existente del documento.

## Paso 6. Limpiar

Borra todos los PDF y `.txt` de `/tmp`. Verifica que **ningún PDF** entró al repo:
`find . -name "*.pdf" -not -path "./node_modules/*"`. Los PDFs nunca se comitean; en el
repo solo va el documento de auditoría.
