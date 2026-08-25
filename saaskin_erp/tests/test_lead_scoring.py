import frappe
from frappe.tests import IntegrationTestCase

from saaskin_erp.lead_scoring import QUALIFY_THRESHOLD, compute_lead_score

SALES_USERS = {"emily.demo@example.com", "john.demo@example.com", "sarah.demo@example.com"}


class TestLeadScoring(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_low_signal_lead_moves_to_nurture(self):
		lead = create_test_lead(first_name="Sparse", email="sparse@example.com")
		lead.reload()

		self.assertLess(lead.lead_score, QUALIFY_THRESHOLD)
		self.assertEqual(lead.status, "Nurture")

	def test_high_signal_lead_becomes_qualified(self):
		lead = create_test_lead(
			first_name="Rich",
			email="rich@example.com",
			mobile_no="+15550002222",
			organization="Rich Org",
		)
		lead.reload()

		self.assertGreaterEqual(lead.lead_score, QUALIFY_THRESHOLD)
		self.assertEqual(lead.status, "Qualified")

	def test_lead_score_caps_at_100(self):
		lead = create_test_lead(
			first_name="Maxed",
			email="maxed@example.com",
			mobile_no="+15550003333",
			organization="Maxed Org",
			website="https://maxed.example.com",
			job_title="VP Sales",
			industry=get_or_create_industry("Maxed Industry"),
			no_of_employees="1000+",
			annual_revenue=5_000_000,
		)
		lead.reload()

		self.assertEqual(lead.lead_score, 100)

	def test_manual_status_not_overridden(self):
		lead = create_test_lead(first_name="Manual", email="manual@example.com")
		lead.reload()
		self.assertEqual(lead.status, "Nurture")

		lead.status = "Converted"
		lead.save()
		lead.reload()

		self.assertEqual(lead.status, "Converted")

	def test_converted_lead_is_not_rescored(self):
		lead = create_test_lead(first_name="Locked", email="locked@example.com")
		lead.reload()
		original_score = lead.lead_score

		lead.db_set("converted", 1, update_modified=False)
		lead.reload()
		lead.organization = "Should Not Affect Score"
		lead.save()
		lead.reload()

		self.assertEqual(lead.lead_score, original_score)

	def test_qualified_lead_gets_auto_assigned_to_sales_user(self):
		lead = create_test_lead(
			first_name="Assign",
			email="assign@example.com",
			mobile_no="+15550004444",
			organization="Assign Org",
		)
		lead.reload()

		self.assertEqual(lead.status, "Qualified")
		self.assertIn(lead.lead_owner, SALES_USERS)


def get_or_create_industry(name):
	if not frappe.db.exists("CRM Industry", name):
		frappe.get_doc({"doctype": "CRM Industry", "industry": name}).insert(ignore_permissions=True)
	return name


def create_test_lead(**kwargs):
	data = {"doctype": "CRM Lead"}
	data.update(kwargs)
	return frappe.get_doc(data).insert(ignore_permissions=True)
