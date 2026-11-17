"""List the makers' files the Timegrapher calibre table links to.

Usage: python3 -I build_manifest.py <timegrapher checkout> > manifest.json

Reads the table's sources and the research link files, keeps files on the
makers' own sites, and prints one entry per file with the folder it goes in.
"""
import json
import re
import sys

repo = sys.argv[1]
table = json.load(open(f"{repo}/crates/timegrapher-core/data/train-wheels.json", encoding="utf-8"))
research = f"{repo}/docs/research"

MAKERS = {  # host -> copyright holder
    "download.s21i.huaweicloudsite.cn": "Hangzhou Watch Co.",
    "50003482.s21i.huaweicloudsite.cn": "Hangzhou Watch Co.",
    "omo-oss-file110.thefastfile.com": "Liaoning Peacock Watch",
    "omo-oss-image1.thefastimg.com": "Liaoning Peacock Watch",
    "www.seagullwatch.com": "Tianjin Seagull",
    "en.jingheshiye.com": "Shanghai Jinghe",
    "www.sellita.ch": "Sellita",
    "seikoserviceusa.com": "Seiko",
    "miyotamovement.com": "Citizen (Miyota)",
}
FILE = re.compile(r"\.(pdf|jpe?g|png)$", re.I)
makers = {r["calibre"]: r["maker"] for r in table}


def slug(s):
    return re.sub(r"[^0-9a-zⅠ-ⅿ]+", "-", s.lower()).strip("-")


def kind(url, hint):
    if hint:
        return hint
    if url.lower().endswith(".pdf"):
        return "spec sheet"
    return "photo"


out, seen = [], set()


def add(calibre, url, hint=None):
    if not url.startswith("http"):
        return
    host = url.split("/")[2]
    if host not in MAKERS or not FILE.search(url) or (calibre, url) in seen:
        return
    seen.add((calibre, url))
    maker = makers.get(calibre, calibre.split(" ")[0])
    out.append({
        "calibre": calibre,
        "folder": f"{slug(maker)}/{slug(calibre)}",
        "url": url,
        "kind": kind(url, hint),
        "copyright": MAKERS[host],
    })


for r in table:
    for s in r.get("sources", []):
        add(r["calibre"], s.split(" ")[0], "manual" if "manual for watch" in s else None)
for name, hint in (("hangzhou-movement-photos.json", "photo"), ("peacock-movement-photos.json", "photo"),
                   ("jinghe-movement-photos.json", None)):
    for calibre, v in json.load(open(f"{research}/{name}", encoding="utf-8")).items():
        if isinstance(v, dict):
            for key, urls in v.items():
                for u in urls:
                    add(calibre, u, "drawing" if key == "function_diagram" else hint)
        else:
            for urls in v.values():
                for u in urls:
                    add(calibre, u, hint)
for calibre, manuals in json.load(open(f"{research}/seagull-watch-manuals.json", encoding="utf-8")).items():
    for m in manuals:
        add(calibre, m["manual"], "manual")
# A file several calibres cite (a maker's catalogue) is kept once, in
# <maker>/shared/, and lists the calibres it serves.
by_url = {}
for e in out:
    by_url.setdefault(e["url"], []).append(e)
merged = []
for url, es in by_url.items():
    e = dict(es[0])
    if len(es) > 1:
        e["folder"] = es[0]["folder"].split("/")[0] + "/shared"
    e["calibres"] = sorted({x["calibre"] for x in es})
    del e["calibre"]
    merged.append(e)
out = merged
json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
print(len(out), "files", file=sys.stderr)
