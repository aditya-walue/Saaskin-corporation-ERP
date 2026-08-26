import frappe
from frappe.tests import IntegrationTestCase

from saaskin_erp.crm_sync import DEFAULT_UOM, FALLBACK_ITEM_CODE


class TestCRMSync(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_won_deal_creates_customer_and_sales_order(self):
		deal = create_test_deal(organization_name="Won Sync Org")
		self.assertFalse(deal.custom_sales_order)

		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		self.assertTrue(deal.custom_customer)
		self.assertTrue(deal.custom_sales_order)

		customer = frappe.db.get_value("Customer", deal.custom_customer, "customer_name")
		self.assertEqual(customer, "Won Sync Org")

		sales_order = frappe.get_doc("Sales Order", deal.custom_sales_order)
		self.assertEqual(sales_order.customer, deal.custom_customer)
		self.assertEqual(sales_order.custom_crm_deal, deal.name)
		self.assertEqual(sales_order.docstatus, 0)

	def test_non_won_status_does_not_create_sales_order(self):
		deal = create_test_deal(organization_name="Open Sync Org")
		deal.status = "Prospecting"
		deal.save()
		deal.reload()

		self.assertFalse(deal.custom_sales_order)
		self.assertFalse(deal.custom_customer)

	def test_saving_won_deal_again_does_not_duplicate_sales_order(self):
		deal = create_test_deal(organization_name="Idempotent Sync Org")
		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		first_sales_order = deal.custom_sales_order
		self.assertTrue(first_sales_order)

		deal.next_step = "Follow up on onboarding"
		deal.save()
		deal.reload()

		self.assertEqual(deal.custom_sales_order, first_sales_order)
		sales_orders = frappe.get_all("Sales Order", filters={"custom_crm_deal": deal.name})
		self.assertEqual(len(sales_orders), 1)

	def test_won_deal_reuses_existing_customer(self):
		existing_customer = frappe.new_doc("Customer")
		existing_customer.customer_name = "Reuse Sync Org"
		existing_customer.customer_type = "Company"
		existing_customer.insert(ignore_permissions=True)

		deal = create_test_deal(organization_name="Reuse Sync Org")
		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		self.assertEqual(deal.custom_customer, existing_customer.name)

	def test_won_deal_products_become_sales_order_items(self):
		item_code = "SYNC-TEST-PRODUCT"
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": "Sync Test Product",
					"item_group": "Products",
					"stock_uom": "Nos",
					"is_stock_item": 0,
				}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("CRM Product", item_code):
			frappe.get_doc(
				{
					"doctype": "CRM Product",
					"product_code": item_code,
					"product_name": "Sync Test Product",
					"standard_rate": 250,
				}
			).insert(ignore_permissions=True)

		deal = create_test_deal(organization_name="Product Sync Org")
		deal.append(
			"products",
			{"product_code": item_code, "product_name": "Sync Test Product", "qty": 3, "rate": 250},
		)
		deal.save()

		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		sales_order = frappe.get_doc("Sales Order", deal.custom_sales_order)
		self.assertEqual(len(sales_order.items), 1)
		item_row = sales_order.items[0]
		self.assertEqual(item_row.item_code, item_code)
		self.assertEqual(item_row.qty, 3)
		self.assertEqual(item_row.rate, 250)
		self.assertEqual(item_row.uom, DEFAULT_UOM)

	def test_won_deal_without_products_uses_fallback_item_and_deal_value(self):
		deal = create_test_deal(organization_name="Fallback Sync Org", deal_value=5000)
		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		sales_order = frappe.get_doc("Sales Order", deal.custom_sales_order)
		self.assertEqual(len(sales_order.items), 1)
		item_row = sales_order.items[0]
		self.assertEqual(item_row.item_code, FALLBACK_ITEM_CODE)
		self.assertEqual(item_row.qty, 1)
		self.assertEqual(item_row.rate, 5000)

	def test_won_deal_links_primary_contact_to_customer(self):
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Sneha",
				"last_name": "Iyer",
				"email_ids": [{"email_id": "sneha@contact-sync-test.example", "is_primary": 1}],
			}
		).insert(ignore_permissions=True)

		deal = create_test_deal(organization_name="Contact Sync Org")
		deal.append("contacts", {"contact": contact.name, "is_primary": 1})
		deal.save()

		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		customer = frappe.get_doc("Customer", deal.custom_customer)
		self.assertEqual(customer.customer_primary_contact, contact.name)
		contact.reload()
		self.assertTrue(
			any(link.link_doctype == "Customer" and link.link_name == customer.name for link in contact.links)
		)

	def test_won_deal_does_not_overwrite_existing_primary_contact(self):
		existing_contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Existing",
				"last_name": "Primary",
				"email_ids": [{"email_id": "existing@contact-sync-test.example", "is_primary": 1}],
			}
		).insert(ignore_permissions=True)

		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Preexisting Primary Contact Org",
				"customer_type": "Company",
				"customer_primary_contact": existing_contact.name,
			}
		).insert(ignore_permissions=True)

		new_contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "New",
				"last_name": "Deal Contact",
				"email_ids": [{"email_id": "new@contact-sync-test.example", "is_primary": 1}],
			}
		).insert(ignore_permissions=True)

		deal = create_test_deal(organization_name="Preexisting Primary Contact Org")
		deal.append("contacts", {"contact": new_contact.name, "is_primary": 1})
		deal.save()

		deal.status = "Closed Won"
		deal.save()
		deal.reload()

		self.assertEqual(deal.custom_customer, customer.name)
		self.assertEqual(
			frappe.db.get_value("Customer", customer.name, "customer_primary_contact"), existing_contact.name
		)

	def test_expected_deal_value_fills_from_products_total_on_first_save(self):
		"""fcrm's own update_expected_deal_value() only overwrites an already
		-nonzero expected_deal_value, so it never fires on a fresh deal (0 is
		falsy). Our hook fixes that -- this locks the fix in."""
		if not frappe.db.get_single_value("FCRM Settings", "auto_update_expected_deal_value"):
			frappe.db.set_single_value("FCRM Settings", "auto_update_expected_deal_value", 1)

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization_name": "Expected Value Org",
				"status": "Prospecting",
				# total/net_total are normally computed client-side and submitted
				# alongside the save; simulate that here.
				"total": 1000,
				"net_total": 1000,
			}
		)
		self.assertFalse(deal.expected_deal_value)
		deal.insert(ignore_permissions=True)
		deal.reload()

		self.assertEqual(deal.expected_deal_value, 1000)


def create_test_deal(**kwargs):
	data = {"doctype": "CRM Deal", "status": "Prospecting"}
	data.update(kwargs)
	return frappe.get_doc(data).insert(ignore_permissions=True)
