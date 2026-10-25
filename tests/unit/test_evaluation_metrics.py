from evaluation.metrics import body_scores,macro_f1
def test_metrics_are_reproducible():
    assert body_scores('Universidad publica anuncia becas','Universidad anuncia becas')['recall']==0.75
    assert macro_f1(['Academia','Becas'],['Academia','Cultura'])==1/3
