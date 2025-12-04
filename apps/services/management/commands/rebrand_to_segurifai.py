"""
Management command to FORCE rebrand ALL plans to SegurifAI naming
Runs on every deployment - UNCONDITIONALLY updates all plan names
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import ServiceCategory, ServicePlan
from apps.providers.models import Provider
import re


class Command(BaseCommand):
    help = 'FORCE rebrand ALL plans to SegurifAI naming (removes ALL MAPFRE)'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('FORCE REBRANDING: Standardizing ALL plan names...')
        self.stdout.write('='*60)

        with transaction.atomic():
            # ========================================
            # STEP 1: FORCE UPDATE ALL SERVICE PLANS
            # ========================================
            self.stdout.write('\n[STEP 1] Force-updating ALL service plans...')

            updated_plans = 0
            for plan in ServicePlan.objects.all():
                original_name = plan.name
                original_desc = plan.description
                category_type = plan.category.category_type if plan.category else ''
                changed = False

                # Determine the correct name and description based on category
                if category_type == 'ROADSIDE':
                    new_name = 'Plan Asistencia Vial'
                    new_desc = 'Plan de asistencia vial con seguro de muerte accidental'
                elif category_type == 'HEALTH':
                    new_name = 'Plan Asistencia Médica'
                    new_desc = 'Plan de asistencia médica con seguro de muerte accidental'
                elif category_type == 'INSURANCE':
                    new_name = 'Plan Seguro Accidentes'
                    new_desc = 'Seguro básico de accidentes personales con cobertura de muerte accidental'
                else:
                    # Fallback: clean any MAPFRE/MAWDY from name and description
                    new_name = re.sub(r'\s*(MAPFRE|MAWDY)\s*', ' ', plan.name, flags=re.IGNORECASE).strip()
                    new_name = re.sub(r'\s+', ' ', new_name)
                    new_desc = plan.description

                # Clean MAPFRE and MAWDY from description regardless
                if plan.description:
                    new_desc = re.sub(r'\s*(MAPFRE|MAWDY)\s*', ' ', plan.description, flags=re.IGNORECASE).strip()
                    new_desc = re.sub(r'\s+', ' ', new_desc)
                    # Replace with standard descriptions for known categories
                    if category_type in ['ROADSIDE', 'HEALTH', 'INSURANCE']:
                        if category_type == 'ROADSIDE':
                            new_desc = 'Plan de asistencia vial con seguro de muerte accidental'
                        elif category_type == 'HEALTH':
                            new_desc = 'Plan de asistencia médica con seguro de muerte accidental'
                        elif category_type == 'INSURANCE':
                            new_desc = 'Seguro básico de accidentes personales con cobertura de muerte accidental'

                if plan.name != new_name:
                    self.stdout.write(f'  Name: "{original_name}" -> "{new_name}"')
                    plan.name = new_name
                    changed = True

                if plan.description != new_desc:
                    self.stdout.write(f'  Desc updated for: {new_name}')
                    plan.description = new_desc
                    changed = True

                if changed:
                    plan.save()
                    updated_plans += 1

            self.stdout.write(f'  Updated {updated_plans} plans')

            # ========================================
            # STEP 2: UPDATE SERVICE CATEGORIES
            # ========================================
            self.stdout.write('\n[STEP 2] Cleaning service categories...')

            updated_cats = 0
            for cat in ServiceCategory.objects.all():
                changed = False

                # Clean MAPFRE from name
                if cat.name and 'mapfre' in cat.name.lower():
                    cat.name = re.sub(r'\s*MAPFRE\s*', ' ', cat.name, flags=re.IGNORECASE).strip()
                    cat.name = re.sub(r'\s+', ' ', cat.name)
                    changed = True

                # Clean MAPFRE from description
                if cat.description and 'mapfre' in cat.description.lower():
                    cat.description = re.sub(r'\s*MAPFRE\s*', ' ', cat.description, flags=re.IGNORECASE).strip()
                    cat.description = re.sub(r'\s+', ' ', cat.description)
                    changed = True

                if changed:
                    cat.save()
                    updated_cats += 1
                    self.stdout.write(f'  Updated category: {cat.name}')

            self.stdout.write(f'  Updated {updated_cats} categories')

            # ========================================
            # STEP 3: UPDATE PROVIDERS
            # ========================================
            self.stdout.write('\n[STEP 3] Cleaning providers...')

            updated_providers = 0
            for provider in Provider.objects.all():
                changed = False

                # Clean company_name
                if provider.company_name and 'mapfre' in provider.company_name.lower():
                    provider.company_name = 'SegurifAI Guatemala'
                    changed = True

                # Clean business_license
                if provider.business_license and 'mapfre' in provider.business_license.lower():
                    provider.business_license = 'SegurifAI-GT-2024'
                    changed = True

                # Fix email
                if provider.business_email and 'mapfre' in provider.business_email.lower():
                    provider.business_email = 'asistencia@segurifai.com.gt'
                    changed = True

                # Fix website
                if provider.website and 'mapfre' in provider.website.lower():
                    provider.website = 'https://www.segurifai.com'
                    changed = True

                # Clean verification_notes
                if provider.verification_notes and 'mapfre' in provider.verification_notes.lower():
                    provider.verification_notes = re.sub(r'MAPFRE', 'SegurifAI', provider.verification_notes, flags=re.IGNORECASE)
                    changed = True

                if changed:
                    provider.save()
                    updated_providers += 1
                    self.stdout.write(f'  Updated provider: {provider.company_name}')

            self.stdout.write(f'  Updated {updated_providers} providers')

        # ========================================
        # FINAL SUMMARY
        # ========================================
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            'FORCE REBRANDING COMPLETE!\n'
            f'  Plans updated: {updated_plans}\n'
            f'  Categories updated: {updated_cats}\n'
            f'  Providers updated: {updated_providers}\n'
            '\n  ALL plan names are now SegurifAI branded!'
        ))
        self.stdout.write('='*60)
