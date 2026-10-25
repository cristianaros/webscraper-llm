"""Seed the top 22 Chilean universities and their news sources."""
from __future__ import annotations

import os
from urllib.parse import urlparse
from database import make_engine, make_session_factory
from models import Source
from services.sources import create_source, create_university
from shared.contracts import SourceInput

UNIVERSITIES = [
    ("Pontificia Universidad Católica de Chile (UC)", "https://www.uc.cl/noticias/"),
    ("Universidad de Chile (UCh)", "https://uchile.cl/noticias"),
    ("Universidad de Santiago de Chile (USACH)", "https://www.usach.cl/noticias"),
    ("Universidad de Concepción (UdeC)", "https://noticias.udec.cl/"),
    ("Universidad Adolfo Ibáñez (UAI)", "https://noticias.uai.cl/"),
    ("Universidad Técnica Federico Santa María (UTFSM)", "https://noticias.usm.cl/"),
    ("Pontificia Universidad Católica de Valparaíso (PUCV)", "https://www.pucv.cl/pucv/noticias"),
    ("Universidad de los Andes (UAndes)", "https://www.uandes.cl/noticias/"),
    ("Universidad Andrés Bello (UNAB)", "https://noticias.unab.cl/"),
    ("Universidad Austral de Chile (UACh)", "https://diario.uach.cl/"),
    ("Universidad Diego Portales (UDP)", "https://www.udp.cl/noticias/"),
    ("Universidad del Desarrollo (UDD)", "https://www.udd.cl/noticias/"),
    ("Universidad de Talca (UTalca)", "https://www.utalca.cl/noticias/"),
    ("Universidad de Valparaíso (UV)", "https://uv.cl/noticias/"),
    ("Universidad Católica del Norte (UCN)", "https://noticias.ucn.cl/"),
    ("Universidad de La Frontera (UFRO)", "https://noticias.ufro.cl/"),
    ("Universidad de Tarapacá (UTA)", "https://www.uta.cl/index.php/category/noticias/"),
    ("Universidad Tecnológica Metropolitana (UTEM)", "https://noticias.utem.cl/"),
    ("Universidad Alberto Hurtado (UAH)", "https://www.uahurtado.cl/noticias/"),
    ("Universidad de Viña del Mar (UVM)", "https://www.uvm.cl/noticias/"),
    ("Universidad de Playa Ancha (UPLA)", "https://www.upla.cl/noticias/"),
    ("Universidad de Las Américas (UDLA)", "https://noticias.udla.cl/"),
]


def seed() -> None:
    db_url = os.getenv("DATABASE_URL", "sqlite:////data/university_news.db")
    engine = make_engine(db_url)
    session_factory = make_session_factory(engine)
    db = session_factory()
    try:
        created_count = 0
        for name, url in UNIVERSITIES:
            try:
                host = urlparse(url).hostname or ""
                allowed = list({host, host.replace("www.", "") if host.startswith("www.") else f"www.{host}"})
                u = create_university(db, name)
                create_source(
                    db,
                    SourceInput(
                        university_id=u.id,
                        start_url=url,
                        allowed_hosts=allowed,
                        allowed_image_hosts=allowed,
                        interval_minutes=360,
                        link_selector="article a[href], .noticia a[href], a[href*='noticia']",
                        title_selector="h1",
                        date_selector="time",
                        render_mode="http",
                        enabled=True,
                        auto_publish=True,
                    ),
                )
                created_count += 1
                print(f"OK: {name}")
            except Exception as exc:
                print(f"Skip ({name}): {exc}")

        for s in db.query(Source).all():
            s.enabled = True
            s.auto_publish = True
            s.validated_revision = s.revision
        db.commit()
        print(f"\nTotal fuentes activadas: {db.query(Source).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
