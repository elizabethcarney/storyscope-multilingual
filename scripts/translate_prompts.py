"""Translate JSON text from English into a target language with the OpenAI API.

Two modes:

  story_prompt (default)
      Input : JSON list of {"id", "title", "prompt"}.
      Translates title and prompt together (one call) so proper nouns are
      adapted to the target language and rendered consistently in both.

  text  (alias: system_prompt)
      General-purpose translation of arbitrary strings, e.g. system prompts,
      instructions, templates. Input can be
        * a JSON list of objects: the fields named by --fields (default: prompt)
          are translated, everything else is copied through; or
        * a JSON object (nested ok): every string value is translated and the
          structure/keys are kept (use --skip-keys to leave some keys alone).
      The translator instruction can be overridden with --instructions or
      --instructions-file (use {lang} for the target language).

Usage:
    # put OPENAI_API_KEY=sk-... in <repo>/.env
    python scripts/translate_prompts.py --input data/prompts_train.json \
        --output data/prompts_train_kannada.json --language Kannada --limit 20

    python scripts/translate_prompts.py --mode text --input my_strings.json \
        --output my_strings_zh.json --language "Mandarin Chinese"

Re-running on a list input resumes: items already present in --output are skipped.
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


STORY_SYSTEM = (
    "You are a professional translator. The user gives a JSON object with a "
    '"title" and a "prompt" (a story-writing prompt) in English. Translate both '
    "into {lang}. Preserve meaning, tone, and any numbers exactly (e.g. word "
    "counts). Adapt proper nouns (character names, places, and the names in the "
    "title) to {lang}, using the natural transliteration or established "
    "{lang} form, and use exactly the same rendering of each name in the title "
    'and the prompt. Reply with only a JSON object: {{"title": "...", "prompt": "..."}}.'
)

# Default for --mode text: instructions / system prompts addressed to a model.
TEXT_SYSTEM = (
    "You are a professional translator. Translate the user's text from English "
    "into {lang}. If it is an instruction addressed to an AI model, keep the "
    "second-person instruction voice and the exact meaning: do not add, soften, "
    "or drop anything. Leave placeholders (e.g. {{name}}), code, and JSON keys "
    "untranslated. Output only the translation, with no preface, notes, or "
    "quotation marks."
)


def with_retries(fn, retries=5):
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:  # rate limits, transient errors
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  retry in {wait}s ({type(e).__name__}: {e})", file=sys.stderr)
            time.sleep(wait)


def translate_story(client, model, lang, title, text):
    """Translate title and prompt together so proper nouns stay consistent."""
    def call():
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": STORY_SYSTEM.format(lang=lang)},
                {"role": "user", "content": json.dumps({"title": title, "prompt": text}, ensure_ascii=False)},
            ],
        )
        out = json.loads(resp.choices[0].message.content)
        return out["title"].strip(), out["prompt"].strip()
    return with_retries(call)


def translate_text(client, model, instructions, lang, text):
    """Plain-text translation using the given translator instructions."""
    def call():
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": instructions.format(lang=lang)},
                {"role": "user", "content": text},
            ],
        )
        return resp.choices[0].message.content.strip()
    return with_retries(call)


def translate_tree(node, fn, skip_keys):
    """Apply fn to every string leaf of a nested dict/list, keeping structure."""
    if isinstance(node, str):
        return fn(node) if node.strip() else node
    if isinstance(node, list):
        return [translate_tree(x, fn, skip_keys) for x in node]
    if isinstance(node, dict):
        return {k: (v if k in skip_keys else translate_tree(v, fn, skip_keys)) for k, v in node.items()}
    return node  # numbers, bools, null


def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--language", required=True, help='Target language, e.g. "Kannada"')
    ap.add_argument("--mode", choices=["story_prompt", "text", "system_prompt"], default="story_prompt")
    ap.add_argument("--model", default="gpt-5.4-mini")
    ap.add_argument("--fields", default="prompt", help="text mode, list input: comma-separated fields to translate (default: prompt)")
    ap.add_argument("--skip-keys", default="", help="text mode, object input: comma-separated keys to leave untranslated")
    ap.add_argument("--instructions", help="text mode: custom translator system prompt (use {lang})")
    ap.add_argument("--instructions-file", help="text mode: read the translator system prompt from a file")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None, help="Only translate the first N items (list input)")
    ap.add_argument("--keep-source", action="store_true", help="List input: also store the English originals as <field>_en")
    ap.add_argument("--env-file", default=os.path.join(REPO_ROOT, ".env"), help="Path to .env file (default: <repo>/.env)")
    args = ap.parse_args()

    load_env(args.env_file)
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit(f"OPENAI_API_KEY not set (add OPENAI_API_KEY=... to {args.env_file})")

    text_mode = args.mode in ("text", "system_prompt")
    instructions = TEXT_SYSTEM
    if args.instructions_file:
        with open(args.instructions_file, encoding="utf-8") as f:
            instructions = f.read().strip()
    elif args.instructions:
        instructions = args.instructions

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    client = OpenAI()
    lang = args.language

    # Object input (text mode): translate every string value, keep structure.
    if isinstance(data, dict):
        if not text_mode:
            sys.exit("Object input needs --mode text")
        skip = {k.strip() for k in args.skip_keys.split(",") if k.strip()}
        strings = []
        translate_tree(data, lambda s: strings.append(s) or s, skip)
        strings = list(dict.fromkeys(strings))  # unique, order kept
        print(f"Translating {len(strings)} strings -> {lang}")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            results = dict(zip(strings, ex.map(lambda s: translate_text(client, args.model, instructions, lang, s), strings)))
        save(args.output, translate_tree(data, lambda s: results[s], skip))
        print(f"Wrote {args.output}")
        return

    # List input: per-item translation with resume (items are matched by "id").
    items = data[: args.limit] if args.limit else data
    key = lambda x: x.get("id")
    fields = [f.strip() for f in args.fields.split(",") if f.strip()]

    done = {}
    if os.path.exists(args.output):
        with open(args.output, encoding="utf-8") as f:
            done = {key(x): x for x in json.load(f)}
    todo = [x for x in items if key(x) not in done]
    print(f"{len(done)} already done, {len(todo)} to translate -> {lang}")

    def work(item):
        out = dict(item)
        if text_mode:
            for fld in fields:
                if item.get(fld):
                    out[fld] = translate_text(client, args.model, instructions, lang, item[fld])
                    if args.keep_source:
                        out[fld + "_en"] = item[fld]
        else:
            out["title"], out["prompt"] = translate_story(client, args.model, lang, item["title"], item["prompt"])
            if args.keep_source:
                out["title_en"], out["prompt_en"] = item["title"], item["prompt"]
        return out

    lock = Lock()
    failed = 0
    ordered = lambda: [done[key(x)] for x in items if key(x) in done]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, it): it for it in todo}
        for n, fut in enumerate(as_completed(futs), 1):
            it = futs[fut]
            try:
                res = fut.result()
            except Exception as e:
                failed += 1
                print(f"FAILED id={key(it)}: {e}", file=sys.stderr)
                continue
            with lock:
                done[key(res)] = res
                if n % 25 == 0:
                    save(args.output, ordered())
                    print(f"  {n}/{len(todo)}")

    save(args.output, ordered())
    print(f"Wrote {len(done)} items to {args.output} ({failed} failed; re-run to retry)")


if __name__ == "__main__":
    main()
