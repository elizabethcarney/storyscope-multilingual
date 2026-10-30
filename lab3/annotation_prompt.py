guidelines = """
#### Task in one sentence
Annotate this story with narrative choices made by the author.

#### Unit of annotation
A short story

#### Labels / codes / scale / span and relation types

Breaking the fourth wall - Binary
no direct address
yes, direct address present
Temporal devices - scale(1-5)
1_strictly_linear_no_frames
2_minor_analepses_or_prologue_only
3_regular_flashbacks_but_easy_to_track
4_complex_frame_or_time_braid
5_heavily_fragmented_time_with_reconstruction_required

#### Definitions and Decision Rules


Breaking the fourth wall: Does the narration or a character directly address the reader or audience as such. Decision Rule: Look for second-person plural or singular addresses like 'you, dear reader', 'let me tell you', or direct comments assuming an audience outside the story-world. Ignore in-world second-person dialogue between characters.
Temporal Devices: To what extent does the story use flashbacks, frame narratives, or time jumps specifically to delay or stage revelations? Decision rule: Identify changes in narrative time: jumps backward/forward, stories told within stories, letters from the future, etc. Evaluate both frequency and structural importance of these devices in controlling when the reader learns key facts, then pick the best-fitting level.



#### Worked examples


- Examples for breaking the fourth wall:
Jane Eyre’s famous “Reader, I married him”
The Catcher in the Rye - “if you really want to hear about it”
- Examples for temporal devices:
1_strictly_linear_no_frames - Of Mice and Men. The action runs across a few days in sequence. Background on George and Lennie comes through brief dialogue, not narrated scenes of the past.
2_minor_analepses_or_prologue_only - Harry Potter and the Philosopher’s Stone. It opens with a short prologue-like scene (the night Harry is left at Privet Drive), then proceeds linearly. The origin of Harry’s scar is explained in small, contained pieces of backstory, and the main mystery unfolds in present time.
3_regular_flashbacks_but_easy_to_track - The Kite Runner. Adult Amir’s present-day narration repeatedly returns to his Kabul childhood, with the betrayal at the heart of the book withheld until a flashback delivers it. The two timelines are distinct, and the transitions are easy to follow.
4_complex_frame_or_time_braid - Walton’s letters frame Victor’s narrative, which in turn frames the creature’s narrative. Key revelations (the creature’s origin, his motives) arrive through nested tellers, so the frame structure directly governs access to information. Another example is The Hours, which braids three women’s timelines.
5_heavily_fragmented_time_with_reconstruction_required - In Slaughterhouse-Five, Billy Pilgrim becomes “unstuck in time,” moving among war, marriage, and captivity in non-sequential fragments. The reader must piece together what happened and in what order.

#### Edge cases and tie-break rules
Retrospective narration is not a flashback. The Great Gatsby and Great Expectations are told from a later vantage point, but the scenes unfold in order. Code them as 1, or 2 if there’s a distinct framing passage.
Backstory in dialogue/narrator addressing the reader directly is not a temporal device. A character summarizing the past in a line or two doesn’t count. It counts only when the past is dramatized as a scene or a sustained passage.
Time travel alone is not a temporal device.
Two alternating timelines, each linear and labeled - Usually 3. It moves to 4 with three or more strands, missing labels, or when the relationship between strands is itself a puzzle.
Nested narrators - Two or more levels that control who knows what: 4, even if each inner story is chronological.

Tie-break rules
Reconstruction test (3 vs. 4 vs. 5). Could a first-time reader draw an accurate timeline? Easily: 3. With effort, but one pass is enough: 4. Only after rereading, or with gaps that stay ambiguous: 5.
Signposting rule. When torn between adjacent levels, go lower if the shifts are clearly marked (dates, headings, tense) and higher if they are unmarked.
Dominant-structure rule. Code the pattern across most of the text, not one experimental section.


#### What to do when unsure
When unsure between adjacent labels, pick the lower label for temporal devices

"""

output_format = """
#### Output format

You will be given one short story at a time. For every story, return exactly one JSON object and nothing else (no markdown fences, no commentary before or after). Use exactly these keys:

{
  "breaking_the_fourth_wall": {
    "evidence": "<short verbatim quote from the story showing direct address to the reader, or \\"\\" if none>",
    "label": "<exactly one of: \\"no\\" or \\"yes\\">"
  },
  "temporal_devices": {
    "evidence": "<one or two sentences naming the specific flashbacks, frames, or time jumps you relied on, or noting that the story is linear>",
    "label": <integer 1-5>
  }
}

Rules for the output:
- Give "evidence" before "label" for each field, and keep each evidence string brief.
- "breaking_the_fourth_wall.label" must be the string "yes" or "no" (lowercase).
- "temporal_devices.label" must be an integer from 1 to 5 (not a string, not the label name), following the scale and tie-break rules above.
- Always output both fields, even if the story is very short. Never output null, a range, or multiple labels; if unsure, follow the "What to do when unsure" rule.
- Output valid JSON only: double-quoted keys and strings, no trailing commas.
"""

prompt = f"""You are a data annotator. Here are the guidelines for your annotation task.

{guidelines}

{output_format}

"""

story_template = """Here is the story to annotate:

<story>
{story}
</story>

Return the JSON object now."""


def build_prompt(story: str) -> str:
    """Full prompt for a single input short story."""
    return prompt + story_template.format(story=story)
