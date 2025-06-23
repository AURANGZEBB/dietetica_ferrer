# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from odoo import fields, models, _
from fpdf import FPDF
from ..models.cttexpress_master_data import CTTEXPRESS_REST_DELIVERY_STATES_LABELS
from odoo.tools import file_open
from io import BytesIO
import xlsxwriter
from odoo.exceptions import UserError
from fpdf import FPDF
from fpdf.enums import XPos, YPos  

class CTTManifestPDF(FPDF):
    def header(self):
        logo_path = file_open('delivery_cttexpress/static/description/icon.png')
        self.image(logo_path.name, x=10, y=8, w=15)

        self.set_font("Helvetica", "B", 12)
        self.set_xy(30, 10)
        self.cell(100, 10, "INFORME DE EXPEDICIONES", new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Mostrar Agencia y Cliente
        if hasattr(self, 'agency_code') and hasattr(self, 'client_code'):
            self.set_font("Helvetica", "", 9)
            self.set_xy(150, 10)
            self.cell(40, 5, f"Agencia: {self.agency_code}", new_x=XPos.RIGHT, new_y=YPos.NEXT)
            self.set_x(150)
            self.cell(40, 5, f"Cliente: {self.client_code}", new_x=XPos.RIGHT, new_y=YPos.NEXT)

        self.ln(5)
        self.add_table_header()

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def add_table_header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(230, 230, 230)
        headers = [
            ("Servicio", 25),
            ("Destinatario", 40),
            ("Población", 30),
            ("Referencia", 50),
            ("Bultos", 20),
            ("Peso", 20),
            ("Estado", 40),
            ("Fecha Envío", 30),
        ]
        for header, width in headers:
            self.cell(width, 8, header, border=1, fill=True)
        self.ln()

    @staticmethod
    def truncate_text(text, max_width, pdf):
        while pdf.get_string_width(text) > max_width and len(text) > 0:
            text = text[:-1]
        return text

    def add_summary(self, total_shipments, total_packages, total_weight):
        self.ln(10)
        self.set_font("Helvetica", "B", 10)
        self.cell(60, 8, f"Total de expediciones: {total_shipments}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(60, 8, f"Total de bultos: {total_packages}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(60, 8, f"Total de peso: {total_weight} kg", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def add_shipment(self, shipment):
        if self.get_y() > 180:
            self.add_page()

        self.set_font("Helvetica", "", 9)
        status_code = shipment.get("shipping_status_code", "")
        status_label = CTTEXPRESS_REST_DELIVERY_STATES_LABELS.get(status_code, "Desconocido")

        data = [
            shipment.get("best_shipping_type_code", "") or "",
            shipment.get("recipient_name", "") or "",
            shipment.get("destin_town_name", "") or "",
            (shipment.get("client_references") or [""])[0],
            str(shipment.get("item_count", 1) or 1),
            f"{shipment.get('shipping_weight_declared', 0) or 0}kg",
            status_label or "",
            shipment.get("shipping_date", "") or ""
        ]

        widths = [25, 40, 30, 50, 20, 20, 40, 30]
        for text, width in zip(data, widths):
            text = str(text or "")
            truncated = self.truncate_text(text, width, self)
            self.cell(width, 8, truncated, border=1)

        self.ln()

class CTTExpressManifestWizard(models.TransientModel):
    _name = "cttexpress.manifest.wizard"
    _description = "Get the CTT Express Manifest for the given date range"

    document_type = fields.Selection(
        selection=[("XLSX", "Excel"), ("PDF", "PDF")],
        string="Format",
        default="XLSX",
        required=True,
    )
    from_date = fields.Date(required=True, default=fields.Date.context_today)
    to_date = fields.Date(required=True, default=fields.Date.context_today)
    carrier_ids = fields.Many2many(
        string="Filter accounts",
        comodel_name="delivery.carrier",
        domain=[("is_ctt", "=", True)],
        help="Leave empty to gather all the CTT account manifests",
    )
    state = fields.Selection(
        selection=[("new", "new"), ("done", "done")],
        default="new",
        readonly=True,
    )
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment", readonly=True, string="Manifests"
    )

    def get_manifest(self):
        carriers = self.carrier_ids or self.env["delivery.carrier"].search([
            ("is_ctt", "=", True)
        ])

        unique_accounts = {
            (c.cttexpress_customer, c.cttexpress_contract, c.cttexpress_agency)
            for c in carriers
        }
        filtered_carriers = self.env["delivery.carrier"]
        for customer, contract, agency in unique_accounts:
            filtered_carriers += fields.first(
                carriers.filtered(
                    lambda x: x.cttexpress_customer == customer
                    and x.cttexpress_contract == contract
                    and x.cttexpress_agency == agency
                )
            )

        from_date_str = fields.Date.to_string(self.from_date)
        to_date_str = fields.Date.to_string(self.to_date)

        for carrier in filtered_carriers:
            if carrier.cttexpress_api == "SOAP":
                ctt_request = carrier._ctt_request()
                error, manifest = ctt_request.report_shipping(
                    "ODOO", self.document_type, from_date_str, to_date_str
                )
                carrier._ctt_check_error(error)
                carrier._ctt_log_request(ctt_request)
                for _filename, file in manifest:
                    filename = "{}{}{}-{}-{}.{}".format(
                        carrier.cttexpress_customer,
                        carrier.cttexpress_contract,
                        carrier.cttexpress_agency,
                        from_date_str.replace("-", ""),
                        to_date_str.replace("-", ""),
                        self.document_type.lower(),
                    )
                    self.attachment_ids += self.env["ir.attachment"].create(
                        {
                            "datas": base64.b64encode(file),
                            "name": filename,
                            "res_model": self._name,
                            "res_id": self.id,
                            "type": "binary",
                        }
                    )
            else:  # REST
                rest_api = carrier._ctt_rest_request()
                shipping_date_range = f"{from_date_str}[range]{to_date_str}"
                result = rest_api.get_bulk_tracking(
                    client_center_code=carrier.cttexpress_rest_agency,
                    shipping_date=shipping_date_range,
                    page_limit=100,
                    page_offsets=1,
                    order_by="-shipping_date",
                )
                if result and "data" in result:
                    if self.document_type == "PDF":
                        pdf = CTTManifestPDF(orientation='L')
                        pdf.set_auto_page_break(auto=True, margin=15)

                        first_shipment = result["data"][0]
                        pdf.agency_code = first_shipment.get("client_center_code", "")
                        pdf.client_code = first_shipment.get("client_code", "")

                        pdf.add_page()

                        for shipment in result["data"]:
                            pdf.add_shipment(shipment)

                        total_shipments = len(result["data"])
                        total_packages = sum(sh.get("item_count", 1) for sh in result["data"])
                        total_weight = sum(sh.get("shipping_weight_declared", 0) for sh in result["data"])

                        pdf.add_summary(total_shipments, total_packages, total_weight)

                        pdf_data = bytes(pdf.output())

                        filename = "{}-{}-{}.pdf".format(
                            carrier.cttexpress_rest_agency,
                            from_date_str.replace("-", ""),
                            to_date_str.replace("-", ""),
                        )
                        self.attachment_ids += self.env["ir.attachment"].create({
                            "datas": base64.b64encode(pdf_data),
                            "name": filename,
                            "res_model": self._name,
                            "res_id": self.id,
                            "type": "binary",
                            "mimetype": "application/pdf",
                        })
                    else:
                        xls_buffer = BytesIO()
                        workbook = xlsxwriter.Workbook(xls_buffer, {'in_memory': True})
                        sheet = workbook.add_worksheet("Expediciones")

                        # Formatos
                        title_format = workbook.add_format({
                            'bold': True, 'font_size': 14,
                            'align': 'center', 'valign': 'vcenter'
                        })
                        header_format = workbook.add_format({
                            'bold': True, 'bg_color': '#D9D9D9',
                            'border': 1, 'align': 'center', 'valign': 'vcenter'
                        })
                        cell_format = workbook.add_format({'border': 1})

                        # Logo
                        try:
                            logo_file = file_open('delivery_cttexpress/static/description/icon.png')
                            sheet.insert_image('A1', logo_file.name, {
                                'x_scale': 0.5,
                                'y_scale': 0.5,
                                'x_offset': 2,
                                'y_offset': 2
                            })
                        except Exception:
                            pass

                        # Título
                        sheet.merge_range('B1:I1', 'INFORME DE EXPEDICIONES', title_format)

                        first_shipment = result["data"][0]
                        agency_code = first_shipment.get("client_center_code", "")
                        client_code = first_shipment.get("client_code", "")

                        sheet.write('G2', "Agencia:", header_format)
                        sheet.write('H2', agency_code, cell_format)

                        sheet.write('G3', "Cliente:", header_format)
                        sheet.write('H3', client_code, cell_format)

                        # Cabeceras
                        headers = [
                            "Servicio", "Destinatario", "Población",
                            "Referencia", "Bultos", "Peso", "Estado", "Fecha Envío"
                        ]
                        col_widths = [len(h) for h in headers]

                        sheet.set_row(4, 20)
                        for col, header in enumerate(headers):
                            sheet.write(4, col, header, header_format)

                        # Datos
                        from ..models.cttexpress_master_data import CTTEXPRESS_REST_DELIVERY_STATES_LABELS
                        for row, shipment in enumerate(result["data"], start=5):
                            status_code = shipment.get("shipping_status_code", "")
                            status_label = CTTEXPRESS_REST_DELIVERY_STATES_LABELS.get(status_code, "Desconocido")
                            values = [
                                shipment.get("best_shipping_type_code", ""),
                                shipment.get("recipient_name", ""),
                                shipment.get("destin_town_name", ""),
                                (shipment.get("client_references") or [""])[0],
                                shipment.get("item_count", 1),
                                f"{shipment.get('shipping_weight_declared', 0)}kg",
                                status_label,
                                shipment.get("shipping_date", "")
                            ]
                            for col, val in enumerate(values):
                                val_str = str(val or "")
                                sheet.write(row, col, val_str, cell_format)
                                col_widths[col] = max(col_widths[col], len(val_str))

                        last_row = 5 + len(result["data"])
                        summary_row = last_row + 1
                        sheet.write(summary_row, 0, "Totales:", header_format)
                        sheet.write(summary_row, 4, f"Expediciones: {len(result['data'])}", cell_format)
                        sheet.write(summary_row, 5, f"Bultos: {sum(sh.get('item_count', 1) for sh in result['data'])}", cell_format)
                        sheet.write(summary_row, 6, f"Peso: {sum(sh.get('shipping_weight_declared', 0) for sh in result['data'])} kg", cell_format)

                        # Ajustar ancho de columnas
                        for col, width in enumerate(col_widths):
                            sheet.set_column(col, col, width + 2)

                        workbook.close()
                        xls_data = xls_buffer.getvalue()
                        xls_buffer.close()

                        filename = "{}-{}-{}.xlsx".format(
                            carrier.cttexpress_rest_agency,
                            from_date_str.replace("-", ""),
                            to_date_str.replace("-", ""),
                        )
                        self.attachment_ids += self.env["ir.attachment"].create({
                            "datas": base64.b64encode(xls_data),
                            "name": filename,
                            "res_model": self._name,
                            "res_id": self.id,
                            "type": "binary",
                            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        })

        self.state = "done"
        return dict(
            self.env["ir.actions.act_window"]._for_xml_id(
                "delivery_cttexpress.action_delivery_cttexpress_manifest_wizard"
            ),
            res_id=self.id,
        )
