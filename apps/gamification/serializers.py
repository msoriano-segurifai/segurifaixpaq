from rest_framework import serializers
from .models import (
    EducationalModule, QuizQuestion, UserProgress,
    UserPoints, Achievement, UserAchievement
)


class QuizQuestionSerializer(serializers.ModelSerializer):
    """Serializer para preguntas de quiz (sin respuesta correcta)"""

    class Meta:
        model = QuizQuestion
        fields = ['id', 'pregunta', 'opcion_a', 'opcion_b', 'opcion_c', 'opcion_d', 'orden']


class QuizQuestionWithAnswerSerializer(serializers.ModelSerializer):
    """Serializer para preguntas con respuesta (solo para verificacion)"""

    class Meta:
        model = QuizQuestion
        fields = ['id', 'pregunta', 'opcion_a', 'opcion_b', 'opcion_c', 'opcion_d',
                  'respuesta_correcta', 'explicacion', 'orden']


class EducationalModuleListSerializer(serializers.ModelSerializer):
    """Serializer para lista de modulos"""
    total_preguntas = serializers.SerializerMethodField()
    completado = serializers.SerializerMethodField()

    class Meta:
        model = EducationalModule
        fields = ['id', 'titulo', 'descripcion', 'categoria', 'dificultad',
                  'imagen_url', 'duracion_minutos', 'puntos_completar',
                  'orden', 'total_preguntas', 'completado']

    def get_total_preguntas(self, obj):
        return obj.preguntas.count()

    def get_completado(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = obj.progresos.filter(user=request.user).first()
            return progress.estado == 'COMPLETADO' if progress else False
        return False


class EducationalModuleDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de modulo con contenido"""
    preguntas = QuizQuestionSerializer(many=True, read_only=True)
    total_preguntas = serializers.SerializerMethodField()
    progreso_usuario = serializers.SerializerMethodField()

    class Meta:
        model = EducationalModule
        fields = ['id', 'titulo', 'descripcion', 'categoria', 'dificultad',
                  'contenido', 'imagen_url', 'video_url', 'duracion_minutos',
                  'puntos_completar', 'puntos_quiz_perfecto', 'orden',
                  'total_preguntas', 'preguntas', 'progreso_usuario']

    def get_total_preguntas(self, obj):
        return obj.preguntas.count()

    def get_progreso_usuario(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = obj.progresos.filter(user=request.user).first()
            if progress:
                return {
                    'estado': progress.estado,
                    'quiz_completado': progress.quiz_completado,
                    'puntos_obtenidos': progress.puntos_obtenidos,
                    'porcentaje_quiz': progress.porcentaje_quiz
                }
        return None


class UserProgressSerializer(serializers.ModelSerializer):
    """Serializer para progreso del usuario"""
    modulo_titulo = serializers.CharField(source='modulo.titulo', read_only=True)
    porcentaje_quiz = serializers.ReadOnlyField()

    class Meta:
        model = UserProgress
        fields = ['id', 'modulo', 'modulo_titulo', 'estado', 'quiz_completado',
                  'respuestas_correctas', 'total_preguntas', 'puntos_obtenidos',
                  'porcentaje_quiz', 'iniciado_en', 'completado_en']
        read_only_fields = ['puntos_obtenidos', 'iniciado_en', 'completado_en']


class SubmitQuizSerializer(serializers.Serializer):
    """Serializer para enviar respuestas del quiz"""
    respuestas = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        help_text='Lista de respuestas: [{"pregunta_id": 1, "respuesta": "A"}, ...]'
    )


class QuizResultSerializer(serializers.Serializer):
    """Serializer para resultado del quiz"""
    correctas = serializers.IntegerField()
    total = serializers.IntegerField()
    porcentaje = serializers.IntegerField()
    puntos_obtenidos = serializers.IntegerField()
    quiz_perfecto = serializers.BooleanField()
    detalles = serializers.ListField(child=serializers.DictField())
    logros_desbloqueados = serializers.ListField(child=serializers.DictField())


class UserPointsSerializer(serializers.ModelSerializer):
    """Serializer para puntos del usuario"""
    nivel_display = serializers.CharField(source='get_nivel_display', read_only=True)
    siguiente_nivel = serializers.SerializerMethodField()
    puntos_para_siguiente = serializers.SerializerMethodField()

    class Meta:
        model = UserPoints
        fields = ['puntos_totales', 'nivel', 'nivel_display', 'modulos_completados',
                  'racha_dias', 'ultima_actividad', 'siguiente_nivel', 'puntos_para_siguiente']

    def get_siguiente_nivel(self, obj):
        niveles = {
            'NOVATO': ('APRENDIZ', 100),
            'APRENDIZ': ('CONOCEDOR', 250),
            'CONOCEDOR': ('EXPERTO', 500),
            'EXPERTO': ('MAESTRO', 1000),
            'MAESTRO': (None, None)
        }
        siguiente = niveles.get(obj.nivel, (None, None))
        return siguiente[0]

    def get_puntos_para_siguiente(self, obj):
        niveles = {
            'NOVATO': 100,
            'APRENDIZ': 250,
            'CONOCEDOR': 500,
            'EXPERTO': 1000,
            'MAESTRO': None
        }
        puntos_requeridos = niveles.get(obj.nivel)
        if puntos_requeridos:
            return max(0, puntos_requeridos - obj.puntos_totales)
        return 0


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer para logros"""
    obtenido = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = ['id', 'nombre', 'descripcion', 'icono', 'puntos_bonus', 'obtenido']

    def get_obtenido(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.usuarios.filter(user=request.user).exists()
        return False


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer para logros del usuario"""
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ['id', 'achievement', 'obtenido_en']


class LeaderboardSerializer(serializers.Serializer):
    """Serializer para tabla de posiciones"""
    posicion = serializers.IntegerField()
    usuario = serializers.CharField()
    puntos = serializers.IntegerField()
    nivel = serializers.CharField()
    modulos_completados = serializers.IntegerField()
