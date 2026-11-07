from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_openai_api_key_encrypted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='openai_api_key_encrypted',
        ),
    ]
