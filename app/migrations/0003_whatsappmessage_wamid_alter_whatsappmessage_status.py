# Generated by Django 5.2 on 2025-04-11 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_whatsappmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsappmessage',
            name='wamid',
            field=models.CharField(blank=True, help_text='ID da mensagem WhatsApp para rastreamento de status', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='whatsappmessage',
            name='status',
            field=models.CharField(choices=[('pending', 'Pendente'), ('sent', 'Enviado'), ('delivered', 'Entregue'), ('read', 'Lido'), ('failed', 'Falhou'), ('received', 'Recebida')], default='pending', max_length=20),
        ),
    ]
