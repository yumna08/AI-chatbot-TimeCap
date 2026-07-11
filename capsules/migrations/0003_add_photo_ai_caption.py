"""Add photo and ai_caption fields to Capsule."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capsules', '0002_alter_capsule_id_alter_reflectionquery_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='capsule',
            name='photo',
            field=models.ImageField(upload_to='capsule_photos/', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='capsule',
            name='ai_caption',
            field=models.CharField(max_length=500, null=True, blank=True),
        ),
    ]
