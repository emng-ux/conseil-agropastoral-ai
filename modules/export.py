"""Export du plan stratégique et du plan d'actions en PDF et Word.
Ces fonctions ne doivent être appelées par l'interface qu'après validation
explicite du conseiller (voir modules/plan_strategique.py::is_validated)."""
import io
from datetime import datetime

from docx import Document
from docx.shared import Pt
from fpdf import FPDF

from modules.plan_strategique import is_validated


class ExportNotAllowedError(Exception):
    """Levée si on tente d'exporter un plan non validé par le conseiller."""


def _check_validated(diagnostic: dict):
    if not is_validated(diagnostic):
        raise ExportNotAllowedError(
            "Le plan doit être validé par le conseiller avant export.")


def export_word_bytes(diagnostic: dict, plan: dict, lang: str = "fr") -> bytes:
    _check_validated(diagnostic)
    doc = Document()

    title = "Plan stratégique et plan d'actions" if lang == "fr" else "Strategic plan and action plan"
    doc.add_heading(title, level=0)

    doc.add_paragraph(f"{'Exploitation / OP' if lang == 'fr' else 'Farm / PO'}: {diagnostic.get('nom', '')}")
    doc.add_paragraph(f"{'Conseiller' if lang == 'fr' else 'Advisor'}: {diagnostic.get('conseiller', '')}")

    validation = diagnostic.get("validation", {})
    doc.add_paragraph(
        (f"Validé par {validation.get('validated_by', '')} le {validation.get('date', '')}"
         if lang == "fr" else
         f"Validated by {validation.get('validated_by', '')} on {validation.get('date', '')}"))

    doc.add_heading("Orientations stratégiques" if lang == "fr" else "Strategic orientations", level=1)
    for o in plan.get("orientations", []):
        doc.add_paragraph(o, style="List Bullet")

    doc.add_heading("Plan d'actions" if lang == "fr" else "Action plan", level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = "Light Grid Accent 1"
    headers = ["Action", "Responsable", "Échéance", "Indicateur"] if lang == "fr" \
        else ["Action", "Responsible", "Deadline", "Indicator"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h

    for item in plan.get("action_plan", []):
        row = table.add_row().cells
        row[0].text = item.get("action", "")
        row[1].text = item.get("responsable", "")
        row[2].text = item.get("echeance", "")
        row[3].text = item.get("indicateur", "")

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_x(self.l_margin)
        self.cell(0, 10, self.title_text, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)

    def line(self, text: str, height: float = 8):
        """multi_cell ne remet pas le curseur en marge gauche par défaut : on le force
        avant chaque ligne pour éviter une largeur disponible nulle/négative."""
        self.set_x(self.l_margin)
        self.multi_cell(0, height, text, new_x="LMARGIN", new_y="NEXT")

    def title_line(self, text: str):
        self.set_x(self.l_margin)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")


def export_pdf_bytes(diagnostic: dict, plan: dict, lang: str = "fr") -> bytes:
    _check_validated(diagnostic)

    title = "Plan strategique et plan d'actions" if lang == "fr" else "Strategic plan and action plan"
    pdf = _PDF()
    pdf.title_text = title
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    pdf.line(f"{'Exploitation / OP' if lang == 'fr' else 'Farm / PO'}: {diagnostic.get('nom', '')}")
    pdf.line(f"{'Conseiller' if lang == 'fr' else 'Advisor'}: {diagnostic.get('conseiller', '')}")

    validation = diagnostic.get("validation", {})
    pdf.line(
        (f"Valide par {validation.get('validated_by', '')} le {validation.get('date', '')}"
         if lang == "fr" else
         f"Validated by {validation.get('validated_by', '')} on {validation.get('date', '')}"))
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.title_line("Orientations strategiques" if lang == "fr" else "Strategic orientations")
    pdf.set_font("Helvetica", size=11)
    for o in plan.get("orientations", []):
        pdf.line(f"- {o}", height=7)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.title_line("Plan d'actions" if lang == "fr" else "Action plan")
    pdf.set_font("Helvetica", size=10)
    for item in plan.get("action_plan", []):
        text = f"- {item.get('action', '')} | {item.get('responsable', '')} | " \
               f"{item.get('echeance', '')} | {item.get('indicateur', '')}"
        pdf.line(text, height=7)

    return bytes(pdf.output())
