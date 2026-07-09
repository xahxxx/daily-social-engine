# Hunk Mao Instagram AI Bot - Final Working Pack

## Daily flow
1. Put your real keys in `.env` or GitHub Actions secrets.
2. Run:
   ```bash
   python run_daily_pipeline.py
   ```
3. Check `post_brief.json` and `generated_post.png`.
4. Publish files locally for GitHub Pages:
   ```bash
   python publish_to_github_pages.py
   ```
5. After the files are public, test your token:
   ```bash
   python test_instagram_token.py
   ```
6. Post to Instagram:
   ```bash
   python publish_test_instagram.py
   ```

## What changed
- Stronger news freshness via Brave daily freshness.
- More category rotation so it does not become crypto-only.
- Hashtag enforcement: crypto hashtags only appear when the actual selected story is crypto-related.
- Safer scoring against generic homepages, live-update pages, and tragedy-heavy stories.
- Clearer news-grounded brief generation.
- More reliable image prompt logic with strict character consistency and text limits.
- Instagram container status polling before publish.
- Shared helper functions and safer JSON writes.

## July 2026 reliability fixes
- Hashtags are normalized safely whether the model returns a JSON array or an accidental string; character-by-character hashtags are impossible.
- Promotional/evergreen search results are rejected before concept selection.
- Strongest concept selection is deterministic; no random downgrade among the top candidates.
- A hard pre-image validation gate rejects malformed hashtags, missing source URLs, empty captions, and promotional concepts.
- Creative prompt explicitly forbids ad/sponsorship layouts and excessive corporate-logo repetition.
