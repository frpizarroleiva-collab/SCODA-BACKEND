from django.core.management.base import BaseCommand
from estados.utils import ausentes

class Command(BaseCommand):
    help = "Marca a todos los alumnos como AUSENTE al iniciar el día"

    def handle(self, *args, **options):
        ausentes()
