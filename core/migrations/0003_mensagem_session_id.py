# Generated by Django 5.2.4 on 2025-07-11 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_consultor_contexto_conversa_parametro'),
    ]

    operations = [
        migrations.AddField(
            model_name='mensagem',
            name='session_id',
            field=models.CharField(blank=None, default='', max_length=100),
        ),
    ]
