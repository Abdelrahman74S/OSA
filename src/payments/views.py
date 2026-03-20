from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction
from django.db.models import Q
from .models import Transaction
from .serializers import TransactionSerializer, TransactionUpdateSerializer


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('auction', 'buyer', 'seller')

    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        transaction = self.get_object()

        if request.user != transaction.buyer:
            return Response(
                {"detail": "Only the buyer can make the payment."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            with db_transaction.atomic():
                buyer = transaction.buyer.__class__.objects.select_for_update().get(pk=transaction.buyer.pk)

                if buyer.balance < transaction.final_price:
                    return Response(
                        {"detail": "Insufficient balance in your wallet."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                buyer.balance -= transaction.final_price
                buyer.save()

                transaction = Transaction.objects.select_for_update().get(pk=transaction.pk)
                transaction.mark_as_paid()

            return Response(
                {"status": "Payment completed successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='ship')
    def ship(self, request, pk=None):
        transaction = self.get_object()

        if request.user != transaction.seller:
            return Response(
                {"detail": "Only the seller can update the shipping status."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TransactionUpdateSerializer(transaction, data=request.data)

        if serializer.is_valid():
            serializer.save()
            try:
                transaction.mark_as_shipped()
                return Response(
                    {"status": "Transaction marked as shipped."},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='confirm-delivery')
    def confirm_delivery(self, request, pk=None):
        transaction = self.get_object()

        # Only buyer can confirm delivery
        if request.user != transaction.buyer:
            return Response(
                {"detail": "Only the buyer can confirm delivery."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            with db_transaction.atomic():
                transaction = Transaction.objects.select_for_update().get(pk=transaction.pk)
                transaction.mark_as_delivered()

                seller = transaction.seller.__class__.objects.select_for_update().get(pk=transaction.seller.pk)
                seller.balance += transaction.seller_earnings
                seller.save()

            return Response(
                {"status": "Delivery confirmed and seller earnings transferred."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )