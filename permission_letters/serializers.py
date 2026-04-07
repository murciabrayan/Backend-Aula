from rest_framework import serializers

from accounts.file_validators import validate_pdf_file
from accounts.models import UserDocument
from accounts.serializers import UserDocumentSerializer
from .models import PermissionLetter, PermissionLetterRecipient


class PermissionLetterRecipientSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_document = serializers.CharField(source="student.cedula", read_only=True)
    signed_document_url = serializers.SerializerMethodField()
    user_document = UserDocumentSerializer(read_only=True)

    class Meta:
        model = PermissionLetterRecipient
        fields = [
            "id",
            "student",
            "student_name",
            "student_email",
            "student_document",
            "status",
            "responded_at",
            "signed_document_url",
            "user_document",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.email

    def get_signed_document_url(self, obj):
        request = self.context.get("request")
        if not obj.signed_document:
            return None
        try:
            return request.build_absolute_uri(obj.signed_document.url) if request else obj.signed_document.url
        except (AttributeError, OSError, ValueError, FileNotFoundError):
            return None


class PermissionLetterSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.nombre", read_only=True)
    document_url = serializers.SerializerMethodField()
    recipients = PermissionLetterRecipientSerializer(many=True, read_only=True)
    accepted_count = serializers.SerializerMethodField()
    rejected_count = serializers.SerializerMethodField()
    pending_count = serializers.SerializerMethodField()

    class Meta:
        model = PermissionLetter
        fields = [
            "id",
            "title",
            "description",
            "course",
            "course_name",
            "document",
            "document_url",
            "created_at",
            "updated_at",
            "accepted_count",
            "rejected_count",
            "pending_count",
            "recipients",
        ]
        extra_kwargs = {"document": {"write_only": True}}

    def validate_document(self, value):
        try:
            return validate_pdf_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))

    def get_document_url(self, obj):
        request = self.context.get("request")
        try:
            return request.build_absolute_uri(obj.document.url) if request else obj.document.url
        except (AttributeError, OSError, ValueError, FileNotFoundError):
            return None

    def get_accepted_count(self, obj):
        return obj.recipients.filter(status=PermissionLetterRecipient.STATUS_ACCEPTED).count()

    def get_rejected_count(self, obj):
        return obj.recipients.filter(status=PermissionLetterRecipient.STATUS_REJECTED).count()

    def get_pending_count(self, obj):
        return obj.recipients.filter(status=PermissionLetterRecipient.STATUS_PENDING).count()


class StudentPermissionLetterSerializer(serializers.ModelSerializer):
    permission_letter_id = serializers.IntegerField(source="permission_letter.id", read_only=True)
    title = serializers.CharField(source="permission_letter.title", read_only=True)
    description = serializers.CharField(source="permission_letter.description", read_only=True)
    course_name = serializers.CharField(source="permission_letter.course.nombre", read_only=True)
    document_url = serializers.SerializerMethodField()
    signed_document_url = serializers.SerializerMethodField()

    class Meta:
        model = PermissionLetterRecipient
        fields = [
            "id",
            "permission_letter_id",
            "title",
            "description",
            "course_name",
            "document_url",
            "status",
            "responded_at",
            "signed_document_url",
        ]

    def get_document_url(self, obj):
        request = self.context.get("request")
        try:
            return (
                request.build_absolute_uri(obj.permission_letter.document.url)
                if request
                else obj.permission_letter.document.url
            )
        except (AttributeError, OSError, ValueError, FileNotFoundError):
            return None

    def get_signed_document_url(self, obj):
        request = self.context.get("request")
        try:
            if obj.user_document and obj.user_document.file:
                return (
                    request.build_absolute_uri(obj.user_document.file.url)
                    if request
                    else obj.user_document.file.url
                )
        except (AttributeError, OSError, ValueError, FileNotFoundError):
            return None
        return None
