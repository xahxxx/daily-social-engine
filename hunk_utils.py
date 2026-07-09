import json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / 'hunk_mao_state.json'

def path_for(filename: str) -> Path: return ROOT / filename

def env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value: raise RuntimeError(f'{name} is missing')
    return value or ''

def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is not None: return default
        raise FileNotFoundError(str(path))
    with path.open('r', encoding='utf-8') as f: return json.load(f)

def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)

def now_iso() -> str: return datetime.now(timezone.utc).isoformat()

def normalize_text(value: Any, max_len: int = 300) -> str:
    return re.sub(r'\s+', ' ', str(value or '')).strip()[:max_len]

def domain_from_url(url: str) -> str:
    m = re.search(r'https?://(?:www\.)?([^/]+)', url or '')
    return m.group(1).lower() if m else ''

def clean_hashtag(tag: str) -> str:
    tag = re.sub(r'[^a-zA-Z0-9_#]', '', str(tag or '').strip().lower())
    tag = re.sub(r'^#+', '#', tag)
    if not tag or tag == '#': return ''
    return tag if tag.startswith('#') else '#' + tag

def coerce_hashtags(value: Any) -> List[str]:
    '''Accept model output as JSON list OR accidental string; never iterate characters.'''
    if value is None: return []
    if isinstance(value, str):
        raw = re.findall(r'#[A-Za-z0-9_]+', value)
        if not raw: raw = re.split(r'[\s,;]+', value)
        return [clean_hashtag(x) for x in raw if clean_hashtag(x)]
    if isinstance(value, (list, tuple, set)):
        out = []
        for item in value:
            if isinstance(item, str):
                found = re.findall(r'#[A-Za-z0-9_]+', item)
                if len(found) > 1: out.extend(clean_hashtag(x) for x in found)
                else: out.append(clean_hashtag(item))
        return [x for x in out if x]
    return []

def unique(items: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for item in items:
        if item and item not in seen: seen.add(item); out.append(item)
    return out
