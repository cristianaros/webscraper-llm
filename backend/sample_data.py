"""
Datos de demo para precargar el sistema con noticias universitarias de ejemplo.
Ejecutar: python sample_data.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import models
from database import SessionLocal, engine
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
    # ── BECAS ─────────────────────────────────────────────────────────────────
    {
        "title": "Convocatoria abierta: becas de intercambio universitario con Europa 2026–2027",
        "summary": "Más de 80 plazas disponibles en universidades de España, Alemania e Italia para el próximo año académico.",
        "content": (
            "La Dirección de Relaciones Internacionales abre la convocatoria para el Programa de Intercambio "
            "Universitario Europa 2026–2027, con 80 plazas distribuidas en 14 universidades socias de España, "
            "Alemania e Italia. Las becas cubren matrícula completa, alojamiento en residencia universitaria "
            "y un subsidio mensual de €600 para gastos de manutención. "
            "Los postulantes deben tener un promedio mínimo de 8.5, nivel B2 en el idioma del país destino "
            "y haber completado al menos el 50% de su carrera. "
            "El proceso de selección incluye revisión de expediente, carta de motivación y entrevista personal. "
            "Las postulaciones se reciben del 1 al 30 de julio exclusivamente a través del portal de movilidad "
            "internacional. Los seleccionados serán notificados el 20 de agosto. "
            "Para más información asiste a la charla informativa el próximo miércoles 25 de junio a las 10:00 "
            "en el Auditorio Principal."
        ),
        "category": "Becas",
        "university": "Universidad Central",
        "author": "Dirección de Relaciones Internacionales",
        "is_featured": True,
        "image_url": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800",
    },
    {
        "title": "Becas de excelencia académica LATAM: hasta $8,000 por año para posgrados",
        "summary": "El Fondo Iberoamericano de Educación Superior abre 200 becas para maestrías y doctorados en toda Latinoamérica.",
        "content": (
            "El Fondo Iberoamericano de Educación Superior (FIES) lanzó su convocatoria anual de Becas de "
            "Excelencia Académica LATAM, destinadas a financiar estudios de posgrado en universidades acreditadas "
            "de América Latina. Se ofrecen 200 becas con un valor de hasta $8,000 anuales, renovables por la "
            "duración del programa. "
            "Las becas están dirigidas a profesionales menores de 35 años con título universitario, promedio "
            "mínimo de 8.0 y proyecto de investigación o propuesta académica aprobada por un tutor institucional. "
            "Las áreas prioritarias son Ciencias de la Salud, Ingeniería, Ciencias Sociales y Educación. "
            "La convocatoria cierra el 15 de agosto. Los formularios de aplicación y la lista de universidades "
            "participantes están disponibles en el sitio web del FIES. "
            "La universidad cuenta con una Oficina de Posgrado e Investigación que ofrece asesoría gratuita "
            "para la elaboración del expediente de postulación."
        ),
        "category": "Becas",
        "university": "Universidad Politécnica",
        "author": "Oficina de Posgrado e Investigación",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800",
    },
    {
        "title": "Nueva beca deportiva para atletas de alto rendimiento: matrícula y entrenamiento pagados",
        "summary": "La universidad cubrirá matrícula completa y acceso al centro deportivo a 30 atletas clasificados a competencias nacionales.",
        "content": (
            "El Departamento de Deportes y la Vicerrectoría Académica firmaron un acuerdo para crear la Beca "
            "Deportiva de Alto Rendimiento, destinada a estudiantes que representen a la universidad en "
            "competencias de nivel nacional o internacional. "
            "Los 30 beneficiarios recibirán matrícula completa, acceso ilimitado al Centro Deportivo, "
            "plan nutricional personalizado y flexibilidad académica para adaptarse a los calendarios de "
            "entrenamiento y competencia. "
            "Podrán postular atletas activos en fútbol, atletismo, natación, baloncesto, tenis y deportes electrónicos. "
            "Los requisitos son: estar compitiendo a nivel nacional, mantener un promedio académico mínimo de 7.0 "
            "y presentar aval del entrenador correspondiente. "
            "Las inscripciones están abiertas en el Departamento de Deportes hasta el 10 de julio."
        ),
        "category": "Becas",
        "university": "Universidad de las Artes",
        "author": "Departamento de Deportes",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800",
    },
    # ── BENEFICIOS ────────────────────────────────────────────────────────────
    {
        "title": "Comedor universitario amplía horarios y renueva su menú con opciones saludables y vegetarianas",
        "summary": "Desde julio el comedor central abrirá de 7:00 a 22:00 y ofrecerá opciones veganas, sin gluten y menú internacional.",
        "content": (
            "La Dirección de Bienestar Universitario anunció la renovación completa del comedor central, "
            "que a partir del 1 de julio ampliará su horario de atención de 7:00 a 22:00, incorporará "
            "opciones veganas y vegetarianas, platos sin gluten y una sección de cocina internacional "
            "con rotación semanal entre gastronomía latinoamericana, asiática y mediterránea. "
            "El precio del menú estudiantil se mantendrá en $2.50 para el almuerzo completo y $1.80 para "
            "el desayuno. Los estudiantes con beca socioeconómica tendrán acceso gratuito a todos los servicios. "
            "El comedor también incorporará un sistema de pedido anticipado por la app universitaria para "
            "reducir tiempos de espera en horas pico. "
            "La remodelación incluyó nueva maquinaria de cocina industrial, sistema de ventilación mejorado "
            "y 80 asientos adicionales con zonas de estudio equipadas con tomas de corriente y Wi-Fi."
        ),
        "category": "Beneficios",
        "university": "Universidad Central",
        "author": "Dirección de Bienestar Universitario",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1567521464027-f127ff144326?w=800",
    },
    {
        "title": "Transporte universitario gratuito: 5 nuevas rutas desde zonas periféricas de la ciudad",
        "summary": "El servicio de buses universitarios se expande con 5 nuevas rutas que conectan barrios alejados con el campus principal.",
        "content": (
            "La Universidad Central habilitará 5 nuevas rutas de transporte gratuito a partir del próximo "
            "semestre, conectando los barrios periféricos del norte, sur y oriente de la ciudad con el campus "
            "principal. Las rutas operarán de lunes a viernes en horarios de 6:30–8:30 y 17:00–20:00 "
            "para cubrir los turnos matutino y vespertino. "
            "La medida beneficiará a aproximadamente 2,400 estudiantes que actualmente gastan entre $60 y $90 "
            "mensuales en transporte público. El servicio utilizará una flota de 12 buses modernos con Wi-Fi, "
            "aire acondicionado y sistema de seguimiento GPS en tiempo real accesible desde la app universitaria. "
            "La Vicerrectora de Bienestar, Msc. Laura Herrera, señaló que 'el transporte es una barrera real "
            "para muchos estudiantes y esta expansión es parte de nuestra política de equidad educativa'. "
            "Los estudiantes deberán registrar su carné universitario para acceder al servicio."
        ),
        "category": "Beneficios",
        "university": "Universidad Central",
        "author": "Vicerrectoría de Bienestar",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?w=800",
    },
    {
        "title": "Seguro médico universitario gratuito se extiende a familiares directos de estudiantes",
        "summary": "El convenio con MedSalud amplía la cobertura del seguro estudiantil para incluir padres y hermanos menores como beneficiarios.",
        "content": (
            "La universidad firmó una ampliación del convenio con la aseguradora MedSalud para extender "
            "la cobertura del seguro médico estudiantil gratuito a los familiares directos (padres y hermanos "
            "menores de 18 años) de los estudiantes matriculados. "
            "El seguro incluye consultas médicas generales y especializadas, hospitalización, medicamentos, "
            "exámenes de laboratorio y emergencias. La cobertura máxima anual es de $15,000 por familia. "
            "Para activar los beneficios familiares, los estudiantes deben presentar documentos de parentesco "
            "en la Oficina de Bienestar antes del 31 de julio. "
            "Actualmente más de 8,000 estudiantes utilizan el seguro individual, y se espera que la extensión "
            "familiar beneficie a más de 12,000 personas adicionales. "
            "La medida forma parte del plan estratégico institucional 2025–2030 que prioriza el bienestar "
            "integral de la comunidad universitaria."
        ),
        "category": "Beneficios",
        "university": "Universidad Politécnica",
        "author": "Oficina de Bienestar Estudiantil",
        "is_featured": True,
        "image_url": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800",
    },
    # ── INCIDENTES ────────────────────────────────────────────────────────────
    {
        "title": "Corte de energía afecta actividades académicas en tres facultades durante el martes",
        "summary": "Una falla en la subestación eléctrica suspendió clases y laboratorios por más de 4 horas en las facultades de Ingeniería, Ciencias y Medicina.",
        "content": (
            "Un corte de energía eléctrica originado en una falla técnica de la subestación norte del campus "
            "afectó durante más de cuatro horas las actividades académicas en las facultades de Ingeniería, "
            "Ciencias Naturales y Medicina. El incidente ocurrió el martes 10 de junio a las 9:15 y fue "
            "restablecido a las 13:45 por el equipo de mantenimiento en coordinación con la empresa eléctrica. "
            "Se suspendieron 47 clases presenciales y 3 prácticas de laboratorio que serán reprogramadas "
            "en los próximos días. Los estudiantes con exámenes programados durante ese período serán evaluados "
            "en fechas alternativas que se comunicarán por correo institucional. "
            "El Director de Infraestructura, Ing. Roberto Salgado, informó que 'se identificó el equipo "
            "defectuoso y se realizará el reemplazo completo de la subestación durante las vacaciones de "
            "julio para evitar que el problema se repita'. "
            "La universidad se disculpó con la comunidad académica por los inconvenientes generados."
        ),
        "category": "Incidentes",
        "university": "Universidad Central",
        "author": "Dirección de Infraestructura",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
    },
    {
        "title": "Estudiantes marchan en rechazo al alza de aranceles y exigen congelamiento de tarifas",
        "summary": "Más de 1,500 estudiantes se movilizaron pacíficamente el viernes para protestar contra el incremento del 12% en las matrículas para 2027.",
        "content": (
            "Aproximadamente 1,500 estudiantes de distintas facultades se movilizaron pacíficamente el viernes "
            "por las principales avenidas del campus en rechazo al incremento del 12% en los aranceles "
            "universitarios anunciado para el ciclo académico 2027. "
            "Los manifestantes, convocados por la Federación de Estudiantes Universitarios (FEU), exigieron "
            "la suspensión del alza, mayor transparencia en el uso del presupuesto institucional y la creación "
            "de un fondo de emergencia para estudiantes en situación crítica. "
            "La marcha transcurrió sin incidentes. Una comisión de 10 representantes estudiantiles fue recibida "
            "por el rectorado al finalizar la manifestación. "
            "El rector Dr. Marcos Villareal se comprometió a convocar una mesa de diálogo con representantes "
            "estudiantiles, docentes y autoridades antes del 30 de junio para revisar la propuesta arancelaria. "
            "La FEU anunció que suspende movilizaciones mientras dure el proceso de negociación."
        ),
        "category": "Incidentes",
        "university": "Universidad Politécnica",
        "author": "Federación de Estudiantes Universitarios",
        "is_featured": True,
        "image_url": "https://images.unsplash.com/photo-1591189863430-ab87e120f312?w=800",
    },
    {
        "title": "Incendio en laboratorio de química es controlado sin víctimas; investigan causas",
        "summary": "Un conato de incendio en el Laboratorio 3B fue sofocado en 20 minutos. No hubo heridos pero se reportan daños en equipos por $30,000.",
        "content": (
            "Un conato de incendio ocurrido en el Laboratorio de Química Orgánica 3B del edificio de Ciencias "
            "fue controlado en aproximadamente 20 minutos gracias a la rápida respuesta del personal de "
            "seguridad y los extintores automáticos instalados en el área. "
            "El incidente se produjo el lunes a las 15:30 cuando un cortocircuito en un equipo de calentamiento "
            "generó llamas que se extendieron a materiales almacenados en la zona. Los 12 estudiantes y 2 "
            "docentes presentes evacuaron sin lesiones siguiendo el protocolo de emergencias. "
            "Los daños materiales se estiman en $30,000 entre equipos de laboratorio y reactivos destruidos. "
            "El laboratorio permanecerá cerrado por al menos dos semanas mientras se realizan reparaciones "
            "y una inspección técnica de seguridad. Las prácticas afectadas serán reubicadas en el "
            "Laboratorio 5A que cuenta con capacidad disponible. "
            "La Dirección de Seguridad Institucional abrió una investigación para determinar las causas exactas."
        ),
        "category": "Incidentes",
        "university": "Universidad de las Artes",
        "author": "Dirección de Seguridad Institucional",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=800",
    },
    # ── NOVEDADES ─────────────────────────────────────────────────────────────
    {
        "title": "La biblioteca universitaria estrena catálogo digital con acceso a 500,000 recursos académicos",
        "summary": "El nuevo sistema integra bases de datos de JSTOR, Scopus y SciELO, y permite descargar artículos sin costo desde cualquier dispositivo.",
        "content": (
            "La Biblioteca Central inauguró su nuevo Sistema de Gestión de Recursos Académicos (SGRA), "
            "que integra las bases de datos de JSTOR, Scopus, SciELO y Web of Science, brindando acceso "
            "a más de 500,000 artículos científicos, libros digitales, tesis y revistas especializadas. "
            "Los estudiantes y docentes pueden acceder desde cualquier dispositivo con su cuenta institucional, "
            "descargar documentos en PDF sin costo y crear colecciones personales de referencias bibliográficas. "
            "El sistema incluye una herramienta de búsqueda semántica potenciada por inteligencia artificial "
            "que sugiere recursos relacionados y detecta artículos altamente citados en cada área temática. "
            "La directora de la biblioteca, Lcda. Isabel Vargas, indicó que 'esto elimina una de las mayores "
            "barreras del proceso investigativo: el acceso a fuentes de calidad'. "
            "Adicionalmente, se habilitaron 40 nuevas cabinas de estudio individual con reserva online "
            "y equipos de cómputo de última generación."
        ),
        "category": "Novedades",
        "university": "Universidad Central",
        "author": "Biblioteca Central",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=800",
    },
    {
        "title": "Inauguran centro deportivo con piscina olímpica, gimnasio y canchas techadas",
        "summary": "El nuevo complejo deportivo de $8 millones abre sus puertas a toda la comunidad universitaria con acceso gratuito para estudiantes.",
        "content": (
            "La universidad inauguró el Centro Deportivo Integral, un complejo de 4,500 m² construido con "
            "una inversión de $8 millones y financiado en parte por un proyecto de cooperación con el "
            "Ministerio del Deporte. Las instalaciones incluyen una piscina semiolímpica de 25 metros, "
            "gimnasio equipado con máquinas de cardio y pesas, dos canchas de baloncesto techadas, "
            "una cancha de fútbol sala, pista de atletismo de 200 metros y sala de artes marciales. "
            "El acceso es completamente gratuito para estudiantes, docentes y personal administrativo "
            "con carné institucional vigente. Las instalaciones también se alquilarán a equipos externos "
            "fuera del horario académico para autofinanciamiento del mantenimiento. "
            "Se ofrecerán clases grupales gratuitas de natación, spinning, yoga y crossfit en horarios "
            "matutino, vespertino y nocturno. Las inscripciones a las clases abren el próximo lunes "
            "a través de la app universitaria con cupos limitados de 20 personas por sesión."
        ),
        "category": "Novedades",
        "university": "Universidad Politécnica",
        "author": "Rectorado",
        "is_featured": True,
        "image_url": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800",
    },
    {
        "title": "Se abre la nueva Facultad de Ciencias del Clima y Energías Renovables para 2027",
        "summary": "La nueva facultad ofrecerá cuatro carreras de pregrado enfocadas en sostenibilidad ambiental, energía solar y cambio climático.",
        "content": (
            "La universidad anunció la creación de la Facultad de Ciencias del Clima y Energías Renovables, "
            "que comenzará operaciones en febrero de 2027 con cuatro programas de pregrado: Ingeniería en "
            "Energías Renovables, Gestión Ambiental y Cambio Climático, Ingeniería Solar y Eólica, "
            "y Desarrollo Sostenible y Políticas Ambientales. "
            "La iniciativa responde a la creciente demanda de profesionales especializados en el sector "
            "verde y fue aprobada por el Consejo de Educación Superior tras tres años de planificación. "
            "La facultad contará con laboratorios de paneles solares, estaciones meteorológicas, "
            "simuladores de turbinas eólicas y un centro de investigación climática en alianza con "
            "el Instituto Nacional de Meteorología. "
            "Las inscripciones para la primera promoción abrirán en octubre de 2026. Se habilitarán "
            "120 cupos por carrera con un 20% reservado para becas completas destinadas a estudiantes "
            "de comunidades rurales directamente afectadas por el cambio climático."
        ),
        "category": "Novedades",
        "university": "Universidad Central",
        "author": "Consejo Académico Institucional",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=800",
    },
    # ── DEPORTES ──────────────────────────────────────────────────────────────
    {
        "title": "Selección universitaria de fútbol conquista el campeonato nacional interuniversitario",
        "summary": "El equipo venció 2-1 a la Universidad del Norte en la final disputada en el Estadio Olímpico ante 8,000 espectadores.",
        "content": (
            "La selección universitaria de fútbol se coronó campeona nacional al vencer por 2-1 a la "
            "Universidad del Norte en una final disputada en el Estadio Olímpico ante más de 8,000 espectadores. "
            "Los goles del equipo fueron marcados por Carlos Menéndez en el minuto 34 y el capitán Diego "
            "Fuentes de penalti en el minuto 78, tras el empate provisional del rival al 61'. "
            "El portero Andrés Rojas fue elegido el Mejor Jugador del Torneo tras una destacada actuación "
            "a lo largo de las 12 jornadas de la competencia. "
            "Es el tercer título nacional consecutivo del equipo, que se consolida como la institución "
            "más ganadora de la última década en el torneo interuniversitario. "
            "El cuerpo técnico, liderado por el entrenador Miguel Ángel Soto, agradeció el apoyo de la "
            "comunidad universitaria: 'Este título es de todos, de los estudiantes, los docentes y "
            "las autoridades que creen en el deporte como parte de la formación integral'."
        ),
        "category": "Deportes",
        "university": "Universidad Politécnica",
        "author": "Departamento de Deportes",
        "is_featured": True,
        "image_url": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=800",
    },
    # ── CONVOCATORIAS ─────────────────────────────────────────────────────────
    {
        "title": "Elecciones del Consejo Estudiantil 2026: fechas, candidatos y cómo votar",
        "summary": "Las elecciones para renovar el Consejo Estudiantil se realizarán el 5 de julio. Se inscribieron 8 listas con propuestas para mejorar la vida universitaria.",
        "content": (
            "La Comisión Electoral Universitaria convoca a toda la comunidad estudiantil a participar "
            "en las Elecciones del Consejo Estudiantil 2026, que se realizarán el viernes 5 de julio "
            "de 8:00 a 17:00 en los locales de votación habilitados en cada facultad. "
            "Para este proceso se inscribieron 8 listas con un total de 64 candidatos que presentan "
            "propuestas en áreas como bienestar estudiantil, mejoras en infraestructura, sostenibilidad, "
            "inclusión, salud mental y vinculación con el sector productivo. "
            "El voto es voluntario y se realiza con el carné universitario vigente. Por primera vez "
            "se habilitará un sistema de voto electrónico desde la app universitaria para facilitar "
            "la participación de estudiantes en modalidad a distancia. "
            "Los resultados se publicarán el mismo día a partir de las 19:00 en el portal institucional. "
            "La Comisión invita a conocer las propuestas de los candidatos en el foro virtual disponible "
            "en el sitio web de la universidad."
        ),
        "category": "Convocatorias",
        "university": "Universidad de las Artes",
        "author": "Comisión Electoral Universitaria",
        "is_featured": False,
        "image_url": "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?w=800",
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
        existing_titles = {row[0] for row in db.query(models.News.title).all()}
        new_entries = [n for n in SAMPLE_NEWS if n["title"] not in existing_titles]

        if not new_entries:
            print(
                f"[OK] Todas las noticias de demo ya están cargadas ({len(existing_titles)} en total). Nada que agregar."
            )
            return

        for news_data in new_entries:
            db.add(models.News(**news_data))

        db.commit()
        print(
            f"[OK] Se agregaron {len(new_entries)} noticias nuevas (total en BD: {len(existing_titles) + len(new_entries)})."
        )

        # Re-query para indexar sólo las recién insertadas
        new_titles = {n["title"] for n in new_entries}

        # Indexar en RAG si hay API key
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "tu_api_key_aqui":
            try:
                from rag.engine import RAGEngine

                rag = RAGEngine()
                to_index = (
                    db.query(models.News)
                    .filter(models.News.title.in_(new_titles))
                    .all()
                )
                for news in to_index:
                    rag.add_news(
                        news_id=news.id,
                        title=news.title,
                        content=news.content,
                        category=news.category,
                        university=news.university,
                        summary=news.summary,
                    )
                    print(f"   [RAG] Indexada: {news.title[:60]}")
                print(
                    f"[OK] {len(to_index)} noticias nuevas indexadas en ChromaDB para RAG."
                )
            except Exception as e:
                print(f"[WARN] No se pudo indexar en RAG: {e}")
                print("   Ejecuta el servidor y las noticias se indexaran al crearlas.")
        else:
            print(
                "[WARN] GEMINI_API_KEY no configurada. Configura tu .env para habilitar el RAG."
            )

    finally:
        db.close()


if __name__ == "__main__":
    load_sample_data()
