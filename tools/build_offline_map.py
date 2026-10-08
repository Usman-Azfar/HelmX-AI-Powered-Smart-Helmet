"""Builds the bundled offline map package for HelmX (Lahore District).

Usage:  python tools/build_offline_map.py app/src/main/assets/offline


Output (OUT dir):
  tiles/{z}/{x}/{y}.pbf      OpenMapTiles-schema vector tiles from OpenFreeMap, z0-14, decompressed
  fonts/{fontstack}/{range}.pbf
  sprites/ofm(.json|.png|@2x.json|@2x.png)
  styles/liberty.json, styles/fiord.json   offline copies pointing at https://helmx.local/...
  maplibre-gl.js, maplibre-gl.css
"""
import concurrent.futures as cf
import gzip
import json
import math
import os
import sys
import time
import urllib.request

OUT = sys.argv[1]
BBOX = (74.0068490, 31.2005939, 74.6546712, 31.7134238)  # Lahore District (OSM relation 16117666)
MAXZOOM = 14
UA = "HelmX-offline-build/1.0 (FYP project; one-time Lahore extract)"
LOCAL = "https://helmx.local"

FONTS = ["Noto Sans Regular", "Noto Sans Bold", "Noto Sans Italic"]
# Latin, Latin-ext, Greek/Cyrillic-ish, Arabic/Urdu, punctuation, Arabic presentation forms
RANGES = [0, 256, 512, 768, 1024, 1536, 1792, 8192, 8448, 64256, 64512, 64768, 65024, 65280]


def get(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
                    data = gzip.decompress(data)
                return r.status, data
        except urllib.error.HTTPError as e:
            if e.code in (204, 404):
                return e.code, b""
            if attempt == retries - 1:
                raise
        except Exception:
            if attempt == retries - 1:
                raise
        time.sleep(1 + attempt)


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def tile_range(z):
    def x_of(lon):
        return int((lon + 180.0) / 360.0 * 2 ** z)

    def y_of(lat):
        r = math.radians(lat)
        return int((1.0 - math.asinh(math.tan(r)) / math.pi) / 2.0 * 2 ** z)

    x0, x1 = x_of(BBOX[0]), x_of(BBOX[2])
    y0, y1 = y_of(BBOX[3]), y_of(BBOX[1])  # north edge has the smaller y
    return [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def main():
    tilejson = json.loads(get("https://tiles.openfreemap.org/planet")[1])
    template = tilejson["tiles"][0]
    tiles = [t for z in range(0, MAXZOOM + 1) for t in tile_range(z)]
    print(f"{len(tiles)} tiles to fetch from {template}", flush=True)

    sizes = {"tiles": 0}
    empty = 0

    def fetch_tile(t):
        z, x, y = t
        status, data = get(template.format(z=z, x=x, y=y))
        return t, status, data

    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for i, (t, status, data) in enumerate(pool.map(fetch_tile, tiles), 1):
            z, x, y = t
            if data:
                save(os.path.join(OUT, "tiles", str(z), str(x), f"{y}.pbf"), data)
                sizes["tiles"] += len(data)
            else:
                empty += 1
            if i % 200 == 0:
                print(f"  {i}/{len(tiles)} tiles", flush=True)
    print(f"tiles: {len(tiles) - empty} saved, {empty} empty, {sizes['tiles'] / 1e6:.1f} MB", flush=True)

    sizes["fonts"] = 0
    for font in FONTS:
        for start in RANGES:
            rng = f"{start}-{start + 255}"
            url = f"https://tiles.openfreemap.org/fonts/{urllib.parse.quote(font)}/{rng}.pbf"
            status, data = get(url)
            if data:
                save(os.path.join(OUT, "fonts", font, f"{rng}.pbf"), data)
                sizes["fonts"] += len(data)
    print(f"fonts: {sizes['fonts'] / 1e6:.2f} MB", flush=True)

    sizes["sprites"] = 0
    for suffix in [".json", ".png", "@2x.json", "@2x.png"]:
        status, data = get(f"https://tiles.openfreemap.org/sprites/ofm_f384/ofm{suffix}")
        save(os.path.join(OUT, "sprites", f"ofm{suffix}"), data)
        sizes["sprites"] += len(data)
    print(f"sprites: {sizes['sprites'] / 1e6:.2f} MB", flush=True)

    for name in ["maplibre-gl.js", "maplibre-gl.css"]:
        status, data = get(f"https://unpkg.com/maplibre-gl@4.7.1/dist/{name}")
        save(os.path.join(OUT, name), data)
        print(f"{name}: {len(data) / 1e6:.2f} MB", flush=True)

    for style_name in ["liberty", "fiord"]:
        style = json.loads(get(f"https://tiles.openfreemap.org/styles/{style_name}")[1])
        style["sources"] = {
            "openmaptiles": {
                "type": "vector",
                "tiles": [LOCAL + "/tiles/{z}/{x}/{y}.pbf"],
                "minzoom": 0,
                "maxzoom": MAXZOOM,
                "bounds": list(BBOX),
                "attribution": tilejson.get("attribution", ""),
            }
        }
        style["layers"] = [l for l in style["layers"] if l.get("source") in (None, "openmaptiles")]
        style["sprite"] = LOCAL + "/sprites/ofm"
        style["glyphs"] = LOCAL + "/fonts/{fontstack}/{range}.pbf"
        save(os.path.join(OUT, "styles", f"{style_name}.json"), json.dumps(style, separators=(",", ":")).encode())
    print("styles written", flush=True)

    # Shown in Settings -> Offline map. The tile set version starts with its build date (YYYYMMDD).
    version = template.split("/planet/")[1].split("/")[0]
    meta = {
        "region": "Lahore District",
        "dataDate": f"{version[0:4]}-{version[4:6]}-{version[6:8]}",
        "maxZoom": MAXZOOM,
        "source": "OpenFreeMap (OpenStreetMap data)",
    }
    save(os.path.join(OUT, "meta.json"), json.dumps(meta).encode())


if __name__ == "__main__":
    import urllib.parse  # noqa: F401  (used above)
    main()
