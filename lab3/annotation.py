import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from annotation_prompt import prompt, story_template

load_dotenv()  # loads OPENAI_API_KEY from .env

MODEL = "gpt-4o-mini"

client = OpenAI()


def annotate(story: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": story_template.format(story=story)},
        ],
    )
    return json.loads(response.choices[0].message.content)


if __name__ == "__main__":
    # usage: python annotation.py stories_folder [output.json]
    if len(sys.argv) < 2:
        sys.exit("usage: python annotation.py stories_folder [output.json]")
    folder = Path(sys.argv[1])
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("annotations.json")

    results = {}
    for path in sorted(folder.glob("*.txt")):
        print(f"annotating {path.name}", file=sys.stderr)
        results[path.name] = annotate(path.read_text())

    output.write_text(json.dumps(results, indent=2))
    print(f"wrote {len(results)} annotations to {output}", file=sys.stderr)
