"""Link a won CRM Deal (fcrm) to an ERPNext Customer + Sales Order.

Bridges the "Order Management" step of Saaskin's business flow: when a
CRM Deal's status resolves to the "Won" type, create (or reuse) an ERPNext
Customer and raise a Draft Sales Order for it, then record both back on the
Deal. Built directly from the deal's items every time -- independent of
whether a Quotation exists or what state it's in (see quote_sync.py for the
separate Proposal -> Quotation step). Left as Draft: submitting/approving
is a manual step from here.
"""

import re

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

	link_deal_contact_to_customer(deal, customer)
	link_deal_address_to_customer(deal, customer)

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


def link_deal_contact_to_customer(deal, customer):
	"""Point the Customer's Primary Contact at the deal's own contact, and
	link that Contact record to the Customer via Dynamic Link -- neither
	happens on its own. fcrm's separate "ERPNext CRM Settings" integration
	(create_customer_on_status_change) can independently build its own,
	worse Contact (whole name dumped into first_name, no phone) in parallel
	with this; that toggle is disabled by install.py for that reason.
	"""
	if frappe.db.get_value("Customer", customer, "customer_primary_contact"):
		return

	contact_name = get_deal_contact(deal)
	if not contact_name:
		return

	contact = frappe.get_doc("Contact", contact_name)
	already_linked = any(
		link.link_doctype == "Customer" and link.link_name == customer for link in contact.links
	)
	if not already_linked:
		contact.append("links", {"link_doctype": "Customer", "link_name": customer})
		contact.save(ignore_permissions=True)

	frappe.db.set_value("Customer", customer, "customer_primary_contact", contact_name)


def link_deal_address_to_customer(deal, customer):
	"""Point the Customer's Primary Address at something -- a Won deal's
	Customer otherwise ends up with no Address at all (fcrm never creates
	one for a Lead/Deal's Contact), which blocks anything downstream that
	needs one (e.g. Shipment's "Delivery to" address auto-fetches from the
	Customer and has nothing to pull). Prefers an Address already linked to
	the deal's own Contact; falls back to building one from the deal's own
	`address` field (saaskin_erp.enrichment's scraped, unstructured text) if
	no Contact-linked Address exists. Does nothing if neither is available --
	never invents an address from nothing.
	"""
	if frappe.db.get_value("Customer", customer, "customer_primary_address"):
		return

	address_name = get_contact_linked_address(deal)
	if not address_name:
		address_name = create_address_from_deal_text(deal, customer)
	if not address_name:
		return

	address = frappe.get_doc("Address", address_name)
	already_linked = any(
		link.link_doctype == "Customer" and link.link_name == customer for link in address.links
	)
	if not already_linked:
		address.append("links", {"link_doctype": "Customer", "link_name": customer})
		address.save(ignore_permissions=True)

	frappe.db.set_value("Customer", customer, "customer_primary_address", address_name)


def get_contact_linked_address(deal):
	contact_name = get_deal_contact(deal)
	if not contact_name:
		return None
	return frappe.db.get_value(
		"Dynamic Link",
		{"parenttype": "Address", "link_doctype": "Contact", "link_name": contact_name},
		"parent",
	)


def create_address_from_deal_text(deal, customer):
	# saaskin_erp.enrichment writes a single unstructured line (e.g. from a
	# site's JSON-LD PostalAddress or a scraped <address> tag) -- Address
	# requires address_line1/city/country broken out, so this is a best
	# effort split, not a real parse.
	raw = (deal.get("address") or "").strip()
	if not raw:
		return None

	from saaskin_erp.install import COUNTRY_NAMES

	country = next((c for c in COUNTRY_NAMES if c.lower() in raw.lower()), None)
	if not country:
		country = frappe.get_cached_value("Company", get_default_company(), "country")
	if not country:
		return None

	parts = [p.strip() for p in raw.split(",") if p.strip()]
	city = None
	for part in parts:
		if country and country.lower() in part.lower():
			continue
		if re.fullmatch(r"[A-Za-z .'-]+", part) and part.lower() != country.lower():
			city = part
	if not city and len(parts) >= 2:
		city = parts[-2]

	address = frappe.new_doc("Address")
	address.address_title = customer
	address.address_type = "Billing"
	address.address_line1 = raw[:140]
	address.city = (city or customer)[:140]
	address.country = country
	address.append("links", {"link_doctype": "Customer", "link_name": customer})
	address.insert(ignore_permissions=True)
	return address.name


def get_deal_contact(deal):
	primary_row = next((row for row in deal.contacts or [] if row.is_primary), None)
	if primary_row and primary_row.contact:
		return primary_row.contact

	if deal.contacts:
		return deal.contacts[0].contact

	return deal.contact or None


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
