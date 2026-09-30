from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='openai_api_key_encrypted',
            field=models.TextField(blank=True, default='', verbose_name='Chave da API OpenAI (criptografada)'),
        ),
    ]
