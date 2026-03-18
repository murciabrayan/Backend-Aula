from rest_framework import serializers
from accounts.file_validators import validate_pdf_file
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
        read_only_fields = ['id', 'fecha_entrega', 'estudiante']

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
