"""Independent collector command line; no backend imports or cwd assumptions."""
from __future__ import annotations
import argparse, json
from datetime import UTC, datetime
from uuid import UUID
from pathlib import Path
import portalocker
from collector.config import load_settings
from collector.pipeline import run_once
from collector.store import CollectorStore
from shared.backup import backup_sqlite

def main(argv=None)->int:
    parser=argparse.ArgumentParser(prog='python -m collector'); parser.add_argument('--env',required=True,type=Path)
    sub=parser.add_subparsers(dest='command',required=True); sub.add_parser('run-once'); sub.add_parser('status'); sub.add_parser('doctor')
    retry_parser=sub.add_parser('retry',help='requeue one local work item'); retry_parser.add_argument('--item',required=True,type=UUID)
    recover_parser=sub.add_parser('reprocess-model-failures',help='archive failed-model deliveries and retry saved documents')
    recover_parser.add_argument('--backup',required=True,type=Path,help='new, verified SQLite backup path')
    backup_parser=sub.add_parser('backup',help='create a verified SQLite backup'); backup_parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv)
    try: settings=load_settings(args.env)
    except Exception as exc: print(f'configuration_error: {exc}'); return 2
    if args.command=='backup':
        try: backup_sqlite(settings.data_dir/'collector.db',args.output); print(json.dumps({'backup':str(args.output.resolve()),'verified':True})); return 0
        except (OSError,ValueError,RuntimeError) as exc: print(f'backup_error: {exc}'); return 1
    if args.command=='retry':
        with CollectorStore(settings.data_dir/'collector.db') as store:
            if not store.retry_item(str(args.item),datetime.now(UTC)): print('retry_error: item_not_found_or_synced'); return 1
        print(json.dumps({'item':str(args.item),'queued':True})); return 0
    if args.command=='reprocess-model-failures':
        try:
            with portalocker.Lock(settings.data_dir/'collector.lock',timeout=0):
                backup_sqlite(settings.data_dir/'collector.db',args.backup)
                with CollectorStore(settings.data_dir/'collector.db') as store:
                    count=store.requeue_model_failures(datetime.now(UTC))
            print(json.dumps({'requeued':count,'backup':str(args.backup.resolve()),'verified':True})); return 0
        except (OSError,ValueError,RuntimeError,portalocker.exceptions.LockException) as exc:
            print(f'reprocess_error: {exc}'); return 1
    if args.command=='status':
        with CollectorStore(settings.data_dir/'collector.db') as store:
            print(json.dumps({'data_dir':str(settings.data_dir),'pending':sum(len(store.pending(s,__import__('datetime').datetime.now(__import__('datetime').UTC),10000)) for s in ('download','llm','delivery'))}))
        return 0
    if args.command=='doctor':
        try: settings.require_secrets(); print('doctor: configuration valid'); return 0
        except ValueError as exc: print(f'doctor: {exc}'); return 2
    summary=run_once(settings); print(summary.model_dump_json()); return summary.exit_code
if __name__=='__main__': raise SystemExit(main())
