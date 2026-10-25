from __future__ import annotations
import re
from collections import Counter
_TOKEN=re.compile(r"\w+",re.UNICODE)
def _tokens(value:str)->Counter[str]: return Counter(_TOKEN.findall(value.casefold()))
def body_scores(expected:str,actual:str)->dict[str,float]:
    gold,pred=_tokens(expected),_tokens(actual); overlap=sum((gold&pred).values())
    precision=overlap/sum(pred.values()) if pred else 0.0; recall=overlap/sum(gold.values()) if gold else (1.0 if not pred else 0.0)
    return {'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 1.0}
def macro_f1(expected:list[str],actual:list[str])->float:
    labels=sorted(set(expected)|set(actual)); scores=[]
    for label in labels:
        tp=sum(e==label and a==label for e,a in zip(expected,actual)); fp=sum(e!=label and a==label for e,a in zip(expected,actual)); fn=sum(e==label and a!=label for e,a in zip(expected,actual)); scores.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    return sum(scores)/len(scores) if scores else 1.0
