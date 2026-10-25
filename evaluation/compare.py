from __future__ import annotations
import argparse,json
from pathlib import Path
from evaluation.metrics import body_scores,macro_f1
def compare(corpus:Path,predictions:Path)->dict:
    gold={str(x['article_id']):x['gold'] for x in json.loads(corpus.read_text(encoding='utf-8'))}; rows=json.loads(predictions.read_text(encoding='utf-8')); bodies=[]; cats=[]; title=dates=total_dates=0
    for row in rows:
        g=gold[str(row['article_id'])]; title+=row.get('title')==g.get('title'); bodies.append(body_scores(g.get('body',''),row.get('body',''))); cats.append((g.get('category'),row.get('category')))
        if g.get('published_on') is not None: total_dates+=1; dates+=row.get('published_on')==g.get('published_on')
    return {'articles':len(rows),'title_accuracy':title/len(rows) if rows else 0.0,'date_accuracy':dates/total_dates if total_dates else None,'date_denominator':total_dates,'body':{k:sum(x[k] for x in bodies)/len(bodies) for k in ('precision','recall','f1')} if bodies else {},'category_macro_f1':macro_f1([x[0] for x in cats],[x[1] for x in cats])}
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--corpus',type=Path,required=True); p.add_argument('--predictions',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(argv); result=compare(a.corpus,a.predictions); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result)); return 0
if __name__=='__main__': raise SystemExit(main())
