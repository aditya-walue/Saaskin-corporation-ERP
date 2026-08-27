from unittest.mock import Mock, patch

import frappe
from frappe.tests import IntegrationTestCase

from saaskin_erp.install import DEAL_ENRICH_FORM_SCRIPT_NAME, LEAD_ENRICH_FORM_SCRIPT_NAME

SAMPLE_HTML = """
<html><head>
<title>Sample Org - Home</title>
<meta name="description" content="A sample company for testing.">
<script type="application/ld+json">
{"@type": "Organization", "address": {"@type": "PostalAddress",
"streetAddress": "123 Sample St", "addressLocality": "Sampletown",
"addressRegion": "CA", "postalCode": "90210", "addressCountry": "United States"}}
</script>
</head><body>
<a href="mailto:hello@sample-org.test">Email us</a>
<a href="tel:+15551234567">Call us</a>
<a href="https://www.linkedin.com/company/sample-org">LinkedIn</a>
</body></html>
"""

SAMPLE_HTML_ADDRESS_TAG_ONLY = """
<html><head><title>Sample Org - Home</title></head><body>
<address>456 Fallback Ave, Tagsville, TX 75001, United States</address>
</body></html>
"""

SAMPLE_HTML_PLAIN_TEXT_ADDRESS = """
<html><head><title>Sample Org - Home</title></head><body>
<div><p>789 Plain Street, Faketown - 60007, United States</p></div>
</body></html>
"""

SAMPLE_HTML_JS_RENDERED = """
<html><head><title>Sample Org - Home</title></head><body>
<a href="https://www.linkedin.com/company/sample-org">LinkedIn</a>
</body></html>
"""


def mocked_response(html=SAMPLE_HTML):
	response = Mock()
	response.text = html
	response.raise_for_status = Mock()
	return response


class TestDealEnrichment(IntegrationTestCase):
	def setUp(self) -> None:
		# Force the requests.get fallback path deterministically -- without
		# this, a real Playwright/Chromium install (present in dev envs) would
		# actually try to render the fake test domain before falling back,
		# which is slow and depends on how DNS failure behaves in the sandbox.
		patcher = patch("saaskin_erp.enrichment._fetch_rendered_html", return_value=None)
		patcher.start()
		self.addCleanup(patcher.stop)

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
			{"organization_name", "company_description", "email", "phone", "linkedin", "address"},
		)
		self.assertEqual(deal.organization_name, "Sample Org")
		self.assertEqual(deal.company_description, "A sample company for testing.")
		self.assertEqual(deal.email, "hello@sample-org.test")
		self.assertEqual(deal.phone, "+15551234567")
		self.assertEqual(deal.linkedin, "https://www.linkedin.com/company/sample-org")
		self.assertTrue(deal.address)
		address = frappe.get_doc("Address", deal.address)
		self.assertIn("123 Sample St", address.address_line1)
		self.assertEqual(address.country, "United States")

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

	@patch("saaskin_erp.enrichment.requests.get")
	def test_enrich_deal_falls_back_to_address_tag(self, mock_get):
		from saaskin_erp.enrichment import enrich_deal

		mock_get.return_value = mocked_response(SAMPLE_HTML_ADDRESS_TAG_ONLY)

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization_name": "Address Tag Org",
				"status": "Prospecting",
				"website": "https://sample-org.test",
			}
		).insert(ignore_permissions=True)

		result = enrich_deal(deal.name)
		deal.reload()

		self.assertIn("address", result["filled_fields"])
		address = frappe.get_doc("Address", deal.address)
		self.assertIn("456 Fallback Ave", address.address_line1)
		self.assertEqual(address.country, "United States")

	@patch("saaskin_erp.enrichment.requests.get")
	def test_enrich_deal_falls_back_to_plain_text_address(self, mock_get):
		from saaskin_erp.enrichment import enrich_deal

		mock_get.return_value = mocked_response(SAMPLE_HTML_PLAIN_TEXT_ADDRESS)

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization_name": "Plain Text Org",
				"status": "Prospecting",
				"website": "https://sample-org.test",
			}
		).insert(ignore_permissions=True)

		result = enrich_deal(deal.name)
		deal.reload()

		self.assertIn("address", result["filled_fields"])
		address = frappe.get_doc("Address", deal.address)
		self.assertIn("789 Plain Street", address.address_line1)
		self.assertEqual(address.country, "United States")

	@patch("saaskin_erp.enrichment._fetch_rendered_html")
	def test_enrich_deal_uses_rendered_html_when_available(self, mock_render):
		from saaskin_erp.enrichment import enrich_deal

		mock_render.return_value = SAMPLE_HTML_JS_RENDERED

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization_name": "JS Rendered Org",
				"status": "Prospecting",
				"website": "https://sample-org.test",
			}
		).insert(ignore_permissions=True)

		result = enrich_deal(deal.name)
		deal.reload()

		self.assertEqual(deal.linkedin, "https://www.linkedin.com/company/sample-org")
		self.assertIn("linkedin", result["filled_fields"])


class TestLeadEnrichment(IntegrationTestCase):
	def setUp(self) -> None:
		# Force the requests.get fallback path deterministically -- without
		# this, a real Playwright/Chromium install (present in dev envs) would
		# actually try to render the fake test domain before falling back,
		# which is slow and depends on how DNS failure behaves in the sandbox.
		patcher = patch("saaskin_erp.enrichment._fetch_rendered_html", return_value=None)
		patcher.start()
		self.addCleanup(patcher.stop)

	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_enrich_form_script_registered_for_crm_lead(self):
		self.assertTrue(frappe.db.exists("CRM Form Script", LEAD_ENRICH_FORM_SCRIPT_NAME))
		dt, view, enabled = frappe.db.get_value(
			"CRM Form Script", LEAD_ENRICH_FORM_SCRIPT_NAME, ["dt", "view", "enabled"]
		)
		self.assertEqual(dt, "CRM Lead")
		self.assertEqual(view, "Form")
		self.assertEqual(enabled, 1)

	def test_enrich_lead_requires_website(self):
		from saaskin_erp.enrichment import enrich_lead

		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "No Website Lead", "status": "New"}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			enrich_lead(lead.name)

	@patch("saaskin_erp.enrichment.requests.get")
	def test_enrich_lead_fills_empty_fields_from_website(self, mock_get):
		from saaskin_erp.enrichment import enrich_lead

		mock_get.return_value = mocked_response()

		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Website Lead",
				"status": "New",
				"organization": "",
				"website": "https://sample-org.test",
			}
		).insert(ignore_permissions=True)

		result = enrich_lead(lead.name)
		lead.reload()

		self.assertEqual(
			set(result["filled_fields"]),
			{"organization", "company_description", "email", "phone", "linkedin", "address"},
		)
		self.assertEqual(lead.organization, "Sample Org")
		self.assertEqual(lead.email, "hello@sample-org.test")
		self.assertEqual(lead.phone, "+15551234567")
		self.assertTrue(lead.address)
		address = frappe.get_doc("Address", lead.address)
		self.assertIn("123 Sample St", address.address_line1)
		self.assertEqual(address.country, "United States")

	@patch("saaskin_erp.enrichment.requests.get")
	def test_enrich_lead_does_not_overwrite_existing_values(self, mock_get):
		from saaskin_erp.enrichment import enrich_lead

		mock_get.return_value = mocked_response()

		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Website Lead",
				"status": "New",
				"organization": "Keep This Org",
				"website": "https://sample-org.test",
			}
		).insert(ignore_permissions=True)

		enrich_lead(lead.name)
		lead.reload()

		self.assertEqual(lead.organization, "Keep This Org")
