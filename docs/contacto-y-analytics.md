# Contacto y Google Analytics

Las dos piezas que dependen de una cuenta externa y que, por eso, salen del repositorio
sin configurar. Mientras falte el dato, el sitio se publica igual: el bloque de contacto
no aparece y no se carga Analytics. Ninguna de las dos rompe el build.

## 1. Formulario de contacto

Al final de cada cápsula hay un bloque que pide **solo el correo** del lector. El mensaje
va prellenado con el título de la cápsula, su enlace y los investigadores, para que quien
reciba el aviso sepa de dónde sale sin tener que preguntar.

### Crear el formulario de Google

1. En Google Forms, formulario nuevo. Dos preguntas, las dos de **respuesta corta**:
   - una para el correo (puede llamarse "Tu correo");
   - otra para el mensaje (puede llamarse "Mensaje").
2. Menú de los tres puntos → **Obtener enlace prellenado**.
3. Escribe cualquier cosa en las dos preguntas y pulsa **Obtener enlace**.
4. Copia el enlace. Tiene esta forma:

   ```
   https://docs.google.com/forms/d/e/1FAIpQLSd.../viewform?usp=pp_url&entry.1234567890=correo&entry.987654321=mensaje
   ```

5. De ahí salen los tres valores:
   - `formId`: el tramo entre `/forms/d/e/` y `/viewform`.
   - `entryCorreo`: el `entry.NNN` que quedó junto a lo que escribiste en la pregunta del correo.
   - `entryMensaje`: el `entry.NNN` de la pregunta del mensaje.
6. En el formulario, pestaña **Respuestas**, activa el aviso por correo para no tener que
   entrar a mirar.

### Pegarlos en el sitio

En `src/lib/contacto.ts`:

```ts
export const FORMULARIO_CONTACTO: ConfigFormulario = {
  formId: '1FAIpQLSd...',
  entryCorreo: 'entry.1234567890',
  entryMensaje: 'entry.987654321',
  correoRespaldo: '',
};
```

Comprueba que quedó bien con `npm test` y mirando una cápsula en `npm run dev`.

### Respaldo por correo

Si no hay formulario, basta con rellenar `correoRespaldo` con una dirección. El bloque
pasa a mostrar un botón que abre el programa de correo del lector con el asunto y el
mensaje ya escritos. Pide menos trabajo y da un resultado peor: no funciona en quien lee
desde un navegador sin cliente de correo configurado.

### Qué pasa con media configuración

Si falta cualquiera de los tres valores del formulario de Google, o un `entry.NNN` está
mal copiado, el bloque **cae al respaldo por correo**; y si tampoco hay correo, no se
publica. Es deliberado: más vale que no aparezca a que aparezca un botón que no lleva a
ninguna parte. Durante el desarrollo (`npm run dev`) sí se ve, con un aviso encima.

## 2. Google Analytics

El ID de medición no es un secreto (viaja en el HTML de cualquier sitio que use
Analytics), pero sí es propio de cada instalación, así que no se escribe en el código.

### En local

```bash
cp .env.example .env
# y edita .env:
PUBLIC_GA_ID=G-XXXXXXXXXX
```

**En `npm run dev` no se carga Analytics aunque el ID esté puesto.** Es deliberado: el
tráfico de las pruebas no debe contar como visitas, y son justo las cifras con las que
cada quien va a reportar su contenido. Para comprobar que quedó bien configurado:

```bash
npm run build && npm run preview
```

que sirve el build de producción. Ahí sí mide.

### En el sitio publicado

En GitHub, `Settings` → `Secrets and variables` → `Actions` → `New repository secret`,
con nombre **`PUBLIC_GA_ID`** y el ID como valor. El workflow de `deploy.yml` ya lo pasa
al build. Si el secreto no existe, el sitio se publica sin Analytics.

### Desglosar el tráfico por cápsula y por autor

Cada vista de página de una cápsula manda tres parámetros propios: `capsula`, `serie` e
`investigadores`. El desglose por URL funciona solo; para que esos tres parámetros aparezcan en
los informes hay que **registrarlos una vez** en GA4:

1. `Administrar` → `Definiciones personalizadas` → `Crear dimensión personalizada`.
2. Una por cada uno, con **ámbito de evento** y el parámetro escrito igual que arriba:
   `capsula`, `serie`, `investigadores`.
3. Los datos empiezan a acumularse desde ese momento; GA4 no rellena hacia atrás.

Además se registran dos eventos:

| Evento | Cuándo | Para qué sirve |
| --- | --- | --- |
| `share` | Clic en un botón de compartir | Qué red usa la gente y en qué cápsula |
| `generate_lead` | Envío del formulario de contacto | Cuántos contactos trae cada cápsula |

### Un apunte de privacidad

Analytics pone cookies de medición. Hoy el sitio no tiene aviso de cookies. Antes de que
deje de ser un prototipo, decidir si hace falta uno.
