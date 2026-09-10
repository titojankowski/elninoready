#!/usr/bin/env python3
"""Build actions-beta/cities.json from the GeoNames cities15000 dump (CC BY 4.0).

    curl -sLO https://download.geonames.org/export/dump/cities15000.zip && unzip -o cities15000.zip
    python3 build_cities.py cities15000.txt

Keeps cities with population >= 100,000, plus every national capital, so the
picker covers most of the world's people in ~5,000 names. Output rows:
    [name, country_code, admin1_code, lat, lon, population]
The dump itself is not committed (it's 10 MB and changes); the JSON is.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "actions-beta", "cities.json")
MIN_POP = 100_000


def main(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            name, ascii_name, feature_code, cc, admin1, pop = c[1], c[2], c[7], c[8], c[10], int(c[14] or 0)
            lat, lon = round(float(c[4]), 2), round(float(c[5]), 2)
            if pop < MIN_POP and feature_code != "PPLC":
                continue
            rows.append([name if name == ascii_name else "%s|%s" % (name, ascii_name), cc, admin1, lat, lon, pop])
    rows.sort(key=lambda r: -r[5])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print("%s: %d cities, %d KB" % (OUT, len(rows), os.path.getsize(OUT) // 1024))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "cities15000.txt")
