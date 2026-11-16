# storyscope-multilingual
Story generation stage extracted from [storyscope](https://github.com/jenna-russell/storyscope) (commit `b82d935`, `storyscope/1_story_generation`).

Renamed `1_story_generation` to `story_generation` so it is importable.

## Usage

```bash
pip install -r requirements.txt
python -m storyscope.story_generation.generate_stories \
    --prompts prompts.json --output-dir outputs/stories --config config/models.yaml --parallel 4
```

## Feature application

Stage 5 (`5_feature_application`) from the same commit, renamed to `feature_application`. Uses `data/taxonomy.json`.

```bash
python -m storyscope.feature_application.apply_features \
    --csv <stories.parquet> --taxonomy data/taxonomy.json --output-dir outputs/features --config config/models.yaml
```

## Translating prompts

`scripts/translate_prompts.py` translates English JSON text into a target language with the OpenAI API (default model `gpt-5.4-mini`).

```bash
python -m venv .venv && source .venv/bin/activate
pip install openai
echo "OPENAI_API_KEY=sk-..." > .env   # .env is gitignored
```

### Story prompts (`--mode story_prompt`, default)

Input is a JSON list of `{id, title, prompt}`. Title and prompt are translated together so proper nouns are adapted to the target language and rendered consistently. IDs are kept.

```bash
# Kannada
python scripts/translate_prompts.py \
    --input data/prompts_train.json \
    --output data/prompts_train_kannada.json \
    --language Kannada

# Mandarin Chinese
python scripts/translate_prompts.py \
    --input data/prompts_train.json \
    --output data/prompts_train_mandarin_chinese.json \
    --language "Mandarin Chinese"
```

The same commands work for `data/prompts_dev.json` (outputs `prompts_dev_kannada.json` / `prompts_dev_mandarin_chinese.json`). Re-running with the same `--output` resumes and skips IDs already translated.

### Any other text (`--mode text`)

For system prompts, instructions, templates, etc. (`--mode system_prompt` is an alias). Accepts:

- **a JSON object** (nested is fine): every string value is translated; keys and structure are kept. Use `--skip-keys a,b` to leave keys untranslated.
- **a JSON list of objects**: the fields in `--fields` (default `prompt`) are translated; everything else is copied through. Resumes by `id`.

```bash
python scripts/translate_prompts.py --mode text \
    --input strings.json --output strings_kannada.json --language Kannada
```

By default the translator keeps the instruction voice and exact meaning and leaves placeholders like `{name}` untouched. To use a different translator prompt, pass `--instructions "..."` or `--instructions-file path` (use `{lang}` for the target language).

`storyscope/story_generation/prompt_translations.json` holds the story-generation system prompt in English, Mandarin Chinese and Kannada (translated with `--mode text`).

### Flags

`--limit N` (first N items only, good for a test), `--workers N` (parallel requests, default 8), `--model`, `--keep-source` (list input: also store the English originals as `<field>_en`), `--env-file` (default `<repo>/.env`).
