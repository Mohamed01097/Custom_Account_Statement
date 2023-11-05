# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.misc import get_lang
from odoo.exceptions import ValidationError
from datetime import date


class AccountCommonReport(models.TransientModel):
    _name = "account.common.report"
    _description = "Account Common Report"

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journals',
        required=True,
        default=lambda self: self.env['account.journal'].search([('company_id', '=', self.company_id.id)]),
        domain="[('company_id', '=', company_id)]",
    )
    tag_ids = fields.Many2many('res.partner.category', string='Tags')
    date_from = fields.Date(string='Start Date', default=date.today(), required=True)
    date_to = fields.Date(string='End Date', default=date.today(), required=True)
    with_old_balance = fields.Boolean(string='إظهار الرصيد الافتتاحى', default=True)
    with_zero_balance = fields.Boolean(string='بدون الرصيد صفر')
    with_total = fields.Boolean(string='إجمالى الارصدة')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='all')

    @api.onchange('with_total')
    def _onchange_with_total(self):
        if self.with_total:
            self.with_old_balance = False

    @api.onchange('with_old_balance')
    def _onchange_with_old_balance(self):
        if self.with_old_balance:
            self.with_total = False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.journal_ids = self.env['account.journal'].search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].search([])

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['with_old_balance'] = data['form']['with_old_balance'] or False
        result['with_zero_balance'] = data['form']['with_zero_balance'] or False
        result['with_total'] = data['form']['with_total'] or False
        result['tag_ids'] = data['form']['tag_ids'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['company_id'] = data['form']['company_id'][0] or False
        return result

    def _print_report(self, data):
        raise NotImplementedError()

    def check_report(self):
        if self.partner_ids and self.tag_ids:
            raise ValidationError(_("You must select only tags or partners"))
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'with_total', 'with_zero_balance','with_old_balance', 'tag_ids', 'date_to', 'journal_ids', 'target_move',
             'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)

        return self.with_context(discard_logo_check=True)._print_report(data)
