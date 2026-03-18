from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    LandingCalendarEntry,
    LandingDocument,
    LandingGalleryItem,
    LandingNews,
)
from .permissions import IsAdminRoleOrReadOnly
from .serializers import (
    LandingCalendarEntrySerializer,
    LandingContentSerializer,
    LandingDocumentSerializer,
    LandingGalleryItemSerializer,
    LandingNewsSerializer,
)


class LandingContentView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        payload = {
            "news": LandingNews.objects.filter(is_active=True),
            "gallery": LandingGalleryItem.objects.filter(is_active=True),
            "documents": LandingDocument.objects.filter(is_active=True),
            "calendar_entries": LandingCalendarEntry.objects.filter(is_active=True),
        }
        serializer = LandingContentSerializer(payload, context={"request": request})
        return Response(serializer.data)


class LandingContactMessageView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        email = (request.data.get("email") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        subject = (request.data.get("subject") or "").strip()
        message = (request.data.get("message") or "").strip()

        if not name or not email or not subject or not message:
            return Response(
                {"error": "Completa todos los campos obligatorios del formulario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "@" not in email:
            return Response(
                {"error": "Ingresa un correo valido para poder responderte."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        context = {
            "name": name,
            "email": email,
            "phone": phone or "No proporcionado",
            "subject": subject,
            "message": message,
        }
        html_message = render_to_string(
            "landing_content/emails/contact_message.html",
            context,
        )
        text_message = strip_tags(html_message)

        contact_email = getattr(settings, "LANDING_CONTACT_EMAIL", settings.DEFAULT_FROM_EMAIL)
        mail = EmailMultiAlternatives(
            subject=f"Nuevo mensaje de contacto - {subject}",
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_email],
            reply_to=[email],
        )
        mail.attach_alternative(html_message, "text/html")
        mail.send()

        return Response(
            {"message": "Tu mensaje fue enviado correctamente al equipo institucional."},
            status=status.HTTP_200_OK,
        )


class LandingNewsViewSet(viewsets.ModelViewSet):
    queryset = LandingNews.objects.all()
    serializer_class = LandingNewsSerializer
    permission_classes = [IsAdminRoleOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]


class LandingGalleryItemViewSet(viewsets.ModelViewSet):
    queryset = LandingGalleryItem.objects.all()
    serializer_class = LandingGalleryItemSerializer
    permission_classes = [IsAdminRoleOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]


class LandingDocumentViewSet(viewsets.ModelViewSet):
    queryset = LandingDocument.objects.all()
    serializer_class = LandingDocumentSerializer
    permission_classes = [IsAdminRoleOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]


class LandingCalendarEntryViewSet(viewsets.ModelViewSet):
    queryset = LandingCalendarEntry.objects.all()
    serializer_class = LandingCalendarEntrySerializer
    permission_classes = [IsAdminRoleOrReadOnly]
