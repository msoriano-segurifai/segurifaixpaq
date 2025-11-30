"""
Data migration to populate initial educational modules, quiz questions, and achievements.
"""
from django.db import migrations


def crear_modulos_educativos(apps, schema_editor):
    EducationalModule = apps.get_model('gamification', 'EducationalModule')
    QuizQuestion = apps.get_model('gamification', 'QuizQuestion')
    Achievement = apps.get_model('gamification', 'Achievement')

    # =====================================================
    # MODULO 1: Seguridad Vial
    # =====================================================
    modulo1 = EducationalModule.objects.create(
        titulo='Seguridad Vial: Conduccion Responsable',
        descripcion='Aprende las mejores practicas para conducir de manera segura y prevenir accidentes en las carreteras de Guatemala.',
        categoria='SEGURIDAD_VIAL',
        dificultad='PRINCIPIANTE',
        contenido='''# Seguridad Vial: Conduccion Responsable

## Introduccion
La seguridad vial es responsabilidad de todos. En Guatemala, los accidentes de transito son una de las principales causas de lesiones y muertes evitables.

## Reglas Basicas de Seguridad

### 1. Uso del Cinturon de Seguridad
- El cinturon reduce el riesgo de muerte en un 45%
- Todos los ocupantes deben usarlo, no solo el conductor
- Los ninos menores de 12 anos deben ir en el asiento trasero

### 2. Respeto a los Limites de Velocidad
- En zonas urbanas: 60 km/h maximo
- En carreteras: 100 km/h maximo
- Cerca de escuelas y hospitales: 30 km/h

### 3. No Conducir Bajo Efectos del Alcohol
- El limite legal en Guatemala es 0.08% de alcohol en sangre
- Si bebes, no manejes
- Designa un conductor responsable

### 4. Evitar Distracciones
- No uses el celular mientras conduces
- Configura el GPS antes de iniciar el viaje
- Evita comer mientras manejas

## Que Hacer en Caso de Accidente

1. Manten la calma
2. Asegura el area con triangulos de seguridad
3. Verifica si hay heridos
4. Llama a emergencias (1510 Bomberos, 110 PMT)
5. No muevas a los heridos a menos que sea necesario
6. Documenta con fotos si es posible

## Conclusion
La prevencion es la mejor herramienta. Siguiendo estas recomendaciones, contribuyes a hacer las carreteras de Guatemala mas seguras para todos.
''',
        duracion_minutos=15,
        puntos_completar=100,
        puntos_quiz_perfecto=50,
        orden=1,
        activo=True
    )

    # Preguntas del Quiz 1
    QuizQuestion.objects.create(
        modulo=modulo1,
        pregunta='Cual es el limite de velocidad maximo en zonas urbanas de Guatemala?',
        opcion_a='40 km/h',
        opcion_b='60 km/h',
        opcion_c='80 km/h',
        opcion_d='100 km/h',
        respuesta_correcta='B',
        explicacion='El limite de velocidad en zonas urbanas de Guatemala es de 60 km/h segun el Reglamento de Transito.',
        orden=1
    )

    QuizQuestion.objects.create(
        modulo=modulo1,
        pregunta='En que porcentaje reduce el cinturon de seguridad el riesgo de muerte en un accidente?',
        opcion_a='25%',
        opcion_b='35%',
        opcion_c='45%',
        opcion_d='55%',
        respuesta_correcta='C',
        explicacion='Estudios demuestran que el uso correcto del cinturon de seguridad reduce el riesgo de muerte en aproximadamente un 45%.',
        orden=2
    )

    QuizQuestion.objects.create(
        modulo=modulo1,
        pregunta='Cual es el numero de emergencia de los Bomberos en Guatemala?',
        opcion_a='110',
        opcion_b='120',
        opcion_c='1510',
        opcion_d='911',
        respuesta_correcta='C',
        explicacion='El numero de los Bomberos Voluntarios en Guatemala es 1510. El 110 es de la PMT.',
        orden=3
    )

    # =====================================================
    # MODULO 2: Primeros Auxilios Basicos
    # =====================================================
    modulo2 = EducationalModule.objects.create(
        titulo='Primeros Auxilios: Actuacion en Emergencias',
        descripcion='Conoce las tecnicas basicas de primeros auxilios para poder ayudar en situaciones de emergencia mientras llega la ayuda profesional.',
        categoria='PRIMEROS_AUXILIOS',
        dificultad='INTERMEDIO',
        contenido='''# Primeros Auxilios: Actuacion en Emergencias

## Principios Basicos: PAS
Antes de actuar, recuerda siempre: **Proteger, Avisar, Socorrer**

### Proteger
- Asegura el area para evitar mas victimas
- Usa guantes si los tienes disponibles
- No te pongas en peligro

### Avisar
- Llama a emergencias inmediatamente
- Bomberos: 1510
- Cruz Roja: 2381-6565
- Proporciona ubicacion exacta y descripcion

### Socorrer
- Actua solo si tienes conocimientos basicos
- No muevas a la victima innecesariamente
- Mantente calmado

## Tecnicas Esenciales

### 1. RCP (Reanimacion Cardiopulmonar)
**Solo si la persona no responde y no respira:**
1. Coloca a la persona boca arriba en superficie dura
2. Pon el talon de tu mano en el centro del pecho
3. Entrelaza los dedos de ambas manos
4. Comprime el pecho 5-6 cm, 100-120 compresiones por minuto
5. Si sabes, alterna 30 compresiones con 2 respiraciones

### 2. Posicion Lateral de Seguridad
**Para personas inconscientes que SI respiran:**
1. Arrodillate junto a la victima
2. Extiende el brazo mas cercano a ti hacia arriba
3. Cruza el otro brazo sobre el pecho
4. Flexiona la rodilla lejana
5. Gira suavemente hacia ti
6. Ajusta la cabeza para mantener via aerea abierta

### 3. Control de Hemorragias
1. Aplica presion directa con un pano limpio
2. Eleva la extremidad si es posible
3. No retires el pano aunque se empape, agrega mas encima
4. Mantiene la presion hasta que llegue ayuda

### 4. Quemaduras
- Enfria con agua corriente por 10-20 minutos
- No apliques hielo, mantequilla o pasta de dientes
- Cubre con un pano limpio y seco
- No revientes ampollas

## Que NO Hacer
- No dar de beber a personas inconscientes
- No mover a victimas de accidentes de transito
- No aplicar torniquetes (salvo formacion especifica)
- No succionar veneno de mordeduras

## Conclusion
Los primeros minutos son criticos. Tu actuacion puede salvar vidas mientras esperas ayuda profesional.
''',
        duracion_minutos=20,
        puntos_completar=150,
        puntos_quiz_perfecto=75,
        orden=2,
        activo=True
    )

    # Preguntas del Quiz 2
    QuizQuestion.objects.create(
        modulo=modulo2,
        pregunta='Cual es el orden correcto de actuacion en primeros auxilios?',
        opcion_a='Socorrer, Proteger, Avisar',
        opcion_b='Avisar, Proteger, Socorrer',
        opcion_c='Proteger, Avisar, Socorrer',
        opcion_d='Proteger, Socorrer, Avisar',
        respuesta_correcta='C',
        explicacion='El protocolo PAS indica: Primero Proteger el area, luego Avisar a emergencias, y finalmente Socorrer a la victima.',
        orden=1
    )

    QuizQuestion.objects.create(
        modulo=modulo2,
        pregunta='Cuantas compresiones por minuto se deben realizar en RCP?',
        opcion_a='60-80',
        opcion_b='80-100',
        opcion_c='100-120',
        opcion_d='120-140',
        respuesta_correcta='C',
        explicacion='Las guias internacionales de RCP recomiendan realizar entre 100 y 120 compresiones por minuto.',
        orden=2
    )

    QuizQuestion.objects.create(
        modulo=modulo2,
        pregunta='Que se debe aplicar a una quemadura leve?',
        opcion_a='Hielo directamente',
        opcion_b='Mantequilla',
        opcion_c='Agua corriente por 10-20 minutos',
        opcion_d='Pasta de dientes',
        respuesta_correcta='C',
        explicacion='El tratamiento correcto es enfriar la quemadura con agua corriente (no helada) durante 10-20 minutos.',
        orden=3
    )

    # =====================================================
    # MODULO 3: Finanzas y Seguros
    # =====================================================
    modulo3 = EducationalModule.objects.create(
        titulo='Finanzas Personales: Protege tu Patrimonio',
        descripcion='Aprende sobre la importancia de los seguros y como proteger tu patrimonio y el de tu familia ante imprevistos.',
        categoria='FINANZAS_PERSONALES',
        dificultad='PRINCIPIANTE',
        contenido='''# Finanzas Personales: Protege tu Patrimonio

## Por Que Son Importantes los Seguros?

Los seguros son una herramienta financiera que te protege ante imprevistos. En lugar de enfrentar gastos enormes de tu bolsillo, pagas una prima mensual o anual que te da tranquilidad.

## Tipos de Seguros que Debes Considerar

### 1. Seguro de Vehiculo
**Coberturas principales:**
- Danos a terceros (obligatorio)
- Robo total
- Danos parciales
- Asistencia vial 24/7

**Consejos:**
- Compara al menos 3 aseguradoras
- Revisa el deducible (lo que pagas tu primero)
- Verifica las exclusiones en la poliza

### 2. Seguro de Gastos Medicos
**Por que es importante:**
- Una hospitalizacion puede costar Q50,000+
- Cirugia de emergencia: Q100,000+
- Tratamiento de enfermedades cronicas: costos continuos

**Que buscar:**
- Red de hospitales y clinicas
- Cobertura de medicamentos
- Periodo de espera para preexistencias

### 3. Seguro de Vida
**Para quien es importante:**
- Si tienes dependientes economicos
- Si tienes deudas (hipoteca, prestamos)
- Para garantizar educacion de hijos

### 4. Seguro de Tarjetas (Proteccion Financiera)
**Coberturas:**
- Fraude y clonacion
- Compras protegidas
- Robo de efectivo en cajeros

## Como Usar PAQ Wallet para Pagar tus Seguros

1. **Vincula tu cuenta** PAQ Wallet a la app SegurifAI
2. **Selecciona el servicio** que deseas pagar
3. **Recibe un codigo PAYPAQ** via SMS
4. **Confirma el pago** ingresando el codigo
5. **Listo!** Tu pago queda registrado instantaneamente

### Ventajas de PAQ Wallet:
- Sin necesidad de tarjeta de credito
- Pagos inmediatos
- Historial de transacciones
- Disponible 24/7

## Consejos para Ahorrar en Seguros

1. **Paga anual** en lugar de mensual (descuentos del 5-15%)
2. **Combina polizas** con la misma aseguradora
3. **Manten buen historial** de manejo para seguro vehicular
4. **Revisa anualmente** tus coberturas

## Plan de Accion

1. Haz un inventario de tus bienes
2. Identifica tus riesgos principales
3. Compara opciones de seguros
4. Contrata lo esencial primero
5. Revisa y actualiza cada ano

## Conclusion
Proteger tu patrimonio no es un gasto, es una inversion en tranquilidad para ti y tu familia.
''',
        duracion_minutos=15,
        puntos_completar=100,
        puntos_quiz_perfecto=50,
        orden=3,
        activo=True
    )

    # Preguntas del Quiz 3
    QuizQuestion.objects.create(
        modulo=modulo3,
        pregunta='Cual es una ventaja de pagar el seguro anualmente en lugar de mensualmente?',
        opcion_a='Es mas facil de recordar',
        opcion_b='Descuentos del 5-15%',
        opcion_c='No hay ninguna ventaja',
        opcion_d='El seguro dura mas tiempo',
        respuesta_correcta='B',
        explicacion='Las aseguradoras ofrecen descuentos del 5-15% cuando pagas la prima anual en lugar de fraccionarla mensualmente.',
        orden=1
    )

    QuizQuestion.objects.create(
        modulo=modulo3,
        pregunta='Que es el deducible en un seguro?',
        opcion_a='El costo mensual del seguro',
        opcion_b='Lo que paga la aseguradora',
        opcion_c='Lo que pagas tu antes de que el seguro cubra',
        opcion_d='El descuento por buen historial',
        respuesta_correcta='C',
        explicacion='El deducible es la cantidad que debes pagar de tu bolsillo antes de que la aseguradora cubra el resto del siniestro.',
        orden=2
    )

    QuizQuestion.objects.create(
        modulo=modulo3,
        pregunta='Que tipo de seguro es obligatorio para vehiculos en Guatemala?',
        opcion_a='Seguro de robo',
        opcion_b='Seguro de danos a terceros',
        opcion_c='Seguro de danos propios',
        opcion_d='Seguro de asistencia vial',
        respuesta_correcta='B',
        explicacion='En Guatemala, el seguro de responsabilidad civil (danos a terceros) es el unico obligatorio por ley para vehiculos.',
        orden=3
    )

    # =====================================================
    # LOGROS
    # =====================================================
    Achievement.objects.create(
        nombre='Primer Paso',
        descripcion='Completaste tu primer modulo educativo. Buen comienzo!',
        icono='rocket',
        puntos_bonus=25,
        condicion='modulos_completados >= 1',
        activo=True
    )

    Achievement.objects.create(
        nombre='Estudiante Dedicado',
        descripcion='Completaste los 3 modulos basicos. Eres todo un experto!',
        icono='graduation-cap',
        puntos_bonus=100,
        condicion='modulos_completados >= 3',
        activo=True
    )

    Achievement.objects.create(
        nombre='Acumulador',
        descripcion='Alcanzaste 250 puntos. Sigue asi!',
        icono='coins',
        puntos_bonus=50,
        condicion='puntos_totales >= 250',
        activo=True
    )

    Achievement.objects.create(
        nombre='Racha de 7 Dias',
        descripcion='Mantuviste actividad por 7 dias consecutivos.',
        icono='fire',
        puntos_bonus=75,
        condicion='racha_dias >= 7',
        activo=True
    )

    Achievement.objects.create(
        nombre='Maestro del Conocimiento',
        descripcion='Alcanzaste 500 puntos. Eres un verdadero maestro!',
        icono='crown',
        puntos_bonus=100,
        condicion='puntos_totales >= 500',
        activo=True
    )


def eliminar_datos(apps, schema_editor):
    EducationalModule = apps.get_model('gamification', 'EducationalModule')
    Achievement = apps.get_model('gamification', 'Achievement')
    EducationalModule.objects.all().delete()
    Achievement.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gamification', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_modulos_educativos, eliminar_datos),
    ]
