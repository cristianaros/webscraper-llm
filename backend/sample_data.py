"""
Datos de demo para precargar el sistema con noticias universitarias de ejemplo.
Ejecutar: python sample_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
import models
from dotenv import load_dotenv

load_dotenv()

SAMPLE_NEWS = [
    {
        "title": "Universidad lanza programa de becas 2026 para estudiantes de bajos recursos",
        "summary": "La universidad anuncia 500 becas completas para el ciclo académico 2026, cubriendo matrícula, alimentación y materiales.",
        "content": (
            "La Universidad Central ha anunciado el lanzamiento de su Programa de Becas Integral 2026, "
            "el más ambicioso en la historia de la institución. Este programa otorgará 500 becas completas "
            "a estudiantes con alto rendimiento académico y situación socioeconómica vulnerable. "
            "Las becas cubren el 100% de la matrícula, una asignación mensual de alimentación de $150, "
            "y materiales de estudio por un valor de $300 al semestre. "
            "Los interesados pueden aplicar desde el 1 de julio hasta el 31 de agosto a través del portal "
            "web institucional. Los requisitos incluyen promedio académico mínimo de 8.0, "
            "documentación socioeconómica y una carta de motivación. "
            "El rector Dr. Marcos Villareal indicó que 'la educación es el motor del desarrollo nacional "
            "y este programa busca garantizar que ningún joven talentoso se quede sin oportunidades por "
            "falta de recursos económicos'."
        ),
        "category": "Becas",
        "university": "Universidad Central",
        "author": "Oficina de Comunicaciones",
        "is_featured": True,
        "image_url": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800",
    },
    {
        "title": "Investigadores universitarios desarrollan algoritmo de IA para detectar enfermedades cardíacas",
        "summary": "El equipo del Laboratorio de Computación Avanzada logra un 94% de precisión en detección temprana de enfermedades del corazón.",
        "content": (
            "Un equipo de investigadores de la Facultad de Ingeniería en Sistemas desarrolló un algoritmo "
            "de inteligencia artificial capaz de detectar enfermedades cardíacas con un 94% de precisión "
            "utilizando únicamente datos de electrocardiogramas digitales. "
            "El proyecto, liderado por la Dra. Ana Sofía Ramírez, empleó técnicas de Deep Learning "
            "y fue entrenado con más de 50,000 registros clínicos anonimizados. "
            "El algoritmo fue validado en el Hospital Universitario durante seis meses, "
            "reduciendo los tiempos de diagnóstico en un 40% y permitiendo intervenciones más tempranas. "
            "La investigación fue publicada en la revista Nature Digital Medicine y ha recibido interés "
            "de tres empresas farmacéuticas internacionales para su comercialización. "
            "El proyecto recibirá financiamiento adicional de $2 millones para su segunda fase."
        ),
        "category": "Investigación",
        "university": "Universidad Central",
        "author": "Dr. Ana Sofía Ramírez",
        "is_featured": True,
        "image_url": "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800",
    },
    {
        "title": "Nuevo campus tecnológico abrirá sus puertas en septiembre 2026",
        "summary": "El Campus Tech contará con laboratorios de última generación, espacios de coworking y un hub de startups para estudiantes.",
        "content": (
            "La Universidad Politécnica anunció la inauguración de su nuevo Campus Tecnológico para septiembre de 2026. "
            "Con una inversión de $15 millones, el campus contará con 20 laboratorios de última generación equipados "
            "con impresoras 3D, equipos de realidad virtual, servidores de alto rendimiento y laboratorios de robótica. "
            "Además, se crearán 200 espacios de coworking para que estudiantes emprendedores trabajen en sus proyectos, "
            "y un Hub de Startups con mentorías de profesionales de la industria tecnológica. "
            "El campus también tendrá una cafetería con tecnología de pago sin contacto, áreas verdes con paneles solares "
            "y conectividad Wi-Fi 6 en todos sus espacios. "
            "Se espera que el nuevo campus beneficie a más de 5,000 estudiantes de las carreras de Ingeniería, "
            "Sistemas, Mecatrónica y Diseño Digital."
        ),
        "category": "Infraestructura",
        "university": "Universidad Politécnica",
        "author": "Rectorado",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1562774053-701939374585?w=800",
    },
    {
        "title": "Festival Cultural Universitario reunirá a 30 países en intercambio artístico",
        "summary": "El VII Festival Cultural Internacional se celebrará en octubre con música, danza, gastronomía y exposiciones de arte.",
        "content": (
            "La Universidad de las Artes anuncia la séptima edición de su Festival Cultural Internacional, "
            "que este año reunirá a representantes de 30 países en una semana de intercambio artístico y cultural. "
            "Del 12 al 19 de octubre, el campus se convertirá en un escenario multicultural con presentaciones "
            "de danza folclórica, conciertos de música internacional, ferias gastronómicas, "
            "exposiciones de arte contemporáneo y talleres creativos abiertos al público. "
            "La entrada es gratuita para toda la comunidad universitaria y el público en general. "
            "Este año se incorpora por primera vez una competencia de cortometrajes universitarios "
            "con un premio de $5,000 para el primer lugar. "
            "Las inscripciones para participar como expositor o tallerista están abiertas hasta el 15 de agosto "
            "en la Dirección de Bienestar Universitario."
        ),
        "category": "Cultura",
        "university": "Universidad de las Artes",
        "author": "Dirección de Bienestar",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=800",
    },
    {
        "title": "Egresados de Ingeniería Industrial ganan competencia internacional de innovación",
        "summary": "El equipo 'InnoTech' representó al país en Boston y obtuvo el primer lugar con su solución de logística sostenible.",
        "content": (
            "Un equipo de cinco egresados recientes de la Facultad de Ingeniería Industrial obtuvo el primer lugar "
            "en el MIT Innovation Challenge 2026, celebrado en Boston, Massachusetts. "
            "El equipo, denominado 'InnoTech', presentó una solución de logística sostenible que reduce "
            "las emisiones de carbono en cadenas de suministro hasta en un 35% mediante el uso de "
            "algoritmos de optimización de rutas y vehículos eléctricos autónomos. "
            "Compitieron contra 250 equipos de 40 países y superaron a finalistas de MIT, Stanford y Cambridge. "
            "El premio incluye $50,000 en capital semilla, mentoría de emprendedores de Silicon Valley "
            "y la posibilidad de incubar su startup en el MIT Media Lab. "
            "El rector expresó su orgullo: 'Este logro demuestra la calidad de nuestros graduados "
            "y su capacidad para competir al más alto nivel internacional'."
        ),
        "category": "Logros",
        "university": "Universidad Central",
        "author": "Dirección de Relaciones Internacionales",
        "is_featured": True,
        "image_url": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=800",
    },
    {
        "title": "Convenio con 15 empresas tecnológicas garantiza prácticas profesionales para estudiantes",
        "summary": "Los acuerdos firmados con empresas como IBM, Microsoft y startups locales aseguran 300 plazas de prácticas para el próximo semestre.",
        "content": (
            "La Facultad de Tecnología e Informática formalizó convenios de cooperación con 15 empresas "
            "del sector tecnológico que garantizan 300 plazas de prácticas profesionales remuneradas "
            "para el primer semestre 2027. "
            "Entre las empresas participantes destacan IBM, Microsoft, Oracle, y doce startups nacionales "
            "en crecimiento en sectores de fintech, healthtech y edtech. "
            "Las prácticas tendrán una duración de 6 meses con una remuneración mínima de $400 mensuales "
            "y la posibilidad de vinculación laboral al finalizar. "
            "La Decana Ing. Patricia Molina señaló que 'estos convenios son el resultado de años de trabajo "
            "construyendo puentes entre la academia y el sector productivo'. "
            "Los estudiantes interesados deben aplicar a través del Centro de Empleo Universitario "
            "a partir del 1 de septiembre. Se requiere tener aprobado el 60% de la carrera."
        ),
        "category": "Empleo",
        "university": "Universidad Politécnica",
        "author": "Ing. Patricia Molina",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800",
    },
    {
        "title": "Semana de Salud Mental: talleres gratuitos para reducir el estrés académico",
        "summary": "Del 20 al 24 de junio se realizarán actividades de mindfulness, yoga, charlas psicológicas y grupos de apoyo entre pares.",
        "content": (
            "El Departamento de Bienestar Estudiantil organiza la Primera Semana de Salud Mental Universitaria, "
            "un espacio dedicado al cuidado emocional y psicológico de la comunidad académica. "
            "Del 20 al 24 de junio se ofrecerán talleres gratuitos de mindfulness, sesiones de yoga matutino, "
            "charlas sobre manejo del estrés académico, grupos de apoyo entre pares y atención psicológica individual. "
            "Las actividades están dirigidas tanto a estudiantes como a docentes y personal administrativo. "
            "La Psic. Carmen Flores, directora del servicio de consejería, destacó que 'el 68% de los estudiantes "
            "reportan altos niveles de ansiedad durante los períodos de exámenes, y este programa busca "
            "dotarlos de herramientas concretas para gestionar esas situaciones'. "
            "La inscripción a los talleres es libre a través de la app universitaria. "
            "Adicionalmente, se habilitará una línea de apoyo emocional 24/7 disponible desde el 1 de julio."
        ),
        "category": "Bienestar",
        "university": "Universidad de las Artes",
        "author": "Psic. Carmen Flores",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1499728603263-13726abce5fd?w=800",
    },
    {
        "title": "Laboratorio de Idiomas estrena plataforma de aprendizaje con IA personalizada",
        "summary": "El nuevo sistema adapta los contenidos de inglés, francés y mandarín al ritmo de aprendizaje de cada estudiante usando inteligencia artificial.",
        "content": (
            "El Centro de Idiomas presentó su nueva plataforma de aprendizaje basada en inteligencia artificial "
            "que personaliza los contenidos educativos según el nivel y ritmo de cada estudiante. "
            "La plataforma, desarrollada en alianza con una empresa de EdTech canadiense, ofrece cursos de "
            "inglés, francés y mandarín con módulos adaptables que detectan las áreas de mayor dificultad "
            "y ajustan los ejercicios automáticamente. "
            "Incluye conversación con chatbots nativos, corrección de pronunciación en tiempo real mediante IA, "
            "y simulaciones de situaciones cotidianas y laborales. "
            "El acceso es gratuito para todos los estudiantes matriculados y el costo para el público externo "
            "es de $30 mensuales. "
            "En la fase piloto, los estudiantes que usaron la plataforma mejoraron su nivel en promedio "
            "un 45% más rápido que con los métodos tradicionales. "
            "La plataforma está disponible en web y aplicación móvil desde el 1 de julio."
        ),
        "category": "Tecnología",
        "university": "Universidad Central",
        "author": "Centro de Idiomas",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800",
    },
]


def load_sample_data():
    """Crea las tablas e inserta los datos de demo."""
    # Crear tablas
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(models.News).count()
        if existing > 0:
            print(f"[OK] Ya existen {existing} noticias en la base de datos. Omitiendo carga de datos de demo.")
            return

        for news_data in SAMPLE_NEWS:
            news = models.News(**news_data)
            db.add(news)

        db.commit()
        print(f"[OK] Se cargaron {len(SAMPLE_NEWS)} noticias de demo correctamente.")

        # Indexar en RAG si hay API key
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "tu_api_key_aqui":
            try:
                from rag.engine import RAGEngine
                rag = RAGEngine()
                news_list = db.query(models.News).all()
                for news in news_list:
                    rag.add_news(
                        news_id=news.id,
                        title=news.title,
                        content=news.content,
                        category=news.category,
                        university=news.university,
                        summary=news.summary,
                    )
                    print(f"   [RAG] Indexada: {news.title[:60]}")
                print(f"[OK] {len(news_list)} noticias indexadas en ChromaDB para RAG.")
            except Exception as e:
                print(f"[WARN] No se pudo indexar en RAG: {e}")
                print("   Ejecuta el servidor y las noticias se indexaran al crearlas.")
        else:
            print("[WARN] GEMINI_API_KEY no configurada. Configura tu .env para habilitar el RAG.")

    finally:
        db.close()


if __name__ == "__main__":
    load_sample_data()
