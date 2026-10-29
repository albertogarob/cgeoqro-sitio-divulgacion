---
name: ficha-recorrido
description: Lleva el ida y vuelta de la ficha de recorrido, la hoja de Drive con la que los investigadores corrigen el texto y las imágenes de un scrollytelling del sitio. Úsalo cuando el usuario diga "mándale el recorrido al autor", "exporta la ficha", "ya me devolvieron las correcciones", "aplica lo que corrigió el investigador", o pida que un autor revise o edite una cápsula. Encapsula el export/import con validación, la subida a Drive como hoja de cálculo, el permiso de edición y la comprobación antes de publicar.
---

# Ficha de recorrido: correcciones de los autores

Los autores corrigen el texto y las imágenes de un recorrido desde una hoja de cálculo
en Drive. No añaden ni reordenan pasos: eso lo hace el equipo, porque cada paso necesita
además una escena visual en el componente Astro.

Referencia humana completa: [docs/ficha-recorrido.md](../../../docs/ficha-recorrido.md).
Reglas del proyecto (derechos de autor, escritura, despliegue): [CLAUDE.md](../../../CLAUDE.md).

## Antes de nada

- Los recorridos viven en `src/content/recorridos/<id>.yaml`. Los ids actuales salen de
  `ls src/content/recorridos/`.
- **Nunca edites ese YAML a mano para aplicar correcciones de un autor.** Pasa siempre
  por el importador: es lo que comprueba que el autor no rompió el amarre entre texto y
  gráfico, y lo que atrapa rayas largas, "QRO", imágenes sin crédito y textos que no
  caben.
- Subir algo a Drive o compartirlo con alguien es una acción hacia fuera: **confírmala
  con el usuario antes de ejecutarla**, y pregunta con qué correo se comparte.

## Ida: mandarle la ficha al autor

1. **Exportar**:

   ```bash
   npm run ficha:exportar -- <recorrido>
   ```

   Deja `fichas/<recorrido>-ficha.csv` (carpeta ignorada por git). Si ese archivo ya
   existe de una exportación anterior, el comando se niega a pisarlo: añade `--forzar`
   para rehacerlo.

2. **Subirla a Drive como hoja de cálculo**, con Composio. El truco es crear el archivo
   desde el texto del CSV pidiendo el tipo de Hoja de cálculo, y Drive lo convierte:

   - `GOOGLEDRIVE_FIND_FILE` con `folder_id` de la carpeta raíz de papers
     (`173mm3nHDzPU8Cjhz7HAjSxi_GzUXaCcM`) para localizar la subcarpeta del investigador.
   - `GOOGLEDRIVE_CREATE_FILE_FROM_TEXT` con:
     - `file_name`: algo como `Ficha de recorrido - <título de la cápsula>`,
     - `text_content`: el contenido literal del CSV,
     - `mime_type`: `application/vnd.google-apps.spreadsheet`,
     - `parent_id`: la subcarpeta del investigador.
   - `GOOGLEDRIVE_GET_FILE_METADATA` con `fields: "webViewLink"` para obtener el enlace
     (la respuesta de creación no lo trae).

3. **Dar acceso al autor**: `GOOGLEDRIVE_CREATE_PERMISSION` con `type: "user"`,
   `email_address` del investigador, `role: "writer"` y un `email_message` corto que
   explique qué se espera. Confirma antes con el usuario.

4. **Decirle al autor qué toca y qué no**: corrige `texto`, `imagen` y `credito`; deja
   `visual`, `pos` y `tipo` como están; todo lo demás (un paso nuevo, una foto suya, una
   duda) va en la columna `comentarios`.

## Vuelta: aplicar las correcciones

1. **Descargar la hoja como CSV**: `GOOGLEDRIVE_DOWNLOAD_FILE` con el `fileId` de la hoja
   y `mime_type: "text/csv"`. Devuelve `downloaded_file_content.s3url`, un enlace
   temporal; bájalo enseguida:

   ```bash
   curl -sL "<s3url>" -o fichas/<recorrido>-ficha.csv
   ```

2. **Revisar en seco** (no escribe nada):

   ```bash
   npm run ficha:importar -- <recorrido> fichas/<recorrido>-ficha.csv
   ```

   Lee la salida entera: lista cambio por cambio el antes y el después, y los problemas.
   Si hay problemas, **no se aplica nada**: hay que resolverlos con el autor, no
   editarlos por tu cuenta. Un texto que se pasa de largo o una raya larga sí los puedes
   ajustar tú en la propia hoja, avisando; un cambio de sentido, no.

3. **Aplicar**:

   ```bash
   npm run ficha:importar -- <recorrido> fichas/<recorrido>-ficha.csv --aplicar
   npm test
   npm run build
   ```

4. **Mirar el recorrido** en el navegador (los textos cambian de largo y pueden romper
   el encaje con los gráficos) y **comitear** el YAML con un mensaje que diga de quién
   vienen las correcciones. Actualiza `revisadoPor` en el frontmatter de la cápsula si
   esta revisión es la que la da por revisada.

## Lo que pide el autor y la ficha no cubre

- **Paso nuevo**: añádelo al YAML con un `visual` propio y dale escena en el componente
  (`src/components/Scrolly<Tema>.astro`), enganchándola con `data-only={v('<visual>')}`
  o `data-from={v('<visual>')}`. Nunca con números de paso: rompe al insertar.
- **Foto que aporta el autor**: resuelve primero autoría y licencia (política en
  CLAUDE.md), guárdala en `public/scrolly/` y deja que la ficha la nombre.
- **Figura del artículo**: solo si la licencia lo permite, revisada figura por figura
  (ver `docs/licencias-papers.md`).
