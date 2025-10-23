from rest_framework import serializers
from .models import Course
from accounts.models import User

class CourseSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='nombre')
    description = serializers.CharField(
        source='descripcion',
        allow_blank=True,
        allow_null=True,
        required=False
    )
    teacher = serializers.PrimaryKeyRelatedField(
        source='docente',
        queryset=User.objects.filter(role='TEACHER'),
        allow_null=True,
        required=False
    )
    students = serializers.PrimaryKeyRelatedField(
        source='estudiantes',
        many=True,
        queryset=User.objects.filter(role='STUDENT'),
        required=False
    )

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'teacher', 'students']

    def update(self, instance, validated_data):
        # Extrae los datos de docente y estudiantes (si vienen en la petición)
        estudiantes_data = validated_data.pop('estudiantes', None)
        docente_data = validated_data.pop('docente', None)

        # Actualiza los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Actualiza el docente (solo uno por curso)
        if docente_data is not None:
            instance.docente = docente_data

        instance.save()

        # 🔹 Si se envían estudiantes, los agrega (no reemplaza)
        if estudiantes_data is not None:
            instance.estudiantes.add(*estudiantes_data)

        return instance
