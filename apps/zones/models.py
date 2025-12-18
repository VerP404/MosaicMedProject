from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import math


def point_in_polygon(point, polygon_coords):
    """
    Проверяет, находится ли точка внутри полигона.
    Использует алгоритм Ray Casting.
    
    Args:
        point: кортеж (longitude, latitude)
        polygon_coords: список координат полигона в формате [[lon, lat], ...]
    
    Returns:
        bool: True если точка внутри полигона
    """
    if not polygon_coords or len(polygon_coords) < 3:
        return False
    
    lon, lat = point
    inside = False
    
    j = len(polygon_coords) - 1
    for i in range(len(polygon_coords)):
        xi, yi = polygon_coords[i]
        xj, yj = polygon_coords[j]
        
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    
    return inside


def calculate_polygon_area(polygon_coords):
    """
    Вычисляет площадь полигона в квадратных метрах.
    Использует формулу Shoelace для сферических координат.
    
    Args:
        polygon_coords: список координат полигона в формате [[lon, lat], ...]
    
    Returns:
        float: площадь в квадратных метрах
    """
    if not polygon_coords or len(polygon_coords) < 3:
        return 0.0
    
    # Радиус Земли в метрах
    R = 6371000
    
    # Закрываем полигон (если первая и последняя точки не совпадают)
    coords = polygon_coords[:]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    
    area = 0.0
    n = len(coords) - 1
    
    for i in range(n):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i + 1]
        
        # Преобразуем в радианы
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon = math.radians(lon2 - lon1)
        
        # Используем формулу для сферической геометрии
        area += dlon * (2 + math.sin(lat1_rad) + math.sin(lat2_rad))
    
    area = abs(area * R * R / 2.0)
    return area


def parse_polygon_from_geojson(geojson_data):
    """
    Парсит GeoJSON данные и возвращает координаты полигона.
    
    Args:
        geojson_data: dict или list с GeoJSON данными
    
    Returns:
        list: список координат [[lon, lat], ...]
    """
    if isinstance(geojson_data, list):
        # Если это уже список координат
        return geojson_data
    elif isinstance(geojson_data, dict):
        # Если это GeoJSON объект
        if geojson_data.get('type') == 'Polygon':
            coords = geojson_data.get('coordinates', [])
            if coords:
                return coords[0]  # Внешнее кольцо
        elif geojson_data.get('type') == 'MultiPolygon':
            coords = geojson_data.get('coordinates', [])
            if coords:
                return coords[0][0]  # Первое кольцо первого полигона
    return []


class Address(models.Model):
    """
    Адрес из OSM данных.
    
    osm_id хранится в формате "type/id" (например, "way/1386954792").
    Уникальность обеспечивается парой (osm_type, osm_id), так как один и тот же
    OSM ID может существовать как node, way и relation одновременно.
    """
    # osm_id в формате "type/id" (например, "way/1386954792")
    osm_id = models.CharField(
        "OSM ID",
        max_length=64,
        help_text="Формат: type/id (например, way/1386954792)",
        db_index=True,
    )
    osm_type = models.CharField(
        "Тип OSM объекта",
        max_length=16,
        db_index=True,
        help_text="node, way или relation",
    )

    latitude = models.FloatField("Широта", db_index=True)
    longitude = models.FloatField("Долгота", db_index=True)

    housenumber = models.CharField(
        "Номер дома",
        max_length=64,
        blank=True,
        db_index=True,
    )
    street = models.CharField(
        "Улица",
        max_length=255,
        blank=True,
        db_index=True,
    )
    city = models.CharField(
        "Город",
        max_length=255,
        blank=True,
        db_index=True,
    )
    postcode = models.CharField(
        "Почтовый индекс",
        max_length=32,
        blank=True,
        db_index=True,
    )

    source = models.CharField(
        "Источник данных",
        max_length=64,
        default="osm_export",
        help_text="Источник импорта: osm_export, pbf_import, manual и т.д.",
        db_index=True,
    )
    raw_tags = models.JSONField(
        "Сырые теги OSM",
        blank=True,
        null=True,
        help_text="Дополнительные теги из OSM (если доступны)",
    )

    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"
        ordering = ["city", "street", "housenumber"]
        # Уникальность по паре (osm_type, osm_id), так как один ID может быть и node, и way
        constraints = [
            models.UniqueConstraint(
                fields=["osm_type", "osm_id"],
                name="unique_osm_address",
            ),
        ]
        indexes = [
            models.Index(fields=["city", "street", "housenumber"]),
            models.Index(fields=["source"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        base = f"{self.street} {self.housenumber}".strip()
        return base or self.osm_id

    def is_inside_polygon(self, polygon_coords):
        """Проверяет, находится ли адрес внутри полигона."""
        if self.longitude is None or self.latitude is None:
            return False
        return point_in_polygon((self.longitude, self.latitude), polygon_coords)


class PolygonBase(models.Model):
    """
    Абстрактная базовая модель для всех сущностей с полигонами.
    
    Содержит общие поля: название, описание, полигон, цвет, площадь,
    метаданные. Наследуется Organization, Corpus, Site.
    """
    name = models.CharField("Название", max_length=255, db_index=True)
    description = models.TextField("Описание", blank=True)
    polygon = models.JSONField(
        "Полигон",
        blank=True,
        null=True,
        help_text="Полигон в формате GeoJSON или массив координат [[lon, lat], ...]",
    )
    color = models.CharField(
        "Цвет",
        max_length=16,
        blank=True,
        help_text="Цвет для отображения на карте, например #ff0000",
    )
    area = models.FloatField(
        "Площадь (кв.м)",
        null=True,
        blank=True,
        help_text="Вычисляется автоматически при сохранении",
    )
    is_active = models.BooleanField("Активен", default=True, db_index=True)
    
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def get_polygon_coords(self):
        """Возвращает координаты полигона в виде списка [[lon, lat], ...]."""
        if not self.polygon:
            return []
        return parse_polygon_from_geojson(self.polygon)

    def save(self, *args, **kwargs):
        """Автоматически вычисляет площадь полигона при сохранении."""
        if self.polygon:
            coords = self.get_polygon_coords()
            if coords and len(coords) >= 3:
                self.area = calculate_polygon_area(coords)
            else:
                self.area = None
        else:
            self.area = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def contains_point(self, longitude, latitude):
        """Проверяет, содержит ли полигон указанную точку."""
        coords = self.get_polygon_coords()
        if not coords:
            return False
        return point_in_polygon((longitude, latitude), coords)

    def contains_address(self, address):
        """Проверяет, содержит ли полигон указанный адрес."""
        if address.longitude is None or address.latitude is None:
            return False
        return self.contains_point(address.longitude, address.latitude)


class Organization(PolygonBase):
    """
    Организация - верхний уровень иерархии.
    
    Определяет общий полигон, внутри которого должны находиться все корпуса.
    Адреса, попадающие в полигон организации, доступны для распределения.
    """
    code = models.CharField(
        "Код",
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Уникальный код организации",
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizations",
        verbose_name="Основной адрес",
    )
    # Дополнительные параметры для будущего расширения
    metadata = models.JSONField(
        "Метаданные",
        blank=True,
        null=True,
        help_text="Дополнительные параметры: удаленность, количество домов и т.д.",
    )

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
        ordering = ["name"]

    def clean(self):
        """Валидация: проверка, что полигон валиден."""
        if self.polygon:
            coords = self.get_polygon_coords()
            if not coords or len(coords) < 3:
                raise ValidationError({"polygon": "Полигон должен содержать минимум 3 точки"})

    def get_addresses_in_polygon(self):
        """Возвращает все адреса, попадающие в полигон организации."""
        if not self.polygon:
            return Address.objects.none()
        
        coords = self.get_polygon_coords()
        if not coords:
            return Address.objects.none()
        
        # Фильтруем адреса по координатам (грубая проверка по bounding box)
        min_lon = min(c[0] for c in coords)
        max_lon = max(c[0] for c in coords)
        min_lat = min(c[1] for c in coords)
        max_lat = max(c[1] for c in coords)
        
        addresses = Address.objects.filter(
            longitude__gte=min_lon,
            longitude__lte=max_lon,
            latitude__gte=min_lat,
            latitude__lte=max_lat
        )
        
        # Точная проверка для каждого адреса
        result = []
        for addr in addresses:
            if self.contains_address(addr):
                result.append(addr)
        
        return Address.objects.filter(id__in=[a.id for a in result])

    def assign_addresses_in_polygon(self):
        """
        Автоматически привязывает все адреса внутри полигона к организации.
        Создает записи OrganizationAddress для адресов, которые еще не привязаны.
        """
        if not self.polygon:
            return 0
        
        addresses = self.get_addresses_in_polygon()
        assigned_count = 0
        
        for address in addresses:
            # Проверяем, не привязан ли уже адрес к этой организации
            if not OrganizationAddress.objects.filter(
                organization=self,
                address=address
            ).exists():
                OrganizationAddress.objects.create(
                    organization=self,
                    address=address,
                    assigned_method='auto'
                )
                assigned_count += 1
        
        return assigned_count

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматической привязки адресов при сохранении полигона."""
        # Вызываем валидацию перед сохранением
        self.full_clean()
        # Сохраняем, чтобы получить ID
        super().save(*args, **kwargs)
        
        # Если полигон установлен, привязываем адреса
        if self.polygon:
            self.assign_addresses_in_polygon()


class OrganizationAddress(models.Model):
    """
    Связь между адресом и организацией.
    
    Автоматически создается при сохранении полигона организации для всех
    адресов, попадающих внутрь полигона.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_addresses",
        verbose_name="Организация",
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name="organization_links",
        verbose_name="Адрес",
    )
    assigned_at = models.DateTimeField(
        "Привязан",
        auto_now_add=True,
    )
    assigned_method = models.CharField(
        "Метод привязки",
        max_length=16,
        default='auto',
        help_text="auto / manual",
    )

    class Meta:
        verbose_name = "Привязка адреса к организации"
        verbose_name_plural = "Привязки адресов к организациям"
        unique_together = ("organization", "address")
        indexes = [
            models.Index(fields=["organization", "assigned_at"]),
        ]

    def __str__(self):
        return f"{self.address} → {self.organization}"


class SiteType(models.Model):
    code = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = "Тип участка"
        verbose_name_plural = "Типы участков"

    def __str__(self):
        return self.name


class Corpus(PolygonBase):
    """
    Корпус - средний уровень иерархии.
    
    Принадлежит организации, имеет свой полигон, который должен находиться
    внутри полигона организации. Внутри корпуса создаются участки.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="corpora",
        verbose_name="Организация",
        help_text="Организация, к которой принадлежит корпус",
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corpora",
        verbose_name="Основной адрес",
    )
    # Дополнительные параметры
    metadata = models.JSONField(
        "Метаданные",
        blank=True,
        null=True,
        help_text="Дополнительные параметры: удаленность, количество домов и т.д.",
    )

    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпуса"
        ordering = ["organization", "name"]
        unique_together = ("organization", "name")

    def clean(self):
        """Валидация корпуса. Полигон корпуса опционален и вычисляется автоматически из участков."""
        # Полигон корпуса не обязателен, поэтому валидация не требуется
        pass

    def update_polygon_from_sites(self):
        """
        Обновляет полигон корпуса на основе полигонов всех привязанных участков.
        
        Создает минимальный охватывающий полигон (bounding box) из всех
        полигонов участков, привязанных к корпусу.
        """
        sites = self.sites.filter(is_active=True).exclude(polygon__isnull=True)
        
        if not sites.exists():
            # Если нет участков, очищаем полигон
            self.polygon = None
            self.area = None
            return False
        
        # Собираем все координаты из всех полигонов участков
        all_coords = []
        for site in sites:
            coords = site.get_polygon_coords()
            if coords and len(coords) >= 3:
                all_coords.extend(coords)
        
        if not all_coords or len(all_coords) < 3:
            return False
        
        # Создаем bounding box (минимальный охватывающий прямоугольник)
        min_lon = min(c[0] for c in all_coords)
        max_lon = max(c[0] for c in all_coords)
        min_lat = min(c[1] for c in all_coords)
        max_lat = max(c[1] for c in all_coords)
        
        # Добавляем небольшой буфер
        buffer = 0.001  # ~100 метров
        polygon_coords = [
            [min_lon - buffer, min_lat - buffer],
            [max_lon + buffer, min_lat - buffer],
            [max_lon + buffer, max_lat + buffer],
            [min_lon - buffer, max_lat + buffer],
            [min_lon - buffer, min_lat - buffer],  # Закрываем полигон
        ]
        
        self.polygon = polygon_coords
        self.save()
        return True

    def get_computed_polygon(self):
        """
        Возвращает вычисленный полигон корпуса на основе участков.
        Если у корпуса есть явно заданный полигон, возвращает его.
        Иначе вычисляет из участков.
        """
        if self.polygon:
            return self.get_polygon_coords()
        
        # Вычисляем из участков
        sites = self.sites.filter(is_active=True).exclude(polygon__isnull=True)
        if not sites.exists():
            return []
        
        all_coords = []
        for site in sites:
            coords = site.get_polygon_coords()
            if coords and len(coords) >= 3:
                all_coords.extend(coords)
        
        if not all_coords or len(all_coords) < 3:
            return []
        
        # Создаем bounding box
        min_lon = min(c[0] for c in all_coords)
        max_lon = max(c[0] for c in all_coords)
        min_lat = min(c[1] for c in all_coords)
        max_lat = max(c[1] for c in all_coords)
        
        buffer = 0.001
        return [
            [min_lon - buffer, min_lat - buffer],
            [max_lon + buffer, min_lat - buffer],
            [max_lon + buffer, max_lat + buffer],
            [min_lon - buffer, max_lat + buffer],
            [min_lon - buffer, min_lat - buffer],
        ]

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова clean перед сохранением."""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_addresses_in_polygon(self):
        """Возвращает все адреса, попадающие в полигон корпуса."""
        if not self.polygon:
            return Address.objects.none()
        
        coords = self.get_polygon_coords()
        if not coords:
            return Address.objects.none()
        
        # Фильтруем адреса по координатам (грубая проверка по bounding box)
        min_lon = min(c[0] for c in coords)
        max_lon = max(c[0] for c in coords)
        min_lat = min(c[1] for c in coords)
        max_lat = max(c[1] for c in coords)
        
        addresses = Address.objects.filter(
            longitude__gte=min_lon,
            longitude__lte=max_lon,
            latitude__gte=min_lat,
            latitude__lte=max_lat
        )
        
        # Точная проверка для каждого адреса
        result = []
        for addr in addresses:
            if self.contains_address(addr):
                result.append(addr)
        
        return Address.objects.filter(id__in=[a.id for a in result])


class CorpusAddress(models.Model):
    corpus = models.ForeignKey(
        Corpus,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name="corpus_links",
    )
    role = models.CharField(
        max_length=32,
        blank=True,
        help_text="main / branch / entrance и т.п.",
    )

    class Meta:
        unique_together = ("corpus", "address")
        verbose_name = "Адрес корпуса"
        verbose_name_plural = "Адреса корпусов"

    def __str__(self):
        return f"{self.corpus} — {self.address}"


class Site(PolygonBase):
    """
    Участок - нижний уровень иерархии.
    
    Принадлежит корпусу, имеет свой полигон, который должен находиться
    внутри полигона корпуса. К участку привязываются адреса.
    """
    corpus = models.ForeignKey(
        Corpus,
        on_delete=models.CASCADE,
        related_name="sites",
        verbose_name="Корпус",
    )
    type = models.ForeignKey(
        SiteType,
        on_delete=models.PROTECT,
        related_name="sites",
        verbose_name="Тип участка",
    )
    # Дополнительные параметры
    metadata = models.JSONField(
        "Метаданные",
        blank=True,
        null=True,
        help_text="Дополнительные параметры: удаленность, количество домов и т.д.",
    )

    class Meta:
        verbose_name = "Участок"
        verbose_name_plural = "Участки"
        unique_together = ("corpus", "type", "name")
        ordering = ["corpus", "type", "name"]

    def clean(self):
        """Валидация: проверка, что полигон участка находится внутри полигона организации."""
        if self.polygon and self.corpus and self.corpus.organization:
            site_coords = self.get_polygon_coords()
            
            if not site_coords:
                return
            
            # Проверяем, что участок находится внутри полигона организации
            org_coords = self.corpus.organization.get_polygon_coords()
            if org_coords:
                for lon, lat in site_coords:
                    if not self.corpus.organization.contains_point(lon, lat):
                        raise ValidationError({
                            "polygon": "Полигон участка должен находиться внутри полигона организации"
                        })

    def assign_addresses_in_polygon(self):
        """
        Автоматически привязывает все адреса внутри полигона к участку.
        Создает записи SiteAddress для адресов, которые еще не привязаны.
        """
        if not self.polygon:
            return 0
        
        addresses = self.get_addresses_in_polygon()
        assigned_count = 0
        
        for address in addresses:
            # Проверяем, не привязан ли уже адрес к этому участку
            if not SiteAddress.objects.filter(
                site=self,
                address=address
            ).exists():
                SiteAddress.objects.create(
                    site=self,
                    address=address,
                    type=self.type,  # Используем тип участка
                    assigned_method='auto'
                )
                assigned_count += 1
        
        return assigned_count

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова clean перед сохранением и обновления полигона корпуса."""
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Если полигон установлен, привязываем адреса
        if self.polygon:
            self.assign_addresses_in_polygon()
        
        # Обновляем полигон корпуса на основе всех участков
        if self.corpus:
            self.corpus.update_polygon_from_sites()

    def __str__(self):
        return f"{self.name} ({self.type.code})"

    def get_addresses_in_polygon(self):
        """Возвращает все адреса, попадающие в полигон участка."""
        if not self.polygon:
            return Address.objects.none()
        
        coords = self.get_polygon_coords()
        if not coords:
            return Address.objects.none()
        
        # Фильтруем адреса по координатам (грубая проверка по bounding box)
        min_lon = min(c[0] for c in coords)
        max_lon = max(c[0] for c in coords)
        min_lat = min(c[1] for c in coords)
        max_lat = max(c[1] for c in coords)
        
        addresses = Address.objects.filter(
            longitude__gte=min_lon,
            longitude__lte=max_lon,
            latitude__gte=min_lat,
            latitude__lte=max_lat
        )
        
        # Точная проверка для каждого адреса
        result = []
        for addr in addresses:
            if self.contains_address(addr):
                result.append(addr)
        
        return Address.objects.filter(id__in=[a.id for a in result])

    def update_polygon_from_addresses(self):
        """
        Обновляет полигон участка на основе координат привязанных адресов.
        
        Создает минимальный охватывающий полигон (convex hull) из всех
        точек адресов, привязанных к участку через SiteAddress.
        """
        addresses = Address.objects.filter(
            site_links__site=self
        ).exclude(longitude__isnull=True, latitude__isnull=True)
        
        if not addresses.exists():
            return False
        
        points = [(addr.longitude, addr.latitude) for addr in addresses if addr.longitude and addr.latitude]
        if not points or len(points) < 3:
            return False
        
        # Создаем convex hull (минимальный охватывающий полигон)
        # Используем простой алгоритм для создания bounding box с небольшим буфером
        if len(points) == 1:
            # Если одна точка, создаем небольшой квадрат вокруг неё
            lon, lat = points[0]
            buffer = 0.001  # ~100 метров
            polygon_coords = [
                [lon - buffer, lat - buffer],
                [lon + buffer, lat - buffer],
                [lon + buffer, lat + buffer],
                [lon - buffer, lat + buffer],
                [lon - buffer, lat - buffer],  # Закрываем полигон
            ]
        elif len(points) == 2:
            # Если две точки, создаем прямоугольник
            lon1, lat1 = points[0]
            lon2, lat2 = points[1]
            buffer = 0.001
            min_lon = min(lon1, lon2) - buffer
            max_lon = max(lon1, lon2) + buffer
            min_lat = min(lat1, lat2) - buffer
            max_lat = max(lat1, lat2) + buffer
            polygon_coords = [
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],  # Закрываем полигон
            ]
        else:
            # Для 3+ точек используем convex hull (упрощенный алгоритм)
            # Сортируем точки по углу от центра
            center_lon = sum(p[0] for p in points) / len(points)
            center_lat = sum(p[1] for p in points) / len(points)
            
            # Сортируем точки по углу
            def angle_from_center(point):
                lon, lat = point
                return math.atan2(lat - center_lat, lon - center_lon)
            
            sorted_points = sorted(points, key=angle_from_center)
            
            # Добавляем буфер
            buffer = 0.001
            polygon_coords = []
            for lon, lat in sorted_points:
                # Смещаем точку наружу от центра
                dx = lon - center_lon
                dy = lat - center_lat
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    scale = (dist + buffer) / dist
                    polygon_coords.append([center_lon + dx * scale, center_lat + dy * scale])
                else:
                    polygon_coords.append([lon + buffer, lat + buffer])
            
            # Закрываем полигон
            if polygon_coords and polygon_coords[0] != polygon_coords[-1]:
                polygon_coords.append(polygon_coords[0])
        
        self.polygon = polygon_coords
        self.save()
        return True


class SiteAddress(models.Model):
    """
    Связь между адресом и участком.
    
    Поле type дублирует site.type для обеспечения ограничения unique_together
    по (address, type) - один адрес может быть привязан только к одному участку
    каждого типа. При создании записи type должен совпадать с site.type.
    """
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="site_addresses",
        verbose_name="Участок",
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name="site_links",
        verbose_name="Адрес",
    )
    # Дублируем тип для ограничения unique_together (address, type)
    # ВАЖНО: type должен совпадать с site.type для согласованности данных
    type = models.ForeignKey(
        SiteType,
        on_delete=models.PROTECT,
        related_name="site_address_links",
        verbose_name="Тип участка",
        help_text="Должен совпадать с типом участка (site.type)",
    )
    assigned_at = models.DateTimeField(
        "Привязан",
        auto_now_add=True,
    )
    assigned_method = models.CharField(
        "Метод привязки",
        max_length=16,
        blank=True,
        help_text="auto / manual",
    )

    class Meta:
        verbose_name = "Привязка адреса к участку"
        verbose_name_plural = "Привязки адресов к участкам"
        unique_together = (
            ("site", "address"),       # не дублировать адрес в одном участке
            ("address", "type"),       # один адрес - один участок каждого типа
        )

    def __str__(self):
        return f"{self.address} → {self.site} ({self.type.code})"
