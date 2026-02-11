# Generated migration for adding database indexes to Order model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_alter_order_desired_color'),
    ]

    operations = [
        # Add index on status field for filtering orders by status
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status'], name='payments_or_status_idx'),
        ),
        # Add composite index on user + status for user's order queries
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['user', 'status'], name='payments_or_user_st_idx'),
        ),
        # Add index on created_at for chronological sorting
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['-created_at'], name='payments_or_created_idx'),
        ),
    ]
