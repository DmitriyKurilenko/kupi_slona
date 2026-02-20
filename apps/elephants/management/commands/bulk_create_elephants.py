"""
Management command for bulk elephant creation from CSV.

CSV format (color_hex is optional, defaults to random):
    recipient_name,sender_name,message
    Иван,Дмитрий,С днём рождения!
    Мария,Дмитрий,Подарок от команды
    Петр,Дмитрий,Синий слон для тебя

Or with explicit colors:
    color_hex,recipient_name,sender_name,message
    #FF0000,Иван,Дмитрий,С днём рождения!
    HUE:240,Мария,Дмитрий,Подарок

Usage:
    python manage.py bulk_create_elephants gifts.csv
    python manage.py bulk_create_elephants gifts.csv --dry-run
    python manage.py bulk_create_elephants gifts.csv --admin-user admin
"""
import csv
import logging

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction

from apps.elephants.services import create_elephant, check_color_availability
from apps.elephants.utils import generate_random_color, generate_color_from_hue, validate_hex_color
from apps.payments.models import Order, Tariff
from apps.gifts.models import GiftLink

logger = logging.getLogger('apps')


class Command(BaseCommand):
    help = 'Bulk create elephants from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument(
            '--admin-user',
            type=str,
            default=None,
            help='Admin username to own elephants (default: first superuser)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate CSV without creating anything',
        )

    def handle(self, *args, **options):
        csv_path = options['csv_file']
        dry_run = options['dry_run']

        # Find admin user
        admin_user = self._get_admin_user(options['admin_user'])
        self.stdout.write(f'Admin user: {admin_user.username} ({admin_user.email})')

        # Get or create a tariff for admin orders
        tariff = Tariff.objects.filter(name=Tariff.BASIC).first()
        if not tariff:
            raise CommandError('No basic tariff found. Create one in admin first.')

        # Read CSV
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f'File not found: {csv_path}')
        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        if not rows:
            raise CommandError('CSV file is empty')

        has_color = 'color_hex' in rows[0]

        self.stdout.write(f'Found {len(rows)} rows in CSV')
        if not has_color:
            self.stdout.write('No color_hex column — all elephants will get random colors')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing will be created'))

        created = 0
        errors = 0

        for i, row in enumerate(rows, 1):
            color_input = row.get('color_hex', '').strip() or 'random'
            recipient_name = row.get('recipient_name', '').strip()
            sender_name = row.get('sender_name', '').strip() or admin_user.username
            message = row.get('message', '').strip()

            # Resolve color
            try:
                color_hex = self._resolve_color(color_input)
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f'  Row {i}: {e}'))
                errors += 1
                continue

            if dry_run:
                gift_info = f' -> gift for {recipient_name}' if recipient_name else ''
                self.stdout.write(f'  Row {i}: {color_hex}{gift_info} — OK')
                created += 1
                continue

            # Create elephant
            try:
                with transaction.atomic():
                    # Create order stub
                    order = Order.objects.create(
                        user=admin_user,
                        tariff=tariff,
                        status='completed',
                        desired_color=color_input,
                    )
                    order.mark_as_paid()
                    order.mark_as_completed()

                    # Create elephant with image
                    elephant = create_elephant(order, color_hex)

                    # Create gift link if recipient specified
                    gift_url = ''
                    if recipient_name:
                        gift = GiftLink.objects.create(
                            elephant=elephant,
                            sender=admin_user,
                            sender_name=sender_name,
                            recipient_name=recipient_name,
                            message=message,
                        )
                        elephant.mark_as_gifted()
                        gift_url = f' -> /gift/{gift.uuid}/'

                    self.stdout.write(self.style.SUCCESS(
                        f'  Row {i}: {elephant.color_hex} (id={elephant.id}){gift_url}'
                    ))
                    created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Row {i}: {e}'))
                errors += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Created: {created}'))
        if errors:
            self.stdout.write(self.style.ERROR(f'Errors: {errors}'))

    def _get_admin_user(self, username=None):
        """Get admin user by username or first superuser"""
        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f'User not found: {username}')

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            raise CommandError('No superuser found. Specify --admin-user')
        return admin

    def _resolve_color(self, color_input):
        """Resolve color input to #RRGGBB"""
        if color_input.lower() == 'random':
            for _ in range(10):
                color = generate_random_color()
                if check_color_availability(color):
                    return color
            raise ValueError('Failed to generate unique random color after 10 attempts')

        if color_input.upper().startswith('HUE:'):
            try:
                hue = int(color_input.split(':')[1])
            except (ValueError, IndexError):
                raise ValueError(f'Invalid hue format: {color_input}')
            for _ in range(10):
                color = generate_color_from_hue(hue)
                if check_color_availability(color):
                    return color
            raise ValueError(f'Failed to generate unique color for hue {hue} after 10 attempts')

        # Exact hex color
        color_hex = color_input.upper()
        if not color_hex.startswith('#'):
            color_hex = f'#{color_hex}'
        if not validate_hex_color(color_hex):
            raise ValueError(f'Invalid hex color: {color_input}')
        if not check_color_availability(color_hex):
            raise ValueError(f'Color {color_hex} is already taken')
        return color_hex
