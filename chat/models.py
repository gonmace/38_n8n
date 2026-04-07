from django.conf import settings
from django.db import models


class PromptProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prompt_profiles'
    )
    name = models.CharField(max_length=100, verbose_name='Nombre del perfil')
    is_active = models.BooleanField(default=False, verbose_name='Activo')

    rol_enabled = models.BooleanField(default=True)
    rol_label = models.CharField(max_length=50, default='ROL')
    prompt_rol = models.TextField(blank=True, default='')

    contexto_enabled = models.BooleanField(default=True)
    contexto_label = models.CharField(max_length=50, default='CONTEXTO')
    prompt_contexto = models.TextField(blank=True, default='')

    comportamiento_enabled = models.BooleanField(default=True)
    comportamiento_label = models.CharField(max_length=50, default='OBJETIVO')
    prompt_comportamiento = models.TextField(blank=True, default='')

    formato_enabled = models.BooleanField(default=True)
    formato_label = models.CharField(max_length=50, default='ESTILO')
    prompt_formato = models.TextField(blank=True, default='')

    restricciones_enabled = models.BooleanField(default=True)
    restricciones_label = models.CharField(max_length=50, default='REGLAS')
    prompt_restricciones = models.TextField(blank=True, default='')

    excepciones_enabled = models.BooleanField(default=True)
    excepciones_label = models.CharField(max_length=50, default='EXCEPCIONES')
    prompt_excepciones = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Perfil de prompt'
        verbose_name_plural = 'Perfiles de prompt'

    def __str__(self):
        return f'{self.name} ({self.user.username})'

    def build_prompt_text(self):
        """Construye el texto del prompt a partir de las secciones activas."""
        SECTIONS = [
            ('rol_enabled', 'rol_label', 'prompt_rol'),
            ('contexto_enabled', 'contexto_label', 'prompt_contexto'),
            ('comportamiento_enabled', 'comportamiento_label', 'prompt_comportamiento'),
            ('formato_enabled', 'formato_label', 'prompt_formato'),
            ('restricciones_enabled', 'restricciones_label', 'prompt_restricciones'),
            ('excepciones_enabled', 'excepciones_label', 'prompt_excepciones'),
        ]
        parts = []
        for enabled_f, label_f, text_f in SECTIONS:
            if getattr(self, enabled_f) and getattr(self, text_f).strip():
                label = getattr(self, label_f).strip().upper() or label_f.replace('_label', '').upper()
                parts.append(f'## {label}\n{getattr(self, text_f).strip()}')
        return '\n\n'.join(parts)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
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
