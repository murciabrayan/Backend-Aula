from rest_framework import serializers
from .models import Indicator, SubjectIndicatorAssignment


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = ["id", "descripcion"]

    def validate_descripcion(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("La descripción no puede estar vacía.")

        qs = Indicator.objects.filter(descripcion__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Ya existe un indicador con esa descripción.")

        return value


class SubjectIndicatorAssignmentSerializer(serializers.ModelSerializer):
    indicador_descripcion = serializers.CharField(
        source="indicador.descripcion",
        read_only=True
    )
    materia_nombre = serializers.CharField(
        source="materia.nombre",
        read_only=True
    )

    class Meta:
        model = SubjectIndicatorAssignment
        fields = [
            "id",
            "materia",
            "materia_nombre",
            "periodo",
            "indicador",
            "indicador_descripcion",
        ]

    def validate(self, attrs):
        materia = attrs.get("materia")
        periodo = attrs.get("periodo")
        indicador = attrs.get("indicador")

        if self.instance:
            materia = materia or self.instance.materia
            periodo = periodo or self.instance.periodo
            indicador = indicador or self.instance.indicador

        if materia and periodo and indicador:
            qs = SubjectIndicatorAssignment.objects.filter(
                materia=materia,
                periodo=periodo,
                indicador=indicador,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    "non_field_errors": [
                        "Ese indicador ya está asignado a la materia en ese periodo."
                    ]
                })

        return attrs