from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_userprofile_structured_prompt'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Crear tabla PromptProfile
        migrations.CreateModel(
            name='PromptProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre del perfil')),
                ('is_active', models.BooleanField(default=False, verbose_name='Activo')),
                ('rol_enabled', models.BooleanField(default=True)),
                ('prompt_rol', models.TextField(blank=True, default='', verbose_name='Rol')),
                ('contexto_enabled', models.BooleanField(default=True)),
                ('prompt_contexto', models.TextField(blank=True, default='', verbose_name='Contexto')),
                ('comportamiento_enabled', models.BooleanField(default=True)),
                ('prompt_comportamiento', models.TextField(blank=True, default='', verbose_name='Comportamiento')),
                ('formato_enabled', models.BooleanField(default=True)),
                ('prompt_formato', models.TextField(blank=True, default='', verbose_name='Formato de respuesta')),
                ('restricciones_enabled', models.BooleanField(default=True)),
                ('prompt_restricciones', models.TextField(blank=True, default='', verbose_name='Restricciones')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='prompt_profiles',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Perfil de prompt',
                'verbose_name_plural': 'Perfiles de prompt',
                'ordering': ['-created_at'],
            },
        ),

        # 2. Migrar datos existentes: si un UserProfile tenía structured prompt, crear un PromptProfile
        migrations.RunPython(
            code=lambda apps, schema_editor: _migrate_prompts(apps, schema_editor),
            reverse_code=migrations.RunPython.noop,
        ),

        # 3. Eliminar campos obsoletos de UserProfile
        migrations.RemoveField(model_name='userprofile', name='system_prompt'),
        migrations.RemoveField(model_name='userprofile', name='use_structured_prompt'),
        migrations.RemoveField(model_name='userprofile', name='prompt_rol'),
        migrations.RemoveField(model_name='userprofile', name='prompt_contexto'),
        migrations.RemoveField(model_name='userprofile', name='prompt_comportamiento'),
        migrations.RemoveField(model_name='userprofile', name='prompt_formato'),
        migrations.RemoveField(model_name='userprofile', name='prompt_restricciones'),
    ]


def _migrate_prompts(apps, schema_editor):
    UserProfile = apps.get_model('chat', 'UserProfile')
    PromptProfile = apps.get_model('chat', 'PromptProfile')

    for profile in UserProfile.objects.select_related('user').all():
        has_content = any([
            profile.prompt_rol.strip(),
            profile.prompt_contexto.strip(),
            profile.prompt_comportamiento.strip(),
            profile.prompt_formato.strip(),
            profile.prompt_restricciones.strip(),
            profile.system_prompt.strip(),
        ])
        if not has_content:
            continue

        # Si tenía prompt estructurado, usar esas secciones; si no, poner en rol
        if profile.use_structured_prompt:
            PromptProfile.objects.create(
                user=profile.user,
                name='Mi prompt',
                is_active=True,
                prompt_rol=profile.prompt_rol,
                prompt_contexto=profile.prompt_contexto,
                prompt_comportamiento=profile.prompt_comportamiento,
                prompt_formato=profile.prompt_formato,
                prompt_restricciones=profile.prompt_restricciones,
            )
        elif profile.system_prompt.strip():
            PromptProfile.objects.create(
                user=profile.user,
                name='Mi prompt',
                is_active=True,
                prompt_rol=profile.system_prompt,
                prompt_contexto='',
                prompt_comportamiento='',
                prompt_formato='',
                prompt_restricciones='',
            )
