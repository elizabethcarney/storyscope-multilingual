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

`scripts/translate_prompts.py` translates the `title` and `prompt` of a prompts JSON file into a target language with the OpenAI API (default model `gpt-5.4-mini`). IDs are kept, and proper nouns are adapted to the target language.

```bash
python -m venv .venv && source .venv/bin/activate
pip install openai
echo "OPENAI_API_KEY=sk-..." > .env   # .env is gitignored
```

Kannada:

```bash
python scripts/translate_prompts.py \
    --input data/prompts_train.json \
    --output data/prompts_train_kannada.json \
    --language Kannada
```

Mandarin Chinese:

```bash
python scripts/translate_prompts.py \
    --input data/prompts_train.json \
    --output data/prompts_train_mandarin_chinese.json \
    --language "Mandarin Chinese"
```

The same commands work for `data/prompts_dev.json` (use `prompts_dev_kannada.json` / `prompts_dev_mandarin_chinese.json` as outputs).

Useful flags: `--limit N` (translate only the first N, good for a test), `--workers N` (parallel requests, default 8), `--model`, `--keep-source` (also store `title_en` / `prompt_en`). Re-running with the same `--output` resumes and skips IDs already translated.
