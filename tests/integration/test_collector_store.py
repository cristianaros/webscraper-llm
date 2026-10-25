from datetime import UTC, datetime
import hashlib
from uuid import uuid4
from collector.store import CollectorStore
from shared.contracts import ArticleFields, Delivery, Document, SourceConfig, TextBlock
from shared.validation import document_digest

def test_outbox_survives_reopen(tmp_path):
    source=SourceConfig(id=1,university_id=1,university_name='Universidad',revision=1,validated_revision=1,start_url='https://uni.example/',allowed_hosts=['uni.example'])
    blocks=[TextBlock(id=0,kind='title',text='Titulo correcto'),TextBlock(id=1,kind='body',text='Cuerpo original')]
    document=Document(source_id=1,source_revision=1,canonical_url='https://uni.example/a',fetched_at=datetime.now(UTC),document_hash=document_digest(blocks,[1]),html_sha256=hashlib.sha256(b'a').hexdigest(),blocks=blocks,expected_body_ids=[1],trusted_container=True)
    delivery=Delivery(delivery_id=uuid4(),run_id=uuid4(),document=document,selection=None,fields=ArticleFields(title='Titulo correcto',content='Cuerpo original'),issues=['llm_selection_missing'],model=None)
    path=tmp_path/'collector.db'
    with CollectorStore(path) as store:
        item=store.enqueue_url(source,document.canonical_url,delivery.run_id); store.save_document(item,document,'<article>Documento</article>'); store.save_delivery(item,delivery)
    with CollectorStore(path) as store:
        pending=store.pending('delivery',datetime.now(UTC),10)
        assert len(pending)==1 and pending[0].delivery.delivery_id==delivery.delivery_id

def test_budget_last_slot_is_atomic(tmp_path):
    now=datetime.now(UTC)
    with CollectorStore(tmp_path/'collector.db') as store:
        assert store.reserve_llm(now,1,1)
        assert not store.reserve_llm(now,1,1)

def test_requeue_model_failures_archives_payload_and_preserves_other_deliveries(tmp_path):
    now=datetime.now(UTC)
    source=SourceConfig(id=1,university_id=1,university_name='Universidad',revision=1,validated_revision=1,start_url='https://uni.example/',allowed_hosts=['uni.example'])
    blocks=[TextBlock(id=0,kind='title',text='Titulo correcto'),TextBlock(id=1,kind='body',text='Cuerpo original')]
    path=tmp_path/'collector.db'
    ids=[]
    with CollectorStore(path) as store:
        for index,code in enumerate(('credentials_or_model_unavailable','invalid_output')):
            doc=Document(source_id=1,source_revision=1,canonical_url=f'https://uni.example/{index}',fetched_at=now,document_hash=document_digest(blocks,[1]),html_sha256=hashlib.sha256(b'a').hexdigest(),blocks=blocks,expected_body_ids=[1])
            delivery=Delivery(delivery_id=uuid4(),run_id=uuid4(),document=doc,selection=None,fields=ArticleFields(title='Titulo correcto',content='Cuerpo original'),issues=['llm_selection_missing',code],model=None)
            item=store.enqueue_url(source,doc.canonical_url,delivery.run_id)
            store.save_document(item,doc,'<article>Documento</article>')
            store.save_delivery(item,delivery)
            ids.append((item,str(delivery.delivery_id)))
        assert store.requeue_model_failures(now)==1
        assert store.requeue_model_failures(now)==0
        assert [item.id for item in store.pending('llm',now,10)]==[ids[0][0]]
        assert [item.id for item in store.pending('delivery',now,10)]==[ids[1][0]]
        archived=store.db.execute('SELECT payload_json FROM archived_outbox WHERE delivery_id=?',(ids[0][1],)).fetchone()
        assert Delivery.model_validate_json(archived[0]).issues[-1]=='credentials_or_model_unavailable'
