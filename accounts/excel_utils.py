from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


EXCEL_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}

NAMESPACE_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NAMESPACE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NAMESPACE_PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

ET.register_namespace("", NAMESPACE_MAIN)
ET.register_namespace("r", NAMESPACE_REL)


TEMPLATE_SHEETS = [
    {
        "name": "Estudiantes",
        "headers": [
            "email",
            "cedula",
            "first_name",
            "last_name",
            "direccion",
            "rh",
            "acudiente_nombre",
            "acudiente_cedula",
            "acudiente_telefono",
            "acudiente_email",
        ],
        "sample": [],
    },
    {
        "name": "Docentes",
        "headers": [
            "email",
            "cedula",
            "first_name",
            "last_name",
            "direccion",
            "rh",
            "especialidad",
            "titulo",
        ],
        "sample": [],
    },
]


def validate_excel_file(uploaded_file):
    if not uploaded_file:
        return uploaded_file

    extension = Path(uploaded_file.name or "").suffix.lower()
    content_type = getattr(uploaded_file, "content_type", "") or ""
    if extension != ".xlsx" or (content_type and content_type not in EXCEL_CONTENT_TYPES):
        raise ValueError("Solo se permiten archivos Excel .xlsx.")
    return uploaded_file


def build_bulk_user_template_workbook() -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", _build_content_types())
        workbook.writestr("_rels/.rels", _build_root_relationships())
        workbook.writestr("docProps/core.xml", _build_core_properties())
        workbook.writestr("docProps/app.xml", _build_app_properties())
        workbook.writestr("xl/workbook.xml", _build_workbook_xml())
        workbook.writestr("xl/_rels/workbook.xml.rels", _build_workbook_relationships())
        workbook.writestr("xl/styles.xml", _build_styles_xml())

        for index, sheet in enumerate(TEMPLATE_SHEETS, start=1):
            workbook.writestr(
                f"xl/worksheets/sheet{index}.xml",
                _build_sheet_xml(sheet["headers"], sheet["sample"]),
            )

    buffer.seek(0)
    return buffer.getvalue()


def parse_bulk_user_workbook(file_obj) -> Dict[str, List[Dict[str, str]]]:
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    with ZipFile(file_obj) as workbook:
        shared_strings = _read_shared_strings(workbook)
        sheet_map = _read_sheet_map(workbook)
        relationships = _read_workbook_relationships(workbook)

        parsed = {}
        for sheet_name, rel_id in sheet_map:
            target = relationships.get(rel_id)
            if not target:
                continue
            normalized_target = target.lstrip("/")
            if not normalized_target.startswith("xl/"):
                normalized_target = f"xl/{normalized_target}"
            with workbook.open(normalized_target) as sheet_file:
                parsed[sheet_name] = _read_sheet_rows(sheet_file.read(), shared_strings)

        return parsed


def _build_content_types():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def _build_root_relationships():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def _build_core_properties():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>Proyecto Aula</dc:creator>
  <cp:lastModifiedBy>Proyecto Aula</cp:lastModifiedBy>
  <dc:title>Plantilla de usuarios masivos</dc:title>
</cp:coreProperties>"""


def _build_app_properties():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Proyecto Aula</Application>
</Properties>"""


def _build_workbook_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Estudiantes" sheetId="1" r:id="rId1"/>
    <sheet name="Docentes" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>"""


def _build_workbook_relationships():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def _build_styles_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1F2937"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/><diagonal/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>"""


def _build_sheet_xml(headers: List[str], sample: List[str]):
    worksheet = ET.Element(f"{{{NAMESPACE_MAIN}}}worksheet")
    sheet_views = ET.SubElement(worksheet, f"{{{NAMESPACE_MAIN}}}sheetViews")
    ET.SubElement(sheet_views, f"{{{NAMESPACE_MAIN}}}sheetView", workbookViewId="0")
    sheet_format_pr = ET.SubElement(worksheet, f"{{{NAMESPACE_MAIN}}}sheetFormatPr", defaultRowHeight="15")
    _ = sheet_format_pr
    cols = ET.SubElement(worksheet, f"{{{NAMESPACE_MAIN}}}cols")
    for index in range(1, max(len(headers), len(sample)) + 1):
        ET.SubElement(
            cols,
            f"{{{NAMESPACE_MAIN}}}col",
            min=str(index),
            max=str(index),
            width="24",
            customWidth="1",
        )

    sheet_data = ET.SubElement(worksheet, f"{{{NAMESPACE_MAIN}}}sheetData")
    _append_row(sheet_data, 1, headers, style="1")
    if sample:
        _append_row(sheet_data, 2, sample, style="0")
    return ET.tostring(worksheet, encoding="utf-8", xml_declaration=True)


def _append_row(sheet_data, row_index: int, values: List[str], style="0"):
    row = ET.SubElement(sheet_data, f"{{{NAMESPACE_MAIN}}}row", r=str(row_index))
    for column_index, value in enumerate(values, start=1):
        cell = ET.SubElement(
            row,
            f"{{{NAMESPACE_MAIN}}}c",
            r=f"{_column_letter(column_index)}{row_index}",
            t="inlineStr",
            s=style,
        )
        is_node = ET.SubElement(cell, f"{{{NAMESPACE_MAIN}}}is")
        text_node = ET.SubElement(is_node, f"{{{NAMESPACE_MAIN}}}t")
        text_node.text = value


def _column_letter(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _read_shared_strings(workbook: ZipFile) -> List[str]:
    try:
        with workbook.open("xl/sharedStrings.xml") as shared:
            root = ET.fromstring(shared.read())
    except KeyError:
        return []

    values = []
    for si in root.findall(f".//{{{NAMESPACE_MAIN}}}si"):
        parts = [node.text or "" for node in si.findall(f".//{{{NAMESPACE_MAIN}}}t")]
        values.append("".join(parts))
    return values


def _read_sheet_map(workbook: ZipFile) -> List[Tuple[str, str]]:
    with workbook.open("xl/workbook.xml") as workbook_file:
        root = ET.fromstring(workbook_file.read())

    result = []
    for sheet in root.findall(f".//{{{NAMESPACE_MAIN}}}sheet"):
        result.append((sheet.attrib.get("name", ""), sheet.attrib.get(f"{{{NAMESPACE_REL}}}id", "")))
    return result


def _read_workbook_relationships(workbook: ZipFile) -> Dict[str, str]:
    with workbook.open("xl/_rels/workbook.xml.rels") as rels_file:
        root = ET.fromstring(rels_file.read())

    result = {}
    for rel in root.findall(f".//{{{NAMESPACE_PACKAGE_REL}}}Relationship"):
        result[rel.attrib.get("Id", "")] = rel.attrib.get("Target", "")
    return result


def _read_sheet_rows(content: bytes, shared_strings: List[str]) -> List[Dict[str, str]]:
    root = ET.fromstring(content)
    rows = []
    header_map = {}

    for row in root.findall(f".//{{{NAMESPACE_MAIN}}}row"):
        row_index = int(row.attrib.get("r", "0") or 0)
        values_by_col = {}

        for cell in row.findall(f"{{{NAMESPACE_MAIN}}}c"):
            cell_ref = cell.attrib.get("r", "")
            column = "".join(character for character in cell_ref if character.isalpha())
            values_by_col[column] = _read_cell_value(cell, shared_strings)

        ordered = [values_by_col[column] for column in sorted(values_by_col.keys(), key=_column_index)]
        if row_index == 1:
            header_map = {index: value.strip() for index, value in enumerate(ordered)}
            continue

        if not header_map:
            continue

        if not any(value.strip() for value in ordered):
            continue

        row_data = {}
        for index, header in header_map.items():
            if not header:
                continue
            row_data[header] = ordered[index].strip() if index < len(ordered) else ""
        rows.append(row_data)

    return rows


def _read_cell_value(cell, shared_strings: List[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        parts = [node.text or "" for node in cell.findall(f".//{{{NAMESPACE_MAIN}}}t")]
        return "".join(parts)

    value_node = cell.find(f"{{{NAMESPACE_MAIN}}}v")
    if value_node is None:
        return ""

    raw_value = value_node.text or ""
    if cell_type == "s":
        try:
            return shared_strings[int(raw_value)]
        except (ValueError, IndexError):
            return ""
    return raw_value


def _column_index(column: str) -> int:
    index = 0
    for character in column:
        index = index * 26 + (ord(character.upper()) - 64)
    return index
