import unicodedata
from datetime import datetime, timezone
from fastapi import HTTPException
from shared.contracts import SourceInput, SourceConfig
from models import University, Source, SourceVersion
def normalize_name(name): return " ".join(unicodedata.normalize("NFC", name).split()).casefold()
def source_config(db, source):
    uni = db.get(University, source.university_id)
    return SourceConfig.model_validate({**source.config_json, "id":source.id, "university_id":source.university_id, "university_name":uni.name, "start_url":source.start_url, "revision":source.revision, "validated_revision":source.validated_revision, "enabled":source.enabled, "auto_publish":source.auto_publish})
def snapshot(db, source): db.add(SourceVersion(source_id=source.id, revision=source.revision, snapshot_json=source_config(db, source).model_dump(mode="json")))
def create_university(db, name):
    value = " ".join(name.split())
    if not value: raise HTTPException(422, "invalid_name")
    row = University(name=value, normalized_name=normalize_name(value)); db.add(row)
    try: db.commit()
    except Exception: db.rollback(); raise HTTPException(409, "duplicate_university")
    db.refresh(row); return row
def create_source(db, payload: SourceInput):
    if not db.get(University, payload.university_id): raise HTTPException(422, "unknown_university")
    raw=payload.model_dump(); raw.pop("university_id"); raw.pop("start_url"); enabled=raw.pop("enabled"); auto=raw.pop("auto_publish")
    source=Source(university_id=payload.university_id,start_url=payload.start_url,config_json=raw,enabled=False,auto_publish=False); db.add(source); db.flush(); snapshot(db,source); db.commit(); return source_config(db,source)
def patch_source(db, ident, data, expected_revision):
    source=db.get(Source,ident)
    if not source: raise HTTPException(404,"source_not_found")
    if source.revision != expected_revision: raise HTTPException(409,"stale_revision")
    existing=source_config(db,source).model_dump(); existing.update(data); existing.pop("id",None); existing.pop("university_name",None); existing.pop("revision",None); existing.pop("validated_revision",None)
    value=SourceInput.model_validate(existing); old=source_config(db,source)
    raw=value.model_dump(); source.university_id=raw.pop("university_id"); source.start_url=raw.pop("start_url"); enabled=raw.pop("enabled"); auto=raw.pop("auto_publish")
    extraction={"start_url","allowed_hosts","allowed_image_hosts","feed_url","article_url_pattern","link_selector","next_selector","content_selector","title_selector","date_selector","render_mode","wait_selector","min_body_chars"}
    changed=any(getattr(old,k)!=getattr(value,k) for k in extraction)
    source.config_json=raw; source.revision+=1; source.enabled=enabled and source.validated_revision==old.revision and not changed; source.auto_publish=auto if not changed else False; source.validated_revision=source.revision if source.validated_revision==old.revision and not changed else None
    snapshot(db,source); db.commit(); return source_config(db,source)
