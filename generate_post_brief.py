import json
from openai import OpenAI
from content_strategy import build_concepts

client = OpenAI()


def generate_post_brief():
    concepts = build_concepts()

    if not concepts:
        raise RuntimeError("No concepts found")

    top_concept = concepts[0]

    prompt = f"""
You are an expert Instagram creative director.

Create a polished daily post brief from this news/trend concept.

Concept:
{json.dumps(top_concept, indent=2)}

Return a JSON object with:
selected_topic, source_url, image_prompt, easter_eggs, caption, hashtags, risk_notes.

Rules:
- Make the image prompt extremely detailed and visually dense.
- Make it square Instagram art.
- Use a fictional pet/mascot character.
- No investment advice.
- No fake claims.
- Keep caption short and engaging.
- Hashtags should be relevant, not spammy.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_object"
            }
        },
    )

    brief = json.loads(response.output_text)

with open("post_brief.json", "w", encoding="utf-8") as f:
    json.dump(brief, f, indent=2)

print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    generate_post_brief()
