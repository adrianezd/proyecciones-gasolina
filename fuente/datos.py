"""
Descarga de precios de carburantes del Ministerio para la Transicion
Ecologica, provincia a provincia.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

CACHE = Path(__file__).parent.parent / "cache"
CACHE.mkdir(exist_ok=True)

CABECERAS = {
    "User-Agent": "proyecciones-gasolina/1.0 (+https://github.com/adrianezd/proyecciones-gasolina)",
    "Accept": "application/json, text/plain, */*",
}

CARBURANTES = ("https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes"
               "/PreciosCarburantes/EstacionesTerrestres")

PROVINCIAS = [
    ("01","Álava"),("02","Albacete"),("03","Alicante"),("04","Almería"),("05","Ávila"),
    ("06","Badajoz"),("07","Illes Balears"),("08","Barcelona"),("09","Burgos"),("10","Cáceres"),
    ("11","Cádiz"),("12","Castellón"),("13","Ciudad Real"),("14","Córdoba"),("15","A Coruña"),
    ("16","Cuenca"),("17","Girona"),("18","Granada"),("19","Guadalajara"),("20","Gipuzkoa"),
    ("21","Huelva"),("22","Huesca"),("23","Jaén"),("24","León"),("25","Lleida"),
    ("26","La Rioja"),("27","Lugo"),("28","Madrid"),("29","Málaga"),("30","Murcia"),
    ("31","Navarra"),("32","Ourense"),("33","Asturias"),("34","Palencia"),("35","Las Palmas"),
    ("36","Pontevedra"),("37","Salamanca"),("38","Santa Cruz de Tenerife"),("39","Cantabria"),
    ("40","Segovia"),("41","Sevilla"),("42","Soria"),("43","Tarragona"),("44","Teruel"),
    ("45","Toledo"),("46","Valencia"),("47","Valladolid"),("48","Bizkaia"),("49","Zamora"),
    ("50","Zaragoza"),("51","Ceuta"),("52","Melilla"),
]


def _descargar(url: str, clave: str, params: dict | None = None) -> Any:
    fichero = CACHE / f"{clave}.json"
    try:
        r = httpx.get(url, params=params, headers=CABECERAS,
                      timeout=40.0, follow_redirects=True)
        r.raise_for_status()
        datos = r.json()
        fichero.write_text(json.dumps(datos), encoding="utf-8")
        print(f"  descargado  {clave}")
        return datos
    except Exception as e:
        if fichero.exists():
            print(f"  CACHE       {clave}  ({type(e).__name__})")
            return json.loads(fichero.read_text(encoding="utf-8"))
        print(f"  FALLO       {clave}  ({e})")
        return None


def _precio(v: Any) -> float | None:
    """El Ministerio manda los precios como texto con coma decimal."""
    if not v:
        return None
    try:
        n = float(str(v).replace(",", "."))
    except ValueError:
        return None
    return n if n > 0 else None


def gasolineras(provincia: str) -> list[dict]:
    datos = _descargar(f"{CARBURANTES}/FiltroProvincia/{provincia}", f"carb-{provincia}")
    if not isinstance(datos, dict):
        return []

    salida = []
    for e in datos.get("ListaEESSPrecio", []):
        g95 = _precio(e.get("Precio Gasolina 95 E5"))
        gao = _precio(e.get("Precio Gasoleo A"))
        if g95 is None and gao is None:
            continue
        salida.append({
            "rotulo": (e.get("Rótulo") or "Sin rotulo").title(),
            "direccion": (e.get("Dirección") or "").title(),
            "municipio": (e.get("Municipio") or "").title(),
            "g95": g95,
            "gasoleo": gao,
        })
    return salida
