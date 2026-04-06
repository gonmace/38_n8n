from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_conversation_messages_json'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Message',
        ),
    ]
