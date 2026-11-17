#!/usr/bin/env python3
"""
Build a standalone HTML viewer that highlights feature evidence in stories.

Reads a directory of stories and a directory of feature JSONs produced by
`apply_features --evidence`, and writes one self-contained HTML file.

Stories can be flat files (story0.txt, 12.txt, ...) or folders
(<id>_<title>/story.txt). Each is paired with
<features-dir>/**/prompt_<id:05d>__*.features.json, matching on the first
number in the story's file or folder name.

Usage:
    python -m storyscope.viewer.build_viewer \
        --stories-dir data/stories_kannada \
        --features-dir outputs/features_kannada_evidence \
        --taxonomy data/taxonomy.json --output viewer.html
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEMPLATE = Path(__file__).with_name("template.html")


def story_id(path: Path):
    name = path.parent.name if path.name == "story.txt" else path.stem
    m = re.search(r"\d+", name)
    return (int(m.group()) if m else None), name


def find_stories(stories_dir: Path):
    paths = list(stories_dir.glob("*/story.txt")) or sorted(stories_dir.glob("*.txt"))
    return sorted(paths, key=lambda p: (story_id(p)[0] is None, story_id(p)[0] or 0, p.name))


def index_features(features_dir: Path):
    idx = {}
    for p in features_dir.rglob("*.features.json"):
        m = re.match(r"prompt_(\d+)__", p.name)
        if m:
            idx.setdefault(int(m.group(1)), p)
    return idx


def feature_meta(taxonomy_path: Path, ids):
    data = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    tax = data.get("feature_taxonomy", data)
    meta = {}
    for dim in tax.values():
        if not isinstance(dim, dict):
            continue
        for asp in dim.get("aspects", {}).values():
            for f in asp.get("features", []):
                if f["id"] in ids:
                    meta[f["id"]] = {"name": f["name"], "question": f["question"], "values": f.get("values", []), "type": f.get("type")}
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stories-dir", required=True)
    ap.add_argument("--features-dir", required=True)
    ap.add_argument("--taxonomy", default="data/taxonomy.json")
    ap.add_argument("--output", default="viewer.html")
    args = ap.parse_args()

    features = index_features(Path(args.features_dir))
    data, skipped = [], 0
    for sp in find_stories(Path(args.stories_dir)):
        sid, name = story_id(sp)
        fp = features.get(sid)
        if fp is None:
            skipped += 1
            continue
        feat = json.loads(fp.read_text(encoding="utf-8"))
        title = feat.get("story_title") or name
        data.append({
            "title": f"{sid}: {title}" if sid is not None else title,
            "text": sp.read_text(encoding="utf-8"),
            "model": feat.get("metadata", {}).get("model"),
            "features": feat["features"],
        })
    if not data:
        raise SystemExit("No stories matched a features file (expected prompt_<id>__*.features.json).")

    ids = {fid for d in data for fid in d["features"]}
    meta = feature_meta(Path(args.taxonomy), ids)
    html = (TEMPLATE.read_text(encoding="utf-8")
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__META__", json.dumps(meta, ensure_ascii=False)))
    # The template is a page fragment (title and style, then body); wrap it for standalone use.
    head, body = html.split("<header>", 1)
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            + head + "</head><body><header>" + body + "</body></html>")
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Wrote {args.output}: {len(data)} stories ({skipped} without features skipped)")


if __name__ == "__main__":
    main()
