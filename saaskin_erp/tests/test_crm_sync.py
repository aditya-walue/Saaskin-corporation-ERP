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


def create_test_deal(**kwargs):
	data = {"doctype": "CRM Deal", "status": "Prospecting"}
	data.update(kwargs)
	return frappe.get_doc(data).insert(ignore_permissions=True)
