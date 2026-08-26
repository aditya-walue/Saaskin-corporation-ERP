import frappe
from frappe.tests import IntegrationTestCase

from saaskin_erp.install import DEAL_ASSIGNMENT_RULE_NAME

SALES_USERS = {"emily.demo@example.com", "john.demo@example.com", "sarah.demo@example.com"}


class TestQualifiedDealAssignment(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_assignment_rule_exists_for_crm_deal(self):
		self.assertTrue(frappe.db.exists("Assignment Rule", DEAL_ASSIGNMENT_RULE_NAME))
		document_type = frappe.db.get_value("Assignment Rule", DEAL_ASSIGNMENT_RULE_NAME, "document_type")
		self.assertEqual(document_type, "CRM Deal")

	def test_deal_reaching_qualified_gets_assigned(self):
		deal = frappe.get_doc(
			{"doctype": "CRM Deal", "organization_name": "Deal Assignment Test Org", "status": "Prospecting"}
		).insert(ignore_permissions=True)
		self.assertFalse(deal.deal_owner)

		deal.status = "Qualified"
		deal.save()
		deal.reload()

		self.assertIn(deal.deal_owner, SALES_USERS)

	def test_already_owned_deal_is_not_reassigned(self):
		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization_name": "Deal Already Owned Org",
				"status": "Prospecting",
				"deal_owner": "john.demo@example.com",
			}
		).insert(ignore_permissions=True)

		deal.status = "Qualified"
		deal.save()
		deal.reload()

		self.assertEqual(deal.deal_owner, "john.demo@example.com")
