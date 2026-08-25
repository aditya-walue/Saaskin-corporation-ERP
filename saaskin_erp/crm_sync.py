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
FALLBACK_ITEM_CODE = "General Service"


def sync_expected_deal_value(doc, method=None):
	"""Fix fcrm's own auto-update: CRMDeal.update_expected_deal_value() only
	overwrites an already-nonzero expected_deal_value, so it never fires on a
	deal's first save (expected_deal_value starts at 0, which is falsy). When
	the site has "Auto Update Expected Deal Value" enabled, this makes it
	actually track the Products total from the start, not just top it up
	once something else has already set it.
	"""
	if not frappe.db.get_single_value("FCRM Settings", "auto_update_expected_deal_value"):
		return

	total = doc.net_total or doc.total
	if total:
		doc.expected_deal_value = total


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
	customer.customer_group = get_default_customer_group()
	customer.territory = deal.territory or get_default_territory()
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


def get_default_customer_group():
	# "All Customer Groups" (or whatever Selling Settings might hold) can be a
	# Group-type node -- ERPNext refuses to assign those to an actual
	# Customer. Only trust a configured default if it's a real leaf; always
	# fall back to any non-group Customer Group that exists on the site.
	configured = frappe.db.get_single_value("Selling Settings", "customer_group")
	if configured and not frappe.db.get_value("Customer Group", configured, "is_group"):
		return configured
	return frappe.db.get_value("Customer Group", {"is_group": 0}, "name")


def get_default_territory():
	configured = frappe.db.get_single_value("Selling Settings", "territory")
	if configured and not frappe.db.get_value("Territory", configured, "is_group"):
		return configured
	return frappe.db.get_value("Territory", {"is_group": 0}, "name")


def get_default_company():
	company = frappe.defaults.get_global_default("company")
	if company:
		return company
	return frappe.get_all("Company", pluck="name", limit=1)[0]
