import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests import IntegrationTestCase

from saaskin_erp.install import PURCHASE_ORDER_WORKFLOW_NAME


class TestPurchaseOrderApprovalWorkflow(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_workflow_is_active_on_purchase_order(self):
		self.assertTrue(frappe.db.exists("Workflow", PURCHASE_ORDER_WORKFLOW_NAME))
		is_active = frappe.db.get_value("Workflow", PURCHASE_ORDER_WORKFLOW_NAME, "is_active")
		self.assertEqual(is_active, 1)

	def test_new_purchase_order_starts_as_draft_and_unsubmitted(self):
		po = create_test_purchase_order()
		self.assertEqual(po.workflow_state, "Draft")
		self.assertEqual(po.docstatus, 0)

	def test_approve_transition_submits_the_document(self):
		po = create_test_purchase_order()

		apply_workflow(po, "Review")
		po.reload()
		self.assertEqual(po.workflow_state, "Pending")
		self.assertEqual(po.docstatus, 0)

		apply_workflow(po, "Approve")
		po.reload()
		self.assertEqual(po.workflow_state, "Approved")
		self.assertEqual(po.docstatus, 1)

	def test_reject_transition_keeps_document_as_draft_docstatus(self):
		po = create_test_purchase_order()

		apply_workflow(po, "Review")
		apply_workflow(po, "Reject")
		po.reload()

		self.assertEqual(po.workflow_state, "Rejected")
		self.assertEqual(po.docstatus, 0)


def create_test_purchase_order():
	supplier_name = "Workflow Test Supplier"
	if not frappe.db.exists("Supplier", supplier_name):
		frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": supplier_name,
				"supplier_group": frappe.db.get_single_value("Buying Settings", "supplier_group")
				or "All Supplier Groups",
			}
		).insert(ignore_permissions=True)

	item_code = "WORKFLOW-TEST-ITEM"
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

	po = frappe.new_doc("Purchase Order")
	po.supplier = supplier_name
	po.company = frappe.get_all("Company", pluck="name", limit=1)[0]
	po.schedule_date = frappe.utils.add_days(frappe.utils.nowdate(), 7)
	po.append(
		"items",
		{"item_code": item_code, "qty": 1, "rate": 100, "schedule_date": po.schedule_date},
	)
	po.insert(ignore_permissions=True)
	return po
