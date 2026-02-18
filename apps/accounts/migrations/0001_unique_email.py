"""
Add unique constraint on auth_user.email at database level.
Django's built-in User model doesn't enforce email uniqueness in DB.

IMPORTANT: Before running this migration, remove duplicate emails:
    docker-compose exec web python manage.py shell -c "
    from django.contrib.auth.models import User
    from django.db.models import Count
    dupes = User.objects.values('email').annotate(cnt=Count('id')).filter(cnt__gt=1)
    for d in dupes:
        users = User.objects.filter(email=d['email']).order_by('id')
        # Keep the first, delete the rest
        for u in list(users)[1:]:
            print(f'Deleting duplicate: id={u.id} username={u.username} email={u.email}')
            u.delete()
    "
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE UNIQUE INDEX unique_user_email ON auth_user (email) WHERE email != \'\';',
            reverse_sql='DROP INDEX IF EXISTS unique_user_email;',
        ),
    ]
