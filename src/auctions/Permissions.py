from rest_framework import permissions

class IsSellerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'auction'):
            return obj.auction.seller == request.user
        return obj.seller == request.user