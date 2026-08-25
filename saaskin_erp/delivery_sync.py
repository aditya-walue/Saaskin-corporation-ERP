"""Stamp who/when confirmed delivery on a Delivery Note.

Bridges the "Inventory & Logistics" step's Delivery Confirmation stage: the
Delivery Confirmation workflow (see install.create_delivery_confirmation_workflow)
moves a Delivery Note through Draft -> Shipped (submit) -> Delivered, and this
records the confirmation moment the first time workflow_state reaches "Delivered".
"""

import frappe


def mark_delivery_confirmed(doc, method=None):
	if doc.workflow_state != "Delivered":
		return

	if doc.get("delivered_on"):
		return

	frappe.db.set_value(
		doc.doctype,
		doc.name,
		{"delivered_on": frappe.utils.now_datetime(), "delivered_by": frappe.session.user},
		update_modified=False,
	)
