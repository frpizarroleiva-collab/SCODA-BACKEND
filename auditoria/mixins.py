from auditoria.models import Auditoria
from django.utils import timezone

class AuditoriaMixin:
    def registrar_auditoria(self, request, accion, entidad, descripcion=""):
        user = getattr(request, "user", None)
        Auditoria.objects.create(
            usuario=user if user and user.is_authenticated else None,
            accion=accion,
            entidad=entidad,
            descripcion=descripcion,
            fecha=timezone.now()
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self.registrar_auditoria(
            self.request, 'CREAR', instance.__class__.__name__,
            f"Se creó un registro con ID {instance.id}"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self.registrar_auditoria(
            self.request, 'ACTUALIZAR', instance.__class__.__name__,
            f"Se actualizó el registro con ID {instance.id}"
        )

    def perform_destroy(self, instance):
        self.registrar_auditoria(
            self.request, 'ELIMINAR', instance.__class__.__name__,
            f"Se eliminó el registro con ID {instance.id}"
        )
        instance.delete()
