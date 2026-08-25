"""Link a won CRM Deal (fcrm) to an ERPNext Customer + Sales Order.

Bridges the "Order Management" step of Saaskin's business flow: when a
CRM Deal's status resolves to the "Won" type, create (or reuse) an ERPNext
Customer and raise a Draft Sales Order for it, then record both back on the
Deal. Built directly from the deal's items every time -- independent of
whether a Quotation exists or what state it's in (see quote_sync.py for the
separate Proposal -> Quotation step). Left as Draft: submitting/approving
is a manual step from here.
"""

import frappe

DEFAULT_ITEM_GROUP = "Products"
DEFAULT_UOM = "Nos"
DEFAULT_CUSTOMER_GROUP = "All Customer Groups"
DEFAULT_TERRITORY = "All Territories"
FALLBACK_ITEM_CODE = "General Service"


def sync_deal_to_sales_order(doc, method=None):
	if not doc.status:
		return

	status_type = frappe.db.get_value("CRM Deal Status", doc.status, "type")
	if status_type != "Won":
		return

	if doc.get("custom_sales_order"):
		return

	create_sales_order_from_deal(doc)


def create_sales_order_from_deal(deal):
	customer = get_or_create_customer(deal)
	company = get_default_company()

	sales_order = frappe.new_doc("Sales Order")
	sales_order.customer = customer
	sales_order.company = company
	sales_order.order_type = "Sales"
	sales_order.transaction_date = frappe.utils.nowdate()
	sales_order.delivery_date = deal.expected_closure_date or frappe.utils.add_days(
		frappe.utils.nowdate(), 7
	)
	sales_order.currency = deal.currency or frappe.get_cached_value(
		"Company", company, "default_currency"
	)
	sales_order.custom_crm_deal = deal.name

	for row in deal.products or []:
		item_code = get_or_create_item(row)
		sales_order.append(
			"items",
			{
				"item_code": item_code,
				"qty": row.qty or 1,
				"rate": row.rate or 0,
				"uom": DEFAULT_UOM,
				"delivery_date": sales_order.delivery_date,
			},
		)

	if not sales_order.items:
		sales_order.append(
			"items",
			{
				"item_code": get_or_create_fallback_item(),
				"qty": 1,
				"rate": deal.deal_value or 0,
				"uom": DEFAULT_UOM,
				"delivery_date": sales_order.delivery_date,
			},
		)

	sales_order.insert(ignore_permissions=True)

	deal.db_set("custom_sales_order", sales_order.name, update_modified=False)
	deal.db_set("custom_customer", customer, update_modified=False)

	return sales_order


def get_or_create_customer(deal):
	customer_name = deal.organization_name or deal.lead_name or deal.name

	existing = frappe.db.exists("Customer", {"customer_name": customer_name})
	if existing:
		return existing

	customer = frappe.new_doc("Customer")
	customer.customer_name = customer_name
	customer.customer_type = "Company" if deal.organization_name else "Individual"
	customer.customer_group = (
		frappe.db.get_single_value("Selling Settings", "customer_group") or DEFAULT_CUSTOMER_GROUP
	)
	customer.territory = deal.territory or (
		frappe.db.get_single_value("Selling Settings", "territory") or DEFAULT_TERRITORY
	)
	customer.insert(ignore_permissions=True)
	return customer.name


def get_or_create_item(row):
	item_code = row.product_code or row.product_name
	if not item_code:
		return get_or_create_fallback_item()

	if frappe.db.exists("Item", item_code):
		return item_code

	item = frappe.new_doc("Item")
	item.item_code = item_code
	item.item_name = row.product_name or item_code
	item.item_group = DEFAULT_ITEM_GROUP
	item.stock_uom = DEFAULT_UOM
	item.is_stock_item = 0
	item.insert(ignore_permissions=True)
	return item.name


def get_or_create_fallback_item():
	if frappe.db.exists("Item", FALLBACK_ITEM_CODE):
		return FALLBACK_ITEM_CODE

	item = frappe.new_doc("Item")
	item.item_code = FALLBACK_ITEM_CODE
	item.item_name = FALLBACK_ITEM_CODE
	item.item_group = DEFAULT_ITEM_GROUP
	item.stock_uom = DEFAULT_UOM
	item.is_stock_item = 0
	item.insert(ignore_permissions=True)
	return item.name


def get_default_company():
	company = frappe.defaults.get_global_default("company")
	if company:
		return company
	return frappe.get_all("Company", pluck="name", limit=1)[0]
