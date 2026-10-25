from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from scripts.datoslab_catalog import DATOSLAB_PROFILES, build_source_input
from scripts.register_datoslab_sources import register_catalog
from scripts.activate_datoslab_sources import activate_from_audit
from database import Base
from models import Source, University
from services.sources import source_config


def test_catalog_matches_closed_university_directory():
    expected = {
        "PUCV", "UNAP", "UACH", "UCT", "UCSC", "UCM", "UCN",
        "UTFSM", "UA", "UDA", "UAYSEN", "UDEC", "ULAGOS", "UMAG",
        "UPLA", "UTALCA", "UTA", "UV", "UFRO", "USERENA", "UBIOBIO",
    }
    assert {profile.slug for profile in DATOSLAB_PROFILES} == expected
    assert len(DATOSLAB_PROFILES) == len(expected)
    for profile in DATOSLAB_PROFILES:
        value = build_source_input(profile, university_id=1)
        assert value.start_url == f"https://uninews.datoslab.cl/universidad/{profile.slug}"
        assert value.article_url_pattern == r"^https://uninews\.datoslab\.cl/detalle/[0-9]+$"
        assert value.link_selector == 'div.album.py-5 p.card-text a[href*="/detalle/"]'
        assert value.allowed_hosts[0] == "uninews.datoslab.cl"
        assert len(value.allowed_hosts) > 1
        assert value.enabled is False
        assert value.auto_publish is False


def test_registration_is_idempotent_and_starts_inactive():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        first = register_catalog(db)
        second = register_catalog(db)
        assert first == {"created": 21, "existing": 0, "updated": 0}
        assert second == {"created": 0, "existing": 21, "updated": 0}
        assert db.query(University).count() == 21
        assert db.query(Source).count() == 21
        for source in db.query(Source).all():
            config = source_config(db, source)
            assert config.enabled is False
            assert config.auto_publish is False
            assert config.validated_revision is None


def test_activation_requires_validated_sample_on_expected_host():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        register_catalog(db)
        sample = {
            "slug": "UPLA", "status": "sample_ok", "published_on": "2026-10-14",
            "url": "https://upla.cl/noticias/una-noticia", "title_chars": 50,
            "body_chars": 500,
        }
        selected_source = db.query(Source).filter(Source.start_url.endswith("/UPLA")).one()
        sample.update({"source_id": selected_source.id, "source_revision": selected_source.revision})
        try:
            activate_from_audit(db, [{**sample, "url": "https://otro.example/noticia"}], {"UPLA"}, {"UPLA"})
        except ValueError as exc:
            assert str(exc) == "unexpected_article_host:UPLA"
        else:
            raise AssertionError("unexpected host was accepted")
        try:
            activate_from_audit(db, [{**sample, "source_revision": 99}], {"UPLA"}, {"UPLA"})
        except ValueError as exc:
            assert str(exc) == "stale_audit:UPLA"
        else:
            raise AssertionError("stale sample was accepted")
        assert activate_from_audit(db, [sample], {"UPLA"}, {"UPLA"}) == {
            "enabled": 1, "auto_publish": 1,
        }
        source = db.query(Source).filter(Source.start_url.endswith("/UPLA")).one()
        assert source.enabled is True
        assert source.auto_publish is True
        assert source.validated_revision == source.revision
        assert register_catalog(db) == {"created": 0, "existing": 21, "updated": 0}


def test_existing_profile_requires_explicit_update():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        register_catalog(db)
        source = db.query(Source).filter(Source.start_url.endswith("/UCT")).one()
        source.config_json = {**source.config_json, "link_selector": "a.old-selector"}
        db.commit()
        try:
            register_catalog(db)
        except ValueError as exc:
            assert str(exc) == "source_was_edited:UCT"
        else:
            raise AssertionError("an existing profile was overwritten")
        result = register_catalog(db, update_inactive=True)
        assert result == {"created": 0, "existing": 20, "updated": 1}
        db.refresh(source)
        assert source.revision == 2
        assert source.config_json["link_selector"] == 'div.album.py-5 p.card-text a[href*="/detalle/"]'
