# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class OnboardingController(http.Controller):

    @http.route('/matricula/matricula_onboarding_panel', auth='user', type='json')
    def matricula_onboarding_panel(self):
        """ Returns the `banner` for the sale onboarding panel.
            It can be empty if the user has closed it or if he doesn't have
            the permission to see it. """

        company = request.env.company
        if company.sale_quotation_onboarding_state == 'closed':
            return {}

        return {
            'html': request.env.ref('modulo_matriculas.matricula_onboarding_panel').render({
                'company': company,
                'state': company.get_and_update_sale_quotation_onboarding_state()
            })
        }
