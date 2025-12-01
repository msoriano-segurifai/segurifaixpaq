from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from datetime import date, timedelta

from .models import (
    EducationalModule, QuizQuestion, UserProgress,
    UserPoints, Achievement, UserAchievement,
    UserDiscountCredits, CreditTransaction
)
from .serializers import (
    EducationalModuleListSerializer, EducationalModuleDetailSerializer,
    UserProgressSerializer, SubmitQuizSerializer, QuizResultSerializer,
    UserPointsSerializer, AchievementSerializer, UserAchievementSerializer,
    LeaderboardSerializer
)


class EducationalModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para modulos educativos"""
    queryset = EducationalModule.objects.filter(activo=True)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EducationalModuleDetailSerializer
        return EducationalModuleListSerializer

    def list(self, request, *args, **kwargs):
        """Override list to wrap response in expected format"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'modules': serializer.data})

    @action(detail=True, methods=['post'], url_path='start')
    def iniciar(self, request, pk=None):
        """Iniciar un modulo educativo"""
        modulo = self.get_object()
        user = request.user

        # Get or create progress
        progress, created = UserProgress.objects.get_or_create(
            user=user,
            modulo=modulo,
            defaults={'estado': 'EN_PROGRESO', 'iniciado_en': timezone.now()}
        )

        if not created and progress.estado == 'NO_INICIADO':
            progress.estado = 'EN_PROGRESO'
            progress.iniciado_en = timezone.now()
            progress.save()

        # Update user activity streak
        self._actualizar_racha(user)

        serializer = UserProgressSerializer(progress)
        return Response({
            'success': True,
            'mensaje': f'Modulo "{modulo.titulo}" iniciado',
            'progreso': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='complete')
    def enviar_quiz(self, request, pk=None):
        """Enviar respuestas del quiz"""
        modulo = self.get_object()
        user = request.user

        # Validate input
        serializer = SubmitQuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        respuestas = serializer.validated_data['respuestas']

        # Get all questions for this module
        preguntas = modulo.preguntas.all()
        total_preguntas = preguntas.count()

        if total_preguntas == 0:
            return Response(
                {'error': 'Este modulo no tiene preguntas de quiz'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check answers
        correctas = 0
        detalles = []

        for pregunta in preguntas:
            respuesta_usuario = None
            for r in respuestas:
                if int(r.get('pregunta_id', 0)) == pregunta.id:
                    respuesta_usuario = r.get('respuesta', '').upper()
                    break

            es_correcta = respuesta_usuario == pregunta.respuesta_correcta
            if es_correcta:
                correctas += 1

            detalles.append({
                'pregunta_id': pregunta.id,
                'pregunta': pregunta.pregunta,
                'tu_respuesta': respuesta_usuario,
                'respuesta_correcta': pregunta.respuesta_correcta,
                'es_correcta': es_correcta,
                'explicacion': pregunta.explicacion if not es_correcta else None
            })

        # Calculate points
        porcentaje = int((correctas / total_preguntas) * 100)
        quiz_perfecto = correctas == total_preguntas

        puntos = modulo.puntos_completar
        if quiz_perfecto:
            puntos += modulo.puntos_quiz_perfecto

        # Update progress
        progress, _ = UserProgress.objects.get_or_create(
            user=user,
            modulo=modulo
        )

        # Only award points if not already completed
        puntos_nuevos = 0
        if progress.estado != 'COMPLETADO':
            progress.estado = 'COMPLETADO'
            progress.completado_en = timezone.now()
            progress.puntos_obtenidos = puntos
            puntos_nuevos = puntos

        progress.quiz_completado = True
        progress.respuestas_correctas = correctas
        progress.total_preguntas = total_preguntas
        progress.save()

        # Update user points
        if puntos_nuevos > 0:
            user_points, _ = UserPoints.objects.get_or_create(user=user)
            user_points.puntos_totales += puntos_nuevos
            user_points.modulos_completados += 1
            user_points.actualizar_nivel()

        # Award discount credits (small amounts that accumulate for subscriptions)
        creditos_ganados = 0
        if puntos_nuevos > 0:
            creditos_ganados = self._otorgar_creditos(user, modulo, quiz_perfecto)

        # Check for achievements
        logros_desbloqueados = self._verificar_logros(user)

        # Update streak
        self._actualizar_racha(user)

        # Process rewards and generate promo codes for point milestones
        from .rewards import RewardsService
        recompensas_codigo = []
        if puntos_nuevos > 0:
            recompensas_codigo = RewardsService.process_quiz_completion(user, progress)

        return Response({
            'success': True,
            'resultado': {
                'correctas': correctas,
                'total': total_preguntas,
                'porcentaje': porcentaje,
                'puntos_obtenidos': puntos_nuevos,
                'creditos_ganados': float(creditos_ganados),
                'quiz_perfecto': quiz_perfecto,
                'detalles': detalles,
                'logros_desbloqueados': logros_desbloqueados,
                'recompensas_codigo': recompensas_codigo
            }
        })

    def _actualizar_racha(self, user):
        """Actualiza la racha de dias del usuario"""
        user_points, _ = UserPoints.objects.get_or_create(user=user)
        hoy = date.today()

        if user_points.ultima_actividad:
            diferencia = (hoy - user_points.ultima_actividad).days
            if diferencia == 1:
                user_points.racha_dias += 1
            elif diferencia > 1:
                user_points.racha_dias = 1
            # If same day, don't change streak
        else:
            user_points.racha_dias = 1

        user_points.ultima_actividad = hoy
        user_points.save()

    def _verificar_logros(self, user):
        """Verifica y otorga logros desbloqueados"""
        logros_nuevos = []
        user_points = UserPoints.objects.filter(user=user).first()

        if not user_points:
            return logros_nuevos

        logros_disponibles = Achievement.objects.filter(activo=True)

        for logro in logros_disponibles:
            # Skip if already obtained
            if UserAchievement.objects.filter(user=user, achievement=logro).exists():
                continue

            # Evaluate condition
            desbloqueado = False
            try:
                if 'modulos_completados' in logro.condicion:
                    desbloqueado = eval(logro.condicion, {'modulos_completados': user_points.modulos_completados})
                elif 'puntos_totales' in logro.condicion:
                    desbloqueado = eval(logro.condicion, {'puntos_totales': user_points.puntos_totales})
                elif 'racha_dias' in logro.condicion:
                    desbloqueado = eval(logro.condicion, {'racha_dias': user_points.racha_dias})
            except Exception:
                pass

            if desbloqueado:
                UserAchievement.objects.create(user=user, achievement=logro)
                user_points.puntos_totales += logro.puntos_bonus
                user_points.save()
                logros_nuevos.append({
                    'nombre': logro.nombre,
                    'descripcion': logro.descripcion,
                    'icono': logro.icono,
                    'puntos_bonus': logro.puntos_bonus
                })

        return logros_nuevos

    def _otorgar_creditos(self, user, modulo, quiz_perfecto=False):
        """
        Award discount credits when completing a module.

        Credits are small amounts (Q1-Q3) that accumulate towards
        the next subscription payment.
        """
        from decimal import Decimal

        # Get or create user's credit account
        creditos, _ = UserDiscountCredits.objects.get_or_create(user=user)

        # Calculate credits to award
        credito_base = modulo.credito_completar or Decimal('2.00')
        credito_total = credito_base

        descripcion = f'Modulo completado: {modulo.titulo}'

        if quiz_perfecto:
            credito_bonus = modulo.credito_quiz_perfecto or Decimal('1.00')
            credito_total += credito_bonus
            descripcion += ' (Quiz Perfecto)'

        # Add credit to user's balance
        creditos.agregar_credito(
            monto=credito_total,
            descripcion=descripcion,
            modulo=modulo
        )

        return credito_total


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_progreso(request):
    """Obtener progreso del usuario actual"""
    user = request.user

    # Get or create user points
    user_points, _ = UserPoints.objects.get_or_create(user=user)

    # Get all progress
    progresos = UserProgress.objects.filter(user=user).select_related('modulo')

    # Get achievements
    logros = UserAchievement.objects.filter(user=user).select_related('achievement')

    # Calculate stats
    total_modulos = EducationalModule.objects.filter(activo=True).count()
    completados = progresos.filter(estado='COMPLETADO').count()

    return Response({
        'puntos': UserPointsSerializer(user_points).data,
        'estadisticas': {
            'modulos_totales': total_modulos,
            'modulos_completados': completados,
            'porcentaje_completado': int((completados / total_modulos * 100)) if total_modulos > 0 else 0
        },
        'progresos': UserProgressSerializer(progresos, many=True).data,
        'logros': UserAchievementSerializer(logros, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    """Tabla de posiciones"""
    limit = int(request.query_params.get('limit', 10))

    top_users = UserPoints.objects.order_by('-puntos_totales')[:limit]

    resultado = []
    for i, up in enumerate(top_users, 1):
        resultado.append({
            'posicion': i,
            'usuario': up.user.first_name or up.user.email.split('@')[0],
            'puntos': up.puntos_totales,
            'nivel': up.get_nivel_display(),
            'modulos_completados': up.modulos_completados
        })

    # Find current user position
    user_points = UserPoints.objects.filter(user=request.user).first()
    mi_posicion = None
    if user_points:
        mi_posicion = UserPoints.objects.filter(
            puntos_totales__gt=user_points.puntos_totales
        ).count() + 1

    return Response({
        'tabla': resultado,
        'mi_posicion': mi_posicion
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logros_disponibles(request):
    """Lista todos los logros disponibles"""
    logros = Achievement.objects.filter(activo=True)
    serializer = AchievementSerializer(logros, many=True, context={'request': request})
    return Response(serializer.data)


# ============================================
# Discount Credits API Endpoints
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_creditos(request):
    """
    Get user's accumulated e-learning discount credits.

    GET /api/gamification/creditos/

    Returns the user's credit balance and usage statistics.
    """
    user = request.user

    # Get or create credit account
    creditos, created = UserDiscountCredits.objects.get_or_create(user=user)

    return Response({
        'saldo_disponible': float(creditos.saldo_disponible),
        'total_acumulado': float(creditos.total_acumulado),
        'total_usado': float(creditos.total_usado),
        'ultimo_uso': creditos.ultimo_uso.isoformat() if creditos.ultimo_uso else None,
        'currency': 'GTQ',
        'descripcion': 'Creditos acumulados por completar modulos educativos. Se aplican automaticamente en tu proxima suscripcion.'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_creditos(request):
    """
    Get user's credit transaction history.

    GET /api/gamification/creditos/historial/

    Query params:
    - limit: Number of transactions to return (default 20)
    - tipo: Filter by type (GANADO, USADO, EXPIRADO, AJUSTE)
    """
    user = request.user
    limit = int(request.query_params.get('limit', 20))
    tipo = request.query_params.get('tipo')

    try:
        creditos = UserDiscountCredits.objects.get(user=user)
    except UserDiscountCredits.DoesNotExist:
        return Response({
            'transacciones': [],
            'count': 0,
            'saldo_actual': 0
        })

    # Get transactions
    transacciones = creditos.transacciones.all()

    if tipo:
        transacciones = transacciones.filter(tipo=tipo.upper())

    transacciones = transacciones[:limit]

    return Response({
        'transacciones': [
            {
                'id': t.id,
                'tipo': t.tipo,
                'monto': float(t.monto),
                'descripcion': t.descripcion,
                'modulo': t.modulo.titulo if t.modulo else None,
                'saldo_despues': float(t.saldo_despues) if t.saldo_despues else None,
                'fecha': t.created_at.isoformat()
            }
            for t in transacciones
        ],
        'count': transacciones.count() if hasattr(transacciones, 'count') else len(transacciones),
        'saldo_actual': float(creditos.saldo_disponible)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumen_creditos(request):
    """
    Get a summary of credits earned from e-learning modules.

    GET /api/gamification/creditos/resumen/

    Returns summary statistics about credit earnings.
    """
    user = request.user

    try:
        creditos = UserDiscountCredits.objects.get(user=user)
    except UserDiscountCredits.DoesNotExist:
        return Response({
            'saldo_disponible': 0,
            'modulos_completados': 0,
            'creditos_por_modulo': [],
            'proximo_credito': None
        })

    # Get completed modules and their credits
    progresos = UserProgress.objects.filter(
        user=user,
        estado='COMPLETADO'
    ).select_related('modulo')

    creditos_por_modulo = []
    for p in progresos:
        credito_ganado = p.modulo.credito_completar
        if p.respuestas_correctas == p.total_preguntas and p.total_preguntas > 0:
            credito_ganado += p.modulo.credito_quiz_perfecto

        creditos_por_modulo.append({
            'modulo': p.modulo.titulo,
            'credito': float(credito_ganado),
            'quiz_perfecto': p.respuestas_correctas == p.total_preguntas,
            'completado_en': p.completado_en.isoformat() if p.completado_en else None
        })

    # Find next available module
    proximo_modulo = EducationalModule.objects.filter(
        activo=True
    ).exclude(
        id__in=[p.modulo_id for p in progresos]
    ).order_by('orden').first()

    return Response({
        'saldo_disponible': float(creditos.saldo_disponible),
        'total_acumulado': float(creditos.total_acumulado),
        'modulos_completados': len(creditos_por_modulo),
        'creditos_por_modulo': creditos_por_modulo,
        'proximo_credito': {
            'modulo': proximo_modulo.titulo,
            'credito_base': float(proximo_modulo.credito_completar),
            'credito_quiz_perfecto': float(proximo_modulo.credito_quiz_perfecto)
        } if proximo_modulo else None,
        'currency': 'GTQ'
    })


# ============================================
# Test/Admin Gamification Reset Endpoint
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_gamification(request):
    """
    Reset gamification data for a test user (admin or self-reset only).

    POST /api/gamification/reset/

    Body:
    {
        "user_id": "30082653" (optional - defaults to current user)
    }

    This endpoint:
    - Resets XP to 0
    - Resets level to 1
    - Resets streak to 0
    - Removes all achievements
    - Removes all module progress
    - Resets discount credits to 0

    Only admins can reset other users. Regular users can only reset themselves.
    """
    from decimal import Decimal
    from django.contrib.auth import get_user_model
    User = get_user_model()

    user = request.user
    target_user_id = request.data.get('user_id')

    # Determine target user
    if target_user_id:
        # Only admins can reset other users
        if not user.is_staff and not user.is_superuser:
            # Allow self-reset by phone number
            if target_user_id != user.phone_number and target_user_id != str(user.id):
                return Response(
                    {'error': 'Solo administradores pueden resetear otros usuarios'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Find target user by phone or ID
        try:
            target_user = User.objects.get(phone_number=target_user_id)
        except User.DoesNotExist:
            try:
                target_user = User.objects.get(id=target_user_id)
            except (User.DoesNotExist, ValueError):
                return Response(
                    {'error': 'Usuario no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
    else:
        target_user = user

    # Reset user points
    user_points, created = UserPoints.objects.get_or_create(user=target_user)
    user_points.puntos_totales = 0
    user_points.nivel = 'PRINCIPIANTE'
    user_points.racha_dias = 0
    user_points.modulos_completados = 0
    user_points.ultima_actividad = None
    user_points.save()

    # Delete all user progress
    progress_deleted = UserProgress.objects.filter(user=target_user).delete()[0]

    # Delete all user achievements
    achievements_deleted = UserAchievement.objects.filter(user=target_user).delete()[0]

    # Reset discount credits
    credits_reset = False
    try:
        creditos = UserDiscountCredits.objects.get(user=target_user)
        creditos.saldo_disponible = Decimal('0.00')
        creditos.total_acumulado = Decimal('0.00')
        creditos.total_usado = Decimal('0.00')
        creditos.ultimo_uso = None
        creditos.save()
        # Delete credit transactions
        CreditTransaction.objects.filter(creditos=creditos).delete()
        credits_reset = True
    except UserDiscountCredits.DoesNotExist:
        pass

    # Reset UserReward (earned promo codes from gamification)
    from .models import UserReward
    rewards_deleted = UserReward.objects.filter(user=target_user).delete()[0]

    # Reset promo code usage for this user (from promotions app)
    promo_usage_deleted = 0
    try:
        from apps.promotions.models import PromoCodeUsage
        promo_usage_deleted = PromoCodeUsage.objects.filter(user=target_user).delete()[0]
    except Exception:
        pass  # Promotions app might not be available

    return Response({
        'success': True,
        'message': f'Gamificacion reseteada para usuario {target_user.phone_number or target_user.email}',
        'reset_summary': {
            'user_id': target_user.id,
            'phone': target_user.phone_number,
            'xp': 0,
            'level': 'PRINCIPIANTE',
            'streak': 0,
            'progress_deleted': progress_deleted,
            'achievements_deleted': achievements_deleted,
            'credits_reset': credits_reset,
            'rewards_deleted': rewards_deleted,
            'promo_usage_deleted': promo_usage_deleted
        }
    })
