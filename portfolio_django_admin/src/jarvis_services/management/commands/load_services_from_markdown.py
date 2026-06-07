from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from jarvis_services.models.services import Service, ServiceContent, ServiceGroup


class Command(BaseCommand):
    help = (
        "Load markdown files from a directory into Service and ServiceContent models. "
        "Expected structure: base_path/<group_title>/<service_title>/<seq>_<name>.md"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "base_path",
            type=str,
            help="Base directory path structured as group_title/service_title/<seq>_<name>.md",
        )

    def handle(self, *args, **kwargs):
        base_path = Path(kwargs["base_path"]).resolve()

        if not base_path.exists() or not base_path.is_dir():
            raise CommandError(f"'{base_path}' does not exist or is not a directory.")

        total_created = 0
        total_updated = 0
        total_skipped_groups = 0
        total_skipped_services = 0

        for group_dir in sorted(base_path.iterdir()):
            if not group_dir.is_dir():
                continue

            group_title = group_dir.name

            try:
                group = ServiceGroup.objects.get(title=group_title)
            except ServiceGroup.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"[SKIP] Group '{group_title}' not found in database — skipping entire directory."
                    )
                )
                total_skipped_groups += 1
                continue

            self.stdout.write(self.style.MIGRATE_HEADING(f"\nGroup: {group_title}"))

            for service_dir in sorted(group_dir.iterdir()):
                if not service_dir.is_dir():
                    continue

                service_title = service_dir.name
                md_files = sorted(
                    f for f in service_dir.iterdir()
                    if f.is_file() and f.suffix == ".md"
                )

                if not md_files:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [SKIP] '{service_title}': no markdown files found."
                        )
                    )
                    total_skipped_services += 1
                    continue

                contents_to_create = []
                parse_error = False

                for md_file in md_files:
                    raw_stem = md_file.stem
                    prefix = raw_stem.split("_", 1)[0]

                    if not prefix.isdigit():
                        self.stdout.write(
                            self.style.WARNING(
                                f"  [SKIP] '{md_file.name}': filename must start with a sequence "
                                f"number followed by '_' (e.g. 1_intro.md). Skipping service."
                            )
                        )
                        parse_error = True
                        break

                    contents_to_create.append(
                        {
                            "sequence_number": int(prefix),
                            "content": md_file.read_text(encoding="utf-8"),
                        }
                    )

                if parse_error:
                    total_skipped_services += 1
                    continue

                with transaction.atomic():
                    try:
                        service = Service.objects.get(title=service_title, group=group)
                        # Existing service — clear contents and re-add
                        deleted_count, _ = service.contents.all().delete()
                        ServiceContent.objects.bulk_create(
                            [
                                ServiceContent(
                                    service=service,
                                    sequence_number=c["sequence_number"],
                                    content=c["content"],
                                )
                                for c in contents_to_create
                            ]
                        )
                        self.stdout.write(
                            self.style.WARNING(
                                f"  [UPDATE] '{service_title}': removed {deleted_count} old "
                                f"content(s), added {len(contents_to_create)} new."
                            )
                        )
                        total_updated += 1

                    except Service.DoesNotExist:
                        # New service — create service and contents
                        service = Service.objects.create(title=service_title, group=group)
                        ServiceContent.objects.bulk_create(
                            [
                                ServiceContent(
                                    service=service,
                                    sequence_number=c["sequence_number"],
                                    content=c["content"],
                                )
                                for c in contents_to_create
                            ]
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  [CREATE] '{service_title}': added {len(contents_to_create)} content(s)."
                            )
                        )
                        total_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. "
                f"{total_created} service(s) created, "
                f"{total_updated} service(s) updated, "
                f"{total_skipped_groups} group(s) skipped, "
                f"{total_skipped_services} service(s) skipped."
            )
        )
