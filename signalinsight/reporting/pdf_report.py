"""Professional multi-page engineering PDF report generator using ReportLab."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from signalinsight.core.constants import APP_NAME, APP_SUBTITLE, APP_VERSION
from signalinsight.core.models import AnalysisResult, ParameterValue


class PDFReportGenerator:
    """Generates an audit-grade laboratory technical report from AnalysisResult."""

    @classmethod
    def generate(cls, result: AnalysisResult, output_pdf_path: Path) -> None:
        output_pdf_path = Path(output_pdf_path)
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_pdf_path),
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        styles = getSampleStyleSheet()
        # Custom dark engineering styling
        primary_color = colors.HexColor("#0f2b48")
        accent_color = colors.HexColor("#0077b6")
        text_color = colors.HexColor("#1e293b")

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=primary_color,
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=accent_color,
            fontName="Helvetica",
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=primary_color,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=text_color,
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=text_color,
        )
        bold_cell_style = ParagraphStyle(
            "BoldTableCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            fontName="Helvetica-Bold",
            textColor=text_color,
        )

        elements = []

        # 1. Header Banner
        header_text = f"<b>{APP_NAME}</b> — ENGINEERING ANALYSIS REPORT"
        elements.append(Paragraph(header_text, title_style))
        elements.append(Paragraph(APP_SUBTITLE, subtitle_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceAfter=8))

        # Metadata info block
        meta_table_data = [
            [
                Paragraph("<b>Session ID:</b>", bold_cell_style),
                Paragraph(result.session_id, table_cell_style),
                Paragraph("<b>Generated:</b>", bold_cell_style),
                Paragraph(result.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"), table_cell_style),
            ],
            [
                Paragraph("<b>Source File:</b>", bold_cell_style),
                Paragraph(Path(result.source_file).name, table_cell_style),
                Paragraph("<b>Software Version:</b>", bold_cell_style),
                Paragraph(f"v{APP_VERSION}", table_cell_style),
            ],
            [
                Paragraph("<b>Duration:</b>", bold_cell_style),
                Paragraph(f"{result.duration_s:.4f} s ({result.sample_count:,} samples)", table_cell_style),
                Paragraph("<b>Sample Rate:</b>", bold_cell_style),
                Paragraph(result.sample_rate.display_str(), table_cell_style),
            ],
        ]
        meta_table = Table(meta_table_data, colWidths=[1.3 * inch, 2.4 * inch, 1.3 * inch, 2.5 * inch])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 0.15 * inch))

        # 2. Key Parameter Estimation Summary
        elements.append(Paragraph("1. Signal Parameters & Physical Measurements", section_style))

        param_rows = [
            [
                Paragraph("<b>Parameter</b>", bold_cell_style),
                Paragraph("<b>Measured Value</b>", bold_cell_style),
                Paragraph("<b>Unit</b>", bold_cell_style),
                Paragraph("<b>Source</b>", bold_cell_style),
                Paragraph("<b>Quality</b>", bold_cell_style),
                Paragraph("<b>Confidence</b>", bold_cell_style),
                Paragraph("<b>Estimation Method</b>", bold_cell_style),
            ]
        ]

        def add_p_row(p: ParameterValue):
            val_str = f"{p.value:,.4f}".rstrip('0').rstrip('.') if isinstance(p.value, float) else str(p.value)
            conf_str = f"{p.confidence * 100:.1f}%" if p.confidence > 0 else "N/A"
            param_rows.append(
                [
                    Paragraph(p.name, bold_cell_style),
                    Paragraph(val_str if p.value is not None else "N/A", table_cell_style),
                    Paragraph(p.unit, table_cell_style),
                    Paragraph(f"[{p.source.value}]", table_cell_style),
                    Paragraph(p.quality.value, table_cell_style),
                    Paragraph(conf_str, table_cell_style),
                    Paragraph(p.method, table_cell_style),
                ]
            )

        add_p_row(result.carrier_frequency)
        add_p_row(result.carrier_offset)
        add_p_row(result.symbol_rate)
        add_p_row(result.occupied_bw_99)
        add_p_row(result.bandwidth_3db)
        add_p_row(result.snr_db)
        add_p_row(result.signal_power)
        add_p_row(result.noise_floor)
        add_p_row(result.dc_offset_i)
        add_p_row(result.dc_offset_q)

        param_table = Table(
            param_rows,
            colWidths=[1.6 * inch, 1.0 * inch, 0.5 * inch, 1.1 * inch, 0.7 * inch, 0.8 * inch, 1.8 * inch],
        )
        param_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2b48")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(param_table)
        elements.append(Spacer(1, 0.15 * inch))

        # 3. Automatic Modulation Classification
        elements.append(Paragraph("2. Automatic Modulation Classification (AMC)", section_style))
        if result.modulation_result:
            mod_res = result.modulation_result
            amc_summary = (
                f"<b>Predicted Modulation:</b> <font color='#0077b6' size='+1'><b>{mod_res.predicted_modulation}</b></font> &nbsp;&nbsp;&nbsp;&nbsp;"
                f"<b>Classification Confidence:</b> <b>{mod_res.confidence * 100:.2f}%</b> &nbsp;&nbsp;&nbsp;&nbsp;"
                f"<b>Model:</b> {mod_res.model_name} (v{mod_res.model_version})"
            )
            elements.append(Paragraph(amc_summary, body_style))
            elements.append(Spacer(1, 0.05 * inch))

            # Probabilities distribution table
            prob_rows = [[Paragraph("<b>Class</b>", bold_cell_style), Paragraph("<b>Probability</b>", bold_cell_style)]]
            for cls_name, prob in mod_res.class_probabilities.items():
                prob_rows.append([Paragraph(cls_name, table_cell_style), Paragraph(f"{prob * 100:.2f}%", table_cell_style)])

            prob_table = Table(prob_rows, colWidths=[2.0 * inch, 2.0 * inch])
            prob_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            elements.append(prob_table)
        else:
            elements.append(Paragraph("Modulation classification not performed.", body_style))

        elements.append(Spacer(1, 0.15 * inch))

        # 4. Cumulants & Signal Invariants
        elements.append(Paragraph("3. Higher-Order Statistics & Cumulant Invariants", section_style))
        cum_rows = [
            [
                Paragraph("<b>Cumulant Feature</b>", bold_cell_style),
                Paragraph("<b>Calculated Value</b>", bold_cell_style),
                Paragraph("<b>Definition / Formula</b>", bold_cell_style),
            ]
        ]
        for name, p in result.cumulants.items():
            val_str = f"{p.value:,.4f}" if isinstance(p.value, float) else str(p.value)
            cum_rows.append(
                [
                    Paragraph(p.name, bold_cell_style),
                    Paragraph(val_str, table_cell_style),
                    Paragraph(p.method, table_cell_style),
                ]
            )

        cum_table = Table(cum_rows, colWidths=[2.5 * inch, 1.5 * inch, 3.5 * inch])
        cum_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2b48")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(cum_table)
        elements.append(Spacer(1, 0.15 * inch))

        # 5. Demodulation & Decoding Status
        elements.append(Paragraph("4. Demodulation, Constellation Quality & Decoding Status", section_style))
        demod_info = []
        if result.demodulation_result and result.demodulation_result.evm_rms_pct:
            evm = result.demodulation_result.evm_rms_pct
            demod_info.append(f"<b>EVM RMS:</b> {evm.value:.2f}% [{evm.quality.value}]")
        if result.decoding_result:
            dec = result.decoding_result
            demod_info.append(f"<b>Decoding Framework:</b> {dec.message}")

        if demod_info:
            for item in demod_info:
                elements.append(Paragraph(item, body_style))
        else:
            elements.append(
                Paragraph(
                    "<b>Decoding Status:</b> Decoding unavailable — coding configuration not specified.",
                    body_style,
                )
            )

        # Build PDF
        doc.build(elements)
