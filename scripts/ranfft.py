"""Read beat rates and lift angles from Ranfft for the calibre table's gaps.

Usage: python3 -I scripts/ranfft.py research/ranfft-targets.json research/ranfft.tsv

Polite: one request every 2 s, plain User-Agent, pages cached in
~/calvin-refs/ranfft/ so a re-run fetches nothing twice. Writes one line
per matched calibre: our calibre, Ranfft URL, Ranfft name, bph, lift.
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

BASE = "https://ranfft.org"
CACHE = os.path.expanduser("~/calvin-refs/ranfft")
os.makedirs(CACHE, exist_ok=True)
last = [0.0]


def get(path):
    f = os.path.join(CACHE, re.sub(r"[^0-9A-Za-z._-]", "_", path) + ".html")
    if os.path.exists(f):
        return open(f, encoding="utf-8").read()
    time.sleep(max(0, 2 - (time.time() - last[0])))
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "timegrapher-calibre-research"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception as e:
        print("  failed", path, e, file=sys.stderr)
        body = ""
    last[0] = time.time()
    open(f, "w", encoding="utf-8").write(body)
    return body


def key(s):
    return "".join(c for c in s.lower() if c.isalnum())


def links(page, kind):
    """(path, text) for every /manufacturer/ or /caliber/ link on a page."""
    out = []
    for m in re.finditer(r'href="(?:https://ranfft\.org)?(/' + kind + r'/\d+-[^"?#]+)[^"]*"[^>]*>(.*?)</a>', page, re.S):
        body = m.group(2)
        head = re.search(r"<h[1-4][^>]*>(.*?)</h[1-4]>", body, re.S)  # cards: the name is the heading
        text = html.unescape(re.sub(r"<[^>]+>", " ", head.group(1) if head else body))
        out.append((m.group(1), " ".join(text.split())))
    return out


def paged(path):
    """Every page of a paginated list, until a page adds no new links."""
    seen, pages, n = set(), [], 1
    while True:
        page = get(path + (f"?page={n}" if n > 1 else ""))
        new = {l for l in links(page, "caliber") + links(page, "manufacturer")} - seen
        if not new:
            return pages
        seen |= new
        pages.append(page)
        n += 1


def figure(page, label):
    m = re.search(r">\s*" + label + r"\s*</div>\s*<div[^>]*>\s*([\d.,]+)", page)
    return m.group(1).replace(",", "") if m else ""


targets = json.load(open(sys.argv[1], encoding="utf-8"))
makers = {}
for page in paged("/manufacturers"):
    for path, text in links(page, "manufacturer"):
        makers.setdefault(key(text or path.split("-", 1)[1]), path)
        makers.setdefault(key(path.split("-", 1)[1]), path)
print(len(makers), "Ranfft manufacturers", file=sys.stderr)

rows = []
for maker in sorted({t["maker"] for t in targets}):
    path = makers.get(key(maker)) or makers.get(key(maker.split(" (")[0]))
    if not path:
        print("no Ranfft maker for", maker, file=sys.stderr)
        continue
    calibres = {}
    for page in paged(path):
        for cpath, text in links(page, "caliber"):
            calibres.setdefault(key(text), cpath)
            calibres.setdefault(key(cpath.split("-", 1)[1]), cpath)
    for t in [t for t in targets if t["maker"] == maker]:
        names = [t["calibre"], t["calibre"][len(maker):]] + [f"{maker} {f}" for f in t["family"]] + t["family"]
        cpath = next((calibres[key(n)] for n in names if key(n) in calibres), None)
        if not cpath:
            continue
        page = get(cpath)
        title = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        title = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", title.group(1))).split()) if title else ""
        rows.append([t["calibre"], BASE + cpath, title, figure(page, "Beat rate"), figure(page, "Lift angle")])
    print(maker, len(rows), file=sys.stderr)

with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write("calibre\tranfft_url\tranfft_name\tbph\tlift_deg\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print(len(rows), "matched", file=sys.stderr)
