"""Read beat rates and lift angles from Ranfft for the calibre table's gaps.

Usage: python3 -I scripts/ranfft.py research/ranfft-targets.json research/ranfft.tsv

Polite: one request every 10 s, plain User-Agent, pages cached in
~/calvin-refs/ranfft/ so a re-run fetches nothing twice. Writes one line
per matched calibre: our calibre, Ranfft URL, Ranfft name, bph, lift.
"""
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request

BASE = "https://ranfft.org"
CACHE = os.path.expanduser("~/calvin-refs/ranfft")
os.makedirs(CACHE, exist_ok=True)
last = [0.0]
GAP = 10  # seconds between requests; at 2 s Ranfft began refusing after ~340 pages


def get(path):
    f = os.path.join(CACHE, re.sub(r"[^0-9A-Za-z._-]", "_", path) + ".html")
    if os.path.exists(f):
        return open(f, encoding="utf-8").read()
    time.sleep(max(0, GAP - (time.time() - last[0])))
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "timegrapher-calibre-research"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception as e:  # not cached, so a later run retries it
        print("  failed", path, e, file=sys.stderr)
        last[0] = time.time()
        if "403" in str(e) or "429" in str(e):
            sys.exit("Ranfft is refusing requests (%s); stopping. Re-run later: the cache keeps what was read." % e)
        return ""
    last[0] = time.time()
    open(f, "w", encoding="utf-8").write(body)
    return body


def key(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()  # Genève -> Geneve
    return "".join(c for c in s.lower() if c.isalnum())


# Our maker name -> Ranfft's, where neither the name nor a unique prefix finds it.
ALIASES = {"A. Schild": "AS", "VEB Glashütte": "GUB", "Shanghai Watch Factory": "Shanghai Watch Co",
           "Fontainemelon": "Fabrique d Horlogerie de Fontainemelon"}


def find_maker(maker):
    for n in (ALIASES.get(maker, maker), maker.split(" (")[0]):
        if key(n) in makers:
            return makers[key(n)]
    hits = {p for k, p in makers.items() if k.startswith(key(maker))}  # "Buren" -> "Buren Watch Company"
    return hits.pop() if len(hits) == 1 else None


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
    path = find_maker(maker)
    if not path:
        print("no Ranfft maker for", maker, file=sys.stderr)
        continue
    calibres = {}
    for page in paged(path):
        for cpath, text in links(page, "caliber"):
            calibres.setdefault(key(text), cpath)
            calibres.setdefault(key(cpath.split("-", 1)[1]), cpath)
    for t in [t for t in targets if t["maker"] == maker]:
        bare = re.sub(r"\s*\([^)]*\)", "", t["calibre"]).strip()  # drop notes like "(52°)"
        names = [t["calibre"], t["calibre"][len(maker):], bare, bare[len(maker):]]
        names += [f"{maker} {f}" for f in t["family"]] + t["family"]
        match = "exact"
        cpath = next((calibres[key(n)] for n in names if key(n) in calibres), None)
        if not cpath:  # fall back to the base number: "ETA 2892A2" -> Ranfft "ETA 2892"
            base = re.match(r"\D*\d+", bare[len(maker):] if bare.startswith(maker) else bare)
            for n in ([f"{maker} {base.group(0).strip()}", base.group(0)] if base else []):
                if key(n) in calibres:
                    cpath, match = calibres[key(n)], "base"
                    break
        if not cpath:
            continue
        page = get(cpath)
        title = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        title = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", title.group(1))).split()) if title else ""
        rows.append([t["calibre"], BASE + cpath, title, figure(page, "Beat rate"), figure(page, "Lift angle"), match])
    print(maker, len(rows), file=sys.stderr)

with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write("calibre\tranfft_url\tranfft_name\tbph\tlift_deg\tmatch\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print(len(rows), "matched", file=sys.stderr)
