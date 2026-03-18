from rest_framework import serializers
from accounts.file_validators import validate_pdf_file
from accounts.models import User
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    course_name = serializers.CharField(source="course.nombre", read_only=True)
    attachment_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_name",
            "date",
            "periodo",
            "status",
            "is_justified",
            "justification_type",
            "notes",
            "attachment",
            "attachment_url",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip()

    def get_attachment_url(self, obj):
        request = self.context.get("request")
        if obj.attachment and request:
            return request.build_absolute_uri(obj.attachment.url)
        if obj.attachment:
            return obj.attachment.url
        return None

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        date = attrs.get("date", getattr(self.instance, "date", None))
        status_value = attrs.get("status", getattr(self.instance, "status", "PRESENT"))
        is_justified = attrs.get(
            "is_justified",
            getattr(self.instance, "is_justified", False)
        )
        justification_type = attrs.get(
            "justification_type",
            getattr(self.instance, "justification_type", "NONE")
        )

        if student and course:
            if not course.estudiantes.filter(id=student.id).exists():
                raise serializers.ValidationError({
                    "student": "El estudiante no pertenece a ese curso."
                })

        if is_justified and status_value == "PRESENT":
            raise serializers.ValidationError({
                "is_justified": "No tiene sentido justificar una asistencia en estado presente."
            })

        if not is_justified and justification_type != "NONE":
            raise serializers.ValidationError({
                "justification_type": "Si no está justificada, el tipo debe ser 'Sin justificar'."
            })

        if is_justified and justification_type == "NONE":
            raise serializers.ValidationError({
                "justification_type": "Debes indicar el tipo de justificación."
            })

        if student and date:
            qs = Attendance.objects.filter(student=student, date=date)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "non_field_errors": [
                        "Ya existe un registro de asistencia para este estudiante en esa fecha."
                    ]
                })

        return attrs

    def validate_attachment(self, value):
        try:
            return validate_pdf_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class BulkAttendanceItemSerializer(serializers.Serializer):
    student = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Attendance.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)


class BulkAttendanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    periodo = serializers.ChoiceField(choices=Attendance.PERIOD_CHOICES)
    records = BulkAttendanceItemSerializer(many=True)

    def validate_records(self, value):
        if not value:
            raise serializers.ValidationError("Debes enviar al menos un registro.")
        return value
