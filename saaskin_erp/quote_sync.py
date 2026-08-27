"""Auto-generate a Quotation when a CRM Deal reaches the "Proposal" stage.

Bridges the Automation Requirements' second example:
Proposal -> Quote Generation -> Finance Approval -> Order Creation -> Invoice.

The Quotation is created as a plain Draft; getting it to "Approved" (and
therefore submitted) runs through the Quotation Finance Approval workflow
(see install.create_quotation_finance_approval_workflow), gated by the
Accounts Manager role. crm_sync.py only converts this Quotation into a
Sales Order once it is submitted -- an unapproved Quotation blocks Order
Creation on a Closed Won deal rather than silently bypassing finance.
"""

import frappe

from saaskin_erp.crm_sync import (
	DEFAULT_UOM,
	get_default_company,
	get_or_create_customer,
	get_or_create_fallback_item,
	get_or_create_item,
)

PROPOSAL_STATUS = "Proposal"


def sync_deal_to_quotation(doc, method=None):
	if doc.status != PROPOSAL_STATUS:
		return

	if doc.get("custom_quotation"):
		return

	create_quotation_from_deal(doc)


def create_quotation_from_deal(deal):
	customer = get_or_create_customer(deal)
	company = get_default_company()

	quotation = frappe.new_doc("Quotation")
	quotation.quotation_to = "Customer"
	quotation.party_name = customer
	quotation.company = company
	quotation.order_type = "Sales"
	quotation.transaction_date = frappe.utils.nowdate()
	quotation.valid_till = frappe.utils.add_days(frappe.utils.nowdate(), 30)
	quotation.currency = deal.currency or frappe.get_cached_value(
		"Company", company, "default_currency"
	)
	quotation.custom_crm_deal = deal.name

	for row in deal.products or []:
		item_code = get_or_create_item(row)
		quotation.append(
			"items",
			{
				"item_code": item_code,
				"qty": row.qty or 1,
				"rate": row.rate or 0,
				"uom": DEFAULT_UOM,
			},
		)

	if not quotation.items:
		quotation.append(
			"items",
			{
				"item_code": get_or_create_fallback_item(),
				"qty": 1,
				"rate": deal.deal_value or 0,
				"uom": DEFAULT_UOM,
			},
		)

	quotation.insert(ignore_permissions=True)

	deal.db_set("custom_quotation", quotation.name, update_modified=False)
	deal.db_set("custom_customer", customer, update_modified=False)

	return quotation
