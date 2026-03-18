from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer


class MyNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(usuario=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, usuario=request.user)
            notification.leida = True
            notification.save()
            return Response({"message": "Notificación marcada como leída"})
        except Notification.DoesNotExist:
            return Response({"error": "No encontrada"}, status=404)


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return Notification.objects.get(pk=pk, usuario=request.user)

    def patch(self, request, pk):
        try:
            notification = self.get_object(request, pk)
        except Notification.DoesNotExist:
            return Response({"error": "No encontrada"}, status=status.HTTP_404_NOT_FOUND)

        notification.leida = request.data.get("leida", True)
        notification.save(update_fields=["leida"])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            notification = self.get_object(request, pk)
        except Notification.DoesNotExist:
            return Response({"error": "No encontrada"}, status=status.HTTP_404_NOT_FOUND)

        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
