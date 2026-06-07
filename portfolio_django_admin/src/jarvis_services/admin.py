
from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Max
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Service, ServiceGroup, ServiceContent


# ── Multi-file upload helpers ────────────────────────────────────────────────

class MultipleFileInput(forms.ClearableFileInput):
    """File input widget that accepts multiple files."""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """FileField that returns a list of uploaded files."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]


# ── Upload form ──────────────────────────────────────────────────────────────

class ServiceContentUploadForm(forms.Form):
    service_group_title = forms.CharField(
        max_length=255,
        label="Service Group Title",
        widget=forms.TextInput(attrs={"class": "vTextField"}),
        help_text="Must match an existing ServiceGroup title exactly.",
    )
    service_title = forms.CharField(
        max_length=255,
        label="Service Title",
        widget=forms.TextInput(attrs={"class": "vTextField"}),
        help_text=(
            "If this Service does not exist it will be created. "
            "If it already exists the upload logic decides whether to append or replace content."
        ),
    )
    content_files = MultipleFileField(
        label="Markdown Files",
        help_text="Select one or more .md files. Files are processed in selection order.",
    )

    def clean_content_files(self):
        files = self.cleaned_data.get("content_files", [])
        non_md = [f.name for f in files if not f.name.lower().endswith(".md")]
        if non_md:
            raise forms.ValidationError(
                f"Only .md files are allowed. Invalid file(s): {', '.join(non_md)}"
            )
        return files


# ── Internal helper ───────────────────────────────────────────────────────────

def _bulk_create_contents(service: Service, files: list, start_seq: int) -> None:
    """Bulk-create ServiceContent rows, reading each file as UTF-8 text."""
    ServiceContent.objects.bulk_create(
        [
            ServiceContent(
                service=service,
                sequence_number=int(f.name.split("_", 1)[0]) + start_seq if ("_" in f.name) and f.name.split("_")[0].isdigit() else start_seq + i,
                content=f.read().decode("utf-8"),
            )
            for i, f in enumerate(files)
        ]
    )



# ── Admin classes ─────────────────────────────────────────────────────────────

@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at", "updated_at")
    search_fields = ("title",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ServiceContent)
class ServiceContentAdmin(admin.ModelAdmin):
    list_display = ("service", "sequence_number", "created_at", "updated_at")
    list_filter = ("service__group",)
    search_fields = ("service__title", "service__group__title")
    ordering = ("service", "sequence_number")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "upload_link")
    list_filter = ("group",)
    search_fields = ("title", "group__title")
    readonly_fields = ("id", "created_at", "updated_at")
    change_list_template = "admin/jarvis_services/service_changelist.html"

    # ── Custom URL ────────────────────────────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "upload-content/",
                self.admin_site.admin_view(self.upload_content_view),
                name="jarvis_services_service_upload_content",
            ),
        ]
        return extra + urls

    # ── Per-row upload shortcut ───────────────────────────────────────────────

    @admin.display(description="Upload Content")
    def upload_link(self, obj):
        url = reverse("admin:jarvis_services_service_upload_content")
        return format_html(
            '<a class="button" href="{}">Upload&nbsp;Content</a>', url
        )

    # ── Upload view ───────────────────────────────────────────────────────────

    def upload_content_view(self, request):
        form_errors = False

        if request.method == "POST":
            form = ServiceContentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                group_title = form.cleaned_data["service_group_title"]
                svc_title = form.cleaned_data["service_title"]
                files = form.cleaned_data["content_files"]

                # ── Step 1: validate ServiceGroup (outside transaction so we
                #    can surface a clean field error without rolling anything back)
                try:
                    group = ServiceGroup.objects.get(title=group_title)
                except ServiceGroup.DoesNotExist:
                    form.add_error(
                        "service_group_title",
                        f'ServiceGroup with title "{group_title}" does not exist.',
                    )
                    form_errors = True

                if not form_errors:
                    try:
                        with transaction.atomic():
                            # ── Step 2: get or create Service ─────────────────
                            service, created = Service.objects.get_or_create(
                                title=svc_title,
                                group=group,
                            )
                            num_files = len(files)

                            if created:
                                # Brand-new service — sequence 1 … N
                                _bulk_create_contents(service, files, start_seq=1)
                                messages.success(
                                    request,
                                    f'Service "{svc_title}" created with '
                                    f"{num_files} content file(s).",
                                )
                            else:
                                # ── Step 3: decide append vs replace ──────────
                                agg = ServiceContent.objects.filter(
                                    service=service
                                ).aggregate(max_seq=Max("sequence_number"))
                                max_existing = agg["max_seq"] or 0

                                if num_files > max_existing:
                                    # More files than current max sequence
                                    # → append, continuing from where we left off
                                    _bulk_create_contents(
                                        service, files, start_seq=max_existing + 1
                                    )
                                    messages.success(
                                        request,
                                        f'Appended {num_files} content file(s) to '
                                        f'service "{svc_title}" '
                                        f"(sequence {max_existing + 1}–"
                                        f"{max_existing + num_files}).",
                                    )
                                else:
                                    # Fewer or equal files → delete all and replace
                                    ServiceContent.objects.filter(
                                        service=service
                                    ).delete()
                                    _bulk_create_contents(service, files, start_seq=1)
                                    messages.success(
                                        request,
                                        f'Replaced all existing content in service '
                                        f'"{svc_title}" with {num_files} new file(s).',
                                    )

                        return redirect(
                            reverse("admin:jarvis_services_service_changelist")
                        )

                    except Exception as exc:
                        messages.error(request, f"Unexpected error: {exc}")

        else:
            form = ServiceContentUploadForm()

        ctx = self.admin_site.each_context(request)
        ctx.update(
            {
                "form": form,
                "title": "Upload Service Content",
                "opts": self.model._meta,
                "has_view_permission": True,
            }
        )
        return render(
            request,
            "admin/jarvis_services/upload_service_content.html",
            ctx,
        )
