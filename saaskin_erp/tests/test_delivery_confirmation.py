import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests import IntegrationTestCase

from saaskin_erp.install import DELIVERY_NOTE_WORKFLOW_NAME


class TestDeliveryConfirmation(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_workflow_is_active_on_delivery_note(self):
		self.assertTrue(frappe.db.exists("Workflow", DELIVERY_NOTE_WORKFLOW_NAME))
		is_active = frappe.db.get_value("Workflow", DELIVERY_NOTE_WORKFLOW_NAME, "is_active")
		self.assertEqual(is_active, 1)

	def test_new_delivery_note_starts_as_draft(self):
		dn = create_test_delivery_note()
		self.assertEqual(dn.workflow_state, "Draft")
		self.assertEqual(dn.docstatus, 0)

	def test_ship_submits_without_marking_delivered(self):
		dn = create_test_delivery_note()
		apply_workflow(dn, "Ship")
		dn.reload()

		self.assertEqual(dn.workflow_state, "Shipped")
		self.assertEqual(dn.docstatus, 1)
		self.assertFalse(dn.delivered_on)
		self.assertFalse(dn.delivered_by)

	def test_confirm_delivery_stamps_who_and_when(self):
		dn = create_test_delivery_note()
		apply_workflow(dn, "Ship")
		apply_workflow(dn, "Confirm Delivery")
		dn.reload()

		self.assertEqual(dn.workflow_state, "Delivered")
		self.assertEqual(dn.docstatus, 1)
		self.assertTrue(dn.delivered_on)
		self.assertEqual(dn.delivered_by, frappe.session.user)

	def test_confirm_delivery_does_not_overwrite_on_resave(self):
		dn = create_test_delivery_note()
		apply_workflow(dn, "Ship")
		apply_workflow(dn, "Confirm Delivery")
		dn.reload()
		first_stamp = dn.delivered_on

		dn.save()
		dn.reload()

		self.assertEqual(dn.delivered_on, first_stamp)


def create_test_delivery_note():
	customer = "Delivery Confirmation Test Customer"
	if not frappe.db.exists("Customer", customer):
		frappe.get_doc(
			{"doctype": "Customer", "customer_name": customer, "customer_type": "Company"}
		).insert(ignore_permissions=True)

	item_code = "DELIVERY-CONFIRMATION-TEST-ITEM"
	if not frappe.db.exists("Item", item_code):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": item_code,
				"item_group": "Products",
				"stock_uom": "Nos",
				"is_stock_item": 0,
			}
		).insert(ignore_permissions=True)

	dn = frappe.new_doc("Delivery Note")
	dn.customer = customer
	dn.company = frappe.get_all("Company", pluck="name", limit=1)[0]
	dn.set_warehouse = "Stores - SCPL"
	dn.append("items", {"item_code": item_code, "qty": 1, "rate": 100, "warehouse": "Stores - SCPL"})
	dn.insert(ignore_permissions=True)
	return dn
