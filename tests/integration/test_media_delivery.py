from datetime import UTC, datetime
from uuid import uuid4

from collector.store import CollectorStore
from shared.contracts import ArticleFields, Delivery, Document, ImageAsset, Receipt, SourceConfig, TextBlock
from shared.validation import document_digest


def test_verified_media_is_queued_only_after_article_receipt(tmp_path):
    source = SourceConfig(id=1, university_id=1, university_name='Universidad', revision=1, validated_revision=1,
        start_url='https://uni.example/', allowed_hosts=['uni.example'])
    blocks = [TextBlock(id=0, kind='title', text='Titulo'), TextBlock(id=1, kind='body', text='Cuerpo')]
    document = Document(source_id=1, source_revision=1, canonical_url='https://uni.example/a', fetched_at=datetime.now(UTC),
        document_hash=document_digest(blocks, [1]), html_sha256='a'*64, blocks=blocks, expected_body_ids=[1])
    image = ImageAsset(status='ready', original_url='https://uni.example/image.png', sha256='b'*64, content_type='image/png', width=300, height=160, byte_size=3)
    delivery = Delivery(delivery_id=uuid4(), run_id=uuid4(), document=document, selection=None,
        fields=ArticleFields(title='Titulo', content='Cuerpo'), issues=[], model=None, image=image)
    with CollectorStore(tmp_path/'collector.db') as store:
        item = store.enqueue_url(source, document.canonical_url, delivery.run_id)
        store.save_document(item, document, '<article/>')
        store.save_image(item, image, b'png')
        store.save_delivery(item, delivery)
        assert store.pending_media(datetime.now(UTC)) == []
        store.acknowledge(delivery.delivery_id, Receipt(delivery_id=delivery.delivery_id, revision_id=7, news_id=None, outcome='pending'))
        pending = store.pending_media(datetime.now(UTC))
        assert len(pending) == 1 and pending[0][0].revision_id == 7 and pending[0][1].read_bytes() == b'png'
