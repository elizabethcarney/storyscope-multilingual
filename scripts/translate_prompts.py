"""Translate the `title` and `prompt` fields of a prompts JSON file into a target language
using the OpenAI API. IDs are preserved; proper nouns are adapted to the target language.

Input : JSON list of {"id", "title", "prompt"}
Output: JSON list of {"id", "title", "prompt"} with title/prompt translated
        (and "title_en"/"prompt_en" with the originals, if --keep-source is given).

Usage:
    # put OPENAI_API_KEY=sk-... in <repo>/.env
    python scripts/translate_prompts.py \
        --input data/prompts_train.json \
        --output data/prompts_train_kannada.json \
        --language Kannada \
        --limit 20

Re-running resumes: ids already present in --output are skipped.
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from openai import OpenAI

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path):
    """Minimal .env loader (KEY=VALUE lines); real env vars take precedence."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.removeprefix("export ").strip()
            v = v.strip().strip("'\"")
            os.environ.setdefault(k, v)


SYSTEM = (
    "You are a professional translator. The user gives a JSON object with a "
    '"title" and a "prompt" (a story-writing prompt) in English. Translate both '
    "into {lang}. Preserve meaning, tone, and any numbers exactly (e.g. word "
    "counts). Adapt proper nouns (character names, places, and the names in the "
    "title) to {lang}, using the natural transliteration or established "
    "{lang} form, and use exactly the same rendering of each name in the title "
    'and the prompt. Reply with only a JSON object: {{"title": "...", "prompt": "..."}}.'
)


def translate(client, model, lang, title, text, retries=5):
    """Translate title and prompt together so proper nouns stay consistent."""
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM.format(lang=lang)},
                    {"role": "user", "content": json.dumps({"title": title, "prompt": text}, ensure_ascii=False)},
                ],
            )
            out = json.loads(resp.choices[0].message.content)
            return out["title"].strip(), out["prompt"].strip()
        except Exception as e:  # rate limits, transient errors
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  retry in {wait}s ({type(e).__name__}: {e})", file=sys.stderr)
            time.sleep(wait)


def save(path, items):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--language", required=True, help='Target language, e.g. "Kannada"')
    ap.add_argument("--model", default="gpt-5.4-mini")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None, help="Only translate the first N items")
    ap.add_argument("--keep-source", action="store_true", help="Also store the English originals as title_en / prompt_en")
    ap.add_argument("--env-file", default=os.path.join(REPO_ROOT, ".env"), help="Path to .env file (default: <repo>/.env)")
    args = ap.parse_args()

    load_env(args.env_file)
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit(f"OPENAI_API_KEY not set (add OPENAI_API_KEY=... to {args.env_file})")

    with open(args.input, encoding="utf-8") as f:
        items = json.load(f)
    if args.limit:
        items = items[: args.limit]

    done = {}
    if os.path.exists(args.output):
        with open(args.output, encoding="utf-8") as f:
            done = {x["id"]: x for x in json.load(f)}
    todo = [x for x in items if x["id"] not in done]
    print(f"{len(done)} already done, {len(todo)} to translate -> {args.language}")

    client = OpenAI()
    lock = Lock()
    failed = 0

    def work(item):
        out = dict(item)
        out["title"], out["prompt"] = translate(client, args.model, args.language, item["title"], item["prompt"])
        if args.keep_source:
            out["title_en"], out["prompt_en"] = item["title"], item["prompt"]
        return out

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, it): it for it in todo}
        for n, fut in enumerate(as_completed(futs), 1):
            it = futs[fut]
            try:
                res = fut.result()
            except Exception as e:
                failed += 1
                print(f"FAILED id={it['id']}: {e}", file=sys.stderr)
                continue
            with lock:
                done[res["id"]] = res
                if n % 25 == 0:
                    save(args.output, [done[x["id"]] for x in items if x["id"] in done])
                    print(f"  {n}/{len(todo)}")

    save(args.output, [done[x["id"]] for x in items if x["id"] in done])
    print(f"Wrote {len(done)} items to {args.output} ({failed} failed; re-run to retry)")


if __name__ == "__main__":
    main()
