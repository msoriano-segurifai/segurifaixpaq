"""
Management command to create/update Mawdy field technician user.

Usage:
    python manage.py create_mawdy_tech
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update Mawdy field technician user'

    def handle(self, *args, **options):
        # Mawdy technician details
        email = 'mawdy@segurifai.gt'
        phone = '50012345678'
        first_name = 'Mawdy'
        last_name = 'Technician'
        role = 'MAWDY_FIELD_TECH'

        # Check if user exists
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone,
                'role': role,
                'is_active': True,
                'is_staff': False,
                'is_verified': True,
                'is_phone_verified': True,
            }
        )

        if created:
            # Set a default password for new user
            user.set_password('mawdy123')
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created Mawdy field technician user: {email}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    f'Default password: mawdy123 (please change in production!)'
                )
            )
        else:
            # Update existing user
            updated = False
            if user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if user.phone_number != phone:
                user.phone_number = phone
                updated = True
            if user.role != role:
                user.role = role
                updated = True
            if not user.is_active:
                user.is_active = True
                updated = True
            if not user.is_verified:
                user.is_verified = True
                updated = True
            if not user.is_phone_verified:
                user.is_phone_verified = True
                updated = True

            if updated:
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated Mawdy field technician user: {email}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Mawdy field technician user already exists and is up to date: {email}'
                    )
                )

        # Display user info
        self.stdout.write('---')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Name: {user.get_full_name()}')
        self.stdout.write(f'Phone: {user.phone_number}')
        self.stdout.write(f'Role: {user.role}')
        self.stdout.write(f'Active: {user.is_active}')
        self.stdout.write(f'ID: {user.id}')
