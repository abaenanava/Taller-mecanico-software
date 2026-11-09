from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models


class ActiveQuerySet(models.QuerySet):
    """Consulta que oculta registros eliminados de forma lógica."""

    def alive(self):
        return self.filter(deleted_at__isnull=True)


class ActiveManager(models.Manager.from_queryset(ActiveQuerySet)):
    """Manager predeterminado: toda lista de negocio excluye eliminados."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    """Base de tablas de negocio: conserva auditoría sin usar DELETE físico."""

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administración'
        RECEPTION = 'RECEPCION', 'Recepción'
        TECHNICIAN = 'TECNICO', 'Técnico'
        VIEWER = 'CONSULTA', 'Consulta'
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.VIEWER)


class WorkOrder(SoftDeleteModel):
    class Status(models.TextChoices):
        DIAGNOSIS = 'DIAGNOSTICO', 'Diagnóstico'
        PROGRESS = 'EN_PROCESO', 'En proceso'
        READY = 'LISTO', 'Listo'
    folio = models.CharField(max_length=20, unique=True)
    vehicle = models.CharField(max_length=120)
    service = models.CharField(max_length=140)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DIAGNOSIS)
    technician = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class PostalCode(SoftDeleteModel):
    """Fila normalizada del catálogo oficial de Correos de México."""

    cp = models.CharField(max_length=5, db_index=True)
    neighborhood = models.CharField(max_length=160)
    settlement_type = models.CharField(max_length=80)
    municipality = models.CharField(max_length=160)
    state = models.CharField(max_length=160)

    class Meta:
        db_table = 'codigos_postales'
        constraints = [models.UniqueConstraint(fields=['cp', 'neighborhood', 'settlement_type', 'municipality', 'state'], name='cp_asentamiento_unico')]


class Status(SoftDeleteModel):
    """Catálogo administrable de estados para clientes y vehículos."""

    name = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'estatus'
        indexes = [models.Index(fields=['name', 'deleted_at'], name='estatus_nombre_activo_idx')]

    def __str__(self):
        return self.name


class Workshop(SoftDeleteModel):
    """Taller administrado; sus clientes se relacionan mediante Client.workshop."""

    name = models.CharField(max_length=120)
    street = models.CharField(max_length=120)
    neighborhood = models.CharField(max_length=120)
    municipality = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=5)
    business_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=16, validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')])
    rfc = models.CharField(max_length=13)
    contact_email = models.EmailField(max_length=254)
    photo = models.FileField(upload_to='workshops/%Y/%m/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'talleres'
        indexes = [models.Index(fields=['deleted_at', 'name'], name='talleres_activos_idx')]

    def __str__(self):
        return self.name


class Client(SoftDeleteModel):
    """Cliente activo de un taller, con estatus del catálogo normalizado."""

    full_name = models.CharField(max_length=160)
    alternate_contact_name = models.CharField(max_length=160)
    age = models.PositiveSmallIntegerField()
    birth_date = models.DateField()
    personal_phone = models.CharField(max_length=16, validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')])
    work_phone = models.CharField(max_length=16, validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')])
    street = models.CharField(max_length=160)
    neighborhood = models.CharField(max_length=160)
    municipality = models.CharField(max_length=160)
    state = models.CharField(max_length=160)
    postal_code = models.CharField(max_length=5)
    personal_email = models.EmailField(max_length=254)
    work_email = models.EmailField(max_length=254, blank=True)
    photo = models.FileField(upload_to='clients/%Y/%m/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT, related_name='clients')
    estatus = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='clients', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes'
        ordering = ['full_name', 'id']
        indexes = [models.Index(fields=['deleted_at', 'workshop', 'estatus'], name='clientes_lista_idx')]

    def __str__(self):
        return self.full_name


class Vehicle(SoftDeleteModel):
    """Vehículo asociado a un cliente que está activo al momento de registrarlo."""

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='vehicles', db_index=True)
    estatus = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='vehicles', db_index=True)
    plate = models.CharField(max_length=9)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    vin = models.CharField(max_length=17)
    year = models.PositiveSmallIntegerField()
    version = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    mileage = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehiculos'
        indexes = [models.Index(fields=['deleted_at', 'client', 'estatus'], name='vehiculos_lista_idx')]

    def __str__(self):
        return f'{self.plate} · {self.brand} {self.model}'
