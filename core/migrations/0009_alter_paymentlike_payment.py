# Generated by Django 5.2 on 2025-04-19 11:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_paymentcomment_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlike',
            name='payment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='core.payment'),
        ),
    ]
