from django.core.management.base import BaseCommand

from jarvis_services.models.services import ServiceGroup


SERVICE_GROUPS = [
    "Jarvis Overview",
    "Jarvis Ingestor",
    "Jarvis Processor",
    "Jarvis Hub",
    "Jarvis Training Academy",
]


class Command(BaseCommand):
    help = "Seed the ServiceGroup model with initial data"

    def handle(self, *args, **kwargs):
        created_count = 0
        skipped_count = 0

        for title in SERVICE_GROUPS:
            _, created = ServiceGroup.objects.get_or_create(title=title)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {title}"))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f"  Skipped (already exists): {title}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {created_count} created, {skipped_count} skipped."
            )
        )
