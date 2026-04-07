from collections import defaultdict
from io import BytesIO
import os
import zipfile

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from accounts.models import User
from accounts.permissions import IsAdminRoleOrReadOnly
from courses.models import Course, Subject
from assignments.models import Assignment, Submission
from attendance.models import Attendance
from .models import (
    ReportCardConfig,
    Indicator,
    SubjectIndicatorAssignment,
)
from .serializers import (
    IndicatorSerializer,
    SubjectIndicatorAssignmentSerializer,
)


RECTOR_FIJO = "Leonardo Murcia"


class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.role in ["ADMIN", "TEACHER"]:
            return Indicator.objects.all().order_by("descripcion")
        return Indicator.objects.none()


class SubjectIndicatorAssignmentViewSet(viewsets.ModelViewSet):
    queryset = SubjectIndicatorAssignment.objects.all().select_related(
        "materia",
        "materia__curso",
        "indicador",
    )
    serializer_class = SubjectIndicatorAssignmentSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = SubjectIndicatorAssignment.objects.all().select_related(
            "materia",
            "materia__curso",
            "indicador",
        )

        subject_id = self.request.query_params.get("subject")
        if subject_id:
            queryset = queryset.filter(materia_id=subject_id)

        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(materia__curso_id=course_id)

        if user.role == "ADMIN":
            return queryset.order_by("materia__nombre", "periodo", "id")

        if user.role == "TEACHER":
            return queryset.filter(materia__docente=user).order_by(
                "materia__nombre", "periodo", "id"
            )

        if user.role == "STUDENT":
            return queryset.filter(materia__curso__estudiantes=user).order_by(
                "materia__nombre", "periodo", "id"
            )

        return SubjectIndicatorAssignment.objects.none()


def get_performance_label(score):
    if score is None:
        return "Sin calificar"
    if score >= 4.6:
        return "SUPERIOR"
    if score >= 4.0:
        return "ALTO"
    if score >= 3.0:
        return "BÁSICO"
    return "BAJO"


def avg_or_none(values):
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def format_score(value):
    return f"{value:.1f}" if value is not None else ""


def format_int_or_blank(value):
    return str(value) if value is not None else ""


def format_indicator_text(text):
    if not text:
        return ""
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br/>")


def unique_keep_order(values):
    seen = set()
    result = []
    for value in values:
        clean = (value or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def build_period_slug(period_value):
    period_value = (period_value or "").strip()
    if not period_value:
        period_value = "periodo"
    return slugify(period_value) or "periodo"


def build_student_pdf_filename(student_name, period_value):
    student_slug = slugify(student_name) or "estudiante"
    period_slug = build_period_slug(period_value)
    return f"boletin_{student_slug}_{period_slug}.pdf"


def build_course_zip_filename(course_name, period_value):
    course_slug = slugify(course_name) or "curso"
    period_slug = build_period_slug(period_value)
    return f"boletines_{course_slug}_{period_slug}.zip"


def get_report_period_title(periodo_value):
    periodo_str = str(periodo_value).strip().upper()

    mapping = {
        "1": "PRIMER PERIODO",
        "2": "SEGUNDO PERIODO",
        "3": "TERCER PERIODO",
        "4": "CUARTO PERIODO",
        "PERIODO 1": "PRIMER PERIODO",
        "PERIODO 2": "SEGUNDO PERIODO",
        "PERIODO 3": "TERCER PERIODO",
        "PERIODO 4": "CUARTO PERIODO",
        "PRIMER PERIODO": "PRIMER PERIODO",
        "SEGUNDO PERIODO": "SEGUNDO PERIODO",
        "TERCER PERIODO": "TERCER PERIODO",
        "CUARTO PERIODO": "CUARTO PERIODO",
    }

    return mapping.get(periodo_str, periodo_str if periodo_str else "PERIODO")


def calculate_ranks(student_scores_map):
    valid_items = [
        (student_id, score)
        for student_id, score in student_scores_map.items()
        if score is not None
    ]
    valid_items.sort(key=lambda item: item[1], reverse=True)

    ranks = {}
    last_score = None
    last_rank = None

    for index, (student_id, score) in enumerate(valid_items, start=1):
        if score == last_score:
            ranks[student_id] = last_rank
        else:
            ranks[student_id] = index
            last_rank = index
            last_score = score

    return ranks


def build_student_academic_rows(
    student,
    subjects,
    assignments,
    submission_map,
    indicators_map,
):
    report_rows = []

    for subject in subjects:
        subject_assignments = [a for a in assignments if a.materia_id == subject.id]
        period_scores = defaultdict(list)

        for assignment in subject_assignments:
            submission = submission_map.get((student.id, assignment.id))
            if submission and submission.calificacion is not None:
                period_scores[assignment.periodo].append(float(submission.calificacion))

        p1 = avg_or_none(period_scores[1])
        p2 = avg_or_none(period_scores[2])
        p3 = avg_or_none(period_scores[3])
        p4 = avg_or_none(period_scores[4])

        definitive_values = [x for x in [p1, p2, p3, p4] if x is not None]
        definitiva = avg_or_none(definitive_values)

        report_rows.append({
            "materia_id": subject.id,
            "materia": subject.nombre,
            "area_id": subject.area_id,
            "area": subject.area.nombre if subject.area else "Sin área",
            "indicadores": unique_keep_order(indicators_map.get(subject.id, [])),
            "p1": p1,
            "p2": p2,
            "p3": p3,
            "p4": p4,
            "definitiva": definitiva,
            "desempeno": get_performance_label(definitiva),
        })

    return report_rows


def build_grouped_rows(report_rows):
    grouped_rows_dict = defaultdict(list)
    for row in report_rows:
        grouped_rows_dict[row["area"]].append(row)

    return [
        {
            "area": area_name,
            "materias": rows,
        }
        for area_name, rows in grouped_rows_dict.items()
    ]


def build_student_period_averages(report_rows):
    promedio_p1 = avg_or_none([row["p1"] for row in report_rows if row["p1"] is not None])
    promedio_p2 = avg_or_none([row["p2"] for row in report_rows if row["p2"] is not None])
    promedio_p3 = avg_or_none([row["p3"] for row in report_rows if row["p3"] is not None])
    promedio_p4 = avg_or_none([row["p4"] for row in report_rows if row["p4"] is not None])
    promedio_def = avg_or_none(
        [row["definitiva"] for row in report_rows if row["definitiva"] is not None]
    )

    return {
        "p1": promedio_p1,
        "p2": promedio_p2,
        "p3": promedio_p3,
        "p4": promedio_p4,
        "definitiva": promedio_def,
        "desempeno_general": get_performance_label(promedio_def),
    }


def build_student_absences(student, course):
    attendance_qs = Attendance.objects.filter(
        student=student,
        course=course,
        status="ABSENT",
        is_justified=False,
    )

    period_absences = {1: 0, 2: 0, 3: 0, 4: 0}

    for item in attendance_qs:
        if item.periodo in period_absences:
            period_absences[item.periodo] += 1

    total_absences = sum(period_absences.values())

    return {
        "p1": period_absences[1],
        "p2": period_absences[2],
        "p3": period_absences[3],
        "p4": period_absences[4],
        "total": total_absences,
    }


def build_course_positions(course, subjects, assignments, indicators_map):
    students = list(
        course.estudiantes.filter(role="STUDENT").order_by("first_name", "last_name")
    )

    submissions = Submission.objects.filter(
        estudiante__in=students,
        tarea__materia__curso=course
    ).select_related("tarea", "tarea__materia", "estudiante")

    submission_map = {
        (submission.estudiante_id, submission.tarea_id): submission
        for submission in submissions
    }

    student_averages_map = {}

    for student in students:
        report_rows = build_student_academic_rows(
            student=student,
            subjects=subjects,
            assignments=assignments,
            submission_map=submission_map,
            indicators_map=indicators_map,
        )
        student_averages_map[student.id] = build_student_period_averages(report_rows)

    return {
        "p1": calculate_ranks({
            student_id: values["p1"]
            for student_id, values in student_averages_map.items()
        }),
        "p2": calculate_ranks({
            student_id: values["p2"]
            for student_id, values in student_averages_map.items()
        }),
        "p3": calculate_ranks({
            student_id: values["p3"]
            for student_id, values in student_averages_map.items()
        }),
        "p4": calculate_ranks({
            student_id: values["p4"]
            for student_id, values in student_averages_map.items()
        }),
        "definitiva": calculate_ranks({
            student_id: values["definitiva"]
            for student_id, values in student_averages_map.items()
        }),
    }


def build_student_report_data(student_id):
    student = get_object_or_404(User, pk=student_id, role="STUDENT")

    course = student.cursos.select_related("docente", "director_curso").first()
    if not course:
        return None, {"detail": "El estudiante no tiene curso asignado."}

    subjects = list(
        Subject.objects.filter(curso=course).select_related("area").order_by(
            "area__nombre", "nombre"
        )
    )

    assignments = list(
        Assignment.objects.filter(materia__curso=course).select_related("materia")
    )

    indicators_qs = SubjectIndicatorAssignment.objects.filter(
        materia__curso=course
    ).select_related("materia", "indicador").order_by("materia__nombre", "periodo", "id")

    indicators_map = defaultdict(list)
    for item in indicators_qs:
        indicators_map[item.materia_id].append(item.indicador.descripcion)

    submissions = Submission.objects.filter(
        estudiante=student,
        tarea__materia__curso=course
    ).select_related("tarea", "tarea__materia", "estudiante")

    submission_map = {
        (submission.estudiante_id, submission.tarea_id): submission
        for submission in submissions
    }

    report_rows = build_student_academic_rows(
        student=student,
        subjects=subjects,
        assignments=assignments,
        submission_map=submission_map,
        indicators_map=indicators_map,
    )

    boletin_agrupado = build_grouped_rows(report_rows)
    promedios = build_student_period_averages(report_rows)
    fallas = build_student_absences(student, course)
    positions = build_course_positions(course, subjects, assignments, indicators_map)

    director_curso = ""
    teacher = course.director_curso
    if teacher:
        director_curso = f"{teacher.first_name} {teacher.last_name}".strip()

    data = {
        "estudiante": {
            "id": student.id,
            "nombre": f"{student.first_name} {student.last_name}".strip(),
            "cedula": student.cedula,
            "email": student.email,
        },
        "curso": {
            "id": course.id,
            "nombre": course.nombre,
            "director_curso": director_curso,
        },
        "rector_nombre": RECTOR_FIJO,
        "boletin": report_rows,
        "boletin_agrupado": boletin_agrupado,
        "promedio_general": promedios["definitiva"],
        "desempeno_general": promedios["desempeno_general"],
        "resumen_periodos": {
            "promedio": {
                "p1": promedios["p1"],
                "p2": promedios["p2"],
                "p3": promedios["p3"],
                "p4": promedios["p4"],
                "definitiva": promedios["definitiva"],
                "desempeno": promedios["desempeno_general"],
            },
            "puesto": {
                "p1": positions["p1"].get(student.id),
                "p2": positions["p2"].get(student.id),
                "p3": positions["p3"].get(student.id),
                "p4": positions["p4"].get(student.id),
                "definitiva": positions["definitiva"].get(student.id),
            },
            "fallas": {
                "p1": fallas["p1"],
                "p2": fallas["p2"],
                "p3": fallas["p3"],
                "p4": fallas["p4"],
                "total": fallas["total"],
            },
        },
    }

    return data, None


def build_report_card_pdf_buffer(data, config, periodo_seleccionado=""):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.6 * cm,
        leftMargin=0.6 * cm,
        topMargin=0.5 * cm,
        bottomMargin=0.6 * cm,
    )

    styles = getSampleStyleSheet()

    institution_style = ParagraphStyle(
        name="InstitutionStyle",
        parent=styles["Normal"],
        fontName="Helvetica-BoldOblique",
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=11,
        spaceAfter=1,
    )

    resolution_style = ParagraphStyle(
        name="ResolutionStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=8,
        spaceAfter=1,
    )

    report_title_style = ParagraphStyle(
        name="ReportTitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=9,
        spaceAfter=1,
    )

    year_style = ParagraphStyle(
        name="YearStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=9,
    )

    small_center = ParagraphStyle(
        name="SmallCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=9,
    )

    section_label = ParagraphStyle(
        name="SectionLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.5,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#0b2a6f"),
        leading=8,
    )

    section_value = ParagraphStyle(
        name="SectionValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#0b2a6f"),
        leading=8,
    )

    grade_label_style = ParagraphStyle(
        name="GradeLabelStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.6,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=8,
    )

    grade_value_style = ParagraphStyle(
        name="GradeValueStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.8,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=8,
    )

    normal_small = ParagraphStyle(
        name="NormalSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.2,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#0b2a6f"),
        leading=7,
    )

    bold_small = ParagraphStyle(
        name="BoldSmall",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.2,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=7,
    )

    area_style = ParagraphStyle(
        name="AreaStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.2,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2a6f"),
        leading=7,
    )

    elements = []

    logo_left_path = os.path.join(settings.BASE_DIR, "assets", "boletin", "logo_izquierdo.png")
    logo_right_path = os.path.join(settings.BASE_DIR, "assets", "boletin", "logo_derecho.png")

    left_logo = ""
    right_logo = ""

    if os.path.exists(logo_left_path):
        left_logo = Image(logo_left_path, width=1.8 * cm, height=1.8 * cm)

    if os.path.exists(logo_right_path):
        right_logo = Image(logo_right_path, width=1.8 * cm, height=1.8 * cm)

    period_title = get_report_period_title(periodo_seleccionado)

    institution_name = "GIMNASIO LOS CERROS SIMIJACA"
    approval_resolution = "RESOLUCION APROBACION No. 001308 23/11/1999 S.E. 004171 10/12/2004 S.E."
    report_title = f"Boletín de calificaciones {period_title}"
    school_year = "Año 2026"

    header_table = Table(
        [[
            left_logo,
            [
                Paragraph(institution_name, institution_style),
                Paragraph(approval_resolution, resolution_style),
                Paragraph(report_title, report_title_style),
                Paragraph(school_year, year_style),
            ],
            right_logo,
        ]],
        colWidths=[2.2 * cm, 11.6 * cm, 2.2 * cm],
    )
    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )

    elements.append(header_table)
    elements.append(Spacer(1, 0.2 * cm))

    grade_box = Table(
        [
            [Paragraph("GRADO:", grade_label_style)],
            [Paragraph(data["curso"]["nombre"].upper(), grade_value_style)],
        ],
        colWidths=[4.6 * cm],
        rowHeights=[0.58 * cm, 0.58 * cm],
    )
    grade_box.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0b2a6f")),
            ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#0b2a6f")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )

    student_info = Table(
        [
            [
                Paragraph("NOMBRES Y APELLIDOS:", section_label),
                Paragraph(data["estudiante"]["nombre"], section_value),
                grade_box,
            ],
            [
                Paragraph("DOCUMENTO DE IDENTIDAD:", section_label),
                Paragraph(str(data["estudiante"]["cedula"]), section_value),
                "",
            ],
        ],
        colWidths=[3.5 * cm, 8.0 * cm, 4.6 * cm],
        rowHeights=[0.58 * cm, 0.58 * cm],
    )
    student_info.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0b2a6f")),
        ("INNERGRID", (0, 0), (1, -1), 1, colors.HexColor("#0b2a6f")),
        ("SPAN", (2, 0), (2, 1)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (1, -1), 3),
        ("RIGHTPADDING", (0, 0), (1, -1), 3),
        ("TOPPADDING", (0, 0), (1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (1, -1), 2),
        ("VALIGN", (2, 0), (2, 1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 1), "CENTER"),
        ("LEFTPADDING", (2, 0), (2, 1), 0),
        ("RIGHTPADDING", (2, 0), (2, 1), 0),
        ("TOPPADDING", (2, 0), (2, 1), 0),
        ("BOTTOMPADDING", (2, 0), (2, 1), 0),
    ]))

    elements.append(student_info)
    elements.append(Spacer(1, 0.15 * cm))

    table_data = [[
        Paragraph("ÁREAS", bold_small),
        Paragraph("ASIGNATURAS", bold_small),
        Paragraph("INDICADORES DE LOGRO", bold_small),
        Paragraph("1P", bold_small),
        Paragraph("2P", bold_small),
        Paragraph("3P", bold_small),
        Paragraph("4P", bold_small),
        Paragraph("DEF", bold_small),
        Paragraph("DES.", bold_small),
    ]]

    area_start_rows = []
    current_row_index = 1

    for group in data["boletin_agrupado"]:
        materias = group["materias"]
        if not materias:
            continue

        area_start = current_row_index

        for idx, row in enumerate(materias):
            indicators_html = (
                "<br/><br/>".join(format_indicator_text(text) for text in row["indicadores"])
                if row["indicadores"]
                else "Sin indicadores registrados."
            )

            table_data.append([
                Paragraph(group["area"] if idx == 0 else "", area_style),
                Paragraph(row["materia"], normal_small),
                Paragraph(indicators_html, normal_small),
                Paragraph(format_score(row["p1"]), bold_small),
                Paragraph(format_score(row["p2"]), bold_small),
                Paragraph(format_score(row["p3"]), bold_small),
                Paragraph(format_score(row["p4"]), bold_small),
                Paragraph(format_score(row["definitiva"]), bold_small),
                Paragraph(row["desempeno"], normal_small),
            ])
            current_row_index += 1

        area_end = current_row_index - 1
        if area_end > area_start:
            area_start_rows.append((area_start, area_end))

    report_table = Table(
        table_data,
        colWidths=[2.4 * cm, 2.1 * cm, 7.0 * cm, 0.7 * cm, 0.7 * cm, 0.7 * cm, 0.7 * cm, 0.8 * cm, 1.5 * cm],
        repeatRows=1,
    )

    style_commands = [
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0b2a6f")),
        ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#0b2a6f")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (3, 1), (7, -1), "CENTER"),
        ("ALIGN", (8, 1), (8, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    for start_row, end_row in area_start_rows:
        style_commands.append(("SPAN", (0, start_row), (0, end_row)))
        style_commands.append(("VALIGN", (0, start_row), (0, end_row), "MIDDLE"))
        style_commands.append(("ALIGN", (0, start_row), (0, end_row), "CENTER"))

    report_table.setStyle(TableStyle(style_commands))

    elements.append(report_table)
    elements.append(Spacer(1, 0.12 * cm))

    resumen = data["resumen_periodos"]

    summary_matrix = Table(
        [
            [
                Paragraph("PROMEDIO", bold_small),
                Paragraph("", bold_small),
                Paragraph("", bold_small),
                Paragraph(format_score(resumen["promedio"]["p1"]), bold_small),
                Paragraph(format_score(resumen["promedio"]["p2"]), bold_small),
                Paragraph(format_score(resumen["promedio"]["p3"]), bold_small),
                Paragraph(format_score(resumen["promedio"]["p4"]), bold_small),
                Paragraph(format_score(resumen["promedio"]["definitiva"]), bold_small),
                Paragraph(resumen["promedio"]["desempeno"], bold_small),
            ],
            [
                Paragraph("PUESTO", bold_small),
                Paragraph("", bold_small),
                Paragraph("", bold_small),
                Paragraph(format_int_or_blank(resumen["puesto"]["p1"]), bold_small),
                Paragraph(format_int_or_blank(resumen["puesto"]["p2"]), bold_small),
                Paragraph(format_int_or_blank(resumen["puesto"]["p3"]), bold_small),
                Paragraph(format_int_or_blank(resumen["puesto"]["p4"]), bold_small),
                Paragraph(format_int_or_blank(resumen["puesto"]["definitiva"]), bold_small),
                Paragraph("", bold_small),
            ],
            [
                Paragraph("NÚMERO DE FALLAS", bold_small),
                Paragraph("", bold_small),
                Paragraph("", bold_small),
                Paragraph(format_int_or_blank(resumen["fallas"]["p1"]), bold_small),
                Paragraph(format_int_or_blank(resumen["fallas"]["p2"]), bold_small),
                Paragraph(format_int_or_blank(resumen["fallas"]["p3"]), bold_small),
                Paragraph(format_int_or_blank(resumen["fallas"]["p4"]), bold_small),
                Paragraph(format_int_or_blank(resumen["fallas"]["total"]), bold_small),
                Paragraph("", bold_small),
            ],
        ],
        colWidths=[2.4 * cm, 2.1 * cm, 7.0 * cm, 0.7 * cm, 0.7 * cm, 0.7 * cm, 0.7 * cm, 0.8 * cm, 1.5 * cm],
    )
    summary_matrix.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0b2a6f")),
        ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#0b2a6f")),
        ("ALIGN", (3, 0), (8, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    elements.append(summary_matrix)
    elements.append(Spacer(1, 0.6 * cm))

    director_name = data["curso"]["director_curso"] or "Director de grupo"
    rector_name = RECTOR_FIJO

    signatures = Table(
        [
            [
                Paragraph("______________________________", small_center),
                Paragraph("______________________________", small_center),
            ],
            [
                Paragraph(director_name, small_center),
                Paragraph(rector_name, small_center),
            ],
            [
                Paragraph("Director de grupo", small_center),
                Paragraph("Rector", small_center),
            ],
        ],
        colWidths=[7.8 * cm, 7.8 * cm],
    )
    signatures.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(signatures)

    doc.build(elements)
    buffer.seek(0)
    return buffer


class AdminCoursesForReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "ADMIN":
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        courses = Course.objects.all().order_by("nombre")

        data = [
            {
                "id": c.id,
                "nombre": c.nombre,
                "docente": (
                    f"{c.director_curso.first_name} {c.director_curso.last_name}".strip()
                    if c.director_curso else "Sin director"
                ),
                "total_estudiantes": c.estudiantes.count(),
            }
            for c in courses
        ]

        return Response(data, status=status.HTTP_200_OK)


class AdminStudentsByCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        if request.user.role != "ADMIN":
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        course = get_object_or_404(Course, pk=course_id)

        students = course.estudiantes.filter(role="STUDENT").order_by("first_name", "last_name")

        data = [
            {
                "id": s.id,
                "nombre": f"{s.first_name} {s.last_name}".strip(),
                "email": s.email,
                "cedula": s.cedula,
            }
            for s in students
        ]

        return Response(
            {
                "curso": {
                    "id": course.id,
                    "nombre": course.nombre,
                },
                "estudiantes": data,
            },
            status=status.HTTP_200_OK
        )


class StudentReportCardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        if request.user.role != "ADMIN":
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        data, error = build_student_report_data(student_id)
        if error:
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)


class StudentReportCardPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        if request.user.role != "ADMIN":
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        data, error = build_student_report_data(student_id)
        if error:
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        config = ReportCardConfig.objects.first()
        periodo = request.query_params.get("periodo", "")
        pdf_buffer = build_report_card_pdf_buffer(data, config, periodo)
        filename = build_student_pdf_filename(data["estudiante"]["nombre"], periodo)

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )


class CourseReportCardsZIPView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        if request.user.role != "ADMIN":
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        course = get_object_or_404(Course, pk=course_id)
        students = course.estudiantes.filter(role="STUDENT").order_by("first_name", "last_name")
        config = ReportCardConfig.objects.first()
        periodo = request.query_params.get("periodo", "")

        if not students.exists():
            return Response(
                {"detail": "El curso no tiene estudiantes asignados."},
                status=status.HTTP_404_NOT_FOUND,
            )

        zip_buffer = BytesIO()
        generated_count = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for student in students:
                data, error = build_student_report_data(student.id)
                if error:
                    continue

                pdf_buffer = build_report_card_pdf_buffer(data, config, periodo)
                pdf_filename = build_student_pdf_filename(
                    data["estudiante"]["nombre"],
                    periodo,
                )
                zip_file.writestr(pdf_filename, pdf_buffer.getvalue())
                generated_count += 1

        if generated_count == 0:
            return Response(
                {"detail": "No se pudieron generar boletines para este curso."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        zip_buffer.seek(0)
        zip_filename = build_course_zip_filename(course.nombre, periodo)

        return FileResponse(
            zip_buffer,
            as_attachment=True,
            filename=zip_filename,
            content_type="application/zip",
        )
