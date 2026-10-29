#!/usr/bin/env python3
r"""Arma la carpeta que se sube a Google Classroom para una sesión.

    python3 tools/classroom.py 14          arma la de la sesión 14
    python3 tools/classroom.py 14 --ver    dice qué haría, sin escribir nada
    python3 tools/classroom.py --todas     arma la de toda sesión con paquete

Deja todo lo que va a la misma publicación en **una sola carpeta**, para que
subirlo sea arrastrar dos archivos a Drive:

    salidas/classroom/S14 - Aprendizaje inductivo y arboles de decision/
        S14 - Aprendizaje inductivo y arboles de decision.zip     el paquete
        S14 - Aprendizaje inductivo y arboles de decision.ipynb   la libreta
        anuncio.md                                                el texto
        LEEME.txt                                                 los pasos

**Por qué existe.** Alberto lo pidió el 19 de octubre de 2026: "cuando suba el
paquete de una sesión a Google Classroom voy a subir en la misma publicación la
libreta colab de la sesión también. Organiza y almacena todo para que esta
tarea se me facilite". Antes el zip se hacía a mano, el nombre se escribía a
mano, y la libreta vivía en la carpeta de la sesión junto a su generador, que es
un sitio del que no se arrastra nada a Drive.

**El nombre lo fija la convención ya publicada**, `SNN - Tema.zip` sin acentos,
tomando el tema de `admin/sesiones.csv`, que es la fuente única. Así se llaman
los zips de las sesiones 9 a 13, que ya están en Classroom.

**Nada se teclea y nada se copia a mano.** El zip se comprime del paquete que
hay en `salidas/`, la libreta se copia de la carpeta de la sesión, y el texto
del anuncio se escribe con el número y el tema de la sesión ya puestos.

**Comprueba antes de armar**, y avisa en vez de callar:

  - que el paquete exista y sea más nuevo que el `index.html` del que sale;
  - que la libreta, si la sesión tiene, sea más nueva que su generador;
  - que el paquete lleve apuntes de estudio, que es lo único que el grupo lee
    después de clase. Sin apuntes avisa, porque subirlo así entrega una
    presentación muda.

Lo que NO hace, y es deliberado: no sube nada ni publica nada. El zip pesa
megas y la API de Classroom no acepta una ruta local, así que esa mitad es de
Alberto. El anuncio se crea en borrador aparte, como manda CLAUDE.md.
"""
import argparse
import csv
import datetime
import os
import pathlib
import re
import shutil
import unicodedata
import zipfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SALIDAS = RAIZ / "salidas"
DESTINO = SALIDAS / "classroom"


def sin_acentos(t):
    """Quita los acentos para el nombre de archivo, como los ya publicados."""
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def nombre_archivo(t):
    """El nombre de archivo: sin acentos y sin lo que estorba en Drive.

    Los temas de admin/sesiones.csv traen dos puntos y un asterisco, y los dos
    dan problemas: el asterisco se expande en el shell al mover el archivo, y
    los dos puntos no son un nombre válido en Windows, que es donde se
    sincroniza Drive. El tema del curso NO se toca; esto es solo el nombre.
    """
    # "A*" se escribe "A estrella", que es como se dice y como lo nombra el
    # curso. Quitarle el asterisco a secas dejaba el nombre en "A", que no
    # dice nada.
    t = sin_acentos(t).replace("A*", "A estrella").replace(":", ",")
    for c in '*/\\?"<>|':
        t = t.replace(c, "")
    return re.sub(r"\s{2,}", " ", t).strip()


def sesiones():
    with open(RAIZ / "admin" / "sesiones.csv", encoding="utf8") as f:
        return list(csv.DictReader(f))


def una(num):
    for s in sesiones():
        if s["num"] == str(int(num)):
            return s
    return None


def fecha_larga(iso):
    MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
           "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    d = datetime.date.fromisoformat(iso)
    return "%d de %s de %d" % (d.day, MES[d.month - 1], d.year)


def liga_colab(deck):
    """La liga de Colab que el propio deck ya lleva escrita, si la lleva.

    Se saca de ahí y no se teclea, por la misma razón que las cifras: el deck
    es el único sitio donde vive, y así el anuncio no puede quedar apuntando a
    una libreta vieja.
    """
    if not deck.exists():
        return None
    m = re.search(r"https://colab\.research\.google\.com/drive/[A-Za-z0-9_-]+",
                  deck.read_text(encoding="utf8", errors="ignore"))
    return m.group(0) if m else None


def anuncio(num, tema, con_libreta, colab=None):
    """El texto del anuncio, corto y en palabras simples.

    Un párrafo por renglón y sin sangrar, para que se copie y se pegue en
    Classroom sin arrastrar saltos de línea ni espacios de más.

    Las dos teclas del lector van siempre, que es la convención de los
    anuncios ya publicados. La libreta solo se menciona si la sesión la tiene.
    """
    t = ["# Sesión %s. %s" % (num, tema), "",
         "Lo de abajo se copia tal cual en Classroom.", "",
         "## Título", "",
         "Sesión %s. %s" % (num, tema), "",
         "## Texto", "",
         "Aquí está la presentación de la sesión %s" % num
         + (" y la libreta de la demostración." if con_libreta else "."),
         "",
         "La presentación viene comprimida. Descárguenla, descompriman el "
         "archivo y abran el HTML con doble clic: funciona sin internet. Con "
         "la tecla A se abre el panel de apuntes de la lámina, y con la tecla "
         "T, los apuntes completos de la sesión."]
    if con_libreta:
        t += ["",
              "La libreta es la que corrimos en clase. Para abrirla, clic "
              "derecho sobre ella en Drive, Abrir con, Google Colaboratory."]
    if colab:
        t += ["", "La misma libreta, ya en Colab: " + colab]
    t += ["", "## Cómo se crea el borrador", "",
          "Con `GOOGLE_CLASSROOM_COURSES_ANNOUNCEMENTS_CREATE`, "
          "`state: DRAFT` y `assigneeMode: ALL_STUDENTS`, en el curso "
          "**876747535092**. Antes hay que listar los que ya existen con "
          "`ANNOUNCEMENTS_LIST` y "
          "`announcementStates: [\"DRAFT\", \"PUBLISHED\"]`, porque los "
          "borradores no salen por omisión y es fácil duplicar uno.", ""]
    return "\n".join(t)


def leeme(nombre, zip_mb, con_libreta, colab=None):
    p = ["Qué subir a Classroom, y en qué orden", "",
         "1. Sube a Drive estos %d archivo%s:" % (2 if con_libreta else 1,
                                                  "s" if con_libreta else ""),
         "", "     %s.zip   (%.1f MB)" % (nombre, zip_mb)]
    if con_libreta:
        p += ["     %s.ipynb" % nombre]
    p += ["",
          "2. Abre el anuncio en borrador del curso, en Classroom.",
          "3. Adjunta los dos archivos desde Drive." if con_libreta
          else "3. Adjunta el archivo desde Drive.",
          "4. Lee el texto y publica.", "",
          "El texto propuesto está en anuncio.md, al lado de este archivo.",
          "El zip lleva dentro un solo HTML: se abre con doble clic, sin",
          "servidor y sin conexión.", ""]
    if con_libreta:
        p += ["La libreta se abre en Colab con clic derecho, Abrir con, Google",
              "Colaboratory. Viene sin salidas guardadas: las celdas se corren",
              "en el momento, que es como se corrió en clase.", ""]
    if colab:
        p += ["La libreta YA está en tu Drive y el deck apunta a ella con esta",
              "liga:", "", "     " + colab, "",
              "OJO con los permisos: mientras el archivo siga privado, esa liga",
              "solo la abres tú. El grupo la abre cuando el archivo se comparte,",
              "o cuando Classroom pide los permisos al adjuntarla.", ""]
    return "\n".join(p)


def arma(s, ver=False):
    num, tema = s["num"], s["tema"]
    carpeta = RAIZ / s["carpeta"]
    deck = carpeta / "index.html"
    paquete = SALIDAS / (carpeta.name + ".html")
    nombre = nombre_archivo("S%02d - %s" % (int(num), tema))
    avisos = []

    if not paquete.exists():
        return None, ["sin paquete en salidas/: corre tools/empaquetar.py"]
    if deck.exists() and deck.stat().st_mtime > paquete.stat().st_mtime:
        avisos.append("el paquete es MÁS VIEJO que el index.html: "
                      "vuelve a correr tools/empaquetar.py")

    # La libreta de la demostración, si la sesión tiene.
    libretas = sorted(carpeta.glob("demo*.ipynb"))
    libreta = libretas[0] if libretas else None
    if len(libretas) > 1:
        avisos.append("hay %d libretas en la carpeta y se toma la primera: %s"
                      % (len(libretas), ", ".join(p.name for p in libretas)))
    if libreta:
        gen = libreta.with_suffix(".py")
        if gen.exists() and gen.stat().st_mtime > libreta.stat().st_mtime:
            avisos.append("la libreta es MÁS VIEJA que %s: vuelve a generarla"
                          % gen.name)
    else:
        avisos.append("la sesión no tiene libreta de Colab; si le toca una, "
                      "ver CLAUDE.md, 'La demostración se corre, no se "
                      "proyecta'")

    # Los apuntes son lo único que el grupo lee después de clase.
    if "class=\"apuntes\"" not in paquete.read_text(encoding="utf8",
                                                    errors="ignore"):
        avisos.append("el paquete NO lleva apuntes de estudio: el grupo "
                      "recibiría la presentación muda")

    d = DESTINO / nombre
    if ver:
        return (nombre, d, paquete, libreta), avisos

    d.mkdir(parents=True, exist_ok=True)
    z = d / (nombre + ".zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as f:
        f.write(paquete, paquete.name)
    if libreta:
        shutil.copy2(libreta, d / (nombre + ".ipynb"))
    else:
        for viejo in d.glob("*.ipynb"):
            viejo.unlink()
    zip_mb = z.stat().st_size / 1e6
    colab = liga_colab(deck)
    (d / "anuncio.md").write_text(anuncio(num, tema, bool(libreta), colab),
                                  encoding="utf8")
    (d / "LEEME.txt").write_text(leeme(nombre, zip_mb, bool(libreta), colab),
                                 encoding="utf8")
    return (nombre, d, paquete, libreta, zip_mb), avisos


def main():
    ap = argparse.ArgumentParser(description="Arma la carpeta de Classroom "
                                             "de una sesión.")
    ap.add_argument("sesion", nargs="?", help="3, S03 o el número a secas")
    ap.add_argument("--todas", action="store_true",
                    help="toda sesión que ya tenga paquete en salidas/")
    ap.add_argument("--ver", action="store_true",
                    help="dice qué haría, sin escribir nada")
    a = ap.parse_args()

    if a.todas:
        objetivo = sesiones()
    else:
        if not a.sesion:
            ap.error("di qué sesión, o pasa --todas")
        n = re.sub(r"\D", "", a.sesion)
        s = una(n) if n else None
        if not s:
            print("No encuentro la sesión %r en admin/sesiones.csv" % a.sesion)
            raise SystemExit(2)
        objetivo = [s]

    hechas, saltadas = 0, 0
    for s in objetivo:
        r, avisos = arma(s, ver=a.ver)
        if r is None:
            if not a.todas:
                print("S%02d: %s" % (int(s["num"]), avisos[0]))
            saltadas += 1
            continue
        hechas += 1
        if a.ver:
            nombre, d, paquete, libreta = r
            print("S%02d  %s" % (int(s["num"]), nombre))
            print("     zip de  %s" % paquete.name)
            print("     libreta %s" % (libreta.name if libreta else "ninguna"))
            print("     en      %s/" % d.relative_to(RAIZ))
        else:
            nombre, d, paquete, libreta, mb = r
            print("S%02d  %s/" % (int(s["num"]), d.relative_to(RAIZ)))
            print("     %s.zip   %.1f MB  (de %s, %.1f MB)"
                  % (nombre, mb, paquete.name, paquete.stat().st_size / 1e6))
            if libreta:
                print("     %s.ipynb   la libreta de Colab, de %s"
                      % (nombre, libreta.name))
            print("     anuncio.md y LEEME.txt")
        for v in avisos:
            print("     AVISO  %s" % v)

    print("classroom.py: %d carpeta%s %s, %d sin paquete"
          % (hechas, "" if hechas == 1 else "s",
             "por armar" if a.ver else "armadas", saltadas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
