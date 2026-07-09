import json, time
from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import urlparse
import requests
from hunk_utils import domain_from_url, env, normalize_text, path_for, save_json

BRAVE_API_KEY = env('BRAVE_SEARCH_API_KEY', required=True)
BRAVE_ENDPOINT = 'https://api.search.brave.com/res/v1/web/search'
QUERIES = [
    {"q": "latest science discovery today unusual breakthrough", "category_hint": "science_technology"},
    {"q": "latest technology breakthrough today AI robotics science", "category_hint": "science_technology"},
    {"q": "artificial intelligence news today breakthrough regulation startup", "category_hint": "ai"},
    {"q": "viral animal rescue unusual pet wildlife story today", "category_hint": "pets_animals"},
    {"q": "space news today NASA SpaceX astronomy discovery", "category_hint": "space"},
    {"q": "weird world news today unusual strange event", "category_hint": "world_weird"},
    {"q": "cryptocurrency news today bitcoin ethereum solana ETF regulation", "category_hint": "cryptocurrency"},
]
BLOCKED_URL_WORDS=['/live/','live-updates','/tag/','/category/','/topics/','/latest','homepage','watch/','video/']
PROMO_TERMS=['anytime anywhere','keeps fans connected','live scores, highlights','watch live','stream anytime','subscribe now','download the app','sign up','according to espn.com','sports fan']
GENERIC_TITLES={'espn','sports','news','latest news','top stories','home'}

def article_like(url:str,title:str,description:str)->bool:
    u=url.lower(); text=f'{title} {description}'.lower().strip()
    if any(x in u for x in BLOCKED_URL_WORDS): return False
    if any(x in text for x in PROMO_TERMS): return False
    if title.lower().strip(' .!-') in GENERIC_TITLES: return False
    path=urlparse(url).path.strip('/')
    if len(path)<8 or path.count('/')<1: return False
    if len(title.split())<5: return False
    return True

def brave_search(query:str, category_hint:str, count:int=10)->List[Dict]:
    r=requests.get(BRAVE_ENDPOINT,headers={'Accept':'application/json','X-Subscription-Token':BRAVE_API_KEY},params={'q':query,'count':count,'freshness':'pd','text_decorations':False,'spellcheck':True},timeout=30)
    r.raise_for_status(); results=r.json().get('web',{}).get('results',[]); clean=[]
    for item in results:
        url=item.get('url') or ''; title=normalize_text(item.get('title'),180); desc=normalize_text(item.get('description'),500)
        if not url or not title or not article_like(url,title,desc): continue
        clean.append({'category_hint':category_hint,'query':query,'title':title,'url':url,'domain':domain_from_url(url),'description':desc,'collected_at':datetime.now(timezone.utc).isoformat()})
    return clean

def collect_trends()->List[Dict]:
    all_results=[]; seen=set(); errors=[]
    for q in QUERIES:
        try:
            for item in brave_search(q['q'],q['category_hint']):
                if item['url'] not in seen: seen.add(item['url']); all_results.append(item)
        except Exception as exc: errors.append({'query':q['q'],'error':str(exc)})
        time.sleep(.2)
    save_json(path_for('trend_results.json'),{'results':all_results,'errors':errors,'generated_at':datetime.now(timezone.utc).isoformat()})
    if not all_results: raise RuntimeError(f'No article-like fresh trend results collected. Errors: {errors}')
    return all_results
if __name__=='__main__': print(json.dumps(collect_trends(),indent=2,ensure_ascii=False))
