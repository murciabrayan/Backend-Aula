from rest_framework import serializers
from accounts.file_validators import validate_pdf_file
from courses.models import Subject
from .models import Assignment, Submission


class AssignmentSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='materia.curso.nombre', read_only=True)
    periodo_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ['id', 'fecha_creacion']

    def get_periodo_nombre(self, obj):
        return f"Periodo {obj.periodo}"

    def validate_archivo(self, value):
        try:
            return validate_pdf_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class SubmissionSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    tarea_titulo = serializers.CharField(source='tarea.titulo', read_only=True)

    class Meta:
        model = Submission
        fields = '__all__'
        read_only_fields = [
            'id',
            'fecha_entrega',
            'estudiante',
            'calificacion',
            'retroalimentacion',
        ]

    def get_estudiante_nombre(self, obj):
        user = obj.estudiante
        if user.first_name or user.last_name:
            return f"{user.first_name} {user.last_name}".strip()
        return user.username

    def validate_archivo(self, value):
        try:
            return validate_pdf_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class DirectActivityGradeEntrySerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    calificacion = serializers.DecimalField(max_digits=3, decimal_places=1, min_value=0, max_value=5)
    retroalimentacion = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class DirectActivityCreateSerializer(serializers.Serializer):
    materia = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    titulo = serializers.CharField(max_length=200)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    fecha_entrega = serializers.DateField()
    periodo = serializers.ChoiceField(choices=Assignment.PERIOD_CHOICES)
    grades = DirectActivityGradeEntrySerializer(many=True, required=False)
