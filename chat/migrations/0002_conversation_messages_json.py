from django.db import migrations, models


def copy_messages_to_json(apps, schema_editor):
    Conversation = apps.get_model('chat', 'Conversation')
    Message = apps.get_model('chat', 'Message')
    for conv in Conversation.objects.all():
        msgs = Message.objects.filter(conversation=conv).order_by('created_at')
        conv.messages_json = [
            {
                'role': m.role,
                'content': m.content,
                'ts': m.created_at.isoformat(),
            }
            for m in msgs
        ]
        conv.save(update_fields=['messages_json'])


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='messages_json',
            field=models.JSONField(
                default=list,
                help_text='Lista de mensajes: [{role, content, ts}]',
                verbose_name='Mensajes',
            ),
        ),
        migrations.RunPython(copy_messages_to_json, migrations.RunPython.noop),
    ]
