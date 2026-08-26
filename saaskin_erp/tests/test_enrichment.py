from unittest.mock import Mock, patch

import frappe
from frappe.tests import IntegrationTestCase

from saaskin_erp.install import DEAL_ENRICH_FORM_SCRIPT_NAME

SAMPLE_HTML = """
<html><head>
<title>Sample Org - Home</title>
<meta name="description" content="A sample company for testing.">
</head><body>
<a href="mailto:hello@sample-org.test">Email us</a>
<a href="tel:+15551234567">Call us</a>
<a href="https://www.linkedin.com/company/sample-org">LinkedIn</a>
</body></html>
"""


def mocked_response():
	response = Mock()
	response.text = SAMPLE_HTML
	response.raise_for_status = Mock()
	return response


class TestDealEnrichment(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_enrich_form_script_registered_for_crm_deal(self):
		self.assertTrue(frappe.db.exists("CRM Form Script", DEAL_ENRICH_FORM_SCRIPT_NAME))
		dt, view, enabled = frappe.db.get_value(
			"CRM Form Script", DEAL_ENRICH_FORM_SCRIPT_NAME, ["dt", "view", "enabled"]
		)
		self.assertEqual(dt, "CRM Deal")
		self.assertEqual(view, "Form")
		self.assertEqual(enabled, 1)

	def test_enrich_deal_requires_website(self):
		from saaskin_erp.enrichment import enrich_deal

		deal = frappe.get_doc(
			{"doctype": "CRM Deal", "organization_name": "No Website Org", "status": "Prospecting"}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			enrich_deal(deal.name)

	@patch("saaskin_erp.enrichment.requests.get")
	def test_enrich_deal_fills_empty_fields_from_website(self, mock_get):
		from saaskin_erp.enrichment import enrich_deal

		mock_get.return_value = mocked_response()

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization_name": "",
				"status": "Prospecting",
				"website": "https://sample-org.test",
			}
		).insert(ignore_permissions=True)

		result = enrich_deal(deal.name)
		deal.reload()

		self.assertEqual(
			set(result["filled_fields"]),
			{"organization_name", "company_description", "email", "phone", "linkedin"},
		)
		self.assertEqual(deal.organization_name, "Sample Org")
		self.assertEqual(deal.company_description, "A sample company for testing.")
		self.assertEqual(deal.email, "hello@sample-org.test")
		self.assertEqual(deal.phone, "+15551234567")
		self.assertEqual(deal.linkedin, "https://www.linkedin.com/company/sample-org")

	@patch("saaskin_erp.enrichment.requests.get")
	def test_enrich_deal_does_not_overwrite_existing_values(self, mock_get):
		from saaskin_erp.enrichment import enrich_deal

		mock_get.return_value = mocked_response()

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization_name": "Keep This Name",
				"status": "Prospecting",
				"website": "https://sample-org.test",
			}
		).insert(ignore_permissions=True)

		enrich_deal(deal.name)
		deal.reload()

		self.assertEqual(deal.organization_name, "Keep This Name")
