"""Strict OpenRouter client for the approved zero-price extraction model."""
from __future__ import annotations
import json
from email.utils import parsedate_to_datetime
from datetime import UTC, datetime
import httpx
from collector.config import CollectorSettings, OPENROUTER_API_URL
from shared.contracts import Document, FREE_MODEL, Selection, stable_json

class LLMDeferred(RuntimeError):
    def __init__(self,code,retry_after_seconds=None): super().__init__(code); self.code,self.retry_after_seconds=code,retry_after_seconds
class LLMRejected(RuntimeError):
    def __init__(self,code): super().__init__(code); self.code=code

def extraction_payload(doc:Document,prompt:str)->dict:
    return {"model":FREE_MODEL,"messages":[{"role":"system","content":prompt},{"role":"user","content":stable_json({"blocks":[b.model_dump() for b in doc.blocks],"expected_body_ids":doc.expected_body_ids})}],"temperature":0,"max_tokens":2048,"reasoning":{"enabled":False},"response_format":{"type":"json_object"},"provider":{"require_parameters":True,"max_price":{"prompt":0,"completion":0}}}

class MiniMaxExtractor:
    def __init__(self,settings:CollectorSettings,client:httpx.Client): self.settings,self.client=settings,client
    def _prompt(self):
        from pathlib import Path
        return (Path(__file__).parent/'prompts'/'extract-v1.txt').read_text(encoding='utf8')
    def check_model(self):
        response=self.client.get(f"{OPENROUTER_API_URL}/models"); response.raise_for_status()
        found=next((x for x in response.json().get('data',[]) if x.get('id')==FREE_MODEL),None)
        if not found or any(str(found.get('pricing',{}).get(x,'0')) not in {'0','0.0','0.00'} for x in ('prompt','completion')): raise LLMRejected('model_not_free_or_unavailable')
    def extract(self,doc:Document)->Selection:
        try: r=self.client.post(f"{OPENROUTER_API_URL}/chat/completions",headers={"Authorization":f"Bearer {self.settings.openrouter_api_key.get_secret_value() if self.settings.openrouter_api_key else ''}"},json=extraction_payload(doc,self._prompt()),timeout=120)
        except httpx.RequestError as exc: raise LLMDeferred('provider_unavailable',300) from exc
        if r.status_code==429:
            retry=r.headers.get('Retry-After'); seconds=int(retry) if retry and retry.isdigit() else 1800; raise LLMDeferred('quota',seconds)
        if r.status_code>=500: raise LLMDeferred('provider_unavailable',300)
        if r.status_code in {401,402,403,404}: raise LLMDeferred('credentials_or_model_unavailable',3600)
        if r.status_code>=400: raise LLMRejected('request_rejected')
        try:
            data=r.json(); choice=data['choices'][0]
            if choice.get('finish_reason')=='length': raise ValueError('truncated')
            selection=Selection.model_validate(json.loads(choice['message']['content']))
        except (KeyError,ValueError,json.JSONDecodeError) as exc: raise LLMRejected('invalid_output') from exc
        blocks={b.id:b.kind for b in doc.blocks}
        if blocks.get(selection.title_id)!='title' or (selection.date_id is not None and blocks.get(selection.date_id)!='date') or any(blocks.get(i)!='body' for i in selection.body_ids): raise LLMRejected('invalid_output')
        return selection
