"""A single, lock-protected and deadline-aware collection invocation."""
from __future__ import annotations
from datetime import UTC, datetime, timedelta
from uuid import uuid4
import time
import httpx
import portalocker
from collector.browser import BrowserFetcher
from collector.discovery import discover
from collector.documents import baseline_extract, build_document
from collector.http import FetchError, HttpFetcher
from collector.images import ImageFetcher, find_image_candidates
from collector.openrouter import LLMDeferred, LLMRejected, MiniMaxExtractor
from collector.store import CollectorStore
from collector.sync import SyncClient
from shared.contracts import Delivery, FREE_MODEL, RunReport, RunSummary
from shared.validation import materialize, validate_article

_COUNT_KEYS=('discovered','downloaded','llm_processed','delivered','published','unchanged','pending','failed')
_BLOCKING_CODES={'robots_denied','destination_host_not_allowed','private_destination','literal_ip_not_allowed','browser_selector_required'}

def process_item(store,item,source,extractor,settings,now):
    doc=item.document; cached=store.lookup_selection(doc,FREE_MODEL,'extract-v2')
    if cached is None:
        if not store.reserve_llm(now,settings.llm_daily_budget,settings.llm_rpm): store.defer(item.id,'llm','local_budget',now+timedelta(minutes=15)); return
        try: cached=extractor.extract(doc)
        except LLMDeferred as exc: store.defer(item.id,'llm',exc.code,now+timedelta(seconds=exc.retry_after_seconds or 1800)); return
        except LLMRejected as exc:
            fields=baseline_extract(doc,source); store.save_delivery(item.id,Delivery(delivery_id=uuid4(),run_id=item.run_id,document=doc,selection=None,fields=fields,issues=validate_article(fields,doc,None,source,now)+[exc.code],model=None,prompt_version='extract-v2',image=store.image_for_item(item.id))); return
        store.cache_selection(doc,FREE_MODEL,'extract-v2',cached)
    fields=materialize(doc,cached,source.timezone); store.save_delivery(item.id,Delivery(delivery_id=uuid4(),run_id=item.run_id,document=doc,selection=cached,fields=fields,issues=validate_article(fields,doc,cached,source,now),model=FREE_MODEL,prompt_version='extract-v2',image=store.image_for_item(item.id)))

def _fetch_due(store,source,fetcher,browser,clock,deadline,monotonic,counts):
    for item in store.pending('download',clock(),source.max_articles,source_id=source.id):
        if monotonic()>=deadline: continue
        try:
            result=(browser if source.render_mode=='browser' else fetcher).fetch(item.url,source)
            if result.status==304: store.defer(item.id,'download','not_modified',clock()+timedelta(minutes=source.interval_minutes)); continue
            if result.status>=400: raise FetchError(f'http_{result.status}')
            store.save_document(item.id,build_document(result,source),result.html or '')
            candidates=find_image_candidates(result.html or '', source, result.url)
            if candidates:
                try:
                    asset, data = ImageFetcher(fetcher).fetch(candidates[0], source)
                    store.save_image(item.id, asset, data)
                except (FetchError, ValueError):
                    # Text remains deliverable; retrying image transport is handled by later refetch/manual work.
                    pass
            counts['downloaded']+=1
        except FetchError as exc:
            if exc.code in _BLOCKING_CODES: store.block(item.id,'download',exc.code)
            else: store.defer(item.id,'download',exc.code,exc.retry_at or clock()+timedelta(minutes=5))

def _deliver(store,sync,clock,deadline,monotonic,counts):
    for item in store.pending('delivery',clock(),100):
        if monotonic()>=deadline:return
        try:
            receipt=sync.send(item.delivery); store.acknowledge(item.delivery.delivery_id,receipt); counts['delivered']+=1; counts[receipt.outcome]=counts.get(receipt.outcome,0)+1
        except httpx.HTTPError: store.defer(item.id,'delivery','api_unavailable',clock()+timedelta(minutes=5))
    for media, path in store.pending_media(clock()):
        if monotonic()>=deadline:return
        try:
            store.acknowledge_media(media.delivery_id, sync.send_media(media, path.read_bytes()))
        except (OSError, httpx.HTTPError):
            store.defer_media(media.delivery_id, clock()+timedelta(minutes=5))

def run_once(settings,*,clock=lambda:datetime.now(UTC),monotonic=None,http_transport=None)->RunSummary:
    monotonic=monotonic or time.monotonic; started=clock(); deadline=monotonic()+settings.run_budget_seconds; counts={key:0 for key in _COUNT_KEYS}
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    try:
      with portalocker.Lock(settings.data_dir/'collector.lock',timeout=0):
       with CollectorStore(settings.data_dir/'collector.db') as store, httpx.Client(transport=http_transport,trust_env=False,timeout=httpx.Timeout(30,connect=10)) as client:
        sync=SyncClient(settings,client); _deliver(store,sync,clock,deadline,monotonic,counts)
        try: sources=sync.sources(); store.cache_sources(sources,started)
        except httpx.HTTPError: sources=store.valid_sources(started,settings.source_cache_ttl_hours)
        try: claims={claim.source.id:claim for claim in sync.claim_runs()}
        except httpx.HTTPError: claims={}
        fetcher=HttpFetcher(client,allow_test_hosts=settings.allow_test_hosts); browser=BrowserFetcher(fetcher); extractor=MiniMaxExtractor(settings,client)
        for source in sources:
            if monotonic()>=deadline:break
            claim=claims.get(source.id)
            if (source.enabled or claim is not None) and store.source_due(source,clock(),force=claim is not None):
                try:
                    batch=discover(source,browser if source.render_mode=='browser' else fetcher,store.source_cursor(source.id),store.known_urls(source.id))
                    for url in batch.urls: store.enqueue_url(source,url,claim.run_id if claim else uuid4())
                    store.save_discovery(source,cursor=batch.next_cursor,now=clock()); counts['discovered']+=len(batch.urls)
                except FetchError: pass
            _fetch_due(store,source,fetcher,browser,clock,deadline,monotonic,counts)
            if claim and claim.trigger=='preview':
                docs=[x.document for x in store.pending('llm',clock(),3) if x.source_id==source.id][:3]
                preview={'source_revision':source.revision,'documents':[x.model_dump(mode='json') for x in docs],'selections':[None]*len(docs),'issues':[validate_article(baseline_extract(x,source),x,None,source,clock()) for x in docs]}
                try: sync.client.put(f'{settings.api_url}/api/collector/runs/{claim.run_id}/preview',headers=sync.headers,json=preview).raise_for_status()
                except httpx.HTTPError: pass
            elif not (claim and claim.trigger=='preview'):
                for item in store.pending('llm',clock(),source.max_articles,source_id=source.id):
                    if monotonic()<deadline: process_item(store,item,source,extractor,settings,clock()); counts['llm_processed']+=1
            if claim:
                report=RunReport(run_id=claim.run_id,source_id=source.id,trigger=claim.trigger,status='partial' if monotonic()>=deadline else 'success',started_at=started,finished_at=clock(),counts=counts)
                try: sync.report_claimed(report,claim)
                except httpx.HTTPError: store.save_run(report)
        _deliver(store,sync,clock,deadline,monotonic,counts)
        for report in store.pending_reports():
            try: sync.report(report); store.acknowledge_report(report.run_id)
            except httpx.HTTPError: break
        pending=sum(len(store.pending(stage,clock(),10000)) for stage in ('download','llm','delivery'))
        return RunSummary(started_at=started,finished_at=clock(),counts=counts,pending_count=pending,exit_code=0)
    except portalocker.exceptions.LockException:
      return RunSummary(started_at=started,finished_at=clock(),counts=counts,pending_count=0,exit_code=0)
