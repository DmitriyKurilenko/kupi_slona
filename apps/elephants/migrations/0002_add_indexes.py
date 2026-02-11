# Generated migration for adding database indexes to Elephant model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elephants', '0001_initial'),
    ]

    operations = [
        # Add index on owner for filtering elephants by user
        migrations.AddIndex(
            model_name='elephant',
            index=models.Index(fields=['owner'], name='elephants_e_owner_idx'),
        ),
        # Add index on created_at for chronological sorting
        migrations.AddIndex(
            model_name='elephant',
            index=models.Index(fields=['-created_at'], name='elephants_e_created_idx'),
        ),
        # Note: color_hex already has a unique constraint which creates an index
    ]
