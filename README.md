# storyscope-multilingual
Story generation stage extracted from [storyscope](https://github.com/jenna-russell/storyscope) (commit `b82d935`, `storyscope/1_story_generation`), renamed to `story_generation` so it is importable.

## Setup

```bash
pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-..." > .env   # gitignored
set -a; source .env; set +a
```

## Generate stories

```bash
python -m storyscope.story_generation.generate_stories \
    --prompts prompts.json --output-dir outputs/stories --config config/models.yaml --parallel 4
```

### In another language

1. Translate the prompts (see below) to `data/prompts_train_<language>.json`.
2. Check the language has a system prompt in `storyscope/story_generation/prompt_translations.json` (`english`, `mandarin_chinese`, `kannada`).
3. Run with `--language` (`{language}` in `--prompts` is replaced by it):

```bash
python -m storyscope.story_generation.generate_stories \
    --prompts 'data/prompts_train_{language}.json' --language kannada \
    --output-dir data/stories_kannada --max-stories 3 --parallel 3
```

Drop `--max-stories` for the full set; `--resume` skips finished stories.

## Translate prompts

```bash
python scripts/translate_prompts.py \
    --input data/prompts_train.json --output data/prompts_train_kannada.json --language Kannada
```

Use `--mode text` for system prompts / other JSON strings, `--limit N` to test on a few.

## Feature application

```bash
python -m storyscope.feature_application.apply_features \
    --csv <stories.parquet> --taxonomy data/taxonomy.json --output-dir outputs/features --config config/models.yaml
```
