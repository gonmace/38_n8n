import json
import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import UserFactForm, UserProfileForm
from .models import Conversation, PromptProfile, UserFact, UserProfile

logger = logging.getLogger(__name__)

TURNS_BEFORE_SUMMARY = 5
DEFAULT_SYSTEM_PROMPT = 'Eres un asistente amigable y educativo.'


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _build_user_context(user, profile):
    """Genera el bloque de contexto del usuario: datos básicos + hechos memorizados.
    Omite campos vacíos y deduplica contra UserFacts existentes."""
    from datetime import date
    facts = list(UserFact.objects.filter(user=user))
    fact_keys = {f.key.lower() for f in facts}
    lines = []

    name = user.first_name.strip() if user.first_name else user.username
    if 'nombre' not in fact_keys:
        lines.append(f'- Nombre: {name}')

    sex_map = {'M': 'Masculino', 'F': 'Femenino', 'O': 'Otro'}
    if profile.sex in sex_map and 'sexo' not in fact_keys:
        lines.append(f'- Sexo: {sex_map[profile.sex]}')

    if profile.birth_date and 'edad' not in fact_keys:
        today = date.today()
        age = today.year - profile.birth_date.year - (
            (today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)
        )
        lines.append(f'- Edad: {age} años')

    for fact in facts:
        lines.append(f'- {fact.key}: {fact.value}')

    return '\n'.join(lines)


def _build_system_prompt(profile, user):
    """Construye el system prompt: solo las secciones del perfil activo."""
    active = PromptProfile.objects.filter(user=user, is_active=True).first()
    return (active.build_prompt_text() if active else '') or DEFAULT_SYSTEM_PROMPT


@login_required
def conversation_list(request):
    latest = request.user.conversations.first()
    if latest:
        return redirect('chat:detail', pk=latest.pk)
    return redirect('chat:new')


@login_required
def new_conversation(request):
    conversation = Conversation.objects.create(user=request.user)
    return redirect('chat:detail', pk=conversation.pk)


@login_required
def chat_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    all_conversations = request.user.conversations.all()
    profile = _get_or_create_profile(request.user)
    return render(request, 'chat/chat.html', {
        'conversation': conversation,
        'conversations': all_conversations,
        'messages': conversation.messages_json,
        'profile': profile,
    })


@login_required
@require_http_methods(['POST'])
def send_message(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    profile = _get_or_create_profile(request.user)

    try:
        data = json.loads(request.body)
        text = data.get('message', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Mensaje inválido'}, status=400)

    if not text:
        return JsonResponse({'error': 'El mensaje no puede estar vacío'}, status=400)

    # Auto-title con el primer mensaje
    if conversation.title == 'Nueva conversación':
        conversation.title = text[:50]

    # Construir prompt con hechos y resumen previo
    system_prompt = _build_system_prompt(profile, request.user)
    if conversation.summary:
        system_prompt += f'\n\nResumen de la conversación anterior:\n{conversation.summary}'

    webhook_url = profile.get_webhook_url()
    if not webhook_url:
        conversation.save()
        return JsonResponse({
            'error': 'El asistente no está configurado. Pregunta al administrador.',
        }, status=503)

    user_context = _build_user_context(request.user, profile)
    full_message = f'Datos del usuario:\n{user_context}\n\nMensaje:\n{text}'

    payload = {
        'message': full_message,
        'session_id': str(conversation.pk),
        'system_prompt': system_prompt,
        'turn_count': conversation.turn_count,
        'previous_summary': conversation.summary or '',
    }

    ai_text = ''
    detected_facts = []
    new_summary = None

    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
        resp.raise_for_status()
        resp_data = resp.json()
        ai_text = resp_data.get('response', '').strip()
        detected_facts = resp_data.get('detected_facts', [])
        new_summary = resp_data.get('new_summary')
    except requests.exceptions.RequestException as exc:
        logger.error('Error llamando n8n webhook: %s', exc)
        ai_text = 'El asistente no está disponible en este momento. Intenta de nuevo.'

    if not ai_text:
        ai_text = 'No recibí respuesta del asistente. Intenta de nuevo.'

    now_ts = timezone.now().isoformat()

    user_entry = {'role': 'user', 'content': text, 'ts': now_ts}
    ai_entry   = {'role': 'assistant', 'content': ai_text, 'ts': now_ts}

    # Gestión de memoria: comprimir historial cuando n8n devuelve new_summary
    if new_summary:
        conversation.summary = new_summary
        conversation.messages_json = [user_entry, ai_entry]
        conversation.turn_count = 1
    else:
        msgs = list(conversation.messages_json)
        msgs.append(user_entry)
        msgs.append(ai_entry)
        conversation.messages_json = msgs
        conversation.turn_count += 1

    conversation.save()

    # Guardar hechos detectados automáticamente por n8n
    saved_facts = 0
    for fact in detected_facts:
        key = fact.get('key', '').strip()
        value = fact.get('value', '').strip()
        if key and value:
            UserFact.objects.update_or_create(
                user=request.user,
                key=key,
                defaults={
                    'value': value,
                    'category': fact.get('category', 'otro'),
                },
            )
            saved_facts += 1

    return JsonResponse({
        'response': ai_text,
        'saved_facts': saved_facts,
        'memory_reset': bool(new_summary),
    })


@login_required
@require_http_methods(['POST'])
def rename_conversation(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)
    if not title:
        return JsonResponse({'error': 'El título no puede estar vacío'}, status=400)
    conversation.title = title[:255]
    conversation.save(update_fields=['title'])
    return JsonResponse({'title': conversation.title})


@login_required
def user_settings(request):
    profile = _get_or_create_profile(request.user)
    facts = UserFact.objects.filter(user=request.user)
    prompt_profiles = PromptProfile.objects.filter(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Configuración guardada!')
            return redirect('chat:settings')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'chat/settings.html', {
        'form': form,
        'facts': facts,
        'fact_form': UserFactForm(),
        'prompt_profiles': prompt_profiles,
    })


@login_required
@require_http_methods(['POST'])
def prompt_profile_save(request, pk=None):
    """Crea o actualiza un PromptProfile."""
    if pk:
        pp = get_object_or_404(PromptProfile, pk=pk, user=request.user)
    else:
        pp = PromptProfile(user=request.user)

    pp.name = request.POST.get('name', '').strip() or 'Sin nombre'
    for sec in ('rol', 'contexto', 'comportamiento', 'formato', 'restricciones', 'excepciones'):
        setattr(pp, f'{sec}_enabled', f'{sec}_enabled' in request.POST)
        setattr(pp, f'{sec}_label', request.POST.get(f'{sec}_label', '').strip() or sec.upper())
        setattr(pp, f'prompt_{sec}', request.POST.get(f'prompt_{sec}', ''))
    pp.save()

    messages.success(request, f'Prompt "{pp.name}" guardado.')
    return redirect('chat:settings')


@login_required
@require_http_methods(['POST'])
def prompt_profile_activate(request, pk):
    """Activa un PromptProfile y desactiva los demás."""
    pp = get_object_or_404(PromptProfile, pk=pk, user=request.user)
    PromptProfile.objects.filter(user=request.user).update(is_active=False)
    pp.is_active = True
    pp.save(update_fields=['is_active'])
    messages.success(request, f'"{pp.name}" activado.')
    return redirect('chat:settings')


@login_required
@require_http_methods(['POST'])
def prompt_profile_delete(request, pk):
    pp = get_object_or_404(PromptProfile, pk=pk, user=request.user)
    name = pp.name
    pp.delete()
    messages.success(request, f'Prompt "{name}" eliminado.')
    return redirect('chat:settings')


@login_required
@require_http_methods(['POST'])
def add_fact(request):
    form = UserFactForm(request.POST)
    if form.is_valid():
        fact = form.save(commit=False)
        fact.user = request.user
        try:
            fact.save()
            messages.success(request, f'Agregué: {fact.key} → {fact.value}')
        except Exception:
            # unique_together violation — actualizar en su lugar
            UserFact.objects.filter(user=request.user, key=fact.key).update(
                value=fact.value,
                category=fact.category,
            )
            messages.success(request, f'Actualicé: {fact.key} → {fact.value}')
    else:
        messages.error(request, 'Por favor completa todos los campos.')
    return redirect('chat:settings')


@login_required
@require_http_methods(['POST'])
def delete_fact(request, pk):
    fact = get_object_or_404(UserFact, pk=pk, user=request.user)
    fact.delete()
    messages.success(request, 'Hecho eliminado.')
    return redirect('chat:settings')
