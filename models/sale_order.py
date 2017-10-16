# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#  OpenERP, Open Source Management Solution.                                 #
#                                                                            #
#  @author @author Daikhi Oualid <o_daikhi@esi.dz>                           #
#                                                                            #
#  This program is free software: you can redistribute it and/or modify      #
#  it under the terms of the GNU Affero General Public License as            #
#  published by the Free Software Foundation, either version 3 of the        #
#  License, or (at your option) any later version.                           #
#                                                                            #
#  This program is distributed in the hope that it will be useful,           #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              #
#  GNU Affero General Public License for more details.                       #
#                                                                            #
#  You should have received a copy of the GNU Affero General Public License  #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.      #
#                                                                            #
##############################################################################

from odoo import models, api, fields, _



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def onchange_saller_id(self):
        if self.product_id:
            seller = self.env['product.supplierinfo'].search(
                [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)], order='sequence', limit=1)

            self.seller_id = seller
        else:
            self.seller_id = False

    seller_id = fields.Many2one('product.supplierinfo', string="Supplier info")

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()
        # set the selected supplier info as true
        if self.seller_id:
            this_seller = self.env['product.supplierinfo'].search([('id', '=', self.seller_id.id)])
            this_seller.write({'selected': True})
            other_sellers = self.env['product.supplierinfo'].search([('id', '!=', self.seller_id.id)])
            other_sellers.write({'selected': False})
        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product),
                                                                                 product.taxes_id, self.tax_id)
        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {'domain': domain}

    @api.onchange('seller_id')
    def product_vendor_change(self):
        if self.seller_id:
            this_seller = self.env['product.supplierinfo'].search([('id', '=', self.seller_id.id)])
            this_seller.write({'selected': True})
            other_sellers = self.env['product.supplierinfo'].search([('id', '!=', self.seller_id.id)])
            other_sellers.write({'selected': False})
            self.product_id_change()

    @api.one
    @api.depends('product_id')
    def get_seller_count(self):
        for vendor in self :
            vendor.seller_count = len(
                self.env['product.supplierinfo'].search([('product_tmpl_id','=',self.product_id.product_tmpl_id.id)]))

    seller_count = fields.Integer(string="Number of vendor",compute=get_seller_count,help="Number of vendor prices for this product")
    @api.one
    @api.depends('product_id')
    def get_template_from_product(self):
        if self.product_id:
            self.product_tmpl_id = self.product_id.product_tmpl_id
    # field product template for domain in view
    product_tmpl_id = fields.Many2one('product.template', string="Product template", compute='get_template_from_product', store=True)




class SupplierInfo(models.Model):

    _inherit = 'product.supplierinfo'
    selected = fields.Boolean(string="Supplier selected")

    @api.multi
    def name_get(self):
        res=[]
        for vendor in self :
            code = vendor.product_code and str(vendor.product_code)+',' or ''
            tt =str(vendor.name.name) + ' [ ' + code + ' ' + str(vendor.price) + ' ]'
            res.append((vendor.id, tt))
        return res
class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'


    @api.multi
    def make_po(self):
        cache = {}
        res = []
        for procurement in self:
            sale_id = False
            line_id =False
            if procurement.group_id:
                sale_id = self.env['sale.order'].search([('name','=',procurement.group_id.display_name)])
                line_id = sale_id.order_line.filtered(lambda r: not r.product_id or r.product_id == procurement.product_id)
            if line_id :
                suppliers = line_id.seller_id

            else:
                suppliers = procurement.product_id.seller_ids.filtered(lambda r: not r.product_id or r.product_id == procurement.product_id)
            if not suppliers:
                procurement.message_post(body=_('No vendor associated to product %s. Please set one to fix this procurement.') % (procurement.product_id.name))
                continue
            supplier = suppliers[0]
            partner = supplier.name

            gpo = procurement.rule_id.group_propagation_option
            group = (gpo == 'fixed' and procurement.rule_id.group_id) or \
                    (gpo == 'propagate' and procurement.group_id) or False

            domain = (
                ('partner_id', '=', partner.id),
                ('state', '=', 'draft'),
                ('picking_type_id', '=', procurement.rule_id.picking_type_id.id),
                ('company_id', '=', procurement.company_id.id),
                ('dest_address_id', '=', procurement.partner_dest_id.id))
            if group:
                domain += (('group_id', '=', group.id),)

            if domain in cache:
                po = cache[domain]
            else:
                po = self.env['purchase.order'].search([dom for dom in domain])
                po = po[0] if po else False
                cache[domain] = po
            if not po:
                vals = procurement._prepare_purchase_order(partner)
                po = self.env['purchase.order'].create(vals)
                name = (procurement.group_id and (procurement.group_id.name + ":") or "") + (procurement.name != "/" and procurement.name or procurement.move_dest_id.raw_material_production_id and procurement.move_dest_id.raw_material_production_id.name or "")
                message = _("This purchase order has been created from: <a href=# data-oe-model=procurement.order data-oe-id=%d>%s</a>") % (procurement.id, name)
                po.message_post(body=message)
                cache[domain] = po
            elif not po.origin or procurement.origin not in po.origin.split(', '):
                # Keep track of all procurements
                if po.origin:
                    if procurement.origin:
                        po.write({'origin': po.origin + ', ' + procurement.origin})
                    else:
                        po.write({'origin': po.origin})
                else:
                    po.write({'origin': procurement.origin})
                name = (self.group_id and (self.group_id.name + ":") or "") + (self.name != "/" and self.name or self.move_dest_id.raw_material_production_id and self.move_dest_id.raw_material_production_id.name or "")
                message = _("This purchase order has been modified from: <a href=# data-oe-model=procurement.order data-oe-id=%d>%s</a>") % (procurement.id, name)
                po.message_post(body=message)
            if po:
                res += [procurement.id]

            # Create Line
            po_line = False
            for line in po.order_line:
                if line.product_id == procurement.product_id and line.product_uom == procurement.product_id.uom_po_id:
                    procurement_uom_po_qty = procurement.product_uom._compute_quantity(procurement.product_qty, procurement.product_id.uom_po_id)
                    seller = procurement.product_id._select_seller(
                        partner_id=partner,
                        quantity=line.product_qty + procurement_uom_po_qty,
                        date=po.date_order and po.date_order[:10],
                        uom_id=procurement.product_id.uom_po_id)

                    price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, line.product_id.supplier_taxes_id, line.taxes_id) if seller else 0.0
                    if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
                        price_unit = seller.currency_id.compute(price_unit, po.currency_id)

                    po_line = line.write({
                        'product_qty': line.product_qty + procurement_uom_po_qty,
                        'price_unit': price_unit,
                        'procurement_ids': [(4, procurement.id)]
                    })
                    break
            if not po_line:
                vals = procurement._prepare_purchase_order_line(po, supplier)
                self.env['purchase.order.line'].create(vals)
        return res
