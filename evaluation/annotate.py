from __future__ import annotations
import argparse,json
from pathlib import Path
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--documents',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(argv); out=[]
    for doc in json.loads(a.documents.read_text(encoding='utf-8')):
        out.append({k:doc[k] for k in ('article_id','university_id','source_id','source_url','captured_at','html_sha256','document_hash')}|{'split':doc.get('split','development'),'gold':{'title':None,'body':None,'category':None,'published_on':None},'annotation_notes':''})
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return 0
if __name__=='__main__': raise SystemExit(main())
