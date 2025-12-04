"""
Management command to rebrand all MAPFRE references to SegurifAI in the database
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import ServiceCategory, ServicePlan
from apps.providers.models import Provider
import re


class Command(BaseCommand):
    help = 'Replace all MAPFRE references with SegurifAI branding in database'

    def clean_mapfre(self, text):
        """Remove all MAPFRE variations from text"""
        if not text:
            return text
        # Remove various MAPFRE patterns
        text = re.sub(r'\s*MAPFRE\s*', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*Mapfre\s*', ' ', text)
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def handle(self, *args, **options):
        self.stdout.write('Rebranding - removing all MAPFRE references...')

        with transaction.atomic():
            # Update service categories
            updated_cats = 0
            for cat in ServiceCategory.objects.all():
                changed = False
                if cat.name and 'mapfre' in cat.name.lower():
                    cat.name = self.clean_mapfre(cat.name)
                    changed = True
                if cat.description and 'mapfre' in cat.description.lower():
                    cat.description = self.clean_mapfre(cat.description)
                    changed = True
                if changed:
                    cat.save()
                    updated_cats += 1
                    self.stdout.write(f'  Updated category: {cat.name}')

            # Update service plans - remove MAPFRE completely from names
            updated_plans = 0
            for plan in ServicePlan.objects.all():
                changed = False
                if plan.name and 'mapfre' in plan.name.lower():
                    plan.name = self.clean_mapfre(plan.name)
                    changed = True
                if plan.description and 'mapfre' in plan.description.lower():
                    plan.description = self.clean_mapfre(plan.description)
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
