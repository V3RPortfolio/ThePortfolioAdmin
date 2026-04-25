# Generated migration

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0003_device_deviceconfiguration'),
    ]

    operations = [
        migrations.AddField(
            model_name='deviceconfiguration',
            name='organization_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deviceconfiguration',
            name='api_key',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deviceconfiguration',
            name='configured_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
