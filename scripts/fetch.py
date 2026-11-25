"""Download the files in manifest.json into <maker>/<calibre>/ and record
each one in that folder's source.json, with a Wayback Machine copy.

Usage: python3 -I scripts/fetch.py manifest.json [--archive]   (from the repo root)

Without --archive the Wayback step is skipped and "archive" is recorded as
null; a later --archive pass fills it in.

Standard library only. Re-running skips files already recorded. Waits a
second between requests so the makers' and archive's servers are not
hammered.
"""
import datetime
import hashlib
import json
import os
import sys
import time
import urllib.request

UA = {"User-Agent": "timegrapher-calibres-archiver"}
today = datetime.date.today().isoformat()


def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read(), r.geturl()


def wayback(url):
    try:
        body, _ = get("https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe=""))
        snap = json.loads(body).get("archived_snapshots", {}).get("closest")
        if snap and snap.get("available"):
            return snap["url"]
        _, final = get("https://web.archive.org/save/" + url, timeout=120)
        return final if "/web/" in final else None
    except Exception as e:  # the archive is slow or refuses: record none
        print("  no archive:", e, file=sys.stderr)
        return None


import urllib.parse  # noqa: E402

ARCHIVE = "--archive" in sys.argv[2:]
failed = []
for i, e in enumerate(json.load(open(sys.argv[1], encoding="utf-8"))):
    os.makedirs(e["folder"], exist_ok=True)
    rec_path = os.path.join(e["folder"], "source.json")
    recs = json.load(open(rec_path, encoding="utf-8")) if os.path.exists(rec_path) else []
    if any(r["url"] == e["url"] for r in recs):
        continue
    base = os.path.basename(urllib.parse.urlparse(e["url"]).path)
    name = urllib.parse.unquote(base)
    if any(r["file"] == name for r in recs):
        name = hashlib.sha1(e["url"].encode()).hexdigest()[:8] + "-" + name
    print(f"[{i}] {e['folder']}/{name}", file=sys.stderr)
    try:
        body, _ = get(e["url"])
    except Exception as ex:
        print("  failed:", ex, file=sys.stderr)
        failed.append(e["url"])
        continue
    open(os.path.join(e["folder"], name), "wb").write(body)
    recs.append({"file": name, "kind": e["kind"], "url": e["url"], "fetched": today,
                 "archive": wayback(e["url"]) if ARCHIVE else None, "copyright": e["copyright"],
                 "calibres": e["calibres"]})
    recs[-1]["sha256"] = hashlib.sha256(body).hexdigest()
    if "licence" in e:
        recs[-1]["licence"] = e["licence"]
    json.dump(recs, open(rec_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    time.sleep(1)
print(len(failed), "failed", *failed, sep="\n", file=sys.stderr)
