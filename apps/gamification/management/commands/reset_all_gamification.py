"""
Management command to reset ALL gamification and promo code data.
This is useful for production resets or testing.

Usage:
    python manage.py reset_all_gamification          # Reset ALL users
    python manage.py reset_all_gamification --user 30082653  # Reset specific user
    python manage.py reset_all_gamification --dry-run  # Preview without making changes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal


class Command(BaseCommand):
    help = 'Reset ALL gamification data (XP, achievements, promos, credits) to zero'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Reset only this user (phone number or user ID)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without making them',
        )

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from apps.gamification.models import (
            UserPoints, UserProgress, UserAchievement,
            UserDiscountCredits, CreditTransaction, UserReward
        )

        User = get_user_model()
        dry_run = options.get('dry_run', False)
        specific_user = options.get('user')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN MODE - No changes will be made ===\n'))

        self.stdout.write(self.style.MIGRATE_HEADING('Resetting Gamification Data...'))

        # Determine which users to reset
        if specific_user:
            try:
                target_users = User.objects.filter(phone_number=specific_user)
                if not target_users.exists():
                    target_users = User.objects.filter(id=specific_user)
                if not target_users.exists():
                    self.stdout.write(self.style.ERROR(f'User not found: {specific_user}'))
                    return
            except Exception:
                self.stdout.write(self.style.ERROR(f'Invalid user ID: {specific_user}'))
                return
            self.stdout.write(f'  Target: User {specific_user}')
        else:
            target_users = User.objects.all()
            self.stdout.write(f'  Target: ALL {target_users.count()} users')

        # Collect stats
        stats = {
            'user_points_reset': 0,
            'progress_deleted': 0,
            'achievements_deleted': 0,
            'credits_reset': 0,
            'credit_transactions_deleted': 0,
            'rewards_deleted': 0,
            'promo_usage_deleted': 0,
        }

        with transaction.atomic():
            # 1. Reset UserPoints to 0
            user_points = UserPoints.objects.filter(user__in=target_users)
            stats['user_points_reset'] = user_points.count()
            if not dry_run:
                user_points.update(
                    puntos_totales=0,
                    nivel='PRINCIPIANTE',
                    racha_dias=0,
                    modulos_completados=0,
                    ultima_actividad=None
                )
            self.stdout.write(f'  [1/7] UserPoints reset: {stats["user_points_reset"]}')

            # 2. Delete UserProgress
            progress = UserProgress.objects.filter(user__in=target_users)
            stats['progress_deleted'] = progress.count()
            if not dry_run:
                progress.delete()
            self.stdout.write(f'  [2/7] UserProgress deleted: {stats["progress_deleted"]}')

            # 3. Delete UserAchievement
            achievements = UserAchievement.objects.filter(user__in=target_users)
            stats['achievements_deleted'] = achievements.count()
            if not dry_run:
                achievements.delete()
            self.stdout.write(f'  [3/7] UserAchievement deleted: {stats["achievements_deleted"]}')

            # 4. Reset UserDiscountCredits
            credits = UserDiscountCredits.objects.filter(user__in=target_users)
            stats['credits_reset'] = credits.count()
            if not dry_run:
                credits.update(
                    saldo_disponible=Decimal('0.00'),
                    total_acumulado=Decimal('0.00'),
                    total_usado=Decimal('0.00'),
                    ultimo_uso=None
                )
            self.stdout.write(f'  [4/7] UserDiscountCredits reset: {stats["credits_reset"]}')

            # 5. Delete CreditTransaction
            credit_ids = credits.values_list('id', flat=True)
            transactions = CreditTransaction.objects.filter(user_credits_id__in=credit_ids)
            stats['credit_transactions_deleted'] = transactions.count()
            if not dry_run:
                transactions.delete()
            self.stdout.write(f'  [5/7] CreditTransaction deleted: {stats["credit_transactions_deleted"]}')

            # 6. Delete UserReward (earned promo codes)
            rewards = UserReward.objects.filter(user__in=target_users)
            stats['rewards_deleted'] = rewards.count()
            if not dry_run:
                rewards.delete()
            self.stdout.write(f'  [6/7] UserReward deleted: {stats["rewards_deleted"]}')

            # 7. Delete PromoCodeUsage
            try:
                from apps.promotions.models import PromoCodeUsage
                promo_usage = PromoCodeUsage.objects.filter(user__in=target_users)
                stats['promo_usage_deleted'] = promo_usage.count()
                if not dry_run:
                    promo_usage.delete()
                self.stdout.write(f'  [7/7] PromoCodeUsage deleted: {stats["promo_usage_deleted"]}')
            except ImportError:
                self.stdout.write(f'  [7/7] PromoCodeUsage: Skipped (promotions app not available)')

            if dry_run:
                # Rollback the transaction in dry run mode
                transaction.set_rollback(True)

        # Summary
        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN COMPLETE - No changes were made ==='))
        else:
            self.stdout.write(self.style.SUCCESS('=== RESET COMPLETE ==='))

        self.stdout.write('')
        self.stdout.write('Summary:')
        self.stdout.write(f'  - UserPoints reset to 0: {stats["user_points_reset"]}')
        self.stdout.write(f'  - Module progress deleted: {stats["progress_deleted"]}')
        self.stdout.write(f'  - Achievements deleted: {stats["achievements_deleted"]}')
        self.stdout.write(f'  - Credits reset to 0: {stats["credits_reset"]}')
        self.stdout.write(f'  - Credit transactions deleted: {stats["credit_transactions_deleted"]}')
        self.stdout.write(f'  - Earned rewards (promos) deleted: {stats["rewards_deleted"]}')
        self.stdout.write(f'  - Promo usage records deleted: {stats["promo_usage_deleted"]}')
        self.stdout.write('')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                'All gamification and promo data has been reset to 0/locked state.\n'
                'Users must complete e-learning modules to unlock promos again.'
            ))
