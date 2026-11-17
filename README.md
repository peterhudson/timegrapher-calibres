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

## How the files get here

`scripts/build_manifest.py <timegrapher checkout>` lists the makers' files
the calibre table links to (`manifest.json`). `scripts/fetch.py manifest.json`
downloads them, saves a Wayback Machine copy of each, and writes the
`source.json` records. Re-running it skips files already recorded.

## Copyright and takedown

The makers' files here are the makers' own work, and their copyright stays
with them. Each one is copied unchanged from a page the maker published,
and `source.json` names that page. If you hold the rights to a file here
and want it removed, open an issue or email the project's owner, and it
will be taken down.

The rest of this repository (`source.json` files, README and scripts) is
released under CC0 1.0, the same as the project's recordings corpus.
