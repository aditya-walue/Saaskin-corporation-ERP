import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests import IntegrationTestCase


class TestQuoteSync(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_proposal_stage_creates_draft_quotation(self):
		deal = create_test_deal(organization_name="Proposal Sync Org")
		self.assertFalse(deal.custom_quotation)

		deal.status = "Proposal"
		deal.save()
		deal.reload()

		self.assertTrue(deal.custom_quotation)
		quotation = frappe.get_doc("Quotation", deal.custom_quotation)
		self.assertEqual(quotation.docstatus, 0)
		self.assertEqual(quotation.workflow_state, "Draft")
		self.assertEqual(quotation.party_name, deal.custom_customer)

	def test_proposal_stage_links_contact_to_customer(self):
		"""Contact/address linking used to only happen when a Sales Order is
		created on Won -- a deal parked at Proposal got a Customer with no
		linked Contact at all, even with a primary contact set on the deal."""
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Proposal",
				"last_name": "Contact",
				"email_ids": [{"email_id": "proposal.contact@quote-sync-test.example", "is_primary": 1}],
			}
		).insert(ignore_permissions=True)

		deal = create_test_deal(organization_name="Proposal Contact Org")
		deal.append("contacts", {"contact": contact.name, "is_primary": 1})
		deal.save()

		deal.status = "Proposal"
		deal.save()
		deal.reload()

		customer = frappe.get_doc("Customer", deal.custom_customer)
		self.assertEqual(customer.customer_primary_contact, contact.name)

	def test_quotation_finance_approval_workflow(self):
		deal = create_test_deal(organization_name="Finance Approval Org")
		deal.status = "Proposal"
		deal.save()
		deal.reload()

		quotation = frappe.get_doc("Quotation", deal.custom_quotation)
		apply_workflow(quotation, "Submit for Finance Approval")
		quotation.reload()
		self.assertEqual(quotation.workflow_state, "Pending")
		self.assertEqual(quotation.docstatus, 0)

		apply_workflow(quotation, "Approve")
		quotation.reload()
		self.assertEqual(quotation.workflow_state, "Approved")
		self.assertEqual(quotation.docstatus, 1)

	def test_closed_won_creates_sales_order_regardless_of_quotation_state(self):
		"""Sales Order creation on Won is independent of Quotation/Proposal --
		it always builds directly from the deal's own items, whether or not a
		Quotation was ever generated or approved."""
		deal = create_test_deal(organization_name="Unapproved Quote Org")
		deal.status = "Proposal"
		deal.save()
		deal.reload()
		self.assertTrue(deal.custom_quotation)

		quotation = frappe.get_doc("Quotation", deal.custom_quotation)
		self.assertEqual(quotation.docstatus, 0)

		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		self.assertTrue(deal.custom_sales_order)
		sales_order = frappe.get_doc("Sales Order", deal.custom_sales_order)
		self.assertEqual(sales_order.docstatus, 0)

	def test_closed_won_without_quotation_creates_sales_order_directly(self):
		deal = create_test_deal(organization_name="No Quote Org")
		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		self.assertFalse(deal.custom_quotation)
		self.assertTrue(deal.custom_sales_order)
		sales_order = frappe.get_doc("Sales Order", deal.custom_sales_order)
		self.assertEqual(sales_order.docstatus, 0)


def create_test_deal(**kwargs):
	data = {"doctype": "CRM Deal", "status": "Prospecting"}
	data.update(kwargs)
	return frappe.get_doc(data).insert(ignore_permissions=True)
