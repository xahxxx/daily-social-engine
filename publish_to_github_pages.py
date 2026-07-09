import os
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

from hunk_utils import load_json, path_for, save_json

PUBLISHED_DIR = path_for("published")
TIMEZONE = os.getenv("POST_TIMEZONE", "America/Los_Angeles")


def main() -> None:
    image_path = path_for("generated_post.png")
    brief_path = path_for("post_brief.json")
    if not image_path.exists():
        raise FileNotFoundError("generated_post.png not found. Run generate_image.py first.")
    if not brief_path.exists():
        raise FileNotFoundError("post_brief.json not found. Run generate_post_brief.py first.")

    stamp = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y%m%d-%H%M%S")
    PUBLISHED_DIR.mkdir(exist_ok=True)

    stamped_image = PUBLISHED_DIR / f"hunk-mao-{stamp}.png"
    stamped_json = PUBLISHED_DIR / f"hunk-mao-{stamp}.json"

    brief = load_json(brief_path)
    brief["post_stamp"] = stamp
    brief["image_filename"] = stamped_image.name

    shutil.copy2(image_path, stamped_image)
    save_json(stamped_json, brief)
    shutil.copy2(stamped_image, PUBLISHED_DIR / "latest.png")
    save_json(PUBLISHED_DIR / "latest.json", brief)

    print(f"POST_STAMP={stamp}")
    print(f"Saved {stamped_image}")
    print(f"Saved {stamped_json}")


if __name__ == "__main__":
    main()
