from rest_framework import permissions, viewsets
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

