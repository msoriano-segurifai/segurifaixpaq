from django.contrib import admin
from .models import (
    EducationalModule, QuizQuestion, UserProgress,
    UserPoints, Achievement, UserAchievement
)


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1


@admin.register(EducationalModule)
class EducationalModuleAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'dificultad', 'puntos_completar', 'activo', 'orden']
    list_filter = ['categoria', 'dificultad', 'activo']
    search_fields = ['titulo', 'descripcion']
    ordering = ['orden']
    inlines = [QuizQuestionInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['modulo', 'pregunta', 'respuesta_correcta', 'orden']
    list_filter = ['modulo']
    search_fields = ['pregunta']


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'modulo', 'estado', 'quiz_completado', 'puntos_obtenidos']
    list_filter = ['estado', 'quiz_completado']
    search_fields = ['user__email', 'modulo__titulo']


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ['user', 'puntos_totales', 'nivel', 'modulos_completados', 'racha_dias']
    list_filter = ['nivel']
    search_fields = ['user__email']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'puntos_bonus', 'activo']
    list_filter = ['activo']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'obtenido_en']
    list_filter = ['achievement']
    search_fields = ['user__email']
