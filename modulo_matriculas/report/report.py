from reportlab.pdfbase.pdfutils import _fusc

from odoo import models, api
from datetime import datetime

class SolicitudMatricula(models.AbstractModel):
    _name = "report.modulo_matriculas.report_solicitud_matricula"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["ma.matricula"].browse(docids)
        self.env["ma.matricula"].search([('user_id', '=', self.env.uid)]).unlink()
        docargs = {
            "docs": docs,
        }
        return docargs