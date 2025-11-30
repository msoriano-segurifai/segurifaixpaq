from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class EducationalModule(models.Model):
    """Modulo educativo para usuarios"""

    class Difficulty(models.TextChoices):
        PRINCIPIANTE = 'PRINCIPIANTE', _('Principiante')
        INTERMEDIO = 'INTERMEDIO', _('Intermedio')
        AVANZADO = 'AVANZADO', _('Avanzado')

    class Category(models.TextChoices):
        SEGURIDAD_VIAL = 'SEGURIDAD_VIAL', _('Seguridad Vial')
        PRIMEROS_AUXILIOS = 'PRIMEROS_AUXILIOS', _('Primeros Auxilios')
        FINANZAS_PERSONALES = 'FINANZAS_PERSONALES', _('Finanzas Personales')
        PREVENCION = 'PREVENCION', _('Prevencion')

    # Basic info
    titulo = models.CharField(_('titulo'), max_length=200)
    descripcion = models.TextField(_('descripcion'))
    categoria = models.CharField(
        _('categoria'),
        max_length=30,
        choices=Category.choices
    )
    dificultad = models.CharField(
        _('dificultad'),
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.PRINCIPIANTE
    )

    # Content
    contenido = models.TextField(
        _('contenido'),
        help_text='Contenido educativo en formato markdown'
    )
    imagen_url = models.URLField(_('imagen URL'), blank=True)
    video_url = models.URLField(_('video URL'), blank=True)
    duracion_minutos = models.PositiveIntegerField(
        _('duracion en minutos'),
        default=10
    )

    # Gamification
    puntos_completar = models.PositiveIntegerField(
        _('puntos al completar'),
        default=100
    )
    puntos_quiz_perfecto = models.PositiveIntegerField(
        _('puntos quiz perfecto'),
        default=50,
        help_text='Puntos extra por responder todas las preguntas correctamente'
    )

    # Discount credits (small amounts that accumulate for next subscription)
    credito_completar = models.DecimalField(
        _('credito al completar'),
        max_digits=5,
        decimal_places=2,
        default=2.00,
        help_text='Creditos (GTQ) otorgados al completar el modulo'
    )
    credito_quiz_perfecto = models.DecimalField(
        _('credito quiz perfecto'),
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text='Creditos extra por quiz perfecto'
    )

    # Order and status
    orden = models.PositiveIntegerField(_('orden'), default=0)
    activo = models.BooleanField(_('activo'), default=True)

    created_at = models.DateTimeField(_('creado'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado'), auto_now=True)

    class Meta:
        verbose_name = _('modulo educativo')
        verbose_name_plural = _('modulos educativos')
        ordering = ['orden', 'id']

    def __str__(self):
        return f'{self.titulo} ({self.get_dificultad_display()})'


class QuizQuestion(models.Model):
    """Preguntas de quiz para cada modulo"""

    modulo = models.ForeignKey(
        EducationalModule,
        on_delete=models.CASCADE,
        related_name='preguntas',
        verbose_name=_('modulo')
    )
    pregunta = models.TextField(_('pregunta'))
    opcion_a = models.CharField(_('opcion A'), max_length=255)
    opcion_b = models.CharField(_('opcion B'), max_length=255)
    opcion_c = models.CharField(_('opcion C'), max_length=255)
    opcion_d = models.CharField(_('opcion D'), max_length=255, blank=True)
    respuesta_correcta = models.CharField(
        _('respuesta correcta'),
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    explicacion = models.TextField(
        _('explicacion'),
        blank=True,
        help_text='Explicacion de por que esta respuesta es correcta'
    )
    orden = models.PositiveIntegerField(_('orden'), default=0)

    class Meta:
        verbose_name = _('pregunta de quiz')
        verbose_name_plural = _('preguntas de quiz')
        ordering = ['orden']

    def __str__(self):
        return f'{self.modulo.titulo} - Pregunta {self.orden}'


class UserProgress(models.Model):
    """Progreso del usuario en modulos educativos"""

    class Status(models.TextChoices):
        NO_INICIADO = 'NO_INICIADO', _('No Iniciado')
        EN_PROGRESO = 'EN_PROGRESO', _('En Progreso')
        COMPLETADO = 'COMPLETADO', _('Completado')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progreso_educativo',
        verbose_name=_('usuario')
    )
    modulo = models.ForeignKey(
        EducationalModule,
        on_delete=models.CASCADE,
        related_name='progresos',
        verbose_name=_('modulo')
    )
    estado = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.NO_INICIADO
    )

    # Quiz results
    quiz_completado = models.BooleanField(_('quiz completado'), default=False)
    respuestas_correctas = models.PositiveIntegerField(
        _('respuestas correctas'),
        default=0
    )
    total_preguntas = models.PositiveIntegerField(
        _('total preguntas'),
        default=0
    )
    puntos_obtenidos = models.PositiveIntegerField(
        _('puntos obtenidos'),
        default=0
    )

    # Timestamps
    iniciado_en = models.DateTimeField(_('iniciado en'), null=True, blank=True)
    completado_en = models.DateTimeField(_('completado en'), null=True, blank=True)

    class Meta:
        verbose_name = _('progreso de usuario')
        verbose_name_plural = _('progresos de usuarios')
        unique_together = ['user', 'modulo']

    def __str__(self):
        return f'{self.user.email} - {self.modulo.titulo}'

    @property
    def porcentaje_quiz(self):
        if self.total_preguntas == 0:
            return 0
        return int((self.respuestas_correctas / self.total_preguntas) * 100)


class UserPoints(models.Model):
    """Puntos totales y nivel del usuario"""

    class Level(models.TextChoices):
        NOVATO = 'NOVATO', _('Novato')
        APRENDIZ = 'APRENDIZ', _('Aprendiz')
        CONOCEDOR = 'CONOCEDOR', _('Conocedor')
        EXPERTO = 'EXPERTO', _('Experto')
        MAESTRO = 'MAESTRO', _('Maestro')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='puntos',
        verbose_name=_('usuario')
    )
    puntos_totales = models.PositiveIntegerField(
        _('puntos totales'),
        default=0
    )
    nivel = models.CharField(
        _('nivel'),
        max_length=20,
        choices=Level.choices,
        default=Level.NOVATO
    )
    modulos_completados = models.PositiveIntegerField(
        _('modulos completados'),
        default=0
    )
    racha_dias = models.PositiveIntegerField(
        _('racha de dias'),
        default=0,
        help_text='Dias consecutivos de actividad'
    )
    ultima_actividad = models.DateField(
        _('ultima actividad'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('puntos de usuario')
        verbose_name_plural = _('puntos de usuarios')

    def __str__(self):
        return f'{self.user.email} - {self.puntos_totales} pts ({self.get_nivel_display()})'

    def actualizar_nivel(self):
        """Actualiza el nivel basado en puntos totales"""
        if self.puntos_totales >= 1000:
            self.nivel = self.Level.MAESTRO
        elif self.puntos_totales >= 500:
            self.nivel = self.Level.EXPERTO
        elif self.puntos_totales >= 250:
            self.nivel = self.Level.CONOCEDOR
        elif self.puntos_totales >= 100:
            self.nivel = self.Level.APRENDIZ
        else:
            self.nivel = self.Level.NOVATO
        self.save()


class Achievement(models.Model):
    """Logros desbloqueables"""

    nombre = models.CharField(_('nombre'), max_length=100)
    descripcion = models.TextField(_('descripcion'))
    icono = models.CharField(
        _('icono'),
        max_length=50,
        default='trophy',
        help_text='Nombre del icono (ej: trophy, star, medal)'
    )
    puntos_bonus = models.PositiveIntegerField(
        _('puntos bonus'),
        default=25
    )
    condicion = models.CharField(
        _('condicion'),
        max_length=100,
        help_text='Condicion para desbloquear (ej: modulos_completados >= 3)'
    )
    activo = models.BooleanField(_('activo'), default=True)

    class Meta:
        verbose_name = _('logro')
        verbose_name_plural = _('logros')

    def __str__(self):
        return self.nombre


class UserAchievement(models.Model):
    """Logros obtenidos por usuarios"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='logros',
        verbose_name=_('usuario')
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='usuarios',
        verbose_name=_('logro')
    )
    obtenido_en = models.DateTimeField(_('obtenido en'), auto_now_add=True)

    class Meta:
        verbose_name = _('logro de usuario')
        verbose_name_plural = _('logros de usuarios')
        unique_together = ['user', 'achievement']

    def __str__(self):
        return f'{self.user.email} - {self.achievement.nombre}'


class UserDiscountCredits(models.Model):
    """
    Accumulated discount credits from completing e-learning modules.

    Credits accumulate and apply to the NEXT subscription payment.
    Credits are small (Q1-Q5 per module) and capped at subscription total.

    Business Rules:
    - Each module completion gives a small credit (default Q2)
    - Perfect quiz gives bonus credit (default Q1)
    - Credits accumulate until next subscription payment
    - Credits cannot exceed subscription total
    - Credits reset after being applied
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='creditos_descuento',
        verbose_name=_('usuario')
    )
    saldo_disponible = models.DecimalField(
        _('saldo disponible'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Creditos acumulados disponibles para usar'
    )
    total_acumulado = models.DecimalField(
        _('total acumulado historico'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Total de creditos ganados historicamente'
    )
    total_usado = models.DecimalField(
        _('total usado'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Total de creditos usados en pagos'
    )
    ultimo_uso = models.DateTimeField(
        _('ultimo uso'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('creditos de descuento')
        verbose_name_plural = _('creditos de descuento')

    def __str__(self):
        return f'{self.user.email} - Q{self.saldo_disponible} disponibles'

    def agregar_credito(self, monto, descripcion='', modulo=None):
        """Add credit to user's balance"""
        from decimal import Decimal
        monto = Decimal(str(monto))
        self.saldo_disponible += monto
        self.total_acumulado += monto
        self.save()

        # Log the transaction
        CreditTransaction.objects.create(
            user_credits=self,
            tipo='GANADO',
            monto=monto,
            descripcion=descripcion,
            modulo=modulo
        )
        return self.saldo_disponible

    def usar_credito(self, monto_maximo, monto_suscripcion):
        """
        Use credits towards subscription payment.
        Returns actual amount to discount (capped at subscription total).
        """
        from decimal import Decimal
        from django.utils import timezone

        monto_maximo = Decimal(str(monto_maximo))
        monto_suscripcion = Decimal(str(monto_suscripcion))

        # Cap: cannot exceed subscription amount or available balance
        monto_usar = min(self.saldo_disponible, monto_maximo, monto_suscripcion)

        if monto_usar > 0:
            self.saldo_disponible -= monto_usar
            self.total_usado += monto_usar
            self.ultimo_uso = timezone.now()
            self.save()

            # Log the transaction
            CreditTransaction.objects.create(
                user_credits=self,
                tipo='USADO',
                monto=monto_usar,
                descripcion=f'Aplicado a suscripcion (Q{monto_suscripcion})'
            )

        return monto_usar


class CreditTransaction(models.Model):
    """Log of all credit transactions (earned and used)"""

    class TipoTransaccion(models.TextChoices):
        GANADO = 'GANADO', _('Credito Ganado')
        USADO = 'USADO', _('Credito Usado')
        EXPIRADO = 'EXPIRADO', _('Credito Expirado')
        AJUSTE = 'AJUSTE', _('Ajuste Manual')

    user_credits = models.ForeignKey(
        UserDiscountCredits,
        on_delete=models.CASCADE,
        related_name='transacciones',
        verbose_name=_('creditos de usuario')
    )
    tipo = models.CharField(
        _('tipo'),
        max_length=20,
        choices=TipoTransaccion.choices
    )
    monto = models.DecimalField(
        _('monto'),
        max_digits=10,
        decimal_places=2
    )
    descripcion = models.CharField(_('descripcion'), max_length=255, blank=True)
    modulo = models.ForeignKey(
        EducationalModule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='creditos_otorgados',
        verbose_name=_('modulo')
    )
    saldo_despues = models.DecimalField(
        _('saldo despues'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('creado en'), auto_now_add=True)

    class Meta:
        verbose_name = _('transaccion de credito')
        verbose_name_plural = _('transacciones de credito')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Capture balance after transaction
        if self.user_credits_id:
            self.saldo_despues = self.user_credits.saldo_disponible
        super().save(*args, **kwargs)

    def __str__(self):
        signo = '+' if self.tipo == 'GANADO' else '-'
        return f'{signo}Q{self.monto} - {self.descripcion}'


class UserReward(models.Model):
    """
    Tracks promo code rewards earned through gamification.

    Rewards are given for:
    - Reaching point thresholds (100, 250, 500, 1000 points)
    - Special achievements (first module, perfect quiz, etc.)
    """

    class RewardType(models.TextChoices):
        POINT_THRESHOLD = 'POINT_THRESHOLD', _('Umbral de Puntos')
        ACHIEVEMENT = 'ACHIEVEMENT', _('Logro')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gamification_rewards',
        verbose_name=_('usuario')
    )
    reward_type = models.CharField(
        _('tipo de recompensa'),
        max_length=20,
        choices=RewardType.choices
    )

    # For point threshold rewards
    threshold = models.PositiveIntegerField(
        _('umbral de puntos'),
        null=True,
        blank=True
    )

    # For achievement rewards
    achievement_key = models.CharField(
        _('clave de logro'),
        max_length=50,
        blank=True
    )

    # Link to generated promo code
    promo_code = models.ForeignKey(
        'promotions.PromoCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gamification_rewards',
        verbose_name=_('codigo promocional')
    )

    # Additional reward data
    reward_data = models.JSONField(
        _('datos de recompensa'),
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(_('creado en'), auto_now_add=True)

    class Meta:
        verbose_name = _('recompensa de usuario')
        verbose_name_plural = _('recompensas de usuarios')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'reward_type']),
            models.Index(fields=['user', 'threshold']),
        ]

    def __str__(self):
        if self.reward_type == self.RewardType.POINT_THRESHOLD:
            return f'{self.user.email} - {self.threshold} puntos'
        return f'{self.user.email} - {self.achievement_key}'
