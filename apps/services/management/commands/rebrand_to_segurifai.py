"""
Management command to rebrand all MAPFRE references to SegurifAI in the database
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import ServiceCategory, ServicePlan
from apps.providers.models import Provider


class Command(BaseCommand):
    help = 'Replace all MAPFRE references with SegurifAI branding in database'

    def handle(self, *args, **options):
        self.stdout.write('Rebranding MAPFRE to SegurifAI...')

        with transaction.atomic():
            # Update service categories
            updated_cats = 0
            for cat in ServiceCategory.objects.all():
                changed = False
                if 'MAPFRE' in (cat.name or ''):
                    cat.name = cat.name.replace('MAPFRE', 'SegurifAI')
                    changed = True
                if 'MAPFRE' in (cat.description or ''):
                    cat.description = cat.description.replace('MAPFRE', 'SegurifAI')
                    changed = True
                if changed:
                    cat.save()
                    updated_cats += 1
                    self.stdout.write(f'  Updated category: {cat.name}')

            # Update service plans
            updated_plans = 0
            for plan in ServicePlan.objects.all():
                changed = False
                if 'MAPFRE' in (plan.name or ''):
                    plan.name = plan.name.replace('MAPFRE', 'SegurifAI')
                    changed = True
                if 'MAPFRE' in (plan.description or ''):
                    plan.description = plan.description.replace('MAPFRE', 'SegurifAI')
                    changed = True
                if changed:
                    plan.save()
                    updated_plans += 1
                    self.stdout.write(f'  Updated plan: {plan.name}')

            # Update providers
            updated_providers = 0
            for provider in Provider.objects.all():
                changed = False
                if 'MAPFRE' in (provider.company_name or ''):
                    provider.company_name = provider.company_name.replace('MAPFRE', 'SegurifAI')
                    changed = True
                if 'MAPFRE' in (provider.business_license or ''):
                    provider.business_license = provider.business_license.replace('MAPFRE', 'SegurifAI')
                    changed = True
                if 'MAPFRE' in (provider.business_email or ''):
                    provider.business_email = 'asistencia@segurifai.com.gt'
                    changed = True
                if 'MAPFRE' in (provider.website or ''):
                    provider.website = 'https://www.segurifai.com'
                    changed = True
                if 'MAPFRE' in (provider.verification_notes or ''):
                    provider.verification_notes = provider.verification_notes.replace('MAPFRE', 'SegurifAI')
                    changed = True
                if changed:
                    provider.save()
                    updated_providers += 1
                    self.stdout.write(f'  Updated provider: {provider.company_name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nRebranding complete!\n'
            f'  Categories updated: {updated_cats}\n'
            f'  Plans updated: {updated_plans}\n'
            f'  Providers updated: {updated_providers}'
        ))
