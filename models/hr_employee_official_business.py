from odoo import models, fields, api, _

from odoo.exceptions import UserError

class HrEmployeeOfficialBusiness(models.Model):
        _name = 'hr.employee.official.business'
        _description = 'HR Employee Official Business'
        _inherit = ['mail.thread','mail.activity.mixin']
        _order = "date_ob desc, id desc"

        name = fields.Char(string='OB #', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
        employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1), track_visibility='always')
        department_id = fields.Many2one('hr.department', 'Department', store=True, compute='_set_employee_details')
        date_ob = fields.Date(required=True, default=fields.Datetime.now(), string='Date of Official Business', track_visibility='always')
        date_submitted = fields.Datetime(string='Submitted Date')
        company_id = fields.Many2one('res.company', 'Company', readonly=True, store=True, default=lambda self: self.env.user.company_id)
        departure_time = fields.Selection([
                ('earlymorning', 'Early Morning'),
                ('morning', 'Morning'),
                ('directob', 'Direct OB'),
                ('afternoon', 'Afternoon'),
        ], string='Estimated Time of Departure', required=True, track_visibility='always')
        visit_purpose = fields.Text(string='Purpose of Visit', required=True, track_visibility='always')
        visit_person = fields.Text(string='Person to Visit')
        visit_place = fields.Text(string='Place to Visit')
        transportation_means = fields.Selection([
                ('uber', 'Uber/Grab'),
                ('companycar', 'With Company Car'),
                ('truck', 'Truck'),
                ('commute','Commute'),
        ], string='Means of Transportation', required=True, track_visibility='always')
        remarks = fields.Text(string='Other Remarks')
        user_id = fields.Many2one('res.user', 'User')
        approver_id = fields.Many2one('hr.employee','Approver', store=True, compute='_set_employee_details', track_visibility='always')
        state = fields.Selection([
                ('draft', 'To Submit'),
                ('confirm', 'Pending'),
                ('cancel', 'Refused'),
                ('validate', 'Approved'),
                ('expense', 'In Expense'),
                ('done', 'Done'),
        ], default='draft', track_visibility='onchange')

        current_user = fields.Many2one('res.users', compute='_get_current_user')

        @api.multi
        def name_get(self):
                res = []
                for rec in self:
                        name = '[%s] %s' % (rec.name, rec.visit_purpose)
                        res.append((rec.id, name))
                return res

        @api.depends()
        def _get_current_user(self):
                for rec in self:
                        rec.current_user = self.env.user
                # i think this work too so you don't have to loop
                self.update({'current_user' : self.env.user.id})
        
        @api.model
        def create(self, values):
                if values.get('name', 'New') == 'New':
                        values['name'] = self.env['ir.sequence'].next_by_code('hr.employee.official.business') or 'New'

                result = super(HrEmployeeOfficialBusiness, self).create(values)
                        
                if values.get('employee_id'):
                        result._add_followers()

                return result

        def _add_followers(self):
                user_ids = []
                employee = self.employee_id
                if employee.user_id:
                        user_ids.append(employee.user_id.id)
                if employee.parent_id:
                        user_ids.append(employee.parent_id.user_id.id)
                if employee.department_id and employee.department_id.manager_id and employee.parent_id != employee.department_id.manager_id:
                        user_ids.append(employee.department_id.manager_id.user_id.id)
                self.message_subscribe_users(user_ids=user_ids)

        @api.depends('employee_id')
        def _set_employee_details(self):
                for ob in self:
                        ob.department_id = ob.employee_id.department_id
                        ob.approver_id = ob.employee_id.parent_id

        @api.multi
        def submit_ob(self):
                for ob in self:
                        ob.state = 'confirm'
                        ob.date_submitted = fields.Datetime.now()

        @api.multi
        def approve_ob(self):
                for ob in self:
                        if ob.approver_id.user_id != ob.current_user:
                                raise UserError("You're not allowed to approve this OB. OB Approver: %s" % (ob.approver_id.name))
                        ob.state = 'validate'

        @api.multi
        def refuse_ob(self):
                for ob in self:
                        if ob.approver_id.user_id != ob.current_user:
                                raise UserError("You're not allowed to refuse this OB. OB Approver: %s" % (ob.approver_id.name))
                        ob.state = 'cancel'

        @api.multi
        def done_ob(self):
                for ob in self:
                        ob.state = 'done'