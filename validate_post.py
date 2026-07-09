import json
from pathlib import Path
from hunk_utils import coerce_hashtags

def validate_post():
    p=Path(__file__).resolve().parent/'post_brief.json'
    b=json.loads(p.read_text(encoding='utf-8'))
    required=['selected_topic','category','source_url','news_angle','image_prompt','caption','hashtags']
    missing=[k for k in required if not b.get(k)]
    if missing: raise RuntimeError(f'VALIDATION FAILED missing: {missing}')
    tags=coerce_hashtags(b.get('hashtags'))
    if len(tags)<10 or '#hunkmao' not in tags: raise RuntimeError(f'VALIDATION FAILED hashtags: {tags}')
    if any(len(t)<3 for t in tags): raise RuntimeError(f'VALIDATION FAILED malformed hashtags: {tags}')
    caption=str(b['caption']).strip()
    if len(caption)<40: raise RuntimeError('VALIDATION FAILED caption too short')
    source=str(b['source_url'])
    if not source.startswith('http'): raise RuntimeError('VALIDATION FAILED source_url')
    promo=['anytime anywhere','keeps fans connected','download the app','subscribe now','sports fan']
    blob=' '.join(str(b.get(k,'')) for k in ['selected_topic','news_angle','caption','image_prompt']).lower()
    if any(x in blob for x in promo): raise RuntimeError('VALIDATION FAILED promotional/evergreen concept detected')
    b['hashtags']=tags[:15]
    p.write_text(json.dumps(b,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Post brief validation passed.')
    return b
if __name__=='__main__': validate_post()
