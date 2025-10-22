from auditoria.models import Auditoria

class AuditoriaMixin:
    def registrar_auditoria(self, request, accion, entidad, descripcion=""):
        user = getattr(request, "user", None)
        Auditoria.objects.create(
            usuario=user if user and user.is_authenticated else None,
            accion=accion,
            entidad=entidad,
            descripcion=descripcion
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self.registrar_auditoria(
            self.request, 'CREAR', self.__class__.__name__,
            f"Se creó un registro con ID {instance.id}"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self.registrar_auditoria(
            self.request, 'ACTUALIZAR', self.__class__.__name__,
            f"Se actualizó el registro con ID {instance.id}"
        )

    def perform_destroy(self, instance):
        self.registrar_auditoria(
            self.request, 'ELIMINAR', self.__class__.__name__,
            f"Se eliminó el registro con ID {instance.id}"
        )
        instance.delete()
