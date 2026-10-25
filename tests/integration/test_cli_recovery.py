import json,os,subprocess,sys
from datetime import UTC,datetime
from pathlib import Path
from uuid import uuid4
from collector.store import CollectorStore
from shared.contracts import SourceConfig
def _run(tmp_path,args):
    return subprocess.run([sys.executable,'-m','collector','--env',str(tmp_path/'.env'),*args],cwd=tmp_path,env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[2])},capture_output=True,text=True)
def test_cli_retry_requeues_deferred_item(tmp_path):
    data=tmp_path/'data'; (tmp_path/'.env').write_text(f'COLLECTOR_DATA_DIR={data.as_posix()}\nCOLLECTOR_API_URL=http://127.0.0.1:8000\n')
    source=SourceConfig(id=1,university_id=1,university_name='U',revision=1,start_url='https://uni.example/',allowed_hosts=['uni.example'])
    with CollectorStore(data/'collector.db') as store: item=store.enqueue_url(source,'https://uni.example/a',uuid4()); store.defer(item,'download','timeout',datetime.now(UTC))
    result=_run(tmp_path,['retry','--item',item]); assert result.returncode==0 and json.loads(result.stdout)['queued'] is True
    with CollectorStore(data/'collector.db') as store: assert store.pending('download',datetime.now(UTC),10)[0].id==item
def test_cli_backup_is_verified(tmp_path):
    data=tmp_path/'data'; (tmp_path/'.env').write_text(f'COLLECTOR_DATA_DIR={data.as_posix()}\nCOLLECTOR_API_URL=http://127.0.0.1:8000\n')
    with CollectorStore(data/'collector.db'): pass
    output=tmp_path/'backup.db'; result=_run(tmp_path,['backup','--output',str(output)]); assert result.returncode==0 and output.exists() and json.loads(result.stdout)['verified']
