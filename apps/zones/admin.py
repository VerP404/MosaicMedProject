import csv
import os
from pathlib import Path
from django.contrib import admin
from django.contrib import messages
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from .models import (
    Address,
    Organization,
    SiteType,
    Corpus,
    CorpusAddress,
    Site,
    SiteAddress,
)


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ("id", "street", "housenumber", "city", "postcode", "osm_id", "source", "created_at")
    list_filter = ("city", "postcode", "source", "osm_type", "created_at")
    search_fields = ("street", "housenumber", "city", "postcode", "osm_id")
    ordering = ("city", "street", "housenumber")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("OSM данные", {
            "fields": ("osm_id", "osm_type", "source"),
        }),
        ("Адрес", {
            "fields": ("street", "housenumber", "city", "postcode"),
        }),
        ("Координаты", {
            "fields": ("latitude", "longitude"),
        }),
        ("Дополнительно", {
            "fields": ("raw_tags", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    list_per_page = 50
    actions_list = ["load_addresses_from_csv"]

    @action(
        description=_("Загрузить адреса из CSV"),
        url_path="load-addresses-csv",
        permissions=["load_addresses_from_csv"]
    )
    def load_addresses_from_csv(self, request: HttpRequest):
        """Загружает адреса из CSV файла."""
        # Определяем путь к файлу
        # admin.py находится в apps/zones/, поэтому нужно подняться на 3 уровня вверх до корня проекта
        base_dir = Path(__file__).resolve().parent.parent.parent
        file_path = base_dir / "apps" / "zones" / "data" / "address.csv"

        if not file_path.exists():
            self.message_user(
                request,
                f"Файл не найден: {file_path}",
                messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse_lazy("admin:zones_address_changelist")
            )

        # Загружаем данные
        loaded = 0
        updated = 0
        skipped = 0
        errors = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Проверяем наличие необходимых колонок
                required_columns = ['osm_id', 'osm_type', 'latitude', 'longitude']
                missing_columns = [col for col in required_columns if col not in reader.fieldnames]
                if missing_columns:
                    self.message_user(
                        request,
                        f'Отсутствуют необходимые колонки: {", ".join(missing_columns)}',
                        messages.ERROR,
                    )
                    return HttpResponseRedirect(
                        reverse_lazy("admin:zones_address_changelist")
                    )

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Парсим osm_id (формат: "type/id")
                        osm_id_full = row.get('osm_id', '').strip()
                        if not osm_id_full:
                            skipped += 1
                            continue

                        # Извлекаем тип и ID из osm_id
                        if '/' in osm_id_full:
                            parts = osm_id_full.split('/', 1)
                            osm_type_from_id = parts[0]
                            osm_id = parts[1]
                        else:
                            osm_type_from_id = row.get('osm_type', '').strip()
                            osm_id = osm_id_full

                        # Используем osm_type из колонки, если есть, иначе из osm_id
                        osm_type = row.get('osm_type', '').strip() or osm_type_from_id

                        # Парсим координаты
                        try:
                            latitude = float(row.get('latitude', 0))
                            longitude = float(row.get('longitude', 0))
                        except (ValueError, TypeError):
                            skipped += 1
                            continue

                        # Получаем остальные поля
                        housenumber = row.get('housenumber', '').strip()
                        street = row.get('street', '').strip()
                        city = row.get('city', '').strip()
                        postcode = row.get('postcode', '').strip()

                        # Создаем или обновляем адрес
                        address_data = {
                            'osm_id': osm_id,
                            'osm_type': osm_type,
                            'latitude': latitude,
                            'longitude': longitude,
                            'housenumber': housenumber,
                            'street': street,
                            'city': city,
                            'postcode': postcode,
                            'source': 'csv_import',
                        }

                        address, created = Address.objects.update_or_create(
                            osm_type=osm_type,
                            osm_id=osm_id,
                            defaults=address_data
                        )
                        if created:
                            loaded += 1
                        else:
                            updated += 1

                    except Exception as e:
                        errors += 1
                        if errors <= 10:  # Логируем только первые 10 ошибок
                            self.message_user(
                                request,
                                f'Ошибка в строке {row_num}: {str(e)}',
                                messages.WARNING,
                            )

            self.message_user(
                request,
                f'Загрузка завершена: загружено новых - {loaded}, обновлено - {updated}, пропущено - {skipped}, ошибок - {errors}',
                messages.SUCCESS,
            )

        except Exception as e:
            self.message_user(
                request,
                f'Критическая ошибка при загрузке: {str(e)}',
                messages.ERROR,
            )

        return HttpResponseRedirect(
            reverse_lazy("admin:zones_address_changelist")
        )

    def has_load_addresses_from_csv_permission(self, request: HttpRequest):
        """Проверка прав на загрузку адресов."""
        return request.user.is_staff


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ("code", "name", "address", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("code", "name", "address__street", "address__housenumber")
    autocomplete_fields = ("address",)
    fieldsets = (
        ("Основная информация", {
            "fields": ("code", "name", "description", "address"),
        }),
        ("Геометрия", {
            "fields": ("polygon", "color", "area"),
        }),
        ("Дополнительно", {
            "fields": ("is_active", "metadata", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("area", "created_at", "updated_at")
    list_per_page = 50


@admin.register(SiteType)
class SiteTypeAdmin(ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


class CorpusAddressInline(TabularInline):
    model = CorpusAddress
    extra = 1
    autocomplete_fields = ("address",)


@admin.register(Corpus)
class CorpusAdmin(ModelAdmin):
    list_display = ("name", "organization", "address", "is_active", "area", "created_at")
    list_filter = ("organization", "is_active", "created_at")
    search_fields = ("name", "organization__name", "address__street", "address__housenumber")
    autocomplete_fields = ("organization", "address")
    inlines = [CorpusAddressInline]
    fieldsets = (
        ("Основная информация", {
            "fields": ("organization", "name", "description", "address"),
        }),
        ("Геометрия", {
            "fields": ("polygon", "color", "area"),
        }),
        ("Дополнительно", {
            "fields": ("is_active", "metadata", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("area", "created_at", "updated_at")
    list_per_page = 50


class SiteAddressInline(TabularInline):
    model = SiteAddress
    extra = 1
    autocomplete_fields = ("address", "type")
    readonly_fields = ("assigned_at",)


@admin.register(Site)
class SiteAdmin(ModelAdmin):
    list_display = ("name", "type", "corpus", "is_active", "area", "created_at")
    list_filter = ("type", "is_active", "corpus", "corpus__organization", "created_at")
    search_fields = ("name", "corpus__name", "corpus__organization__name")
    autocomplete_fields = ("corpus", "type")
    inlines = [SiteAddressInline]
    fieldsets = (
        ("Основная информация", {
            "fields": ("corpus", "name", "type", "description"),
        }),
        ("Геометрия", {
            "fields": ("polygon", "color", "area"),
        }),
        ("Дополнительно", {
            "fields": ("is_active", "metadata", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("area", "created_at", "updated_at")
    list_per_page = 50
    actions = ["update_polygon_from_addresses"]

    @admin.action(description="Обновить полигон из координат привязанных адресов")
    def update_polygon_from_addresses(self, request, queryset):
        """Действие для обновления полигонов участков на основе адресов."""
        updated = 0
        for site in queryset:
            if site.update_polygon_from_addresses():
                updated += 1
        
        if updated:
            self.message_user(
                request,
                f"Полигоны обновлены для {updated} из {queryset.count()} участков.",
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "Не удалось обновить полигоны. Проверьте, что к участкам привязаны адреса с координатами.",
                messages.WARNING,
            )


@admin.register(SiteAddress)
class SiteAddressAdmin(ModelAdmin):
    list_display = ("address", "site", "type", "assigned_method", "assigned_at")
    list_filter = ("type", "assigned_method", "site__corpus")
    search_fields = (
        "address__street",
        "address__housenumber",
        "site__name",
        "site__corpus__name",
    )
    autocomplete_fields = ("address", "site", "type")
    readonly_fields = ("assigned_at",)


@admin.register(CorpusAddress)
class CorpusAddressAdmin(ModelAdmin):
    list_display = ("corpus", "address", "role")
    list_filter = ("role", "corpus")
    search_fields = (
        "corpus__name",
        "address__street",
        "address__housenumber",
    )
    autocomplete_fields = ("corpus", "address")
