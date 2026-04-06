from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    system_prompt = models.TextField(
        blank=True,
        default='',
        verbose_name='Prompt del sistema',
        help_text='Describe cómo quieres que se comporte el asistente. Ej: "Eres un pirata divertido".'
    )
    assistant_name = models.CharField(
        max_length=100,
        default='Asistente',
        verbose_name='Nombre del asistente'
    )
    avatar_emoji = models.CharField(
        max_length=10,
        default='🤖',
        verbose_name='Emoji del asistente'
    )
    # Campos opcionales para workflow n8n personalizado por usuario
    SEX_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('', 'Prefiero no decir'),
    ]
    sex = models.CharField(
        max_length=1,
        blank=True,
        default='',
        choices=SEX_CHOICES,
        verbose_name='Sexo',
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de nacimiento',
    )
    n8n_webhook_url = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='URL webhook n8n personalizada',
        help_text='Dejar vacío para usar el webhook global configurado en .env'
    )
    n8n_workflow_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='ID workflow n8n'
    )

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def get_webhook_url(self):
        """Devuelve el webhook personalizado del usuario o el global como fallback."""
        return self.n8n_webhook_url or settings.N8N_WEBHOOK_URL


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    title = models.CharField(max_length=255, default='Nueva conversación')
    summary = models.TextField(
        blank=True,
        default='',
        verbose_name='Resumen del historial',
        help_text='Resumen comprimido de los turnos anteriores para optimizar tokens.'
    )
    turn_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Contador de turnos'
    )
    messages_json = models.JSONField(
        default=list,
        verbose_name='Mensajes',
        help_text='Lista de mensajes: [{role, content, ts}]'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Conversación'
        verbose_name_plural = 'Conversaciones'

    def __str__(self):
        return f'{self.title} ({self.user.username})'



class UserFact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='facts'
    )
    category = models.CharField(
        max_length=50,
        default='otro',
        verbose_name='Categoría',
        help_text='Ej: amigo, color_favorito, tema, mascota'
    )
    key = models.CharField(
        max_length=100,
        verbose_name='Qué recordar',
        help_text='Ej: "Mejor amigo", "Color favorito"'
    )
    value = models.CharField(
        max_length=255,
        verbose_name='Valor',
        help_text='Ej: "Carlos", "azul"'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'key']
        ordering = ['category', 'key']
        verbose_name = 'Hecho del usuario'
        verbose_name_plural = 'Hechos del usuario'

    def __str__(self):
        return f'{self.key}: {self.value} ({self.user.username})'
