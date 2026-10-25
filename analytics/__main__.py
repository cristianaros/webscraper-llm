from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(prog="python -m analytics"); sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--database", required=True); p.add_argument("--output", required=True); p.add_argument("--limit", type=int, default=1000)
    i = sub.add_parser("inspect"); i.add_argument("--manifest", required=True)
    args = parser.parse_args()
    if args.command == "inspect":
        m = json.loads(Path(args.manifest).read_text(encoding="utf-8")); raw = Path(m["ndjson_path"]).read_bytes(); rows = [x for x in raw.splitlines() if x]
        if hashlib.sha256(raw).hexdigest() != m["sha256"] or len(rows) != m["record_count"]: raise SystemExit("manifest validation failed")
        from .schema import NEWS_COLUMNS
        for line in rows:
            if set(json.loads(line)) != set(NEWS_COLUMNS): raise SystemExit("schema validation failed")
        print(json.dumps({"valid": True, "records": len(rows), "sha256": m["sha256"]})); return
    from database import make_engine, make_session_factory
    from .exporter import prepare_batch
    import models
    engine = make_engine(f"sqlite:///{Path(args.database).resolve()}"); db = make_session_factory(engine)()
    try:
        result = prepare_batch(db, Path(args.output)); print(json.dumps(result.to_dict() if result else {"empty": True}))
    finally: db.close()
if __name__ == "__main__": main()
