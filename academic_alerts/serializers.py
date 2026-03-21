from rest_framework import serializers

from .models import AcademicAlert, AcademicAlertEvent


class AcademicAlertEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AcademicAlertEvent
        fields = [
            "id",
            "event_type",
            "title",
            "notes",
            "metadata",
            "visible_to_student",
            "actor",
            "actor_name",
            "created_at",
        ]

    def get_actor_name(self, obj):
        if not obj.actor:
            return None
        return f"{obj.actor.first_name} {obj.actor.last_name}".strip()


class AcademicAlertSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_name = serializers.CharField(source="course.nombre", read_only=True)
    resolved_by_name = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()

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
            "next_follow_up_due_at",
            "resolved_by",
            "resolved_by_name",
            "resolution_notes",
            "resolved_at",
            "created_at",
            "updated_at",
            "events",
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

    def get_events(self, obj):
        request = self.context.get("request")
        events = obj.events.all()

        if request and getattr(request.user, "role", None) == "STUDENT":
            events = events.filter(visible_to_student=True)

        return AcademicAlertEventSerializer(events, many=True).data


class TeacherFollowUpSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
    improvement_confirmed = serializers.BooleanField(required=False)


class AdminInitialReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    notes = serializers.CharField(required=False, allow_blank=True)


class AdminCloseAlertSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=["POSITIVE", "NEGATIVE"])
    notes = serializers.CharField(required=False, allow_blank=True)
