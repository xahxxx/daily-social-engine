from generate_post_brief import generate_post_brief
from generate_image import generate_image
from hunk_utils import load_json, path_for, save_json, now_iso


def main() -> None:
    brief = generate_post_brief()
    generate_image()

    state = load_json(path_for("hunk_mao_state.json"), default={})
    state.update({
        "last_category": brief.get("category"),
        "last_selected_topic": brief.get("selected_topic"),
        "last_source_url": brief.get("source_url"),
        "last_generated_at": now_iso(),
    })
    save_json(path_for("hunk_mao_state.json"), state)
    print("Daily Hunk Mao brief and image completed.")


if __name__ == "__main__":
    main()
