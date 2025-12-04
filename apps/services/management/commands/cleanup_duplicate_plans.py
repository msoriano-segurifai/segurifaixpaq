"""
Management command to cleanup duplicate plans
Keeps only ONE active plan per category type with correct SegurifAI pricing
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import ServiceCategory, ServicePlan


class Command(BaseCommand):
    help = 'Cleanup duplicate plans - keep only one active per category'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('CLEANING UP DUPLICATE PLANS...')
        self.stdout.write('='*60)

        # Define the ONLY plans that should be active (correct SegurifAI pricing)
        correct_plans = {
            'ROADSIDE': {
                'name': 'Plan Asistencia Vial',
                'price_monthly': 36.88,
                'price_yearly': 442.56,
            },
            'HEALTH': {
                'name': 'Plan Asistencia Médica',
                'price_monthly': 34.26,
                'price_yearly': 411.12,
            },
            'INSURANCE': {
                'name': 'Plan Seguro Accidentes',
                'price_monthly': 4.12,
                'price_yearly': 49.44,
            },
        }

        with transaction.atomic():
            deactivated_count = 0
            kept_count = 0

            for category_type, plan_info in correct_plans.items():
                self.stdout.write(f'\n[{category_type}] Processing...')

                # Get or create category
                category = ServiceCategory.objects.filter(category_type=category_type).first()
                if not category:
                    self.stdout.write(f'  No category found for {category_type}')
                    continue

                # Find all plans in this category
                all_plans = ServicePlan.objects.filter(category=category)
                self.stdout.write(f'  Found {all_plans.count()} plans in category')

                # Find the correct plan (by name and price)
                correct_plan = all_plans.filter(
                    name=plan_info['name'],
                    price_monthly=plan_info['price_monthly']
                ).first()

                if correct_plan:
                    # Keep this one active
                    correct_plan.is_active = True
                    correct_plan.save()
                    kept_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  KEPT: {correct_plan.name} @ Q{correct_plan.price_monthly}/mes'
                    ))

                    # Deactivate all others in this category
                    others = all_plans.exclude(pk=correct_plan.pk)
                    for plan in others:
                        if plan.is_active:
                            plan.is_active = False
                            plan.save()
                            deactivated_count += 1
                            self.stdout.write(f'  DEACTIVATED: {plan.name} @ Q{plan.price_monthly}/mes')
                else:
                    # Create or update the correct plan
                    self.stdout.write(f'  Creating correct plan: {plan_info["name"]}')
                    # Deactivate all existing
                    for plan in all_plans:
                        if plan.is_active:
                            plan.is_active = False
                            plan.save()
                            deactivated_count += 1

            # Deactivate ALL card insurance plans
            card_plans = ServicePlan.objects.filter(
                category__category_type='CARD_INSURANCE',
                is_active=True
            )
            for plan in card_plans:
                plan.is_active = False
                plan.save()
                deactivated_count += 1
                self.stdout.write(f'  DEACTIVATED CARD: {plan.name}')

            # Deactivate any other plans not in our correct list
            all_active = ServicePlan.objects.filter(is_active=True)
            for plan in all_active:
                cat_type = plan.category.category_type if plan.category else None
                if cat_type not in correct_plans:
                    plan.is_active = False
                    plan.save()
                    deactivated_count += 1
                    self.stdout.write(f'  DEACTIVATED OTHER: {plan.name}')

        # Final count
        active_plans = ServicePlan.objects.filter(is_active=True)
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'CLEANUP COMPLETE!\n'
            f'  Plans kept active: {kept_count}\n'
            f'  Plans deactivated: {deactivated_count}\n'
            f'  Total active plans now: {active_plans.count()}'
        ))

        self.stdout.write('\nActive plans:')
        for plan in active_plans:
            self.stdout.write(f'  - {plan.name} ({plan.category.category_type}) @ Q{plan.price_monthly}/mes')
        self.stdout.write('='*60)
