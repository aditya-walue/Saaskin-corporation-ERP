import frappe
from frappe.tests import IntegrationTestCase

from saaskin_erp.install import DEAL_STATUS_PIPELINE


class TestDealPipelineAlignment(IntegrationTestCase):
	def test_deal_statuses_match_business_flow(self):
		statuses = frappe.get_all(
			"CRM Deal Status",
			fields=["name", "type", "position", "color"],
			order_by="position",
		)
		status_by_name = {row.name: row for row in statuses}

		for name, status_type, position, _probability, color in DEAL_STATUS_PIPELINE:
			self.assertIn(name, status_by_name)
			self.assertEqual(status_by_name[name].type, status_type)
			self.assertEqual(status_by_name[name].position, position)
			self.assertEqual(status_by_name[name].color, color)

	def test_new_deal_defaults_to_prospecting(self):
		deal = frappe.get_doc({"doctype": "CRM Deal", "organization_name": "Default Status Org"}).insert(
			ignore_permissions=True
		)
		self.assertEqual(deal.status, "Prospecting")
		frappe.db.rollback()
