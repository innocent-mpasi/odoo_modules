from odoo import fields, models , api
from datetime import date

class prod_order_app(models.Model):
	"""real name of the model"""
	_name = "prod_order.model"
	_description = "For Production application"
	_inherit =["mail.thread","mail.activity.mixin"]
	_rec_name="customer_ref"
	_order="id"



	customer_refe=fields.Many2one('sale.order.line',string="sale_order_lines",tracking=True)
	main_sales_id=fields.Many2one('sale.order',string="Production_order",tracking=True)
	orderLines_ids=fields.One2many(related='main_sales_id.order_line', string="")


	order=fields.Datetime(related='main_sales_id.date_order' ,string="Order Date")
	customer_ref= fields.Char(related='main_sales_id.partner_id.name')
	deli_address=fields.Many2one(related='main_sales_id.partner_invoice_id' ,string="Delivery Address")
	delivery_date=fields.Datetime(related='main_sales_id.commitment_date',string="Delivery Date",tracking=True)
	delivery_week=fields.Integer(string="Delivered Week",tracking=True)


	delivered_date=fields.Date(string="Delivered Date",tracking=True)
	total_vol = fields.Float(string="Total Volume", default="0.00")
	total_wei = fields.Float(string="Total Weight", default="0.00")
	total_ite = fields.Char(string="Total iteams")
	all_del = fields.Boolean(string="All iteams as Delivered?", default=False)

	state=fields.Selection(
        string='Status',
        tracking=True,
        default='new',
        selection=[
        ('new','New'),
        ('prod','In Production'),
        ('cancel','Cancel'),
        ('delivered','Delivered')])


	# def _filter(self):
	# 	for rec in self:
	# 		ap_count=self.env['sale.order'].filtered(lambda s: s.state == 'sent' or s.state == 'draft')
	# 		rec.main_sales_id=ap_count

	# add this line
	@api.onchange("all_del")
	def _onchange_alldel(self):
		if self.all_del == True:
			for rec in self.orderLines_ids:
				rec.delivered_Qty = rec.product_uom_qty
			self.state = 'delivered'
		else:
			for rec in self.orderLines_ids:
				rec.delivered_Qty = 0
			self.state = 'prod'

	def action_new(self):
		self.state='new'

	def action_prod(self):
		self.state='prod'

	def action_cancelled(self):
		self.state='cancel'

	def action_delivered(self):
		self.state='delivered'
		for record in self:
			created_all = self.env["account.move"].search_count([('link_prod_id', '=', record.id)])
			if created_all == 0:
				invoice_lines = []
				for line in record.orderLines_ids:
					vals = {
						'name': line.name,
						'price_unit': line.price_unit,
						'quantity': line.product_uom_qty,
						'product_id': line.product_id.id,
						'product_uom_id': line.product_uom.id,
						'tax_ids': [(6, 0, line.tax_id.ids)],
						'sale_line_ids': [(6, 0, [line.id])],
					}
					invoice_lines.append((0, 0, vals))
				self.env['account.move'].create({
					'link_prod_id':record.id,
					'ref': record.main_sales_id.client_order_ref,
					'state':'draft',
					'move_type': 'out_invoice',
					'invoice_origin': record.main_sales_id.name,
					'invoice_user_id': record.main_sales_id.user_id.id,
					'partner_id': record.main_sales_id.partner_invoice_id.id,
					'currency_id': record.main_sales_id.pricelist_id.currency_id.id,
					'invoice_line_ids': invoice_lines
				})


				record_to_update = self.env["account.move"].search([('link_prod_id', '=',record.id )])
				if record_to_update.exists():
					vali = {
						'state': 'posted',
						'invoice_date':date.today()
					}
					record_to_update.write(vali)
