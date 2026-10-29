#!/usr/bin/env python3
"""Crea el esqueleto de una sesión a partir del plan.

    python3 tools/nueva-sesion.py 2

Lee `admin/sesiones.csv`, crea la carpeta que ahí se indica, y copia
`plantillas/tema-centrogeo/plantilla-sesion.html` con el título, la fecha y
las rutas relativas ya resueltas. No sobrescribe una sesión existente.
"""
import csv, sys, pathlib, re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto",
         "septiembre","octubre","noviembre","diciembre"]

def main(arg):
    n = int(re.sub(r"\D", "", arg))
    filas = list(csv.DictReader(open(RAIZ / "admin/sesiones.csv", encoding="utf-8")))
    fila = next((x for x in filas if int(x["num"]) == n), None)
    if not fila:
        print(f"No existe la sesión {n} en admin/sesiones.csv"); return 1

    destino = RAIZ / fila["carpeta"]
    if (destino / "index.html").exists():
        print(f"Ya existe {fila['carpeta']}/index.html. No se toca."); return 1

    a, m, d = fila["fecha"].split("-")
    fecha = f"{int(d)} de {MESES[int(m)-1]} de {a}"
    ruta = "../" * len(pathlib.Path(fila["carpeta"]).parts) + "plantillas/tema-centrogeo"

    html = (RAIZ / "plantillas/tema-centrogeo/plantilla-sesion.html").read_text(encoding="utf-8")
    html = (html.replace("{{TITULO}}", f"S{n:02d} {fila['tema']}, Fundamentos de IA")
                .replace("{{RUTA}}", ruta.rstrip("/"))
                .replace("{{SESION}}", str(n))
                .replace("{{TEMA}}", fila["tema"])
                .replace("{{FECHA}}", fecha))
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "index.html").write_text(html, encoding="utf-8")

    # Los ids estables son parte de la infraestructura de revisión: sin ellos
    # las notas se anclan a números y se pierden al reordenar láminas.
    import subprocess
    subprocess.run([sys.executable, str(RAIZ / "tools/ids.py"),
                    str(destino / "index.html")], check=True)

    print(f"Creada {fila['carpeta']}/index.html")
    print(f"  sesión {n}, {fila['dia']} {fila['fecha']}, {fila['horario']}")
    print(f"  bloque: {fila['bloque']}")
    print(f"  tema:   {fila['tema']}")
    print(f"  base:   {fila['base_2024']}")
    print(f"\n  Siguiente: escribir el contenido y el guion, luego correr")
    print(f"  ids.py, guion.py, verifica.py y tiempos.py.")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "1"))
