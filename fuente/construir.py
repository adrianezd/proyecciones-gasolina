"""
Generador de esta pagina: precio de la gasolina, portada + una pagina por
provincia (53 URLs en total).

    python -m fuente.construir
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import calculo, datos
from .enlaces import HUB, MENU, jsonld_pagina

AQUI = Path(__file__).parent
PROYECTO = AQUI.parent
SALIDA = PROYECTO / "docs"

BASE_URL = "https://adrianezd.github.io/proyecciones-gasolina"
FUENTE_NOMBRE = "Ministerio para la Transicion Ecologica"
FUENTE_URL = "https://www.miteco.gob.es"

entorno = Environment(
    loader=FileSystemLoader(AQUI / "plantillas"),
    autoescape=select_autoescape(["html"]),
)

HOY = dt.date.today().isoformat()
rutas_generadas: list[str] = []


def json_seguro(obj) -> str:
    texto = json.dumps(obj, ensure_ascii=False)
    return (texto
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace(" ", "\\u2028")
            .replace(" ", "\\u2029"))


def escribir(ruta_rel: str, plantilla: str, **contexto) -> None:
    destino = SALIDA / ruta_rel / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)

    profundidad = len([p for p in ruta_rel.split("/") if p])
    contexto.setdefault("raiz", "../" * profundidad or "./")
    contexto.setdefault("menu", MENU)
    contexto.setdefault("hub", HUB)
    contexto.setdefault("base_url", BASE_URL)
    contexto.setdefault("ruta", "/" + ruta_rel)
    contexto.setdefault("generado", HOY)
    contexto.setdefault("jsonld", jsonld_pagina(
        titulo=contexto["titulo"],
        descripcion=contexto["descripcion"],
        url=contexto["base_url"] + contexto["ruta"],
        fuente_nombre=FUENTE_NOMBRE,
        fuente_url=FUENTE_URL,
    ))

    destino.write_text(entorno.get_template(plantilla).render(**contexto), encoding="utf-8")
    rutas_generadas.append(ruta_rel)
    print(f"  escrito     {ruta_rel or '/'}")


def main() -> None:
    print("Construyendo: gasolina\n")

    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir(parents=True)
    shutil.copytree(PROYECTO / "estatico", SALIDA / "estatico")

    carpeta_datos = SALIDA / "datos"
    carpeta_datos.mkdir(parents=True, exist_ok=True)

    primera = None

    for cod, nombre in datos.PROVINCIAS:
        estaciones = datos.gasolineras(cod)
        if not estaciones:
            print(f"  sin datos   gasolina {nombre}")
            continue

        p95 = sorted(e["g95"] for e in estaciones if e["g95"])
        pga = sorted(e["gasoleo"] for e in estaciones if e["gasoleo"])
        baratas95 = sorted((e for e in estaciones if e["g95"]), key=lambda e: e["g95"])[:10]
        baratasDiesel = sorted((e for e in estaciones if e["gasoleo"]), key=lambda e: e["gasoleo"])[:10]

        paquete = {
            "cod": cod,
            "nombre": nombre,
            "total": len(estaciones),
            "combustibles": {
                "g95": {
                    "etiqueta": "Gasolina 95",
                    "med": round(calculo.percentil(p95, 0.5), 3) if p95 else None,
                    "min": p95[0] if p95 else None,
                    "max": p95[-1] if p95 else None,
                    "hist": calculo.histograma(p95),
                    "baratas": baratas95,
                } if p95 else None,
                "gasoleo": {
                    "etiqueta": "Gasoleo A",
                    "med": round(calculo.percentil(pga, 0.5), 3) if pga else None,
                    "min": pga[0] if pga else None,
                    "max": pga[-1] if pga else None,
                    "hist": calculo.histograma(pga),
                    "baratas": baratasDiesel,
                } if pga else None,
            },
        }

        (carpeta_datos / f"{cod}.json").write_text(json.dumps(paquete), encoding="utf-8")

        if primera is None:
            primera = paquete

        escribir(
            cod, "gasolina.html",
            titulo=f"Precio de la gasolina hoy en {nombre}",
            descripcion=f"Precio medio de la gasolina 95 y el gasoleo A hoy en {nombre}, "
                        f"con las estaciones mas baratas. Datos oficiales del Ministerio.",
            acento="gasolina",
            provincia=nombre,
            cod_actual=cod,
            provincias=datos.PROVINCIAS,
            datos_json=json_seguro({"provincia": paquete, "raiz": "../"}),
        )

    if primera:
        escribir(
            "", "gasolina.html",
            titulo="Precio de la gasolina hoy en España",
            descripcion="Precio medio de la gasolina 95 y el gasoleo A por provincia, "
                        "con las estaciones mas baratas. Datos oficiales del Ministerio.",
            acento="gasolina",
            provincia=None,
            cod_actual=primera["cod"],
            provincias=datos.PROVINCIAS,
            datos_json=json_seguro({"provincia": primera, "raiz": "./"}),
        )
    else:
        print("  SALTADA     gasolina (el Ministerio no devolvio datos de ninguna provincia)")

    urls = "".join(
        f"\n  <url><loc>{BASE_URL}/{r}{'/' if r else ''}</loc>"
        f"<lastmod>{HOY}</lastmod></url>"
        for r in sorted(set(rutas_generadas))
    )
    (SALIDA / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}\n</urlset>\n",
        encoding="utf-8",
    )
    (SALIDA / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    (SALIDA / ".nojekyll").write_text("", encoding="utf-8")

    print(f"\nListo. {len(rutas_generadas)} paginas en docs/")


if __name__ == "__main__":
    main()
