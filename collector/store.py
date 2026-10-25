"""Durable local SQLite queue. Every external boundary is persisted first."""
from __future__ import annotations
import gzip, json, sqlite3
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4
from shared.contracts import Delivery, Document, ImageAsset, ImageDelivery, MediaReceipt, Receipt, Selection, SourceConfig, payload_digest

def _dt(value: datetime | None) -> str | None: return value.astimezone(UTC).isoformat() if value else None
def _model(value): return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)

class CollectorStore(AbstractContextManager):
    def __init__(self, path: Path) -> None: self.path, self.db = path, None
    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True); self.db = sqlite3.connect(self.path); self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL"); self.db.execute("PRAGMA busy_timeout=5000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS work_items(id TEXT PRIMARY KEY, source_id INTEGER NOT NULL, url TEXT NOT NULL, run_id TEXT NOT NULL, state TEXT NOT NULL, stage TEXT NOT NULL, document_json TEXT, html_gzip BLOB, attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at TEXT, error_code TEXT, UNIQUE(source_id,url,state));
        CREATE TABLE IF NOT EXISTS outbox(delivery_id TEXT PRIMARY KEY,item_id TEXT UNIQUE NOT NULL,payload_json TEXT NOT NULL,payload_hash TEXT NOT NULL,receipt_json TEXT,next_attempt_at TEXT,attempts INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS archived_outbox(delivery_id TEXT PRIMARY KEY,item_id TEXT NOT NULL,payload_json TEXT NOT NULL,payload_hash TEXT NOT NULL,next_attempt_at TEXT,attempts INTEGER NOT NULL,archived_at TEXT NOT NULL,reason TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS llm_cache(cache_key TEXT PRIMARY KEY,response_json TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS budgets(period TEXT PRIMARY KEY,attempts INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS source_cache(source_id INTEGER PRIMARY KEY,payload_json TEXT NOT NULL,generated_at TEXT NOT NULL,next_scan_at TEXT,cursor TEXT,last_success_at TEXT);
        CREATE TABLE IF NOT EXISTS runtime_state(key TEXT PRIMARY KEY,value_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS local_runs(run_id TEXT PRIMARY KEY,report_json TEXT NOT NULL,acknowledged INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS local_media(item_id TEXT PRIMARY KEY,image_json TEXT NOT NULL,data_path TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS media_outbox(delivery_id TEXT PRIMARY KEY,payload_json TEXT NOT NULL,data_path TEXT NOT NULL,next_attempt_at TEXT,attempts INTEGER NOT NULL DEFAULT 0,receipt_json TEXT);
        """)
        # Early development builds shipped a three-column cache.  Additive local
        # migration preserves the queue instead of recreating it.
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(source_cache)")}
        for name, definition in (("next_scan_at", "TEXT"), ("cursor", "TEXT"), ("last_success_at", "TEXT")):
            if name not in columns:
                self.db.execute(f"ALTER TABLE source_cache ADD COLUMN {name} {definition}")
        self.db.commit(); return self
    def __exit__(self,*args):
        if self.db: self.db.close()
    def enqueue_url(self, source: SourceConfig, url: str, run_id: UUID, *, refresh: bool=False) -> str:
        row=self.db.execute("SELECT id FROM work_items WHERE source_id=? AND url=? AND state != 'synced'",(source.id,url)).fetchone()
        if row: return row[0]
        item=str(uuid4()); self.db.execute("INSERT INTO work_items(id,source_id,url,run_id,state,stage) VALUES(?,?,?,?,?,?)",(item,source.id,url,str(run_id),"discovered","download")); self.db.commit(); return item
    def save_document(self,item_id:str,doc:Document,html:str)->None:
        self.db.execute("UPDATE work_items SET document_json=?,html_gzip=?,state='fetched',stage='llm' WHERE id=?",(_model(doc),gzip.compress(html.encode()),item_id)); self.db.commit()
    def save_image(self, item_id: str, asset: ImageAsset, data: bytes) -> None:
        """Durably retain verified original bytes before any API request."""
        from collector.images import store_original
        path = store_original(self.path.parent / 'media', asset, data)
        with self.db:
            self.db.execute("INSERT INTO local_media(item_id,image_json,data_path) VALUES(?,?,?) ON CONFLICT(item_id) DO UPDATE SET image_json=excluded.image_json,data_path=excluded.data_path", (item_id, _model(asset), str(path)))
    def image_for_item(self, item_id: str) -> ImageAsset:
        row = self.db.execute("SELECT image_json FROM local_media WHERE item_id=?", (item_id,)).fetchone()
        return ImageAsset.model_validate_json(row[0]) if row else ImageAsset(status='not_found')
    def save_delivery(self,item_id:str,delivery:Delivery)->None:
        payload=delivery.model_dump(mode="json"); digest=payload_digest(payload)
        with self.db:
            old=self.db.execute("SELECT payload_hash FROM outbox WHERE delivery_id=?",(str(delivery.delivery_id),)).fetchone()
            if old and old[0] != digest: raise ValueError("delivery_id_payload_conflict")
            self.db.execute("INSERT OR IGNORE INTO outbox VALUES(?,?,?,?,?,?,?)",(str(delivery.delivery_id),item_id,json.dumps(payload,ensure_ascii=False,sort_keys=True),digest,None,None,0))
            self.db.execute("UPDATE work_items SET state='ready',stage='delivery' WHERE id=?",(item_id,))
    def acknowledge(self,delivery_id:UUID,receipt:Receipt)->None:
        with self.db:
            row=self.db.execute("SELECT item_id FROM outbox WHERE delivery_id=?",(str(delivery_id),)).fetchone()
            if not row: raise KeyError("unknown_delivery")
            self.db.execute("UPDATE outbox SET receipt_json=? WHERE delivery_id=?",(_model(receipt),str(delivery_id)))
            self.db.execute("UPDATE work_items SET state='synced',stage='done' WHERE id=?",(row[0],))
            if receipt.revision_id:
                image = self.image_for_item(row[0])
                if image.status == 'ready':
                    media = ImageDelivery(delivery_id=delivery_id, revision_id=receipt.revision_id, expected_document_hash=Delivery.model_validate_json(self.db.execute("SELECT payload_json FROM outbox WHERE delivery_id=?", (str(delivery_id),)).fetchone()[0]).document.document_hash, image=image)
                    path = self.db.execute("SELECT data_path FROM local_media WHERE item_id=?", (row[0],)).fetchone()[0]
                    self.db.execute("INSERT OR IGNORE INTO media_outbox(delivery_id,payload_json,data_path,attempts) VALUES(?,?,?,0)", (str(delivery_id), _model(media), path))
    def defer(self,item_id:str,stage:str,code:str,next_attempt_at:datetime)->None:
        self.db.execute("UPDATE work_items SET state=?,stage=?,attempts=attempts+1,error_code=?,next_attempt_at=? WHERE id=?",("llm_wait" if stage=="llm" else "deferred",stage,code,_dt(next_attempt_at),item_id)); self.db.commit()
    def retry_item(self, item_id: str, now: datetime) -> bool:
        """Explicitly requeue one deferred item for operator recovery."""
        row = self.db.execute("SELECT id, state, stage FROM work_items WHERE id=?", (item_id,)).fetchone()
        if row is None or row[1] == "synced": return False
        state = "fetched" if row[2] == "llm" else "discovered" if row[2] == "download" else "ready"
        self.db.execute("UPDATE work_items SET state=?, next_attempt_at=?, error_code=NULL WHERE id=?", (state, _dt(now), item_id))
        self.db.commit(); return True
    def requeue_model_failures(self, now: datetime) -> int:
        """Archive unacknowledged failed-model deliveries and retry saved documents."""
        rows = self.db.execute("""
            SELECT o.*, w.state, w.stage, w.document_json
            FROM outbox AS o JOIN work_items AS w ON w.id=o.item_id
            WHERE o.receipt_json IS NULL AND w.state='ready' AND w.stage='delivery'
              AND w.document_json IS NOT NULL
        """).fetchall()
        count = 0
        with self.db:
            for row in rows:
                delivery = Delivery.model_validate_json(row['payload_json'])
                if delivery.selection is not None or delivery.model is not None or 'credentials_or_model_unavailable' not in delivery.issues:
                    continue
                self.db.execute("""INSERT INTO archived_outbox
                    (delivery_id,item_id,payload_json,payload_hash,next_attempt_at,attempts,archived_at,reason)
                    VALUES(?,?,?,?,?,?,?,?)""", (row['delivery_id'],row['item_id'],row['payload_json'],row['payload_hash'],row['next_attempt_at'],row['attempts'],_dt(now),'model_unavailable'))
                self.db.execute("DELETE FROM outbox WHERE delivery_id=?", (row['delivery_id'],))
                self.db.execute("UPDATE work_items SET state='fetched',stage='llm',next_attempt_at=?,error_code=NULL WHERE id=?", (_dt(now),row['item_id']))
                count += 1
        return count
    def block(self,item_id: str, stage: str, code: str) -> None:
        """A policy denial is visible and never retried automatically."""
        self.db.execute("UPDATE work_items SET state='blocked',stage=?,attempts=attempts+1,error_code=?,next_attempt_at=NULL WHERE id=?", (stage, code, item_id)); self.db.commit()
    def pending(self, stage: str, now: datetime, limit: int, source_id: int | None = None):
        if source_id is not None:
            rows = self.db.execute("SELECT * FROM work_items WHERE stage=? AND source_id=? AND state NOT IN ('synced', 'blocked') AND (next_attempt_at IS NULL OR next_attempt_at<=?) LIMIT ?", (stage, source_id, _dt(now), limit)).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM work_items WHERE stage=? AND state NOT IN ('synced', 'blocked') AND (next_attempt_at IS NULL OR next_attempt_at<=?) LIMIT ?", (stage, _dt(now), limit)).fetchall()
        return [self._item(row) for row in rows]
    def _item(self,row):
        from dataclasses import dataclass
        @dataclass
        class WorkItem: id:str; source_id:int; url:str; run_id:UUID; state:str; document:Document|None; delivery:Delivery|None; attempts:int; next_attempt_at:datetime|None
        out=self.db.execute("SELECT payload_json FROM outbox WHERE item_id=?",(row['id'],)).fetchone()
        return WorkItem(row['id'],row['source_id'],row['url'],UUID(row['run_id']),row['state'],Document.model_validate_json(row['document_json']) if row['document_json'] else None,Delivery.model_validate_json(out[0]) if out else None,row['attempts'],datetime.fromisoformat(row['next_attempt_at']) if row['next_attempt_at'] else None)
    def _key(self,doc,model,prompt): return f"{doc.source_id}:{doc.canonical_url}:{doc.document_hash}:{doc.source_revision}:{prompt}:{model}"
    def lookup_selection(self,doc,model,prompt):
        row=self.db.execute("SELECT response_json FROM llm_cache WHERE cache_key=?",(self._key(doc,model,prompt),)).fetchone(); return Selection.model_validate_json(row[0]) if row else None
    def cache_selection(self,doc,model,prompt,selection): self.db.execute("INSERT OR REPLACE INTO llm_cache VALUES(?,?,?)",(self._key(doc,model,prompt),_model(selection),_dt(datetime.now(UTC)))); self.db.commit()
    def reserve_llm(self,now,daily_limit,minute_limit):
        day,minute=f"day:{now:%Y-%m-%d}",f"minute:{now:%Y-%m-%dT%H:%M}"
        self.db.execute("BEGIN IMMEDIATE")
        try:
            values={key:(self.db.execute("SELECT attempts FROM budgets WHERE period=?",(key,)).fetchone() or [0])[0] for key in (day,minute)}
            if values[day]>=daily_limit or values[minute]>=minute_limit: self.db.rollback(); return False
            for key in (day,minute): self.db.execute("INSERT INTO budgets VALUES(?,1) ON CONFLICT(period) DO UPDATE SET attempts=attempts+1",(key,))
            self.db.commit(); return True
        except: self.db.rollback(); raise
    def cache_sources(self,sources,generated_at):
        with self.db:
            for source in sources:
                previous = self.db.execute("SELECT payload_json FROM source_cache WHERE source_id=?", (source.id,)).fetchone()
                revision_changed = previous is not None and SourceConfig.model_validate_json(previous[0]).revision != source.revision
                if revision_changed:
                    self.db.execute("UPDATE source_cache SET payload_json=?,generated_at=?,next_scan_at=NULL,cursor=NULL,last_success_at=NULL WHERE source_id=?", (_model(source),_dt(generated_at),source.id))
                else:
                    self.db.execute("INSERT INTO source_cache(source_id,payload_json,generated_at) VALUES(?,?,?) ON CONFLICT(source_id) DO UPDATE SET payload_json=excluded.payload_json,generated_at=excluded.generated_at",(source.id,_model(source),_dt(generated_at)))
    def valid_sources(self,now, ttl_hours: int = 24):
        threshold = _dt(now - timedelta(hours=ttl_hours))
        return [SourceConfig.model_validate_json(row[0]) for row in self.db.execute("SELECT payload_json FROM source_cache WHERE generated_at>=?", (threshold,))]
    def source_due(self, source: SourceConfig, now: datetime, *, force: bool = False) -> bool:
        row = self.db.execute("SELECT next_scan_at FROM source_cache WHERE source_id=?", (source.id,)).fetchone()
        return force or row is None or row[0] is None or row[0] <= _dt(now)
    def source_cursor(self, source_id: int) -> str | None:
        row = self.db.execute("SELECT cursor FROM source_cache WHERE source_id=?", (source_id,)).fetchone()
        return row[0] if row else None
    def save_discovery(self, source: SourceConfig, *, cursor: str | None, now: datetime) -> None:
        with self.db:
            self.db.execute("UPDATE source_cache SET cursor=?, last_success_at=?, next_scan_at=? WHERE source_id=?", (cursor, _dt(now), _dt(now + timedelta(minutes=source.interval_minutes)), source.id))
    def known_urls(self, source_id: int) -> set[str]:
        return {row[0] for row in self.db.execute("SELECT url FROM work_items WHERE source_id=?", (source_id,))}
    def save_run(self, report) -> None:
        with self.db:
            self.db.execute("INSERT INTO local_runs(run_id,report_json,acknowledged) VALUES(?,?,0) ON CONFLICT(run_id) DO UPDATE SET report_json=excluded.report_json", (str(report.run_id), _model(report)))
    def pending_reports(self):
        from shared.contracts import RunReport
        return [RunReport.model_validate_json(row[0]) for row in self.db.execute("SELECT report_json FROM local_runs WHERE acknowledged=0")]
    def acknowledge_report(self, run_id: UUID) -> None:
        with self.db: self.db.execute("UPDATE local_runs SET acknowledged=1 WHERE run_id=?", (str(run_id),))
    def pending_media(self, now: datetime, limit: int = 100):
        rows = self.db.execute("SELECT * FROM media_outbox WHERE receipt_json IS NULL AND (next_attempt_at IS NULL OR next_attempt_at<=?) LIMIT ?", (_dt(now), limit)).fetchall()
        return [(ImageDelivery.model_validate_json(row['payload_json']), Path(row['data_path'])) for row in rows]
    def acknowledge_media(self, delivery_id: UUID, receipt: MediaReceipt) -> None:
        with self.db: self.db.execute("UPDATE media_outbox SET receipt_json=? WHERE delivery_id=?", (_model(receipt), str(delivery_id)))
    def defer_media(self, delivery_id: UUID, next_attempt_at: datetime) -> None:
        with self.db: self.db.execute("UPDATE media_outbox SET attempts=attempts+1,next_attempt_at=? WHERE delivery_id=?", (_dt(next_attempt_at), str(delivery_id)))
