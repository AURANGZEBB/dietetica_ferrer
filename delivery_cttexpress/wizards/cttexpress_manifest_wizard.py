# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import fields, models, _


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
        """List of shippings for the given dates as CTT provides them"""
        # Se obtienen los carriers filtrados por is_ctt
        carriers = self.carrier_ids or self.env["delivery.carrier"].search(
            [("is_ctt", "=", True)]
        )
        # Evitar obtener manifiestos repetidos. Los carriers con distinta configuración
        # de servicio podrían producir el mismo manifiesto.
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
        for carrier in filtered_carriers:
            ctt_request = carrier._ctt_request()
            from_date_str = fields.Date.to_string(self.from_date)
            to_date_str = fields.Date.to_string(self.to_date)
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
        self.state = "done"
        return dict(
            self.env["ir.actions.act_window"]._for_xml_id(
                "delivery_cttexpress.action_delivery_cttexpress_manifest_wizard"
            ),
            res_id=self.id,
        )
