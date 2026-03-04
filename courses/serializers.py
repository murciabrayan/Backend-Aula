from rest_framework import serializers
from .models import Course, Subject
from accounts.models import User


# ===================== SUBJECT =====================

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


# ===================== COURSE =====================

class CourseSerializer(serializers.ModelSerializer):
    # nombres amigables para frontend
    name = serializers.CharField(source="nombre")
    description = serializers.CharField(
        source="descripcion",
        allow_blank=True,
        allow_null=True,
        required=False
    )

    teacher = serializers.PrimaryKeyRelatedField(
        source="docente",
        queryset=User.objects.filter(role="TEACHER"),
        allow_null=True,
        required=False
    )

    students = serializers.PrimaryKeyRelatedField(
        source="estudiantes",
        many=True,
        queryset=User.objects.filter(role="STUDENT"),
        required=False
    )

    subjects = SubjectSerializer(
        source="materias",
        many=True,
        read_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "teacher",
            "students",
            "subjects",
        ]

    # ===================== VALIDATION =====================

    def validate(self, attrs):
        nombre = attrs.get("nombre")

        if nombre:
            qs = Course.objects.filter(nombre__iexact=nombre)

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    "name": "Ya existe un curso con ese nombre."
                })

        return attrs

    # ===================== UPDATE () =====================

    def update(self, instance, validated_data):
        estudiantes_data = validated_data.pop("estudiantes", None)
        docente_data = validated_data.pop("docente", None)

        # actualizar campos simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # actualizar docente
        if docente_data is not None:
            instance.docente = docente_data

        instance.save()

        # 🔥 REEMPLAZA COMPLETAMENTE LOS ESTUDIANTES
        if estudiantes_data is not None:
            instance.estudiantes.set(estudiantes_data)

        return instance