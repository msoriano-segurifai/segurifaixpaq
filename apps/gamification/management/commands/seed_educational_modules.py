"""
Management command to seed educational modules with quiz questions
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.gamification.models import EducationalModule, QuizQuestion


class Command(BaseCommand):
    help = 'Seed educational modules with quiz questions for testing'

    def handle(self, *args, **options):
        self.stdout.write('Seeding educational modules...')

        with transaction.atomic():
            # Clear existing data
            QuizQuestion.objects.all().delete()
            EducationalModule.objects.all().delete()

            modules_data = [
                {
                    'titulo': 'Seguridad al Volante',
                    'descripcion': 'Aprende las mejores prácticas para conducir de forma segura en carretera y prevenir accidentes.',
                    'categoria': 'SEGURIDAD_VIAL',
                    'dificultad': 'PRINCIPIANTE',
                    'contenido': '''
# Seguridad al Volante: Guía Completa para Conductores Responsables

## Introducción
La seguridad vial es uno de los temas más importantes para cualquier conductor. En Guatemala, los accidentes de tránsito son una de las principales causas de muerte y lesiones graves. Según estadísticas recientes, más del 90% de los accidentes son prevenibles con buenas prácticas de manejo. Este módulo te enseñará las técnicas y hábitos que pueden salvar tu vida y la de otros.

## El Cinturón de Seguridad: Tu Primera Línea de Defensa

El cinturón de seguridad reduce el riesgo de muerte en un accidente en aproximadamente un **45%** para conductores y pasajeros del asiento delantero. Datos importantes:

- **Funciona siempre**: No importa si vas cerca o lejos, el cinturón debe estar puesto
- **Posición correcta**: La banda diagonal debe cruzar el pecho (no el cuello) y la banda inferior debe ir sobre las caderas (no el estómago)
- **Para todos**: Todos los ocupantes del vehículo deben usarlo, incluyendo pasajeros traseros
- **Niños**: Los menores de 12 años deben viajar en el asiento trasero, preferiblemente en silla de seguridad apropiada para su edad

## La Regla de los 2 Segundos

Una de las técnicas más importantes para prevenir colisiones es mantener una distancia segura. La "Regla de los 2 Segundos" es fácil de aplicar:

1. Observa cuando el vehículo de adelante pasa un punto fijo (un poste, un árbol)
2. Cuenta "mil uno, mil dos"
3. Si llegas al punto antes de terminar de contar, estás muy cerca

**Aumenta la distancia a 4 segundos cuando**:
- Está lloviendo
- Es de noche
- El pavimento está mojado o resbaloso
- Conduces un vehículo grande o pesado
- Vas detrás de una motocicleta

## Distracciones al Volante: El Enemigo Silencioso

Las distracciones son responsables del 25% de los accidentes. Los tipos más peligrosos son:

**Distracciones visuales**: Quitar los ojos del camino
- Ver el celular
- Buscar objetos en el carro
- Mirar accidentes o eventos en la vía

**Distracciones manuales**: Quitar las manos del volante
- Comer o beber
- Ajustar controles del radio/GPS
- Maquillarse o arreglarse

**Distracciones cognitivas**: Quitar la mente de la conducción
- Conversaciones intensas
- Problemas personales
- Cansancio o somnolencia

**El celular combina los 3 tipos**, por eso es tan peligroso. Enviar un mensaje de texto te quita los ojos del camino por 5 segundos en promedio - a 60 km/h, eso equivale a recorrer la longitud de una cancha de fútbol con los ojos cerrados.

## Conducción Defensiva

La conducción defensiva significa anticipar peligros y estar preparado para reaccionar. Principios clave:

- **Espera lo inesperado**: Asume que otros conductores pueden cometer errores
- **Usa los espejos constantemente**: Revisa los retrovisores cada 5-8 segundos
- **Mantén una ruta de escape**: Siempre ten un plan si necesitas maniobrar de emergencia
- **Observa más allá del vehículo de adelante**: Mira 12-15 segundos adelante para anticipar frenados
- **Cuidado en intersecciones**: El 40% de los accidentes ocurren allí

## Condiciones Climáticas Adversas

**Lluvia**:
- Reduce la velocidad un 30%
- Aumenta la distancia de seguimiento
- Enciende las luces
- Evita frenar bruscamente

**Niebla**:
- Usa luces bajas (las altas reflejan y ciegan)
- Reduce significativamente la velocidad
- Si es muy densa, estacionate en un lugar seguro

**Noche**:
- Verifica que todas tus luces funcionen
- No mires directamente las luces de otros vehículos
- Reduce velocidad ya que tu visibilidad es limitada

## Conclusión
Conducir con responsabilidad no es difícil, pero requiere atención y compromiso constante. Recuerda: el objetivo no es solo llegar a tu destino, sino llegar de forma segura. Un conductor responsable protege su vida, la de su familia y la de todos los demás usuarios de la vía.
''',
                    'duracion_minutos': 15,
                    'puntos_completar': 100,
                    'puntos_quiz_perfecto': 50,
                    'credito_completar': 2.00,
                    'credito_quiz_perfecto': 1.00,
                    'orden': 1,
                    'questions': [
                        {
                            'pregunta': '¿Cual es la distancia minima recomendada entre vehiculos?',
                            'opcion_a': '1 metro',
                            'opcion_b': '2 segundos de distancia',
                            'opcion_c': '5 metros',
                            'opcion_d': '10 metros',
                            'respuesta_correcta': 'B',
                            'explicacion': 'La regla de los 2 segundos permite tiempo suficiente para reaccionar en caso de emergencia.',
                            'orden': 1
                        },
                        {
                            'pregunta': '¿Cuándo debes revisar los espejos retrovisores?',
                            'opcion_a': 'Solo al estacionar',
                            'opcion_b': 'Una vez al dia',
                            'opcion_c': 'Constantemente mientras conduces',
                            'opcion_d': 'Solo en autopista',
                            'respuesta_correcta': 'C',
                            'explicacion': 'Debes revisar los espejos constantemente para estar consciente de tu entorno.',
                            'orden': 2
                        },
                        {
                            'pregunta': '¿Que debes hacer si llueve fuertemente?',
                            'opcion_a': 'Acelerar para salir rapido',
                            'opcion_b': 'Reducir velocidad y aumentar distancia',
                            'opcion_c': 'Mantener la misma velocidad',
                            'opcion_d': 'Apagar las luces',
                            'respuesta_correcta': 'B',
                            'explicacion': 'En lluvia, la visibilidad y traccion se reducen, por lo que debes ir mas despacio.',
                            'orden': 3
                        },
                        {
                            'pregunta': '¿El cinturon de seguridad debe usarse...?',
                            'opcion_a': 'Solo en autopista',
                            'opcion_b': 'Solo en viajes largos',
                            'opcion_c': 'Siempre, sin excepcion',
                            'opcion_d': 'Solo si hay transito',
                            'respuesta_correcta': 'C',
                            'explicacion': 'El cinturon debe usarse siempre, es la forma mas efectiva de prevenir lesiones.',
                            'orden': 4
                        },
                        {
                            'pregunta': '¿Cuándo puedes usar el celular mientras conduces?',
                            'opcion_a': 'Con manos libres',
                            'opcion_b': 'En semaforos',
                            'opcion_c': 'Solo para emergencias',
                            'opcion_d': 'Nunca, mejor detenerse',
                            'respuesta_correcta': 'D',
                            'explicacion': 'Es mejor detenerse completamente para usar el celular y evitar distracciones.',
                            'orden': 5
                        }
                    ]
                },
                {
                    'titulo': 'Primeros Auxilios Basicos',
                    'descripcion': 'Conocimientos esenciales de primeros auxilios que pueden salvar vidas.',
                    'categoria': 'PRIMEROS_AUXILIOS',
                    'dificultad': 'PRINCIPIANTE',
                    'contenido': '''
# Primeros Auxilios Básicos: Conocimientos que Salvan Vidas

## Introducción
Los primeros auxilios son la atención inmediata que se da a una persona herida o enferma antes de que llegue ayuda profesional. En situaciones de emergencia, los primeros minutos son críticos. Tener conocimientos básicos de primeros auxilios puede marcar la diferencia entre la vida y la muerte. En Guatemala, donde los servicios de emergencia pueden tardar en llegar a ciertas áreas, estos conocimientos son aún más valiosos.

## El Protocolo PAS: Proteger, Avisar, Socorrer

Antes de actuar en cualquier emergencia, recuerda **PAS**:

**P - Proteger**
- Asegúrate de que la escena sea segura para ti
- Identifica peligros: tráfico, fuego, cables eléctricos, sustancias tóxicas
- Si hay peligro, no te conviertas en otra víctima
- Señaliza el área si es posible (triángulos, luces de emergencia)

**A - Avisar**
- Llama al **123** (número de emergencias en Guatemala)
- Proporciona información clara: ubicación exacta, número de víctimas, tipo de emergencia
- No cuelgues hasta que te lo indiquen
- Si estás solo con una víctima inconsciente, llama primero y luego atiende

**S - Socorrer**
- Solo actúa dentro de tus conocimientos
- No intentes procedimientos que no conozcas
- Tu rol principal es estabilizar hasta que llegue ayuda profesional

## Evaluación Inicial de la Víctima

Cuando te acerques a una víctima, sigue estos pasos:

1. **Verificar consciencia**: Toca el hombro y pregunta "¿Está usted bien?"
2. **Abrir vía aérea**: Inclina suavemente la cabeza hacia atrás, levanta el mentón
3. **Verificar respiración**: Mira, escucha y siente por 10 segundos máximo
4. **Verificar circulación**: Busca señales de vida, movimiento, pulso en el cuello

## Control de Hemorragias

Las hemorragias severas pueden causar la muerte en minutos. Cómo controlarlas:

**Hemorragia externa**:
1. Ponte guantes si tienes (o usa una bolsa plástica)
2. Aplica presión directa con un trapo limpio o gasa
3. Mantén la presión constante por al menos 10 minutos
4. NO levantes para ver si dejó de sangrar
5. Si la sangre empapa el vendaje, añade más encima sin quitar el original
6. Eleva la extremidad si es posible (y no hay fractura)

**Cuándo NO aplicar torniquete**: Solo en hemorragias que amenazan la vida y cuando la presión directa ha fallado.

## RCP (Reanimación Cardiopulmonar) Básica

La RCP para adultos se realiza cuando la persona no respira y no tiene pulso:

1. **Posición**: Coloca a la víctima boca arriba en superficie dura
2. **Ubicación de manos**: Centro del pecho, entre los pezones
3. **Compresiones**:
   - Presiona fuerte y rápido (5-6 cm de profundidad)
   - Ritmo de 100-120 compresiones por minuto
   - Permite que el pecho suba completamente entre compresiones
4. **Ciclos**: 30 compresiones, 2 respiraciones (si estás entrenado)
5. **Solo manos**: Si no estás entrenado, haz solo compresiones continuas

**Importante**: La RCP de baja calidad es mejor que no hacer nada. No temas causar daño.

## Atragantamiento (Obstrucción de Vía Aérea)

**Si la persona puede toser**:
- Anímala a seguir tosiendo
- NO le des palmadas ni hagas la maniobra de Heimlich
- La tos es el mecanismo más efectivo para expulsar objetos

**Si la persona NO puede toser, hablar ni respirar**:
1. Párate detrás de la persona
2. Coloca un puño cerrado arriba del ombligo
3. Agarra tu puño con la otra mano
4. Realiza compresiones abdominales hacia arriba y adentro
5. Repite hasta que expulse el objeto o pierda consciencia

**En personas embarazadas u obesas**: Las compresiones se hacen en el pecho, no en el abdomen.

## Quemaduras

**Qué hacer**:
- Enfría la quemadura con agua corriente (NO helada) por 10-20 minutos
- Quita anillos, relojes o ropa antes de que hinche (si no está pegada)
- Cubre con vendaje limpio y holgado
- No revientes ampollas

**Qué NO hacer**:
- NO apliques mantequilla, pasta de dientes, huevo ni remedios caseros
- NO uses hielo directamente
- NO quites ropa que esté pegada a la piel

## Fracturas y Esguinces

**Señales de fractura**:
- Dolor intenso
- Hinchazón
- Deformidad visible
- Incapacidad de mover la zona
- Sonido de "crack" al momento de la lesión

**Qué hacer**:
- Inmoviliza la zona (no intentes alinear el hueso)
- Aplica hielo envuelto en tela (20 min cada hora)
- Eleva la extremidad si es posible
- NO permitas que la persona camine si sospecha fractura de pierna

## Cuándo NO Mover a una Víctima

**No muevas a una persona si**:
- Fue un accidente de auto fuerte
- Cayó de altura
- Se queja de dolor en cuello o espalda
- Está inconsciente y no sabes qué pasó
- Tiene hormigueo o no puede mover extremidades

**Excepción**: Solo muévela si hay peligro inmediato (fuego, tráfico, sustancias tóxicas).

## Conclusión
Los primeros auxilios son una responsabilidad ciudadana. No necesitas ser médico para salvar una vida. Con estos conocimientos básicos, puedes estabilizar a una persona hasta que llegue ayuda profesional. Recuerda: mantén la calma, llama a emergencias, y actúa dentro de tus capacidades.
''',
                    'duracion_minutos': 20,
                    'puntos_completar': 150,
                    'puntos_quiz_perfecto': 75,
                    'credito_completar': 3.00,
                    'credito_quiz_perfecto': 1.50,
                    'orden': 2,
                    'questions': [
                        {
                            'pregunta': '¿Cual es el numero de emergencias en Guatemala?',
                            'opcion_a': '911',
                            'opcion_b': '123',
                            'opcion_c': '110',
                            'opcion_d': '999',
                            'respuesta_correcta': 'B',
                            'explicacion': 'El 123 es el numero de emergencias unificado en Guatemala.',
                            'orden': 1
                        },
                        {
                            'pregunta': '¿Como detienes un sangrado severo?',
                            'opcion_a': 'Con agua fria',
                            'opcion_b': 'Presion directa sobre la herida',
                            'opcion_c': 'Frotar alcohol',
                            'opcion_d': 'Dejar que sangre',
                            'respuesta_correcta': 'B',
                            'explicacion': 'La presion directa es la forma mas efectiva de controlar sangrados.',
                            'orden': 2
                        },
                        {
                            'pregunta': '¿Que significa RCP?',
                            'opcion_a': 'Revision Cardiaca Preventiva',
                            'opcion_b': 'Reanimacion Cardiopulmonar',
                            'opcion_c': 'Respiracion con Presion',
                            'opcion_d': 'Revision de Pulso Cardiaco',
                            'respuesta_correcta': 'B',
                            'explicacion': 'RCP es Reanimacion Cardiopulmonar, usada cuando alguien no respira o no tiene pulso.',
                            'orden': 3
                        },
                        {
                            'pregunta': '¿Que haces si alguien se atraganta pero puede toser?',
                            'opcion_a': 'Golpear su espalda inmediatamente',
                            'opcion_b': 'Hacer la maniobra de Heimlich',
                            'opcion_c': 'Animarlo a seguir tosiendo',
                            'opcion_d': 'Darle agua',
                            'respuesta_correcta': 'C',
                            'explicacion': 'Si la persona puede toser, significa que hay paso de aire. Animala a seguir tosiendo.',
                            'orden': 4
                        },
                        {
                            'pregunta': '¿Debes mover a una persona inconsciente?',
                            'opcion_a': 'Siempre, para comodidad',
                            'opcion_b': 'Solo si hay peligro inmediato',
                            'opcion_c': 'Nunca',
                            'opcion_d': 'Si, para que respire mejor',
                            'respuesta_correcta': 'B',
                            'explicacion': 'Solo mueve a alguien inconsciente si hay peligro inmediato (fuego, trafico, etc.).',
                            'orden': 5
                        },
                        {
                            'pregunta': '¿Que debes verificar primero en una emergencia?',
                            'opcion_a': 'La respiracion',
                            'opcion_b': 'El pulso',
                            'opcion_c': 'La seguridad de la escena',
                            'opcion_d': 'Las heridas',
                            'respuesta_correcta': 'C',
                            'explicacion': 'Primero asegura que la escena sea segura para ti y para la victima.',
                            'orden': 6
                        }
                    ]
                },
                {
                    'titulo': 'Ahorro Inteligente',
                    'descripcion': 'Estrategias practicas para administrar tu dinero y construir un fondo de emergencia.',
                    'categoria': 'FINANZAS_PERSONALES',
                    'dificultad': 'PRINCIPIANTE',
                    'contenido': '''
# Ahorro Inteligente: Construye tu Seguridad Financiera

## Introducción
El ahorro es la base de la libertad financiera. En Guatemala, donde muchas familias viven al día, desarrollar el hábito del ahorro puede transformar tu vida y la de tu familia. No importa cuánto ganes; lo importante es empezar. Incluso pequeñas cantidades, ahorradas consistentemente, pueden convertirse en un colchón financiero que te proteja en momentos difíciles.

## La Regla 50/30/20: Un Presupuesto Simple

Esta regla divide tus ingresos en tres categorías:

**50% - Necesidades** (gastos fijos e indispensables):
- Vivienda (alquiler, hipoteca)
- Alimentación básica
- Servicios (agua, luz, teléfono)
- Transporte al trabajo
- Salud y medicamentos esenciales
- Educación de los hijos

**30% - Deseos** (gastos que mejoran tu calidad de vida):
- Entretenimiento
- Salidas a comer
- Compras no esenciales
- Suscripciones (Netflix, Spotify)
- Hobbies

**20% - Ahorro y deudas**:
- Fondo de emergencia
- Ahorro para metas específicas
- Pago de deudas (más del mínimo)
- Inversiones

**Adaptación a la realidad guatemalteca**: Si tus necesidades superan el 50%, empieza con lo que puedas ahorrar (aunque sea 5-10%) y trabaja para reducir gastos gradualmente.

## "Págate Primero a Ti Mismo"

Este principio es transformador: **ahorra antes de gastar, no lo que sobra**.

**Cómo implementarlo**:
1. El día que recibas tu salario, transfiere inmediatamente tu ahorro
2. Abre una cuenta separada solo para ahorros
3. Si es posible, automatiza la transferencia
4. Trata ese dinero como si no existiera

**Por qué funciona**: Si esperas a ver qué sobra al final del mes, probablemente no sobrará nada. Pero si lo separas primero, te adaptas a vivir con lo que queda.

## El Fondo de Emergencia: Tu Red de Seguridad

Un fondo de emergencia es dinero reservado exclusivamente para situaciones imprevistas: pérdida de empleo, emergencias médicas, reparaciones urgentes del hogar o vehículo.

**Cuánto necesitas**:
- **Meta inicial**: Q5,000 (para emergencias pequeñas)
- **Meta intermedia**: 1-3 meses de gastos básicos
- **Meta ideal**: 3-6 meses de gastos básicos

**Dónde guardarlo**:
- En una cuenta de ahorros separada de tu cuenta principal
- Que sea de fácil acceso pero no demasiado (para no tentarte)
- NO en inversiones de riesgo, debe ser dinero seguro

**Qué SÍ es una emergencia**:
- Pérdida de empleo
- Gastos médicos inesperados
- Reparación urgente del vehículo o vivienda
- Gastos funerarios familiares

**Qué NO es una emergencia**:
- Ofertas de "oportunidad única"
- Vacaciones
- Compras impulsivas
- Gastos que podrías planificar

## Los Gastos Hormiga: El Enemigo Silencioso

Los gastos hormiga son pequeños gastos diarios que parecen insignificantes pero se acumulan dramáticamente:

**Ejemplos comunes**:
| Gasto | Diario | Mensual | Anual |
|-------|--------|---------|-------|
| Café de tienda | Q15 | Q450 | Q5,400 |
| Snacks | Q10 | Q300 | Q3,600 |
| Uber innecesario | Q25 | Q500 | Q6,000 |
| Comida rápida | Q40 | Q800 | Q9,600 |
| **Total** | Q90 | Q2,050 | **Q24,600** |

**Cómo identificarlos**:
1. Lleva un registro de TODOS tus gastos por una semana
2. Anota hasta el gasto más pequeño
3. Al final, revisa y suma por categoría
4. Te sorprenderá cuánto se va en "cositas"

**No se trata de eliminarlos todos**, sino de ser consciente y elegir cuáles valen la pena.

## Estrategias Prácticas de Ahorro

**En el supermercado**:
- Haz lista antes de ir y cíñete a ella
- Compara precios por unidad, no por paquete
- Las marcas propias suelen ser igual de buenas
- Evita ir con hambre

**En servicios**:
- Revisa si usas todas las suscripciones que pagas
- Negocia tarifas de internet y teléfono
- Apaga luces y desconecta aparatos
- Cocina en casa más seguido

**En transporte**:
- Planifica rutas para optimizar combustible
- Comparte viajes con compañeros de trabajo
- Mantenimiento preventivo es más barato que reparaciones

**En compras grandes**:
- Espera 48 horas antes de comprar algo caro
- Investiga y compara precios online
- Pregúntate: "¿Lo necesito o lo quiero?"

## Las Deudas: Cómo Evitarlas y Salir de Ellas

**Tipos de deuda**:
- **Deuda buena**: Genera valor (educación, negocio, vivienda)
- **Deuda mala**: Consume sin generar valor (tarjetas, préstamos para consumo)

**Cómo salir de deudas** (Método Bola de Nieve):
1. Lista todas tus deudas de menor a mayor
2. Paga el mínimo en todas excepto la más pequeña
3. A la más pequeña, pon todo el extra que puedas
4. Cuando la liquides, usa ese dinero para la siguiente
5. La motivación de ir eliminando deudas te impulsa

**Evita**:
- Préstamos para pagar otros préstamos
- Usar tarjeta de crédito si no puedes pagar el total mensual
- Préstamos informales con tasas altas
- Comprar a crédito cosas que se deprecian rápidamente

## Metas de Ahorro: Soñar en Grande, Empezar en Pequeño

Define metas específicas y con plazo:

**Corto plazo (1-12 meses)**:
- Fondo de emergencia inicial
- Reparación del vehículo
- Vacaciones familiares

**Mediano plazo (1-5 años)**:
- Enganche de casa
- Educación superior
- Negocio propio

**Largo plazo (5+ años)**:
- Jubilación
- Educación universitaria de los hijos
- Propiedad pagada

**Fórmula para alcanzar metas**:
Meta ÷ Meses = Ahorro mensual necesario

Ejemplo: Casa Q100,000 enganche en 5 años = Q100,000 ÷ 60 = Q1,667/mes

## Conclusión
El ahorro no es un sacrificio, es una inversión en tu tranquilidad futura. Empieza hoy, aunque sea con Q50. El mejor momento para comenzar fue hace 10 años; el segundo mejor momento es ahora. Tu yo del futuro te lo agradecerá.
''',
                    'duracion_minutos': 12,
                    'puntos_completar': 100,
                    'puntos_quiz_perfecto': 50,
                    'credito_completar': 2.00,
                    'credito_quiz_perfecto': 1.00,
                    'orden': 3,
                    'questions': [
                        {
                            'pregunta': '¿Que es la regla 50/30/20?',
                            'opcion_a': '50% ahorros, 30% necesidades, 20% deseos',
                            'opcion_b': '50% necesidades, 30% deseos, 20% ahorros',
                            'opcion_c': '50% deseos, 30% ahorros, 20% necesidades',
                            'opcion_d': '50% gastos, 30% ahorros, 20% inversion',
                            'respuesta_correcta': 'B',
                            'explicacion': 'La regla 50/30/20 sugiere: 50% para necesidades, 30% para deseos, 20% para ahorros.',
                            'orden': 1
                        },
                        {
                            'pregunta': '¿Cuántos meses de gastos debe cubrir tu fondo de emergencia?',
                            'opcion_a': '1 mes',
                            'opcion_b': '2 meses',
                            'opcion_c': '3-6 meses',
                            'opcion_d': '12 meses',
                            'respuesta_correcta': 'C',
                            'explicacion': 'Lo ideal es tener un fondo que cubra 3 a 6 meses de gastos esenciales.',
                            'orden': 2
                        },
                        {
                            'pregunta': '¿Que son los "gastos hormiga"?',
                            'opcion_a': 'Gastos de supermercado',
                            'opcion_b': 'Pequeños gastos diarios que se acumulan',
                            'opcion_c': 'Gastos en mascotas',
                            'opcion_d': 'Gastos medicos',
                            'respuesta_correcta': 'B',
                            'explicacion': 'Los gastos hormiga son pequenos gastos diarios (cafe, snacks) que se acumulan rapidamente.',
                            'orden': 3
                        },
                        {
                            'pregunta': '¿Que significa "pagarte primero a ti mismo"?',
                            'opcion_a': 'Comprar lo que quieras primero',
                            'opcion_b': 'Ahorrar antes de gastar',
                            'opcion_c': 'Pagar tus deudas',
                            'opcion_d': 'Ganar mas dinero',
                            'respuesta_correcta': 'B',
                            'explicacion': 'Significa apartar dinero para ahorros antes de gastarlo en otras cosas.',
                            'orden': 4
                        },
                        {
                            'pregunta': '¿Cual es una buena forma de reducir gastos?',
                            'opcion_a': 'Dejar de comer',
                            'opcion_b': 'No salir nunca',
                            'opcion_c': 'Comparar precios y buscar ofertas',
                            'opcion_d': 'Usar todas las tarjetas de credito',
                            'respuesta_correcta': 'C',
                            'explicacion': 'Comparar precios y buscar ofertas te ayuda a reducir gastos sin sacrificar calidad de vida.',
                            'orden': 5
                        }
                    ]
                },
                {
                    'titulo': 'Prevencion de Robos y Fraudes',
                    'descripcion': 'Aprende a protegerte contra robos, fraudes y estafas comunes.',
                    'categoria': 'PREVENCION',
                    'dificultad': 'INTERMEDIO',
                    'contenido': '''
# Prevención de Robos y Fraudes: Protege lo Tuyo

## Introducción
Guatemala enfrenta desafíos significativos en seguridad. Sin embargo, muchos robos y fraudes son prevenibles con las precauciones adecuadas. Este módulo te enseñará estrategias prácticas para proteger tu persona, tu patrimonio y tu información. Recuerda: los delincuentes buscan víctimas fáciles; tu mejor defensa es no serlo.

## Seguridad Personal en la Calle

**Camina con propósito**:
- Mantén la cabeza en alto y mira a tu alrededor
- Evita caminar mirando el celular
- Proyecta confianza con tu lenguaje corporal
- Los delincuentes evitan a personas alertas

**Protege tus pertenencias**:
- Lleva la cartera en bolsillo delantero o bolso cruzado al frente
- No exhibas joyas, relojes caros o fajos de dinero
- En el transporte público, abraza tu mochila al frente
- Divide tu dinero: algo en la cartera, algo escondido

**Zonas y horarios de riesgo**:
- Evita zonas solitarias, especialmente de noche
- Identifica las "zonas rojas" de tu ciudad
- Si debes pasar por un lugar riesgoso, hazlo rápido y alerta
- Varía tus rutas y horarios regulares

**Si te asaltan**:
- Tu vida vale más que cualquier objeto material
- No te resistas físicamente
- Entrega lo que pidan sin movimientos bruscos
- Trata de observar características del asaltante para reportar después
- Reporta inmediatamente a la policía (llama al 110)

## Seguridad en el Vehículo

**Prevención de robo de vehículo**:
- Siempre cierra con llave, incluso por "un momentito"
- No dejes objetos visibles en el interior
- Estaciona en lugares iluminados y vigilados
- Instala alarma y/o rastreador GPS

**Mientras conduces**:
- Mantén vidrios arriba y seguros puestos
- En semáforos, deja espacio con el vehículo de adelante (para poder maniobrar)
- Evita detenerte en lugares solitarios
- Si sospechas que te siguen, no vayas a tu casa; dirígete a una estación de policía

**Si intentan robarte el vehículo**:
- No te resistas si están armados
- No persigas a los ladrones
- Recuerda el número de placa si puedes
- Reporta inmediatamente

## Fraudes Telefónicos: El Engaño que Llama a tu Puerta

**El "familiar en problemas"**:
- Recibes llamada: "Hola, soy yo" (esperan que digas un nombre)
- Dicen estar detenidos, en un accidente o secuestrados
- Piden dinero urgente por transferencia
- **Defensa**: Cuelga y llama directamente al familiar

**El "premio" o "sorteo"**:
- Te dicen que ganaste un premio que no recuerdas haber participado
- Piden dinero para "gastos de envío" o "impuestos"
- **Regla de oro**: Si no participaste, no ganaste nada

**Llamadas "del banco"**:
- Piden confirmar datos, PIN, contraseñas o códigos SMS
- Amenazan con bloquear tu cuenta si no cooperas
- **Defensa**: Los bancos NUNCA piden PIN ni contraseñas. Cuelga y llama tú al número oficial del banco

**El "SAT" o autoridad fiscal**:
- Dicen que debes impuestos y que enviarán a la policía
- Piden pago inmediato en efectivo o tarjeta de regalo
- **Defensa**: Las autoridades reales no operan así. Nunca envían mensajes de amenaza

## Fraudes Digitales: Protege tu Identidad Online

**Phishing (correos falsos)**:
- Imitan correos de bancos, tiendas o servicios conocidos
- Tienen enlaces que llevan a páginas falsas
- **Cómo identificarlos**:
  - Errores ortográficos o de gramática
  - Direcciones de correo sospechosas (ej: banco@gmail.com)
  - Enlaces acortados o con dominios raros
  - Urgencia extrema ("¡Tu cuenta será cerrada!")

**Estafas en redes sociales**:
- Ofertas de trabajo "desde casa" con pagos irreales
- Ventas de productos muy baratos que nunca llegan
- Perfiles falsos que piden préstamos
- **Defensa**: Si es demasiado bueno para ser verdad, probablemente lo es

**Compras online seguras**:
- Verifica que la página tenga "https://" y candado
- Investiga la reputación del vendedor
- Usa tarjetas virtuales o PayPal cuando sea posible
- Desconfía de precios muy por debajo del mercado

## Protección de Contraseñas e Información

**Contraseñas seguras**:
- Mínimo 12 caracteres
- Combina mayúsculas, minúsculas, números y símbolos
- NO uses: tu nombre, fecha de nacimiento, "123456", "password"
- Usa contraseñas DIFERENTES para cada cuenta importante

**Información que NUNCA debes compartir**:
- PIN de tarjetas
- Contraseñas completas
- Códigos de verificación SMS
- Datos completos de tarjetas de crédito por teléfono
- Fotos de tu DPI o documentos

**Autenticación de dos factores (2FA)**:
- Actívala en todas las cuentas que la ofrezcan
- Preferiblemente usa una app autenticadora
- Los códigos SMS son mejor que nada, pero menos seguros

## Esquemas Piramidales y Estafas de Inversión

**Señales de alarma**:
- Prometen rendimientos garantizados muy altos
- Ganas principalmente por reclutar nuevos miembros
- No hay producto real o el producto es secundario
- Presión para invertir rápidamente
- "Oportunidad única" que "no puede esperar"

**Ejemplos comunes en Guatemala**:
- "Multiniveles" donde casi nadie vende pero todos reclutan
- "Inversiones" en criptomonedas con rendimientos fijos
- "Tandas" o "círculos de dinero" que eventualmente colapsan

**La matemática simple**: Si 100 personas ponen Q1,000 cada una y se promete doblar el dinero, alguien tiene que perder Q100,000. Ese alguien usualmente son los últimos en entrar.

## Qué Hacer si Fuiste Víctima

**De robo**:
1. Reporta a la PNC (110) inmediatamente
2. Si robaron documentos, haz la denuncia para el reposición
3. Si robaron tarjetas, bloquéalas inmediatamente
4. Guarda números de denuncia para trámites

**De fraude financiero**:
1. Contacta a tu banco inmediatamente
2. Bloquea tarjetas y cuentas comprometidas
3. Cambia todas las contraseñas
4. Presenta denuncia en el MP
5. Monitorea tus cuentas por movimientos sospechosos

## Conclusión
La prevención es tu mejor herramienta. Mantente alerta, confía en tu instinto, y recuerda: los delincuentes buscan víctimas fáciles. Al aplicar estas precauciones, reduces significativamente tu riesgo de ser víctima. Comparte este conocimiento con tu familia para que todos estén protegidos.
''',
                    'duracion_minutos': 18,
                    'puntos_completar': 120,
                    'puntos_quiz_perfecto': 60,
                    'credito_completar': 2.50,
                    'credito_quiz_perfecto': 1.25,
                    'orden': 4,
                    'questions': [
                        {
                            'pregunta': '¿Que debes hacer si recibes una llamada "de tu banco" pidiendo tu PIN?',
                            'opcion_a': 'Darles el PIN inmediatamente',
                            'opcion_b': 'Colgar y llamar tu al banco',
                            'opcion_c': 'Pedir mas informacion',
                            'opcion_d': 'Ir al banco a verificar',
                            'respuesta_correcta': 'B',
                            'explicacion': 'Los bancos NUNCA piden tu PIN. Cuelga y llama tu al numero oficial del banco.',
                            'orden': 1
                        },
                        {
                            'pregunta': '¿Como identificas un correo de phishing?',
                            'opcion_a': 'Tiene errores ortograficos y enlaces sospechosos',
                            'opcion_b': 'Viene de tu banco',
                            'opcion_c': 'Tiene logos oficiales',
                            'opcion_d': 'Pide informacion personal',
                            'respuesta_correcta': 'A',
                            'explicacion': 'Los correos de phishing suelen tener errores y enlaces sospechosos. Verifica siempre la direccion del remitente.',
                            'orden': 2
                        },
                        {
                            'pregunta': '¿Que hacer si pierdes tu tarjeta de credito?',
                            'opcion_a': 'Esperar a ver si aparece',
                            'opcion_b': 'Reportarla inmediatamente al banco',
                            'opcion_c': 'Bloquearla en una semana',
                            'opcion_d': 'Pedir una nueva sin reportar',
                            'respuesta_correcta': 'B',
                            'explicacion': 'Reporta inmediatamente para evitar cargos fraudulentos.',
                            'orden': 3
                        },
                        {
                            'pregunta': '¿Es seguro usar WiFi publico para transacciones bancarias?',
                            'opcion_a': 'Si, siempre',
                            'opcion_b': 'Solo en cafeterias',
                            'opcion_c': 'No, es riesgoso',
                            'opcion_d': 'Si tienes antivirus',
                            'respuesta_correcta': 'C',
                            'explicacion': 'El WiFi publico no es seguro para transacciones financieras. Usa tu red movil o VPN.',
                            'orden': 4
                        },
                        {
                            'pregunta': '¿Que es una estafa piramidal?',
                            'opcion_a': 'Un negocio legitimo',
                            'opcion_b': 'Un esquema donde ganas solo reclutando gente',
                            'opcion_c': 'Una inversion segura',
                            'opcion_d': 'Un tipo de ahorro',
                            'respuesta_correcta': 'B',
                            'explicacion': 'Las piramides son ilegales. Prometen ganancias faciles pero solo ganan los primeros participantes.',
                            'orden': 5
                        },
                        {
                            'pregunta': '¿Debes compartir codigos de verificacion SMS?',
                            'opcion_a': 'Solo con personas de confianza',
                            'opcion_b': 'Con empresas que lo pidan',
                            'opcion_c': 'Nunca, con nadie',
                            'opcion_d': 'Solo por telefono',
                            'respuesta_correcta': 'C',
                            'explicacion': 'Los codigos de verificacion son solo para ti. Nadie legitimo te los pedira.',
                            'orden': 6
                        }
                    ]
                },
                {
                    'titulo': 'Mantenimiento Vehicular Basico',
                    'descripcion': 'Aprende a cuidar tu vehiculo para prevenir averias y prolongar su vida util.',
                    'categoria': 'SEGURIDAD_VIAL',
                    'dificultad': 'INTERMEDIO',
                    'contenido': '''
# Mantenimiento Vehicular Básico: Cuida tu Inversión

## Introducción
Tu vehículo es probablemente una de las inversiones más grandes que has hecho. El mantenimiento preventivo no solo prolonga la vida de tu carro, sino que también previene averías costosas y peligrosas. Un vehículo bien mantenido es más seguro, más eficiente en combustible, y conserva mejor su valor de reventa. En Guatemala, donde las condiciones de las carreteras pueden ser difíciles, el mantenimiento regular es aún más importante.

## El Tablero: Tu Centro de Información

**Luces de advertencia y su significado**:

| Luz | Color | Significado | Acción |
|-----|-------|-------------|--------|
| Check Engine | Amarilla/Roja | Problema en el motor | Llevar al mecánico pronto |
| Aceite | Roja | Presión de aceite baja | DETENER inmediatamente |
| Batería | Roja | Sistema de carga fallando | Revisar batería/alternador |
| Temperatura | Roja | Motor sobrecalentado | DETENER inmediatamente |
| ABS | Amarilla | Sistema antibloqueo con falla | Frenos funcionan, pero sin ABS |
| Frenos | Roja | Problema en frenos o freno de mano | Verificar freno de mano y nivel de líquido |

**Regla general**:
- Luz ROJA = Problema grave, detente lo antes posible
- Luz AMARILLA = Problema que requiere atención pronto
- Luz VERDE/AZUL = Sistema activo (normal)

## El Aceite: La Sangre de tu Motor

**Por qué es vital**:
- Lubrica las partes móviles del motor
- Reduce fricción y desgaste
- Enfría componentes internos
- Limpia residuos del motor

**Cómo verificar el nivel**:
1. Estaciona en superficie plana
2. Apaga el motor y espera 5 minutos
3. Saca la varilla y limpia con un trapo
4. Inserta completamente y saca de nuevo
5. El nivel debe estar entre MIN y MAX
6. Si está bajo, agrega aceite del tipo correcto

**Cuándo cambiarlo**:
- Cada **5,000 km** para aceite convencional
- Cada **7,500-10,000 km** para aceite sintético
- O cada **6 meses**, lo que ocurra primero
- Siempre cambia el filtro de aceite junto con el aceite

**Señales de aceite en mal estado**:
- Color muy oscuro o negro (debe ser ámbar/miel)
- Consistencia muy espesa
- Partículas visibles
- Olor a quemado

## Las Llantas: Tu Contacto con el Camino

**Presión de aire**:
- Verifica la presión cuando las llantas estén FRÍAS
- La presión correcta está en una etiqueta en la puerta del conductor
- Generalmente entre 30-35 PSI para autos
- Revisa semanalmente o antes de viajes largos

**Consecuencias de presión incorrecta**:
- **Muy baja**: Mayor consumo de combustible, desgaste irregular, riesgo de reventón
- **Muy alta**: Menor tracción, desgaste en el centro, viaje incómodo

**Profundidad del dibujo (labrado)**:
- Mínimo legal: 1.6 mm
- Recomendado: más de 3 mm
- **Prueba de la moneda**: Inserta una moneda de Q1 en el surco. Si ves toda la orilla, necesitas llantas nuevas

**Rotación de llantas**:
- Cada 10,000 km
- Prolonga la vida de las llantas
- Asegura desgaste uniforme

**Alineación y balanceo**:
- Si el volante jala hacia un lado: necesitas alineación
- Si el volante vibra a alta velocidad: necesitas balanceo
- Después de golpear hoyos fuertes, verifica ambos

## Sistema de Frenos: Tu Seguridad

**Señales de problemas en frenos**:
- Chirrido al frenar (pastillas gastadas)
- Volante o pedal vibra al frenar (discos dañados)
- Pedal se va hasta abajo (aire en el sistema o fuga)
- Vehículo se jala hacia un lado al frenar (caliper pegado)

**Componentes y su vida útil aproximada**:
- **Pastillas**: 30,000-70,000 km
- **Discos**: 50,000-100,000 km
- **Líquido de frenos**: Cambiar cada 2 años
- **Calipers**: Vida útil del vehículo (con mantenimiento)

**Líquido de frenos**:
- Verifica nivel en el depósito (bajo el cofre)
- Debe estar entre MIN y MAX
- Si baja frecuentemente, hay fuga (peligroso)
- El líquido absorbe humedad con el tiempo, por eso se cambia

## Sistema de Enfriamiento

**El refrigerante (anticongelante)**:
- Evita que el motor se sobrecaliente
- Protege contra corrosión interna
- Previene congelamiento en climas fríos

**Verificación**:
- NUNCA abras el radiador con el motor caliente (riesgo de quemaduras graves)
- Verifica el nivel en el depósito de expansión
- El nivel debe estar entre MIN y MAX cuando está frío

**Señales de problemas**:
- Temperatura sube más de lo normal
- Vapor o líquido verde/amarillo bajo el cofre
- Olor dulce dentro del carro (fuga en el calefactor)
- Manchas de refrigerante donde estacionas

**Cambio recomendado**: Cada 2-3 años o 40,000 km

## La Batería

**Vida útil promedio**: 3-5 años en Guatemala (el calor acorta la vida)

**Señales de batería débil**:
- Motor arranca lento
- Luces del tablero se atenúan al arrancar
- Necesitas "pasar corriente" frecuentemente
- Batería hinchada o con corrosión

**Cómo pasar corriente (cables de arranque)**:
1. Conecta cable ROJO al positivo (+) de batería buena
2. Conecta otro extremo ROJO al positivo (+) de batería muerta
3. Conecta cable NEGRO al negativo (-) de batería buena
4. Conecta otro extremo NEGRO a metal del motor (NO a la batería)
5. Enciende el carro con batería buena
6. Espera 2 minutos e intenta arrancar el otro
7. Desconecta en orden inverso

**Mantenimiento**:
- Limpia la corrosión (polvo blanco) con agua y bicarbonato
- Asegúrate de que las conexiones estén firmes
- Verifica el nivel de agua destilada (si aplica)

## Filtros Importantes

**Filtro de aire del motor**:
- Evita que entre polvo al motor
- Cambiar cada 15,000-30,000 km (más frecuente en calles polvorientas)
- Filtro sucio = menor rendimiento y mayor consumo

**Filtro de aire del habitáculo**:
- Limpia el aire que entra al interior
- Cambiar cada 15,000-20,000 km
- Importante para alergias y calidad del aire

**Filtro de combustible**:
- Limpia impurezas de la gasolina
- Cambiar cada 30,000-40,000 km
- Filtro tapado = motor se jalonea o no arranca

## Programa de Mantenimiento Sugerido

| Intervalo | Servicio |
|-----------|----------|
| Semanal | Verificar presión de llantas, nivel de aceite |
| Mensual | Verificar todos los líquidos, luces, limpiaparabrisas |
| 5,000 km | Cambio de aceite y filtro |
| 10,000 km | Rotación de llantas |
| 20,000 km | Revisar frenos, filtro de aire |
| 40,000 km | Cambiar bujías, refrigerante, líquido de frenos |
| 60,000 km | Cambiar banda de distribución (según modelo) |

## Conclusión
El mantenimiento preventivo es una inversión que se paga sola. Un problema detectado a tiempo cuesta mucho menos que una reparación mayor. Además, un vehículo bien mantenido es más seguro para ti y tu familia. Lleva un registro de los servicios realizados y sigue el programa de mantenimiento de tu vehículo.
''',
                    'duracion_minutos': 16,
                    'puntos_completar': 110,
                    'puntos_quiz_perfecto': 55,
                    'credito_completar': 2.25,
                    'credito_quiz_perfecto': 1.10,
                    'orden': 5,
                    'questions': [
                        {
                            'pregunta': '¿Cada cuanto debes cambiar el aceite de motor?',
                            'opcion_a': 'Cada 1,000 km',
                            'opcion_b': 'Cada 5,000 km',
                            'opcion_c': 'Cada 20,000 km',
                            'opcion_d': 'Una vez al año',
                            'respuesta_correcta': 'B',
                            'explicacion': 'El aceite debe cambiarse aproximadamente cada 5,000 km o segun el manual del vehiculo.',
                            'orden': 1
                        },
                        {
                            'pregunta': '¿Como verificas la presion de las llantas?',
                            'opcion_a': 'Pateando la llanta',
                            'opcion_b': 'Con un manometro',
                            'opcion_c': 'A simple vista',
                            'opcion_d': 'No es necesario',
                            'respuesta_correcta': 'B',
                            'explicacion': 'Usa un manometro para medir la presion exacta. Verifica cuando las llantas esten frias.',
                            'orden': 2
                        },
                        {
                            'pregunta': '¿Que indica una luz roja en el tablero?',
                            'opcion_a': 'Todo esta bien',
                            'opcion_b': 'Es decorativa',
                            'opcion_c': 'Problema grave, detenerse',
                            'opcion_d': 'Solo es advertencia',
                            'respuesta_correcta': 'C',
                            'explicacion': 'Las luces rojas indican problemas graves. Detente de forma segura y verifica.',
                            'orden': 3
                        },
                        {
                            'pregunta': '¿Que liquido es amarillo o verde en el motor?',
                            'opcion_a': 'Aceite',
                            'opcion_b': 'Gasolina',
                            'opcion_c': 'Refrigerante',
                            'opcion_d': 'Liquido de frenos',
                            'respuesta_correcta': 'C',
                            'explicacion': 'El refrigerante (anticongelante) suele ser amarillo o verde y enfria el motor.',
                            'orden': 4
                        },
                        {
                            'pregunta': '¿Cuándo debes revisar los frenos?',
                            'opcion_a': 'Solo cuando hacen ruido',
                            'opcion_b': 'Regularmente, cada 20,000 km',
                            'opcion_c': 'Una vez al año',
                            'opcion_d': 'Nunca',
                            'respuesta_correcta': 'B',
                            'explicacion': 'Los frenos deben revisarse regularmente, no esperes a que fallen.',
                            'orden': 5
                        }
                    ]
                },
                {
                    'titulo': 'Servicios SegurifAI: Tu Asistencia en Carretera',
                    'descripcion': 'Conoce todos los servicios de asistencia vial y de salud que SegurifAI te ofrece en Guatemala.',
                    'categoria': 'SEGURIDAD_VIAL',
                    'dificultad': 'PRINCIPIANTE',
                    'contenido': '''
# Servicios SegurifAI: Tu Asistencia Integral en Guatemala

## Introducción
SegurifAI, a través de la app SegurifAI integrada con PAQ Wallet, te ofrece asistencia vial y de salud las 24 horas del día, los 7 días de la semana, los 365 días del año en todo el territorio guatemalteco. Ya sea que tengas una emergencia en carretera o necesites orientación médica a medianoche, SegurifAI está para ayudarte.

## Planes Disponibles

SegurifAI ofrece tres opciones diseñadas para cubrir diferentes necesidades:

**Plan Drive (Vial) - $3.15/mes**
Ideal para conductores que buscan protección en carretera.

**Plan Health (Salud) - $2.90/mes**
Perfecto para quienes priorizan el cuidado de su salud y la de su familia.

**Plan Combo (Drive + Health) - $5.50/mes**
La protección más completa: asistencia vial Y de salud a un precio especial.

## Servicios del Plan Drive (Asistencia Vial)

### Grúa del Vehículo
- **Eventos por año**: 3
- **Monto máximo por evento**: $150
- **Cobertura**: Por accidente de tránsito, falla mecánica o eléctrica
- **Uso**: Remolque hasta el taller más cercano o de tu preferencia

### Abasto de Combustible
- **Eventos por año**: Ilimitados
- **Cantidad**: 1 galón de gasolina
- **Uso**: Cuando te quedas sin combustible en carretera
- **Nota**: El galón es cortesía; si necesitas más, lo pagas al proveedor

### Cambio de Neumáticos
- **Eventos por año**: 3
- **Monto máximo por evento**: $150
- **Uso**: Técnico va a tu ubicación y cambia la llanta ponchada por tu repuesto
- **Importante**: Debes tener llanta de repuesto en buen estado

### Paso de Corriente
- **Eventos por año**: Ilimitados
- **Uso**: Cuando tu batería se descarga
- **Servicio**: Técnico llega con equipo para pasar corriente

### Cerrajería Automotriz
- **Eventos por año**: 3
- **Monto máximo por evento**: $150
- **Uso**: Cuando te quedas fuera del vehículo
- **Servicio**: Apertura profesional sin dañar el vehículo

### Ambulancia por Accidente de Tránsito
- **Eventos por año**: 1
- **Monto máximo**: $100
- **Uso**: Traslado de emergencia si tienes un accidente
- **Nota**: Solo en caso de accidente de tránsito

### Conductor Profesional
- **Eventos por año**: 1
- **Monto máximo**: $60
- **Uso**: Si no puedes conducir (indisposición, medicamentos, etc.)
- **Servicio**: Un conductor te lleva a tu destino en tu propio vehículo

### Taxi al Aeropuerto
- **Eventos por año**: 1
- **Monto máximo**: $60
- **Uso**: Traslado al aeropuerto internacional
- **Cobertura**: Desde cualquier punto de la ciudad capital

### Asistencia Legal Telefónica
- **Eventos por año**: 1
- **Monto máximo**: $200
- **Uso**: Orientación legal en caso de accidente de tránsito
- **Servicio**: Asesoría de abogado especializado

### Apoyo Económico por Emergencia
- **Eventos por año**: 1
- **Monto máximo**: $1,000
- **Uso**: En caso de lesión grave o fallecimiento del titular por accidente de tránsito
- **Documentación**: Requiere presentar documentos que acrediten el hecho

### Rayos X por Accidente
- **Eventos por año**: 1
- **Monto máximo**: $300
- **Uso**: Estudios de rayos X si resultaste lesionado en accidente de tránsito
- **Red**: En clínicas afiliadas de SegurifAI

### Descuentos en Red de Proveedores
- **Descuento**: 20% en servicios automotrices
- **Red**: Talleres, refaccionarias, y proveedores afiliados
- **Uso**: Presentando tu membresía SegurifAI

## Servicios del Plan Health (Asistencia de Salud)

### Orientación Médica Telefónica
- **Eventos por año**: Ilimitados
- **Disponibilidad**: 24/7, los 365 días
- **Servicio**: Médicos reales responden tus dudas de salud
- **Uso**: Síntomas, dudas sobre medicamentos, qué hacer ante una emergencia

### Conexión con Especialistas
- **Eventos por año**: Ilimitados
- **Servicio**: Te referimos con el especialista adecuado según tu necesidad
- **Especialidades**: Cardiología, dermatología, pediatría, ginecología, etc.

### Consulta Médica Presencial
- **Eventos por año**: 3
- **Monto máximo por evento**: $150
- **Red**: Clínicas y consultorios afiliados a SegurifAI
- **Beneficio**: Medicina general y algunas especialidades

### Coordinación de Medicamentos
- **Eventos por año**: Ilimitados
- **Servicio**: Te ayudamos a localizar medicamentos en farmacias
- **Plus**: Descuentos en farmacias de la red

### Cuidados Post-Operatorios
- **Eventos por año**: 1
- **Monto máximo**: $100
- **Servicio**: Enfermería a domicilio después de una operación
- **Duración**: Visitas según indicación médica

### Exámenes de Laboratorio
- **Eventos por año**: 2
- **Monto máximo por evento**: $100
- **Red**: Laboratorios clínicos afiliados
- **Cobertura**: Exámenes básicos de sangre, orina, etc.

### Nutricionista por Videollamada
- **Eventos por año**: 4
- **Monto máximo por evento**: $150
- **Servicio**: Consultas virtuales con nutricionistas certificados
- **Beneficio**: Plan alimenticio personalizado

### Psicología por Videollamada
- **Eventos por año**: 4
- **Monto máximo por evento**: $150
- **Servicio**: Sesiones virtuales con psicólogos profesionales
- **Confidencialidad**: Total privacidad garantizada

### Ambulancia por Accidente
- **Eventos por año**: 2
- **Monto máximo por evento**: $150
- **Uso**: Cualquier emergencia médica (no solo accidente de tránsito)
- **Servicio**: Traslado al hospital más cercano

### Descuentos en Red Médica
- **Descuento**: 20% en consultas, estudios y procedimientos
- **Red**: Clínicas, hospitales, laboratorios y farmacias afiliados
- **Uso**: Presentando tu membresía SegurifAI

## Cómo Solicitar un Servicio

### A través de la App SegurifAI
1. Abre la app y asegúrate de tener tu sesión iniciada
2. Activa tu ubicación GPS para que te localicemos
3. Selecciona la categoría de servicio (Vial o Salud)
4. Elige el servicio específico que necesitas
5. Confirma tu solicitud
6. Recibe confirmación con tiempo estimado de llegada
7. El proveedor te contactará o llegará a tu ubicación

### Por Teléfono
- Llama a la línea de emergencias SegurifAI
- Ten a la mano tu número de membresía
- Describe tu emergencia
- Proporciona tu ubicación exacta

### Tiempos de Respuesta
- **Áreas urbanas**: 30-45 minutos promedio
- **Áreas rurales**: 45-90 minutos promedio
- **Emergencias médicas**: Prioridad máxima

## Cobertura Geográfica

SegurifAI tiene cobertura en todo el territorio de Guatemala:

**Departamentos con mayor infraestructura**:
- Guatemala (área metropolitana)
- Sacatepéquez (Antigua Guatemala)
- Quetzaltenango
- Escuintla
- Alta Verapaz
- Petén

**Áreas remotas**: La cobertura existe, pero los tiempos de respuesta pueden ser mayores.

## Preguntas Frecuentes

**¿Puedo usar el servicio si no soy el conductor?**
Sí, la membresía cubre al titular y puede usarse incluso si otra persona conduce tu vehículo.

**¿Qué pasa si uso todos mis eventos anuales?**
Puedes solicitar servicios adicionales pagando el costo regular del proveedor.

**¿La membresía se renueva automáticamente?**
Sí, a través de tu suscripción en PAQ Wallet. Puedes cancelar en cualquier momento.

**¿Puedo cambiar de plan?**
Sí, puedes hacer upgrade o downgrade desde la app en cualquier momento.

## Conclusión
SegurifAI es tu red de seguridad tanto en la carretera como en tu salud. Con una pequeña inversión mensual, tienes acceso a servicios que pueden ahorrarte miles de quetzales en emergencias. Recuerda: más vale tenerlo y no necesitarlo, que necesitarlo y no tenerlo.
''',
                    'duracion_minutos': 10,
                    'puntos_completar': 100,
                    'puntos_quiz_perfecto': 50,
                    'credito_completar': 2.00,
                    'credito_quiz_perfecto': 1.00,
                    'orden': 6,
                    'questions': [
                        {
                            'pregunta': '¿Que servicio NO ofrece SegurifAI?',
                            'opcion_a': 'Asistencia vial con grua',
                            'opcion_b': 'Cambio de llanta',
                            'opcion_c': 'Reparacion mecanica completa',
                            'opcion_d': 'Servicio de ambulancia',
                            'respuesta_correcta': 'C',
                            'explicacion': 'SegurifAI ofrece asistencia inmediata pero no reparaciones mecanicas completas. Te llevamos al taller.',
                            'orden': 1
                        },
                        {
                            'pregunta': '¿En que horario esta disponible SegurifAI?',
                            'opcion_a': 'Solo de dia (8am - 6pm)',
                            'opcion_b': 'De lunes a viernes',
                            'opcion_c': '24 horas, 7 dias a la semana',
                            'opcion_d': 'Solo fines de semana',
                            'respuesta_correcta': 'C',
                            'explicacion': 'SegurifAI esta disponible 24/7 para asistirte cuando lo necesites.',
                            'orden': 2
                        },
                        {
                            'pregunta': '¿Como solicitas un servicio de SegurifAI?',
                            'opcion_a': 'Llamando al 911',
                            'opcion_b': 'A traves de la app SegurifAI',
                            'opcion_c': 'Yendo a una oficina',
                            'opcion_d': 'Por correo electronico',
                            'respuesta_correcta': 'B',
                            'explicacion': 'La forma mas rapida es a traves de la app SegurifAI, que detecta tu ubicacion automaticamente.',
                            'orden': 3
                        },
                        {
                            'pregunta': '¿Que incluye la asistencia de salud de SegurifAI?',
                            'opcion_a': 'Solo llamadas telefonicas',
                            'opcion_b': 'Ambulancia y orientacion medica',
                            'opcion_c': 'Solo descuentos en farmacias',
                            'opcion_d': 'Cirugías gratuitas',
                            'respuesta_correcta': 'B',
                            'explicacion': 'SegurifAI ofrece servicio de ambulancia y orientacion medica telefonica 24/7.',
                            'orden': 4
                        },
                        {
                            'pregunta': '¿Donde tiene cobertura SegurifAI en Guatemala?',
                            'opcion_a': 'Solo en la ciudad de Guatemala',
                            'opcion_b': 'Solo en carreteras principales',
                            'opcion_c': 'En todo el territorio guatemalteco',
                            'opcion_d': 'Solo en el area metropolitana',
                            'respuesta_correcta': 'C',
                            'explicacion': 'SegurifAI tiene cobertura en todo Guatemala, no importa donde te encuentres.',
                            'orden': 5
                        }
                    ]
                }
            ]

            # Create modules with questions
            for module_data in modules_data:
                questions_data = module_data.pop('questions')

                module = EducationalModule.objects.create(**module_data)
                self.stdout.write(f'  Created module: {module.titulo}')

                # Create questions for this module
                for question_data in questions_data:
                    QuizQuestion.objects.create(
                        modulo=module,
                        **question_data
                    )

                self.stdout.write(f'    Added {len(questions_data)} questions')

        total_modules = EducationalModule.objects.count()
        total_questions = QuizQuestion.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created {total_modules} modules with {total_questions} questions!'
        ))
