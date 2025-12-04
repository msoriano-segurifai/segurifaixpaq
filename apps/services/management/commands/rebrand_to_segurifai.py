"""
Management command to rebrand all MAPFRE references to SegurifAI in the database
Runs on every deployment to ensure clean branding
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import ServiceCategory, ServicePlan
from apps.providers.models import Provider
import re


class Command(BaseCommand):
    help = 'Replace all MAPFRE references with SegurifAI branding in database'

    def clean_mapfre(self, text):
        """Remove all MAPFRE variations from text aggressively"""
        if not text:
            return text
        # Remove various MAPFRE patterns (case insensitive)
        text = re.sub(r'\bMAPFRE\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bMapfre\b', '', text, flags=re.IGNORECASE)
        # Remove common patterns with MAPFRE
        text = re.sub(r'Asistencia\s+(Vial|Médica|Medica)\s+MAPFRE', r'Plan Asistencia \1', text, flags=re.IGNORECASE)
        text = re.sub(r'MAPFRE\s+Asistencia', 'Plan Asistencia', text, flags=re.IGNORECASE)
        # Clean up double spaces and extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove any leading/trailing spaces or dashes
        text = re.sub(r'^[\s\-]+|[\s\-]+$', '', text)
        return text

    def standardize_plan_name(self, name):
        """Standardize plan names to proper format without MAPFRE"""
        if not name:
            return name

        # First clean MAPFRE
        name = self.clean_mapfre(name)

        # Standardize common plan names
        name_lower = name.lower()

        if 'vial' in name_lower and 'médica' not in name_lower and 'medica' not in name_lower:
            if 'premium' in name_lower:
                return 'Plan Asistencia Vial Premium'
            elif 'básica' in name_lower or 'basica' in name_lower:
                return 'Plan Asistencia Vial Básica'
            else:
                return 'Plan Asistencia Vial'

        if 'médica' in name_lower or 'medica' in name_lower:
            if 'vial' in name_lower:
                return 'Combo Vial + Médica'
            elif 'premium' in name_lower:
                return 'Plan Asistencia Médica Premium'
            elif 'básica' in name_lower or 'basica' in name_lower:
                return 'Plan Asistencia Médica Básica'
            else:
                return 'Plan Asistencia Médica'

        if 'accidente' in name_lower or 'seguro' in name_lower:
            if 'premium' in name_lower:
                return 'Plan Seguro Accidentes Premium'
            elif 'básica' in name_lower or 'basica' in name_lower:
                return 'Plan Seguro Accidentes Básico'
            else:
                return 'Plan Seguro Accidentes'

        if 'tarjeta' in name_lower:
            if 'premium' in name_lower:
                return 'SegurifAI Seguro de Tarjeta Premium'
            else:
                return 'SegurifAI Seguro de Tarjeta Básico'

        # Return cleaned name if no specific match
        return name

    def handle(self, *args, **options):
        self.stdout.write('='*50)
        self.stdout.write('REBRANDING: Removing ALL MAPFRE references...')
        self.stdout.write('='*50)

        with transaction.atomic():
            # Update service categories
            updated_cats = 0
            for cat in ServiceCategory.objects.all():
                changed = False
                original_name = cat.name
                original_desc = cat.description

                if cat.name and 'mapfre' in cat.name.lower():
                    cat.name = self.clean_mapfre(cat.name)
                    changed = True
                if cat.description and 'mapfre' in cat.description.lower():
                    cat.description = self.clean_mapfre(cat.description)
                    changed = True
                if changed:
                    cat.save()
                    updated_cats += 1
                    self.stdout.write(f'  Category: "{original_name}" -> "{cat.name}"')

            # Update service plans - remove MAPFRE and standardize names
            updated_plans = 0
            for plan in ServicePlan.objects.all():
                changed = False
                original_name = plan.name
                original_desc = plan.description

                # Check for MAPFRE in name
                if plan.name and 'mapfre' in plan.name.lower():
                    plan.name = self.standardize_plan_name(plan.name)
                    changed = True

                # Check for MAPFRE in description
                if plan.description and 'mapfre' in plan.description.lower():
                    plan.description = self.clean_mapfre(plan.description)
                    changed = True

                if changed:
                    plan.save()
                    updated_plans += 1
                    self.stdout.write(f'  Plan: "{original_name}" -> "{plan.name}"')

            # Update providers - more aggressive cleaning
            updated_providers = 0
            for provider in Provider.objects.all():
                changed = False

                # Check company_name (case insensitive)
                if provider.company_name and 'mapfre' in provider.company_name.lower():
                    provider.company_name = provider.company_name.replace('MAPFRE', 'SegurifAI').replace('Mapfre', 'SegurifAI').replace('mapfre', 'SegurifAI')
                    changed = True

                # Check business_license
                if provider.business_license and 'mapfre' in provider.business_license.lower():
                    provider.business_license = provider.business_license.replace('MAPFRE', 'SegurifAI').replace('Mapfre', 'SegurifAI').replace('mapfre', 'SegurifAI')
                    changed = True

                # Check business_email - fix any mapfre domain
                if provider.business_email and 'mapfre' in provider.business_email.lower():
                    provider.business_email = 'asistencia@segurifai.com.gt'
                    changed = True

                # Check website - fix any mapfre domain
                if provider.website and 'mapfre' in provider.website.lower():
                    provider.website = 'https://www.segurifai.com'
                    changed = True

                # Check verification_notes
                if provider.verification_notes and 'mapfre' in provider.verification_notes.lower():
                    provider.verification_notes = provider.verification_notes.replace('MAPFRE', 'SegurifAI').replace('Mapfre', 'SegurifAI').replace('mapfre', 'SegurifAI')
                    changed = True

                if changed:
                    provider.save()
                    updated_providers += 1
                    self.stdout.write(f'  Provider updated: {provider.company_name}')

        self.stdout.write('='*50)
        self.stdout.write(self.style.SUCCESS(
            f'REBRANDING COMPLETE!\n'
            f'  Categories updated: {updated_cats}\n'
            f'  Plans updated: {updated_plans}\n'
            f'  Providers updated: {updated_providers}'
        ))
        self.stdout.write('='*50)
