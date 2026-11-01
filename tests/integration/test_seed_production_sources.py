from models import Source, SourceVersion
from scripts.bootstrap_db import bootstrap_database
from database import make_engine, make_session_factory
from scripts.datoslab_catalog import VERIFIED_SLUGS
from scripts.seed_production_sources import seed_production_sources


def test_seed_registers_catalog_enables_verified_and_is_idempotent(tmp_path):
    url = f"sqlite:///{(tmp_path / 'seed.db').as_posix()}"
    bootstrap_database(url)
    factory = make_session_factory(make_engine(url))
    with factory() as db:
        first = seed_production_sources(db)
        assert first["universities_total"] == 21
        assert first["sources_enabled"] == len(VERIFIED_SLUGS) == 11

        ucm = db.query(Source).filter(Source.start_url.endswith("/UCM")).one()
        snapshot = db.get(SourceVersion, (ucm.id, ucm.revision))
        assert snapshot is not None
        assert snapshot.snapshot_json["enabled"] is False
        assert snapshot.snapshot_json["auto_publish"] is False

        upla = db.query(Source).filter(Source.start_url.endswith("/UPLA")).one()
        assert upla.enabled is True
        assert upla.auto_publish is True
        assert upla.validated_revision == upla.revision

        # Simulate an operator disabling a verified source from /admin.
        upla.enabled = False
        upla.revision += 1
        db.commit()

        second = seed_production_sources(db)
        db.refresh(upla)
        assert upla.enabled is False
        assert second["sources_created"] == 0


def test_catalog_images_include_directory_and_www_domain_variants():
    from scripts.datoslab_catalog import DATOSLAB_PROFILES, build_source_input

    profile = next(profile for profile in DATOSLAB_PROFILES if profile.slug == "UAYSEN")
    source = build_source_input(profile, university_id=1)
    assert source.max_articles == 10
    assert source.allowed_image_hosts == ["uninews.datoslab.cl", "uaysen.cl", "www.uaysen.cl"]
