"""
Management command to remove MAPFRE/MAWDY from educational modules
Runs on every deployment to ensure clean branding
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.gamification.models import EducationalModule, QuizQuestion
import re


class Command(BaseCommand):
    help = 'Remove MAPFRE/MAWDY branding from educational modules'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('REBRANDING EDUCATIONAL MODULES...')
        self.stdout.write('='*60)

        with transaction.atomic():
            updated_modules = 0
            updated_questions = 0

            # Process all educational modules
            for module in EducationalModule.objects.all():
                changed = False

                # Clean titulo
                if module.titulo and self._contains_old_branding(module.titulo):
                    module.titulo = self._clean_text(module.titulo)
                    changed = True
                    self.stdout.write(f'  Cleaned titulo: {module.titulo[:50]}...')

                # Clean descripcion
                if module.descripcion and self._contains_old_branding(module.descripcion):
                    module.descripcion = self._clean_text(module.descripcion)
                    changed = True
                    self.stdout.write(f'  Cleaned descripcion for: {module.titulo}')

                # Clean contenido
                if module.contenido and self._contains_old_branding(module.contenido):
                    module.contenido = self._clean_text(module.contenido)
                    changed = True
                    self.stdout.write(f'  Cleaned contenido for: {module.titulo}')

                if changed:
                    module.save()
                    updated_modules += 1

            # Process all quiz questions
            for question in QuizQuestion.objects.all():
                changed = False

                # Clean pregunta
                if question.pregunta and self._contains_old_branding(question.pregunta):
                    question.pregunta = self._clean_text(question.pregunta)
                    changed = True

                # Clean all options
                for field in ['opcion_a', 'opcion_b', 'opcion_c', 'opcion_d']:
                    value = getattr(question, field, '')
                    if value and self._contains_old_branding(value):
                        setattr(question, field, self._clean_text(value))
                        changed = True

                # Clean explicacion
                if question.explicacion and self._contains_old_branding(question.explicacion):
                    question.explicacion = self._clean_text(question.explicacion)
                    changed = True

                if changed:
                    question.save()
                    updated_questions += 1
                    self.stdout.write(f'  Cleaned question: {question.pregunta[:50]}...')

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'EDUCATIONAL MODULES REBRANDING COMPLETE!\n'
            f'  Modules cleaned: {updated_modules}\n'
            f'  Questions cleaned: {updated_questions}'
        ))
        self.stdout.write('='*60)

    def _contains_old_branding(self, text):
        """Check if text contains MAPFRE or MAWDY"""
        if not text:
            return False
        text_lower = text.lower()
        return 'mapfre' in text_lower or 'mawdy' in text_lower

    def _clean_text(self, text):
        """Remove MAPFRE and MAWDY from text, replace with SegurifAI where appropriate"""
        if not text:
            return text

        # Replace MAPFRE with SegurifAI
        text = re.sub(r'\bMAPFRE\b', 'SegurifAI', text, flags=re.IGNORECASE)
        # Remove MAWDY (usually appears as standalone brand)
        text = re.sub(r'\bMAWDY\b', 'SegurifAI', text, flags=re.IGNORECASE)
        # Clean up any double spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
