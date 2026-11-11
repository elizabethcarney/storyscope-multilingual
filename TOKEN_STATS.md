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

# Feature application (stage 5), English dev set

Script: `scripts/estimate_feature_tokens.py` (tiktoken `o200k_base`). Default model in config: Gemini 3 Flash.

Structure: 10 dimensions, 304 features. Each story triggers **10 separate calls** (one per dimension), and every call includes the full story. So input is about 10x the story length plus per-dimension instructions.

## Input tokens per story (all 10 calls)

| Source | Mean | Median | Max |
|---|---|---|---|
| GPT | 102,726 | 101,731 | 203,136 |
| Claude | 101,926 | 96,136 | 299,786 |
| Kimi | 62,839 | 60,451 | 127,656 |
| Gemini | 60,854 | 58,376 | 106,536 |
| DeepSeek | 57,451 | 56,056 | 95,156 |

Mean across sources: ~77,000 input tokens/story (the instruction and feature-spec text adds ~21k per story).

## Output tokens per story

~4,800 (JSON with 304 feature values, estimated from the first allowed value per feature; actual values vary). Reasoning/thinking tokens are extra.

## Full-run estimate (61,608 stories, 6 sources)

- Input: ~4.7B tokens (human stories not in dev data; assumed similar to the average).
- Output: ~300M tokens.

Caveats: failed or malformed JSON is retried up to 3 times per dimension; prompt caching of the repeated story could reduce billed input cost; non-English text tokenizes at higher rates.

## The 10 dimensions (one API call each per story)

| Dimension | Features | Focus |
|---|---|---|
| Agents | 54 | Characters: identities, roles, attributes, emotions, motivations, archetypes |
| Social Networks | 39 | Relationships: types, dynamics, power structures, social topology |
| Style | 39 | Language: figurative language, sentence structure, register, tone, allusion, prose texture |
| Plot | 28 | Story structure: themes, conflicts, arcs, resolutions, moral content |
| Setting | 27 | Where and when: locations, time, atmosphere, world-building |
| Events | 26 | What happens: event types, density, causality, schemas, escalation |
| Revelation | 25 | Information disclosure: suspense, curiosity, surprise, dramatic irony |
| Situatedness | 25 | Literary positioning: genre, metafiction, intertextuality, assumed reader |
| Temporal Structure | 24 | Time handling: duration, order, pacing, frequency, manipulation |
| Perspective | 17 | Narration: point of view, focalization, dialogue, voice, interior access |
