from rest_framework import serializers
from .models import Course, Subject, Area
from accounts.models import User


# ===================== SUBJECT =====================

class SubjectSerializer(serializers.ModelSerializer):
    area_nombre = serializers.CharField(source="area.nombre", read_only=True)

    class Meta:
        model = Subject
        fields = "__all__"


# ===================== AREA =====================

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = "__all__"


# ===================== COURSE =====================

class CourseSerializer(serializers.ModelSerializer):
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

    areas = AreaSerializer(
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
            "areas",
        ]

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

    def update(self, instance, validated_data):
        estudiantes_data = validated_data.pop("estudiantes", None)
        docente_data = validated_data.pop("docente", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if docente_data is not None:
            instance.docente = docente_data

        instance.save()

        if estudiantes_data is not None:
            instance.estudiantes.set(estudiantes_data)

        return instance