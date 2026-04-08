from rest_framework import serializers

from accounts.file_validators import validate_image_file

from .models import (
    LandingCalendarEntry,
    LandingDocument,
    LandingGalleryItem,
    LandingNews,
)


class MediaUrlMixin(serializers.ModelSerializer):
    def build_absolute_media_url(self, file_field):
        request = self.context.get("request")
        if not file_field:
            return None
        try:
            file_url = file_field.url
        except (AttributeError, OSError, ValueError, FileNotFoundError):
            return None

        if request:
            return request.build_absolute_uri(file_url)
        return file_url


class LandingNewsSerializer(MediaUrlMixin):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LandingNews
        fields = [
            "id",
            "title",
            "summary",
            "published_at",
            "image",
            "image_url",
            "display_order",
            "is_active",
        ]
        extra_kwargs = {"image": {"write_only": True, "required": False}}

    def get_image_url(self, obj):
        return self.build_absolute_media_url(obj.image)

    def validate_image(self, value):
        try:
            return validate_image_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class LandingGalleryItemSerializer(MediaUrlMixin):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LandingGalleryItem
        fields = [
            "id",
            "title",
            "detail",
            "event_date",
            "image",
            "image_url",
            "display_order",
            "is_active",
        ]
        extra_kwargs = {"image": {"write_only": True, "required": False}}

    def get_image_url(self, obj):
        return self.build_absolute_media_url(obj.image)

    def validate_image(self, value):
        try:
            return validate_image_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class LandingDocumentSerializer(MediaUrlMixin):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = LandingDocument
        fields = [
            "id",
            "title",
            "description",
            "file",
            "file_url",
            "display_order",
            "is_active",
        ]
        extra_kwargs = {"file": {"write_only": True, "required": False}}

    def get_file_url(self, obj):
        return self.build_absolute_media_url(obj.file)


class LandingCalendarEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingCalendarEntry
        fields = [
            "id",
            "title",
            "detail",
            "event_date",
            "event_time",
            "location",
            "display_order",
            "is_active",
        ]


class LandingContentSerializer(serializers.Serializer):
    news = LandingNewsSerializer(many=True)
    gallery = LandingGalleryItemSerializer(many=True)
    documents = LandingDocumentSerializer(many=True)
    calendar_entries = LandingCalendarEntrySerializer(many=True)
