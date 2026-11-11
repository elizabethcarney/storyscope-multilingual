# storyscope-multilingual
Story generation stage extracted from [storyscope](https://github.com/jenna-russell/storyscope) (commit `b82d935`, `storyscope/1_story_generation`).

Renamed `1_story_generation` to `story_generation` so it is importable.

## Usage

```bash
pip install -r requirements.txt
python -m storyscope.story_generation.generate_stories \
    --prompts prompts.json --output-dir outputs/stories --config config/models.yaml --parallel 4
```
