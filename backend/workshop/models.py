from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administración'
        RECEPTION = 'RECEPCION', 'Recepción'
        TECHNICIAN = 'TECNICO', 'Técnico'
        VIEWER = 'CONSULTA', 'Consulta'
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.VIEWER)


class WorkOrder(models.Model):
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


class PostalCode(models.Model):
    """Fila normalizada del catálogo oficial de Correos de México."""
    cp = models.CharField(max_length=5, db_index=True)
    neighborhood = models.CharField(max_length=160)
    settlement_type = models.CharField(max_length=80)
    municipality = models.CharField(max_length=160)
    state = models.CharField(max_length=160)

    class Meta:
        db_table = 'codigos_postales'
        constraints = [models.UniqueConstraint(fields=['cp', 'neighborhood', 'settlement_type', 'municipality', 'state'], name='cp_asentamiento_unico')]


class Workshop(models.Model):
    """Taller administrado; sus clientes se relacionan mediante Client.workshop."""
    name = models.CharField(max_length=120)
    street = models.CharField(max_length=120)
    neighborhood = models.CharField(max_length=120)
    municipality = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=5)
    business_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=16, validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')])
    rfc = models.CharField(max_length=13, unique=True)
    contact_email = models.EmailField(max_length=254)
    photo = models.FileField(upload_to='workshops/%Y/%m/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'talleres'
        constraints = [models.UniqueConstraint(fields=['name', 'street', 'neighborhood', 'municipality', 'state', 'postal_code'], name='taller_nombre_direccion_unico')]

    def __str__(self):
        return self.name


class Client(models.Model):
    """Cliente del taller y su relación obligatoria con un taller."""
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVO', 'Activo'
        SUSPENDED = 'SUSPENDIDO', 'Suspendido'
    full_name = models.CharField(max_length=160)
    alternate_contact_name = models.CharField(max_length=160)
    age = models.PositiveSmallIntegerField()
    birth_date = models.DateField()
    personal_phone = models.CharField(max_length=16, unique=True, validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')])
    work_phone = models.CharField(max_length=16, validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')])
    street = models.CharField(max_length=160)
    neighborhood = models.CharField(max_length=160)
    municipality = models.CharField(max_length=160)
    state = models.CharField(max_length=160)
    postal_code = models.CharField(max_length=5)
    personal_email = models.EmailField(max_length=254, unique=True)
    work_email = models.EmailField(max_length=254, blank=True)
    photo = models.FileField(upload_to='clients/%Y/%m/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT, related_name='clients')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes'
        ordering = ['full_name', 'id']
        constraints = [models.UniqueConstraint(fields=['full_name', 'birth_date'], name='clientes_nombre_fecha_nacimiento_unico')]

    def __str__(self):
        return self.full_name
