# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Numérigraphe SARL.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Select a Supplier Info From Sales Order',
    'version': '1.0',
    'category': 'Sales',
    'description': """
    The sales order lines table provides an option (drop-down box) to select a supplierinfo.
    The drop-down box only lists supplierinfos that belong to the selected product.
    The price for a sale order line is computed again on every change (different product / supplierinfo)
""",
    'author' : u'DAIKHI Oualid',
    'images': ['static/description/vendor_sale_order.png'],
    'depends': ['base','sale','purchase'],
    'data': ['Views.xml'
	],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
