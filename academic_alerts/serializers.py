from rest_framework import serializers
from .models import AcademicAlert


class AcademicAlertSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_name = serializers.CharField(source="course.nombre", read_only=True)
    resolved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AcademicAlert
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_name",
            "period",
            "alert_type",
            "level",
            "status",
            "title",
            "message_student",
            "message_teacher",
            "message_admin",
            "metric_value",
            "threshold_value",
            "details",
            "resolved_by",
            "resolved_by_name",
            "resolution_notes",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "resolved_at",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip()

    def get_resolved_by_name(self, obj):
        if not obj.resolved_by:
            return None
        return f"{obj.resolved_by.first_name} {obj.resolved_by.last_name}".strip()


class ResolveAcademicAlertSerializer(serializers.Serializer):
    resolution_notes = serializers.CharField(required=False, allow_blank=True)