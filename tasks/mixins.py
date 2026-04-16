from django.core.exceptions import PermissionDenied


class UserIsOwnerMixin:
    """
    Mixin that checks whether the current user is the owner of the task.
    Raises PermissionDenied (403) if not.
    """

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.owner != request.user:
            raise PermissionDenied("Ви не маєте доступу до цієї задачі.")
        return super().dispatch(request, *args, **kwargs)
