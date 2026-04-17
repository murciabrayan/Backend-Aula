from rest_framework import serializers
from .models import Course, Subject, Area
from accounts.models import User


# ===================== SUBJECT =====================

class SubjectSerializer(serializers.ModelSerializer):
    area_nombre = serializers.CharField(source="area.nombre", read_only=True)
    course_name = serializers.CharField(source="curso.nombre", read_only=True)
    teacher = serializers.PrimaryKeyRelatedField(
        source="docente",
        queryset=User.objects.filter(role="TEACHER"),
        allow_null=True,
        required=False
    )
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            "id",
            "nombre",
            "curso",
            "area",
            "area_nombre",
            "course_name",
            "teacher",
            "teacher_name",
        ]

    def get_teacher_name(self, obj):
        if obj.docente_id:
            return f"{obj.docente.first_name} {obj.docente.last_name}".strip()
        return ""


class SubjectBulkAssignSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    area = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(),
        allow_null=True,
        required=False,
    )
    teacher = serializers.PrimaryKeyRelatedField(
        source="docente",
        queryset=User.objects.filter(role="TEACHER"),
        allow_null=True,
        required=False,
    )
    courses = serializers.PrimaryKeyRelatedField(
        source="cursos",
        many=True,
        queryset=Course.objects.all(),
    )


class SubjectCourseSyncSerializer(serializers.Serializer):
    subject_id = serializers.PrimaryKeyRelatedField(source="subject", queryset=Subject.objects.all())
    nombre = serializers.CharField(max_length=100)
    area = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(),
        allow_null=True,
        required=False,
    )
    teacher = serializers.PrimaryKeyRelatedField(
        source="docente",
        queryset=User.objects.filter(role="TEACHER"),
        allow_null=True,
        required=False,
    )
    courses = serializers.PrimaryKeyRelatedField(
        source="cursos",
        many=True,
        queryset=Course.objects.all(),
    )


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
        source="director_curso",
        queryset=User.objects.filter(role="TEACHER"),
        allow_null=True,
        required=False
    )
    teacher_name = serializers.SerializerMethodField()
    director_teacher = serializers.SerializerMethodField()

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

    student_details = serializers.SerializerMethodField()

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
            "teacher_name",
            "director_teacher",
            "students",
            "student_details",
            "subjects",
            "areas",
        ]

    def validate(self, attrs):
        nombre = attrs.get("nombre")
        students = attrs.get("estudiantes")

        if nombre:
            qs = Course.objects.filter(nombre__iexact=nombre)

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    "name": "Ya existe un curso con ese nombre."
                })

        if students is not None:
            course_query = Course.objects.filter(estudiantes__in=students).distinct()

            if self.instance:
                course_query = course_query.exclude(pk=self.instance.pk)

            if course_query.exists():
                assigned_names = ", ".join(
                    f"{student.first_name} {student.last_name}".strip()
                    for student in students
                    if course_query.filter(estudiantes=student).exists()
                )
                raise serializers.ValidationError({
                    "students": (
                        "No se puede asignar un estudiante a dos cursos. "
                        f"Ya tienen curso asignado: {assigned_names}."
                    )
                })

        return attrs

    def update(self, instance, validated_data):
        estudiantes_data = validated_data.pop("estudiantes", None)
        director_data = validated_data.pop("director_curso", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if director_data is not None:
            instance.director_curso = director_data
            instance.docente = director_data

        instance.save()

        if estudiantes_data is not None:
            instance.estudiantes.set(estudiantes_data)

        return instance

    def create(self, validated_data):
        estudiantes_data = validated_data.pop("estudiantes", [])
        director_data = validated_data.get("director_curso")

        instance = Course.objects.create(
            **validated_data,
            docente=director_data,
        )

        if estudiantes_data:
            instance.estudiantes.set(estudiantes_data)

        return instance

    def get_student_details(self, obj):
        return [
            {
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "email": student.email,
            }
            for student in obj.estudiantes.filter(role="STUDENT").order_by("first_name", "last_name")
        ]

    def get_teacher_name(self, obj):
        teacher = obj.director_curso or obj.docente
        if not teacher:
            return ""
        return f"{teacher.first_name} {teacher.last_name}".strip()

    def get_director_teacher(self, obj):
        teacher = obj.director_curso or obj.docente
        return teacher.id if teacher else None
