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

To run on a directory of generated stories (`<id>_<title>/story.txt`) and only some features, use `--stories-dir` and `--feature-ids` (`--source` labels the stories, default `gpt`):

```bash
python -m storyscope.feature_application.apply_features \
    --stories-dir data/stories_kannada --taxonomy data/taxonomy.json \
    --output-dir outputs/features_kannada --config config/models.yaml \
    --feature-ids STY_ALL_017 PLT_STR_003 REV_DIS_003 AGENT_EMO_009 SIT_MET_002 PLT_MOR_002 SET_LOC_011 PER_DIA_001
```

Add `--evidence` to also get verbatim supporting quotes and reasoning for each feature (each feature becomes `{"value", "evidence", "reasoning"}`). Use a separate `--output-dir` for evidence runs.

## Annotation viewer

Build a standalone HTML page that highlights each feature's evidence in the story, shows the model's value and reasoning, and lets humans record their own values:

```bash
python -m storyscope.viewer.build_viewer \
    --stories-dir data/stories_kannada --features-dir outputs/features_kannada_evidence \
    --taxonomy data/taxonomy.json --output viewer.html
```

Stories are paired with `prompt_<id>__*.features.json` by the first number in the story's file or folder name, so `--features-dir` must come from an `--evidence` run. Open `viewer.html` in a browser: pick a feature to see its evidence highlighted, choose your own value (Blind mode hides the model's answer until you do), and use Export for JSON/CSV. Annotations are saved in the browser as you work.
