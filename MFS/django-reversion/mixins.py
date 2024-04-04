from typing import Any

from django.http import JsonResponse
from reversion.models import Version, Revision
from django.core.cache import cache
from rest_framework.decorators import action
from rest_framework.request import Request


class UndoMixin:
    """
    A mixin to add undo functionality to a viewset.
    """
    @staticmethod
    def set_m2m_fields(m2m_fields: dict, obj: Any) -> None:
        """
        Set Many-to-Many fields for the given object.

        Args:
            m2m_fields (dict): A dictionary containing Many-to-Many field names and values.
            obj: The object for which the Many-to-Many fields need to be set.
        """
        if m2m_fields:
            if not isinstance(m2m_fields, dict):
                obj.items.clear()
                obj.items.set(m2m_fields)
            else:
                for field_name, field_value in m2m_fields.items():
                    field = getattr(obj, field_name)
                    field.set(field_value)

    @action(methods=["get"], detail=True)
    def undo(self, request: Request, pk: int, **kwargs) -> JsonResponse:
        """
        Undo the changes made to the object with the specified primary key.

        Args:
            request: The request object.
            pk: The primary key of the object to undo changes for.
            kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: A JSON response indicating the success or failure of the action.
        """
        obj = self.get_serializer_class().Meta.model.objects.filter(id=pk).first()
        m2m_fields = cache.get(hash(obj))

        if not obj:
            revision = Revision.objects.filter(user=request.user).order_by('-date_created').first()
            revision.revert()
            obj = self.get_serializer_class().Meta.model.objects.filter(id=pk).first()
            m2m_fields = cache.get(hash(obj))
            self.set_m2m_fields(m2m_fields, obj)

        elif Revision.objects.filter(id=Version.objects.get_for_object(obj)[0].revision_id).first().user == request.user:
            if len(Version.objects.get_for_object(obj)) >= 2:
                Version.objects.get_for_object(obj)[1].revert()
                revision = Version.objects.get_for_object(obj)[0].revision
                Version.objects.get_for_object(obj)[0].delete()
                revision.delete()
                self.set_m2m_fields(m2m_fields, obj)
            else:
                obj.delete()
        else:
            return JsonResponse({"message": 'The changes was not detected'}, status=200)
        return JsonResponse({"message": 'The action was cancelled'}, status=200)
