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


class Client(models.Model):
    """Cliente del taller; se mantiene independiente para asociarlo a sucursales en una fase posterior."""

    full_name = models.CharField(max_length=160)
    alternate_contact_name = models.CharField(max_length=160)
    age = models.PositiveSmallIntegerField()
    birth_date = models.DateField()
    personal_phone = models.CharField(
        max_length=16,
        unique=True,
        validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')],
    )
    work_phone = models.CharField(
        max_length=16,
        validators=[RegexValidator(r'^\+52\d{10}$', 'El teléfono debe almacenarse como +52 seguido de 10 dígitos.')],
    )
    street = models.CharField(max_length=160)
    neighborhood = models.CharField(max_length=120)
    municipality = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=5, validators=[RegexValidator(r'^\d{5}$', 'El código postal debe tener 5 dígitos.')])
    personal_email = models.EmailField(max_length=254, unique=True)
    work_email = models.EmailField(max_length=254, blank=True)
    photo = models.FileField(upload_to='clients/%Y/%m/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes'
        ordering = ['full_name', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['full_name', 'birth_date'],
                name='clientes_nombre_fecha_nacimiento_unico',
            ),
        ]

    def __str__(self):
        return self.full_name
