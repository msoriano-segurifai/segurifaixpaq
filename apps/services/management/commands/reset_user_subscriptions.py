"""
Reset user subscriptions management command.

Usage:
    python manage.py reset_user_subscriptions 30082653
    python manage.py reset_user_subscriptions 30082653 --delete
    python manage.py reset_user_subscriptions 30082653 --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.services.models import UserService


User = get_user_model()


class Command(BaseCommand):
    help = 'Reset (cancel or delete) all subscriptions for a user identified by phone number'

    def add_arguments(self, parser):
        parser.add_argument(
            'phone_number',
            type=str,
            help='Phone number of the user (8 digits, without country code)'
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete subscriptions instead of just cancelling them'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        phone_number = options['phone_number']
        delete_mode = options['delete']
        dry_run = options['dry_run']

        # Normalize phone number (remove any formatting)
        phone_normalized = phone_number.replace(' ', '').replace('-', '').replace('+502', '')

        self.stdout.write(f"Looking for user with phone: {phone_normalized}")

        # Find user by phone number (try various formats)
        user = None
        search_patterns = [
            phone_normalized,
            f'+502{phone_normalized}',
            f'502{phone_normalized}',
        ]

        for pattern in search_patterns:
            try:
                user = User.objects.get(phone_number__icontains=pattern[-8:])
                break
            except User.DoesNotExist:
                continue
            except User.MultipleObjectsReturned:
                self.stdout.write(self.style.WARNING(
                    f"Multiple users found with phone containing {pattern[-8:]}"
                ))
                # Get the first one
                user = User.objects.filter(phone_number__icontains=pattern[-8:]).first()
                break

        if not user:
            raise CommandError(f'User with phone number {phone_number} not found')

        self.stdout.write(self.style.SUCCESS(
            f"Found user: {user.email} (ID: {user.id}, Phone: {user.phone_number})"
        ))

        # Get user's subscriptions
        subscriptions = UserService.objects.filter(user=user)
        count = subscriptions.count()

        if count == 0:
            self.stdout.write(self.style.WARNING(
                f"User has no subscriptions to reset"
            ))
            return

        self.stdout.write(f"Found {count} subscription(s):")
        for sub in subscriptions:
            self.stdout.write(
                f"  - ID: {sub.id} | Plan: {sub.plan.name} | Status: {sub.status} | "
                f"Start: {sub.start_date} | End: {sub.end_date}"
            )

        if dry_run:
            action = "Would delete" if delete_mode else "Would cancel"
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] {action} {count} subscription(s)"
            ))
            return

        if delete_mode:
            # Delete all subscriptions
            deleted_count, _ = subscriptions.delete()
            self.stdout.write(self.style.SUCCESS(
                f"\nDeleted {deleted_count} subscription(s) for user {user.email}"
            ))
        else:
            # Cancel all subscriptions (mark as cancelled, don't delete)
            updated_count = subscriptions.update(status=UserService.Status.CANCELLED)
            self.stdout.write(self.style.SUCCESS(
                f"\nCancelled {updated_count} subscription(s) for user {user.email}"
            ))

        # Verify
        remaining = UserService.objects.filter(user=user, status=UserService.Status.ACTIVE).count()
        self.stdout.write(f"User now has {remaining} active subscription(s)")
