"""Find and retain original, permitted article images without transformation."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, io, json
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from collector.http import HttpFetcher
from shared.contracts import ImageAsset, SourceConfig
from shared.urls import normalize_url

@dataclass(frozen=True)
class ImageCandidate: url:str; alt:str|None; credit:str|None; origin:str
@dataclass(frozen=True)
class ImageInfo: sha256:str; width:int; height:int; content_type:str

_IMAGE_PROXIES = {"i0.wp.com", "i1.wp.com", "i2.wp.com"}
_HOST_PREFIXES = ("www.", "noticias.", "diario.", "portal.", "comunicaciones.")

def is_allowed_image_host(hostname: str | None, source: SourceConfig) -> bool:
    if not hostname: return False
    host = hostname.lower().rstrip(".")
    if host in _IMAGE_PROXIES: return True
    configured = {item.lower().rstrip(".") for item in source.allowed_hosts + source.allowed_image_hosts}
    if host in configured: return True
    for allowed in configured:
        if allowed == "uninews.datoslab.cl": continue
        root = allowed
        changed = True
        while changed:
            changed = False
            for prefix in _HOST_PREFIXES:
                if root.startswith(prefix) and root[len(prefix):].count(".") >= 1:
                    root = root[len(prefix):]; changed = True; break
        labels = root.split(".")
        # .cl institutional registrations have two labels (uach.cl); for other suffixes
        # the configured host itself is the safe registrable boundary.
        if len(labels) >= 2 and (host == root or host.endswith("." + root)):
            return True
    return False

def inspect_image(data:bytes,min_width:int=300,min_height:int=160)->ImageInfo:
    if not 0 < len(data) <= 5*1024*1024: raise ValueError('image_size_limit')
    kinds={'JPEG':'image/jpeg','PNG':'image/png','WEBP':'image/webp'}
    try:
        with Image.open(io.BytesIO(data)) as picture:
            width,height,kind=picture.width,picture.height,picture.format
            if kind not in kinds or width*height>40_000_000: raise ValueError('unsupported_or_oversized_image')
            if width<min_width or height<min_height: raise ValueError('image_too_small')
            picture.verify()
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as exc: raise ValueError('invalid_image') from exc
    return ImageInfo(hashlib.sha256(data).hexdigest(),width,height,kinds[kind])

def find_image_candidates(html:str,source:SourceConfig,article_url:str)->list[ImageCandidate]:
    soup=BeautifulSoup(html,'html.parser'); found=[]
    container = soup.select_one(source.content_selector) if source.content_selector else soup
    nodes = list((container or soup).select('figure img, img'))
    nodes.extend(soup.select('meta[property="og:image"], meta[name="twitter:image"]'))
    for node in nodes:
        raw=node.get('data-src') or node.get('data-lazy-src') or node.get('data-original') or node.get('content')
        last_srcset = None
        if node.get('srcset'):
            # Pick the largest declared candidate; this is metadata, not a gallery crawl.
            last_srcset = node['srcset'].split(',')[-1].strip().split()[0]
        raw = raw or last_srcset or node.get('src')
        if not raw: continue
        try: url=normalize_url(raw,article_url)
        except ValueError: continue
        if not is_allowed_image_host(urlsplit(url).hostname, source): continue
        text=' '.join((node.get('class') or [])).lower()
        if any(word in text for word in ('logo','icon','avatar')): continue
        candidate=ImageCandidate(url,node.get('alt'),None,'article' if node.name=='img' else 'og:image')
        if candidate.url not in {x.url for x in found}: found.append(candidate)
    for script in soup.select('script[type="application/ld+json"]'):
        try: values=json.loads(script.string or '')
        except (TypeError,json.JSONDecodeError): continue
        values=values.get('@graph',[]) if isinstance(values,dict) and '@graph' in values else (values if isinstance(values,list) else [values])
        for value in values:
            if not isinstance(value,dict) or 'NewsArticle' not in str(value.get('@type','')): continue
            raw=value.get('image')
            if isinstance(raw,list): raw=raw[0] if raw else None
            if isinstance(raw,dict): raw=raw.get('url')
            if not isinstance(raw,str): continue
            try: url=normalize_url(raw,article_url)
            except ValueError: continue
            if is_allowed_image_host(urlsplit(url).hostname, source) and url not in {x.url for x in found}:
                found.append(ImageCandidate(url,None,None,'jsonld'))
    return found

class ImageFetcher:
    def __init__(self,fetcher:HttpFetcher): self.fetcher=fetcher
    def fetch(self,candidate:ImageCandidate,source:SourceConfig)->tuple[ImageAsset,bytes]:
        # HTTP fetcher intentionally applies the source host boundary before bytes are trusted.
        result=self.fetcher.fetch(candidate.url,source,binary=True)
        info=inspect_image(result.content,source.image_min_width,source.image_min_height)
        return ImageAsset(status='ready',original_url=result.url,sha256=info.sha256,content_type=info.content_type,width=info.width,height=info.height,byte_size=len(result.content),alt=candidate.alt,credit=candidate.credit),result.content

def store_original(root:Path,asset:ImageAsset,data:bytes)->Path:
    if asset.status!='ready' or not asset.sha256 or not asset.content_type: raise ValueError('image_not_ready')
    ext={'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}[asset.content_type]; path=root/asset.sha256[:2]/f'{asset.sha256}.{ext}'
    path.parent.mkdir(parents=True,exist_ok=True); temporary=path.with_suffix(path.suffix+'.tmp'); temporary.write_bytes(data); temporary.replace(path); return path
