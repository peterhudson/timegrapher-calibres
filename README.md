# Timegrapher calibre assets

Spec sheets, drawings and movement photos for the calibres in
[Timegrapher](https://github.com/peterhudson/timegrapher)'s calibre table
(`crates/timegrapher-core/data/train-wheels.json`). They are kept here so
the app's links keep working when a maker's site moves or goes offline, and
so the main repository stays small.

## Layout

```
<maker>/<calibre>/
  source.json          where each file came from
  <file>               the file as the source published it
```

`<maker>` and `<calibre>` use the table's `maker` and `calibre` names,
lower-cased, with spaces as `-` (for example `hangzhou/hangzhou-hz36k0e/`).

Each `source.json` lists every file in the folder:

```json
[
  {
    "file": "assembly-drawing-HZ36K0E.pdf",
    "kind": "spec sheet",
    "url": "https://… (the maker's original address)",
    "fetched": "2026-11-17",
    "archive": "https://web.archive.org/web/… (a Wayback Machine copy)",
    "copyright": "Hangzhou Watch Co.",
    "calibres": ["Hangzhou HZ36K0E"]
  }
]
```

A file several calibres cite, such as a maker's catalogue, is kept once in
`<maker>/shared/`, and its `calibres` lists them all.

`kind` is one of `spec sheet`, `drawing`, `manual`, `photo (dial side)`,
`photo (balance side)` or `photo`.

Records written since 2026-11-25 also carry `sha256` (of the file as
downloaded) and, for files added by hand, a `licence` note saying what
terms the source states.

## Addresses kept without the file

`addresses.json` lists documents and photos for the calibres that are **not**
copied here, only their addresses: each record gives the calibres, the
kind, the address, the date it was checked, the copyright holder, the
source's terms quoted word for word where it states them, and why the
file is not kept. A file is kept as an address only when its source
forbids copying or redistribution, when it sits on a third party's site
rather than the maker's own, when it is a section of a web page rather
than a file, when it could not be read, or when its terms are not yet
checked.

## How the files get here

`scripts/build_manifest.py <timegrapher checkout>` lists the makers' files
the calibre table links to (`manifest.json`), plus the files found by hand
in `research/added-by-hand.json`. `scripts/fetch.py manifest.json`
downloads them and writes the `source.json` records; with `--archive` it
also asks the Wayback Machine for a copy of each. Re-running it skips files
already recorded.

So far only 5 records have an `archive` link; the rest are `null` until an
archive pass fills them in.

## Copyright and takedown

The makers' files here are the makers' own work, and their copyright stays
with them. They are **not** covered by this repository's CC0 dedication.
Each maker's folder has a `NOTICE` saying so. Each file is copied unchanged
from the maker's own site, and its `source.json` record gives the address it
was downloaded from (`url`).

**To have a file removed**, open a
[takedown request](https://github.com/peterhudson/timegrapher-calibres/issues/new?template=takedown.yml)
naming the file, or contact the repository's owner through GitHub. The file
and its record are then deleted from `main` and the app stops linking to it.
Earlier commits still hold a copy until the history is rewritten; whether to
do that is the owner's decision for each request.

The rest of this repository (`source.json` files, README and scripts) is
released under CC0 1.0, the same as the project's recordings corpus, except
`research/ranfft.tsv`. That file holds figures read from Ranfft's watch
movement database ([ranfft.org](https://ranfft.org)), which are credited to
Ranfft and not covered by CC0. The project read Ranfft slowly, only for
specific gaps in the table, and stopped when Ranfft limited automated
reading.
