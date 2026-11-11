# Token statistics (English dev set)

Source: `data/stories_dev.parquet` from storyscope (commit `b82d935`), 100 prompts.
Tokenizer: tiktoken `o200k_base` (approximate for other models).
Prompts are in `data/prompts_dev.json`.

## Input tokens per story

| | Words | Tokens |
|---|---|---|
| Prompt (mean) | 91 | 116 (min 83, max 151, median 116) |
| System prompt | | 13 |
| **Total input** | | **~130** |

Full run (~51,360 LLM stories): ~6.7M input tokens.

## Output tokens per story (visible text only)

| Model | Mean words | Mean tokens | Median tokens | Max tokens |
|---|---|---|---|---|
| GPT | 6,385 | 8,099 | 8,000 | 18,140 |
| Claude | 6,559 | 8,019 | 7,440 | 27,805 |
| Kimi | 3,161 | 4,110 | 3,872 | 10,592 |
| Gemini | 3,022 | 3,912 | 3,664 | 8,480 |
| DeepSeek | 2,672 | 3,571 | 3,432 | 7,342 |

Mean across the five models: ~5,540 tokens/story.
Full run per model: 10,272 prompts x mean (e.g. GPT ~83M, Claude ~82M).

## Caveats

- Reasoning models bill hidden reasoning tokens on top of these counts.
- Non-English text tokenizes at higher tokens per word; recount with the target tokenizer.
- Prompts end with a length instruction ("approximately N words"), yet stories run much longer.
- Dev set only; full 10,272-prompt set is not in the repo.
