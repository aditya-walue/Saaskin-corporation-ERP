import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CRM_SALES_ORDER_CUSTOM_FIELDS = {
	"CRM Deal": [
		{
			"fieldname": "saaskin_sales_order_section",
			"label": "Sales Order",
			"fieldtype": "Section Break",
			"insert_after": "products",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer",
			"insert_after": "saaskin_sales_order_section",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_quotation",
			"label": "Quotation",
			"fieldtype": "Link",
			"options": "Quotation",
			"insert_after": "custom_customer",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_sales_order",
			"label": "Sales Order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"insert_after": "custom_quotation",
			"read_only": 1,
			"no_copy": 1,
		},
	],
	"Sales Order": [
		{
			"fieldname": "custom_crm_deal",
			"label": "CRM Deal",
			"fieldtype": "Link",
			"options": "CRM Deal",
			"insert_after": "customer",
			"read_only": 1,
			"no_copy": 1,
		},
	],
	"Quotation": [
		{
			"fieldname": "custom_crm_deal",
			"label": "CRM Deal",
			"fieldtype": "Link",
			"options": "CRM Deal",
			"insert_after": "party_name",
			"read_only": 1,
			"no_copy": 1,
		},
	],
}

CRM_LEAD_CAPTURE_CUSTOM_FIELDS = {
	"CRM Lead": [
		{
			"fieldname": "campaign_tracking_section",
			"label": "Campaign Tracking",
			"fieldtype": "Section Break",
			"insert_after": "source",
			"collapsible": 1,
		},
		{
			"fieldname": "utm_source",
			"label": "UTM Source",
			"fieldtype": "Data",
			"insert_after": "campaign_tracking_section",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "utm_medium",
			"label": "UTM Medium",
			"fieldtype": "Data",
			"insert_after": "utm_source",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "utm_campaign",
			"label": "UTM Campaign",
			"fieldtype": "Data",
			"insert_after": "utm_medium",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "campaign_tracking_column_break",
			"fieldtype": "Column Break",
			"insert_after": "utm_campaign",
		},
		{
			"fieldname": "utm_content",
			"label": "UTM Content",
			"fieldtype": "Data",
			"insert_after": "campaign_tracking_column_break",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "landing_page",
			"label": "Landing Page",
			"fieldtype": "Small Text",
			"insert_after": "utm_content",
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "lead_score",
			"label": "Lead Score",
			"fieldtype": "Int",
			"insert_after": "landing_page",
			"read_only": 1,
			"no_copy": 1,
			"default": "0",
		},
		{
			"fieldname": "country",
			"label": "Country",
			"fieldtype": "Link",
			"options": "Country",
			"insert_after": "mobile_no",
		},
		{
			"fieldname": "message",
			"label": "Message",
			"fieldtype": "Small Text",
			"insert_after": "country",
		},
	],
}

DELIVERY_CONFIRMATION_CUSTOM_FIELDS = {
	"Delivery Note": [
		{
			"fieldname": "delivery_confirmation_section",
			"label": "Delivery Confirmation",
			"fieldtype": "Section Break",
			"insert_after": "transporter_name",
			"collapsible": 1,
		},
		{
			"fieldname": "delivered_on",
			"label": "Delivered On",
			"fieldtype": "Datetime",
			"insert_after": "delivery_confirmation_section",
			"read_only": 1,
			"no_copy": 1,
			"allow_on_submit": 1,
		},
		{
			"fieldname": "delivered_by",
			"label": "Delivery Confirmed By",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "delivered_on",
			"read_only": 1,
			"no_copy": 1,
			"allow_on_submit": 1,
		},
	],
}


LABEL_TRANSLATIONS = {
	"Convert to Deal": "Convert",
}

LEAD_ASSIGNMENT_RULE_NAME = "Qualified Lead - Sales Assignment"
ASSIGNMENT_DAYS = [
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
	"Sunday",
]


def after_install():
	create_crm_sales_order_custom_fields()
	create_crm_lead_capture_custom_fields()
	create_web_form_lead_source()
	create_label_translations()
	create_lead_assignment_rule()
	create_qualified_deal_assignment_rule()
	align_deal_pipeline_with_business_flow()
	create_purchase_order_approval_workflow()
	create_quotation_finance_approval_workflow()
	create_deal_form_script()
	create_sales_dashboard()
	create_operations_dashboard()
	create_support_dashboard()
	create_inquiry_web_form()
	create_get_in_touch_web_page()
	create_delivery_confirmation_custom_fields()
	create_delivery_confirmation_workflow()


def after_migrate():
	create_crm_sales_order_custom_fields()
	create_crm_lead_capture_custom_fields()
	create_web_form_lead_source()
	create_label_translations()
	create_lead_assignment_rule()
	create_qualified_deal_assignment_rule()
	align_deal_pipeline_with_business_flow()
	create_purchase_order_approval_workflow()
	create_quotation_finance_approval_workflow()
	create_deal_form_script()
	create_sales_dashboard()
	create_operations_dashboard()
	create_support_dashboard()
	create_inquiry_web_form()
	create_get_in_touch_web_page()
	create_delivery_confirmation_custom_fields()
	create_delivery_confirmation_workflow()


def create_crm_sales_order_custom_fields():
	if "crm" not in frappe.get_installed_apps():
		return
	create_custom_fields(CRM_SALES_ORDER_CUSTOM_FIELDS, update=True)


def create_crm_lead_capture_custom_fields():
	if "crm" not in frappe.get_installed_apps():
		return
	create_custom_fields(CRM_LEAD_CAPTURE_CUSTOM_FIELDS, update=True)


def create_web_form_lead_source():
	# The lead-capture web forms default source to "Web Form" -- fcrm doesn't
	# ship this as a standard CRM Lead Source on every site, so submissions
	# fail with a LinkValidationError until this exists.
	if "crm" not in frappe.get_installed_apps():
		return
	if frappe.db.exists("CRM Lead Source", "Web Form"):
		return
	frappe.get_doc({"doctype": "CRM Lead Source", "source_name": "Web Form"}).insert(
		ignore_permissions=True
	)


def create_delivery_confirmation_custom_fields():
	if not frappe.db.exists("DocType", "Delivery Note"):
		return
	create_custom_fields(DELIVERY_CONFIRMATION_CUSTOM_FIELDS, update=True)


def create_label_translations():
	if "crm" not in frappe.get_installed_apps():
		return
	for source_text, translated_text in LABEL_TRANSLATIONS.items():
		existing = frappe.db.exists("Translation", {"source_text": source_text, "language": "en"})
		if existing:
			frappe.db.set_value("Translation", existing, "translated_text", translated_text)
			continue
		frappe.get_doc(
			{
				"doctype": "Translation",
				"language": "en",
				"source_text": source_text,
				"translated_text": translated_text,
			}
		).insert(ignore_permissions=True)


def create_lead_assignment_rule():
	if "crm" not in frappe.get_installed_apps():
		return
	if frappe.db.exists("Assignment Rule", LEAD_ASSIGNMENT_RULE_NAME):
		return

	sales_users = frappe.get_all(
		"Has Role",
		filters={"role": "Sales User", "parenttype": "User"},
		pluck="parent",
	)
	sales_users = [
		user
		for user in sales_users
		if user != "Administrator" and frappe.db.get_value("User", user, "enabled")
	]
	if not sales_users:
		return

	rule = frappe.new_doc("Assignment Rule")
	rule.name = LEAD_ASSIGNMENT_RULE_NAME
	rule.document_type = "CRM Lead"
	rule.assign_condition = "status == 'Qualified' and not lead_owner"
	rule.rule = "Round Robin"
	rule.description = "Auto-assign qualified leads to the sales team, round robin."
	for day in ASSIGNMENT_DAYS:
		rule.append("assignment_days", {"day": day})
	for user in sales_users:
		rule.append("users", {"user": user})
	rule.insert(ignore_permissions=True)


DEAL_ASSIGNMENT_RULE_NAME = "Qualified Deal - Sales Assignment"


def create_qualified_deal_assignment_rule():
	if "crm" not in frappe.get_installed_apps():
		return
	if frappe.db.exists("Assignment Rule", DEAL_ASSIGNMENT_RULE_NAME):
		return

	sales_users = frappe.get_all(
		"Has Role",
		filters={"role": "Sales User", "parenttype": "User"},
		pluck="parent",
	)
	sales_users = [
		user
		for user in sales_users
		if user != "Administrator" and frappe.db.get_value("User", user, "enabled")
	]
	if not sales_users:
		return

	rule = frappe.new_doc("Assignment Rule")
	rule.name = DEAL_ASSIGNMENT_RULE_NAME
	rule.document_type = "CRM Deal"
	rule.assign_condition = "status == 'Qualified' and not deal_owner"
	rule.rule = "Round Robin"
	rule.description = "Auto-assign qualified deals to the sales team, round robin."
	for day in ASSIGNMENT_DAYS:
		rule.append("assignment_days", {"day": day})
	for user in sales_users:
		rule.append("users", {"user": user})
	rule.insert(ignore_permissions=True)


DEAL_STATUS_RENAMES = {
	"Qualification": "Prospecting",
	"Demo/Making": "Contacted",
	"Proposal/Quotation": "Qualified",
	"Ready to Close": "Proposal",
	"Won": "Closed Won",
	"Lost": "Closed Lost",
}

# name, type, position, probability, color
DEAL_STATUS_PIPELINE = [
	("Prospecting", "Open", 1, 10, "gray"),
	("Contacted", "Ongoing", 2, 20, "orange"),
	("Qualified", "Ongoing", 3, 40, "blue"),
	("Proposal", "Ongoing", 4, 60, "purple"),
	("Negotiation", "Ongoing", 5, 75, "yellow"),
	("Closed Won", "Won", 6, 100, "green"),
	("Closed Lost", "Lost", 7, 0, "red"),
]


def align_deal_pipeline_with_business_flow():
	if "crm" not in frappe.get_installed_apps():
		return
	if not frappe.db.exists("DocType", "CRM Deal Status"):
		return

	for old_name, new_name in DEAL_STATUS_RENAMES.items():
		if frappe.db.exists("CRM Deal Status", old_name) and not frappe.db.exists(
			"CRM Deal Status", new_name
		):
			frappe.rename_doc("CRM Deal Status", old_name, new_name)

	for name, status_type, position, probability, color in DEAL_STATUS_PIPELINE:
		if not frappe.db.exists("CRM Deal Status", name):
			frappe.get_doc(
				{
					"doctype": "CRM Deal Status",
					"deal_status": name,
					"type": status_type,
					"position": position,
					"probability": probability,
					"color": color,
				}
			).insert(ignore_permissions=True)
			continue
		frappe.db.set_value(
			"CRM Deal Status",
			name,
			{"type": status_type, "position": position, "probability": probability, "color": color},
			update_modified=False,
		)


PURCHASE_ORDER_WORKFLOW_NAME = "Purchase Order Approval"

# state, doc_status, allow_edit role
PURCHASE_ORDER_WORKFLOW_STATES = [
	("Draft", "0", "Purchase User"),
	("Pending", "0", "Purchase Manager"),
	("Approved", "1", "Purchase Manager"),
	("Rejected", "0", "Purchase User"),
]

# state, action, next_state, allowed role
PURCHASE_ORDER_WORKFLOW_TRANSITIONS = [
	("Draft", "Review", "Pending", "Purchase User"),
	("Pending", "Approve", "Approved", "Purchase Manager"),
	("Pending", "Reject", "Rejected", "Purchase Manager"),
	("Rejected", "Review", "Pending", "Purchase User"),
]


def create_purchase_order_approval_workflow():
	create_approval_workflow(
		PURCHASE_ORDER_WORKFLOW_NAME,
		"Purchase Order",
		PURCHASE_ORDER_WORKFLOW_STATES,
		PURCHASE_ORDER_WORKFLOW_TRANSITIONS,
	)


QUOTATION_WORKFLOW_NAME = "Quotation Finance Approval"

# state, doc_status, allow_edit role
QUOTATION_WORKFLOW_STATES = [
	("Draft", "0", "Sales User"),
	("Pending", "0", "Accounts Manager"),
	("Approved", "1", "Accounts Manager"),
	("Rejected", "0", "Sales User"),
]

# state, action, next_state, allowed role
QUOTATION_WORKFLOW_TRANSITIONS = [
	("Draft", "Submit for Finance Approval", "Pending", "Sales User"),
	("Pending", "Approve", "Approved", "Accounts Manager"),
	("Pending", "Reject", "Rejected", "Accounts Manager"),
	("Rejected", "Submit for Finance Approval", "Pending", "Sales User"),
]


def create_quotation_finance_approval_workflow():
	create_approval_workflow(
		QUOTATION_WORKFLOW_NAME,
		"Quotation",
		QUOTATION_WORKFLOW_STATES,
		QUOTATION_WORKFLOW_TRANSITIONS,
	)


DELIVERY_NOTE_WORKFLOW_NAME = "Delivery Confirmation"

# state, doc_status, allow_edit role
DELIVERY_NOTE_WORKFLOW_STATES = [
	("Draft", "0", "Stock User"),
	("Shipped", "1", "Stock User"),
	("Delivered", "1", "Stock User"),
]

# state, action, next_state, allowed role
DELIVERY_NOTE_WORKFLOW_TRANSITIONS = [
	("Draft", "Ship", "Shipped", "Stock User"),
	("Shipped", "Confirm Delivery", "Delivered", "Stock User"),
]


def create_delivery_confirmation_workflow():
	create_approval_workflow(
		DELIVERY_NOTE_WORKFLOW_NAME,
		"Delivery Note",
		DELIVERY_NOTE_WORKFLOW_STATES,
		DELIVERY_NOTE_WORKFLOW_TRANSITIONS,
	)


def create_approval_workflow(workflow_name, document_type, states, transitions):
	if not frappe.db.exists("DocType", document_type):
		return
	if frappe.db.exists("Workflow", workflow_name):
		return

	for state_name, _doc_status, _role in states:
		if not frappe.db.exists("Workflow State", state_name):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state_name}).insert(
				ignore_permissions=True
			)

	for _state, action_name, _next_state, _role in transitions:
		if not frappe.db.exists("Workflow Action Master", action_name):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action_name}
			).insert(ignore_permissions=True)

	workflow = frappe.new_doc("Workflow")
	workflow.workflow_name = workflow_name
	workflow.document_type = document_type
	workflow.workflow_state_field = "workflow_state"
	workflow.is_active = 1
	workflow.send_email_alert = 0

	for state_name, doc_status, role in states:
		workflow.append(
			"states", {"state": state_name, "doc_status": doc_status, "allow_edit": role}
		)

	for state_name, action_name, next_state, role in transitions:
		workflow.append(
			"transitions",
			{"state": state_name, "action": action_name, "next_state": next_state, "allowed": role},
		)

	workflow.insert(ignore_permissions=True)


DEAL_FORM_SCRIPT_NAME = "Saaskin - Deal Order Actions"

DEAL_FORM_SCRIPT = """function setupForm({ doc, updateField }) {
	let actions = []

	const PIPELINE_STATUSES = [
		['Prospecting', '⚪'],
		['Contacted', '🟠'],
		['Qualified', '🔵'],
		['Proposal', '🟣'],
		['Negotiation', '🟡'],
		['Closed Won', '🟢'],
		['Closed Lost', '🔴'],
	]

	actions.push({
		buttonLabel: __('Convert'),
		group: __('Convert'),
		items: PIPELINE_STATUSES.map(([status, dot]) => ({
			label: __(status),
			icon: dot,
			onClick: () => {
				if (status === doc.status) return
				updateField('status', status)
			},
		})),
	})

	return { actions }
}"""


def create_deal_form_script():
	if "crm" not in frappe.get_installed_apps():
		return
	if frappe.db.exists("CRM Form Script", DEAL_FORM_SCRIPT_NAME):
		frappe.db.set_value(
			"CRM Form Script", DEAL_FORM_SCRIPT_NAME, {"script": DEAL_FORM_SCRIPT, "enabled": 1}
		)
		return

	frappe.get_doc(
		{
			"doctype": "CRM Form Script",
			"name": DEAL_FORM_SCRIPT_NAME,
			"dt": "CRM Deal",
			"view": "Form",
			"enabled": 1,
			"is_standard": 0,
			"script": DEAL_FORM_SCRIPT,
		}
	).insert(ignore_permissions=True)


def create_number_card(document_type, label, function="Count", filters=None, aggregate_field=None, color=None):
	# Number Card.autoname() always derives name from label (frappe wipes any
	# pre-set doc.name before calling it) -- label IS the identifier.
	if frappe.db.exists("Number Card", label):
		return
	card = frappe.new_doc("Number Card")
	card.label = label
	card.document_type = document_type
	card.type = "Document Type"
	card.function = function
	if aggregate_field:
		card.aggregate_function_based_on = aggregate_field
	card.filters_json = frappe.as_json(filters or [])
	card.is_public = 1
	if color:
		card.color = color
	card.insert(ignore_permissions=True)


def create_group_by_chart(document_type, group_by_based_on, label, chart_type="Bar", filters=None):
	# Dashboard Chart autonames field:chart_name -- same rule as above.
	if frappe.db.exists("Dashboard Chart", label):
		return
	chart = frappe.new_doc("Dashboard Chart")
	chart.chart_name = label
	chart.document_type = document_type
	chart.chart_type = "Group By"
	chart.group_by_type = "Count"
	chart.group_by_based_on = group_by_based_on
	chart.timeseries = 0
	chart.type = chart_type
	chart.filters_json = frappe.as_json(filters or [])
	chart.is_public = 1
	chart.insert(ignore_permissions=True)


def create_dashboard(dashboard_name, card_names, chart_names):
	if frappe.db.exists("Dashboard", dashboard_name):
		return
	dashboard = frappe.new_doc("Dashboard")
	dashboard.dashboard_name = dashboard_name
	dashboard.is_default = 0
	for card_name in card_names:
		dashboard.append("cards", {"card": card_name})
	for chart_name in chart_names:
		dashboard.append("charts", {"chart": chart_name, "width": "Half"})
	dashboard.insert(ignore_permissions=True)


SALES_DASHBOARD_CARDS = [
	dict(document_type="CRM Lead", label="Total Leads"),
	dict(
		document_type="CRM Deal",
		label="Open Opportunities",
		filters=[["CRM Deal", "status", "not in", ["Closed Won", "Closed Lost"]]],
	),
	dict(
		document_type="CRM Deal",
		label="Won Value (All Time)",
		function="Sum",
		aggregate_field="deal_value",
		filters=[["CRM Deal", "status", "=", "Closed Won"]],
	),
	dict(
		document_type="CRM Deal",
		label="Expected Pipeline Value (Forecast)",
		function="Sum",
		aggregate_field="expected_deal_value",
		filters=[["CRM Deal", "status", "not in", ["Closed Won", "Closed Lost"]]],
	),
	dict(
		document_type="CRM Task",
		label="Open Follow-up Tasks",
		filters=[["CRM Task", "status", "not in", ["Done", "Canceled"]]],
	),
]

SALES_DASHBOARD_CHARTS = [
	dict(
		document_type="CRM Deal",
		group_by_based_on="status",
		label="Pipeline by Stage",
		chart_type="Donut",
	),
]

OPERATIONS_DASHBOARD_CARDS = [
	dict(
		document_type="Sales Order",
		label="Open Sales Orders",
		filters=[["Sales Order", "status", "not in", ["Completed", "Closed", "Cancelled"]]],
	),
	dict(document_type="Item", label="Active SKUs", filters=[["Item", "disabled", "=", 0]]),
	dict(
		document_type="Purchase Order",
		label="Pending Purchase Orders",
		filters=[["Purchase Order", "workflow_state", "in", ["Draft", "Pending"]]],
	),
	dict(
		document_type="Delivery Note",
		label="Deliveries In Transit",
		filters=[["Delivery Note", "workflow_state", "=", "Shipped"]],
	),
]

OPERATIONS_DASHBOARD_CHARTS = [
	dict(
		document_type="Delivery Note",
		group_by_based_on="workflow_state",
		label="Delivery Status Breakdown",
		chart_type="Donut",
	),
]

SUPPORT_DASHBOARD_CARDS = [
	dict(
		document_type="HD Ticket",
		label="Open Tickets",
		filters=[["HD Ticket", "status", "=", "Open"]],
	),
	dict(
		document_type="HD Ticket",
		label="Avg Resolution Time (sec)",
		function="Average",
		aggregate_field="resolution_time",
	),
]

SUPPORT_DASHBOARD_CHARTS = [
	dict(
		document_type="HD Ticket",
		group_by_based_on="agreement_status",
		label="Tickets by SLA Status",
		chart_type="Donut",
	),
	dict(
		document_type="HD Ticket",
		group_by_based_on="priority",
		label="Tickets by Priority",
		chart_type="Bar",
	),
]


def create_sales_dashboard():
	create_dashboard_from_specs("Sales Dashboard", SALES_DASHBOARD_CARDS, SALES_DASHBOARD_CHARTS)


def create_operations_dashboard():
	if not frappe.db.exists("DocType", "Purchase Order"):
		return
	create_dashboard_from_specs(
		"Operations Dashboard", OPERATIONS_DASHBOARD_CARDS, OPERATIONS_DASHBOARD_CHARTS
	)


def create_support_dashboard():
	if "helpdesk" not in frappe.get_installed_apps():
		return
	create_dashboard_from_specs("Customer Support Dashboard", SUPPORT_DASHBOARD_CARDS, SUPPORT_DASHBOARD_CHARTS)


def create_dashboard_from_specs(dashboard_name, card_specs, chart_specs):
	for spec in card_specs:
		if not frappe.db.exists("DocType", spec["document_type"]):
			continue
		create_number_card(**spec)

	for spec in chart_specs:
		if not frappe.db.exists("DocType", spec["document_type"]):
			continue
		create_group_by_chart(**spec)

	card_names = [s["label"] for s in card_specs if frappe.db.exists("Number Card", s["label"])]
	chart_names = [s["label"] for s in chart_specs if frappe.db.exists("Dashboard Chart", s["label"])]
	create_dashboard(dashboard_name, card_names, chart_names)


GET_IN_TOUCH_PAGE_ROUTE = "contact"

GET_IN_TOUCH_PAGE_HTML = """
<style>
	nav.navbar {
		display: none !important;
	}

	.sk-contact {
		max-width: 1100px;
		margin: 0 auto;
		padding: 3rem 1.25rem 4rem;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
		color: #1a1a1a;
		display: grid;
		grid-template-columns: 340px 1fr;
		gap: 2rem;
	}

	.sk-contact__info {
		background: #EAF0FE;
		border-radius: 10px;
		padding: 2rem 1.75rem;
	}

	.sk-contact__info h2 {
		color: #2952CC;
		font-size: 1.6rem;
		font-weight: 700;
		margin: 0 0 1.5rem;
	}

	.sk-contact__item {
		display: flex;
		gap: 0.85rem;
		margin-bottom: 1.5rem;
	}

	.sk-contact__item svg {
		flex: none;
		width: 20px;
		height: 20px;
		margin-top: 2px;
		color: #2952CC;
	}

	.sk-contact__item h3 {
		font-size: 1rem;
		font-weight: 600;
		color: #2952CC;
		margin: 0 0 0.3rem;
	}

	.sk-contact__item p {
		font-size: 0.95rem;
		line-height: 1.45;
		color: #444;
		margin: 0;
	}

	.sk-contact__main iframe.sk-contact__map {
		width: 100%;
		height: 260px;
		border: 1px solid #e2e2e2;
		border-radius: 8px;
		margin-bottom: 2rem;
	}

	.sk-contact__main h2 {
		color: #2952CC;
		font-size: 1.6rem;
		font-weight: 700;
		margin: 0 0 1rem;
	}

	.sk-inquiry-form__row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.sk-inquiry-form input,
	.sk-inquiry-form select,
	.sk-inquiry-form textarea {
		width: 100%;
		box-sizing: border-box;
		font: inherit;
		font-size: 0.95rem;
		padding: 0.85rem 1rem;
		margin-bottom: 1rem;
		border: 1px solid #d7dbe3;
		border-radius: 8px;
		background: #fff;
		color: #1a1a1a;
	}

	.sk-inquiry-form input:focus,
	.sk-inquiry-form select:focus,
	.sk-inquiry-form textarea:focus {
		outline: none;
		border-color: #2952CC;
	}

	.sk-inquiry-form textarea {
		resize: vertical;
		min-height: 140px;
	}

	.sk-inquiry-form button {
		width: 100%;
		font: inherit;
		font-size: 1rem;
		font-weight: 600;
		color: #fff;
		background: #2952CC;
		border: none;
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
	}

	.sk-inquiry-form button:hover {
		background: #23459E;
	}

	.sk-inquiry-form button:disabled {
		opacity: 0.6;
		cursor: default;
	}

	.sk-inquiry-form__status {
		margin: 0.85rem 0 0;
		font-size: 0.9rem;
	}

	.sk-inquiry-form__status[data-state="error"] {
		color: #B3261E;
	}

	.sk-inquiry-form__status[data-state="success"] {
		color: #1E7A34;
	}

	@media (max-width: 780px) {
		.sk-contact {
			grid-template-columns: 1fr;
		}

		.sk-inquiry-form__row {
			grid-template-columns: 1fr;
		}
	}

	.sk-contact__logo {
		grid-column: 1 / -1;
		margin-bottom: 0.5rem;
	}

	.sk-contact__logo img {
		height: 80px;
		width: auto;
		display: block;
	}
</style>

<div class="sk-contact">
	<div class="sk-contact__logo">
		<img src="/files/saaskin-logo.png" alt="Saaskin Corporation">
	</div>

	<div class="sk-contact__info">
		<h2>Contact Information</h2>

		<div class="sk-contact__item">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 6-9 12-9 12s-9-6-9-12a9 9 0 0 1 18 0Z"/><circle cx="12" cy="10" r="3"/></svg>
			<div>
				<h3>Address</h3>
				<p>275/184, First Floor, Office No: 2, Golden Enclave Periyar EVR Salai, Poonamallee High Rd, Kilpauk, Chennai, India</p>
			</div>
		</div>

		<div class="sk-contact__item">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
			<div>
				<h3>Working Hours</h3>
				<p>Monday - Saturday<br>9:30 AM - 6:30 PM</p>
			</div>
		</div>

		<div class="sk-contact__item">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.362 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0 1 22 16.92Z"/></svg>
			<div>
				<h3>Contact Numbers</h3>
				<p>+91-9940116677<br>+91-9840819191</p>
			</div>
		</div>

		<div class="sk-contact__item">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/></svg>
			<div>
				<h3>Email</h3>
				<p>info@saaskin.com</p>
			</div>
		</div>
	</div>

	<div class="sk-contact__main">
		<iframe
			class="sk-contact__map"
			src="https://www.google.com/maps?q=Saaskin+Corporation+Private+Limited+Golden+Enclave+Periyar+EVR+Salai+Kilpauk+Chennai&output=embed"
			title="Saaskin Corporation location"
			loading="lazy"
		></iframe>

		<h2>Send Us a Message</h2>

		<form class="sk-inquiry-form" id="sk-inquiry-form">
			<div class="sk-inquiry-form__row">
				<input type="text" name="first_name" placeholder="Name" autocomplete="name" required>
				<input type="email" name="email" placeholder="Email" autocomplete="email" required>
			</div>
			<select name="country" id="sk-inquiry-country" autocomplete="country-name">
				<option value="">Select Country</option>
			</select>
			<input type="tel" name="mobile_no" placeholder="Phone Number" autocomplete="tel">
			<textarea name="message" placeholder="Your Message" autocomplete="off"></textarea>
			<button type="submit" id="sk-inquiry-submit">Send Message</button>
			<p class="sk-inquiry-form__status" id="sk-inquiry-status"></p>
		</form>
	</div>
</div>

<script>
	(function () {
		var COUNTRIES = __SAASKIN_COUNTRIES_JSON__;
		var select = document.getElementById("sk-inquiry-country");
		COUNTRIES.forEach(function (name) {
			var opt = document.createElement("option");
			opt.value = name;
			opt.textContent = name;
			select.appendChild(opt);
		});

		var params = new URLSearchParams(window.location.search);
		var hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ""));
		hashParams.forEach(function (value, key) {
			if (!params.has(key)) params.set(key, value);
		});
		var form = document.getElementById("sk-inquiry-form");
		var submitBtn = document.getElementById("sk-inquiry-submit");
		var status = document.getElementById("sk-inquiry-status");

		form.addEventListener("submit", function (e) {
			e.preventDefault();

			var payload = {
				doctype: "CRM Lead",
				web_form_name: "get-in-touch",
				first_name: form.first_name.value,
				email: form.email.value,
				country: form.country.value,
				mobile_no: form.mobile_no.value,
				message: form.message.value,
				source: "Web Form",
				utm_source: params.get("utm_source") || "",
				utm_medium: params.get("utm_medium") || "",
				utm_campaign: params.get("utm_campaign") || "",
				utm_content: params.get("utm_content") || "",
				landing_page: window.location.href,
			};

			submitBtn.disabled = true;
			status.textContent = "";
			status.removeAttribute("data-state");

			fetch("/api/method/frappe.website.doctype.web_form.web_form.accept", {
				method: "POST",
				credentials: "omit",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ web_form: "get-in-touch", data: JSON.stringify(payload) }),
			})
				.then(function (res) {
					if (!res.ok) throw new Error("request_failed");
					return res.json();
				})
				.then(function () {
					status.setAttribute("data-state", "success");
					status.textContent = "Thanks for reaching out! Our team will get back to you shortly.";
					form.reset();
				})
				.catch(function () {
					status.setAttribute("data-state", "error");
					status.textContent = "Something went wrong. Please try again or email info@saaskin.com directly.";
				})
				.finally(function () {
					submitBtn.disabled = false;
				});
		});
	})();
</script>
"""

COUNTRY_NAMES = [
	"Afghanistan", "Åland Islands", "Albania", "Algeria", "American Samoa", "Andorra", "Angola",
	"Anguilla", "Antarctica", "Antigua and Barbuda", "Argentina", "Armenia", "Aruba", "Australia",
	"Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium",
	"Belize", "Benin", "Bermuda", "Bhutan", "Bolivia, Plurinational State of",
	"Bonaire, Sint Eustatius and Saba", "Bosnia and Herzegovina", "Botswana", "Bouvet Island", "Brazil",
	"British Indian Ocean Territory", "Brunei Darussalam", "Bulgaria", "Burkina Faso", "Burundi",
	"Cambodia", "Cameroon", "Canada", "Cape Verde", "Cayman Islands", "Central African Republic", "Chad",
	"Chile", "China", "Christmas Island", "Cocos (Keeling) Islands", "Colombia", "Comoros", "Congo",
	"Congo, The Democratic Republic of the", "Cook Islands", "Costa Rica", "Croatia", "Cuba",
	"Curaçao", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
	"Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia",
	"Falkland Islands (Malvinas)", "Faroe Islands", "Fiji", "Finland", "France", "French Guiana",
	"French Polynesia", "French Southern Territories", "Gabon", "Gambia", "Georgia", "Germany", "Ghana",
	"Gibraltar", "Greece", "Greenland", "Grenada", "Guadeloupe", "Guam", "Guatemala", "Guernsey",
	"Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Heard Island and McDonald Islands",
	"Holy See (Vatican City State)", "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia",
	"Iran", "Iraq", "Ireland", "Isle of Man", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan",
	"Jersey", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea, Democratic Peoples Republic of",
	"Korea, Republic of", "Kosovo", "Kuwait", "Kyrgyzstan", "Lao Peoples Democratic Republic", "Latvia",
	"Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Macao",
	"Macedonia", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
	"Martinique", "Mauritania", "Mauritius", "Mayotte", "Mexico", "Micronesia, Federated States of",
	"Moldova, Republic of", "Monaco", "Mongolia", "Montenegro", "Montserrat", "Morocco", "Mozambique",
	"Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Caledonia", "New Zealand", "Nicaragua",
	"Niger", "Nigeria", "Niue", "Norfolk Island", "Northern Mariana Islands", "Norway", "Oman",
	"Pakistan", "Palau", "Palestinian Territory, Occupied", "Panama", "Papua New Guinea", "Paraguay",
	"Peru", "Philippines", "Pitcairn", "Poland", "Portugal", "Puerto Rico", "Qatar", "Réunion",
	"Romania", "Russian Federation", "Rwanda", "Saint Barthélemy",
	"Saint Helena, Ascension and Tristan da Cunha", "Saint Kitts and Nevis", "Saint Lucia",
	"Saint Martin (French part)", "Saint Pierre and Miquelon", "Saint Vincent and the Grenadines",
	"Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles",
	"Sierra Leone", "Singapore", "Sint Maarten (Dutch part)", "Slovakia", "Slovenia", "Solomon Islands",
	"Somalia", "South Africa", "South Georgia and the South Sandwich Islands", "South Sudan", "Spain",
	"Sri Lanka", "Sudan", "Suriname", "Svalbard and Jan Mayen", "Swaziland", "Sweden", "Switzerland",
	"Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tokelau", "Tonga",
	"Trinidad and Tobago", "Tunisia", "Türkiye", "Turkmenistan", "Turks and Caicos Islands",
	"Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
	"United States Minor Outlying Islands", "Uruguay", "Uzbekistan", "Vanuatu",
	"Venezuela, Bolivarian Republic of", "Vietnam", "Virgin Islands, British", "Virgin Islands, U.S.",
	"Wallis and Futuna", "Western Sahara", "Yemen", "Zambia", "Zimbabwe",
]

GET_IN_TOUCH_PAGE_HTML = GET_IN_TOUCH_PAGE_HTML.replace(
	"__SAASKIN_COUNTRIES_JSON__", json.dumps(COUNTRY_NAMES)
)

INQUIRY_WEB_FORM_ROUTE = "inquiry"

INQUIRY_WEB_FORM_CLIENT_SCRIPT = """frappe.web_form.events.on('after_load', () => {
	const params = new URLSearchParams(window.location.search);
	const utm_fields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'];

	utm_fields.forEach((fieldname) => {
		const value = params.get(fieldname);
		if (value) {
			frappe.web_form.set_value(fieldname, value);
		}
	});

	frappe.web_form.set_value('landing_page', window.location.href);
});
"""

INQUIRY_WEB_FORM_FIELDS = [
	{"fieldname": "first_name", "fieldtype": "Data", "label": "Name", "reqd": 1},
	{"fieldname": "email", "fieldtype": "Data", "label": "Email", "options": "Email", "reqd": 1},
	{"fieldname": "country", "fieldtype": "Link", "label": "Select Country", "options": "Country"},
	{"fieldname": "mobile_no", "fieldtype": "Data", "label": "Phone Number", "options": "Phone"},
	{"fieldname": "message", "fieldtype": "Small Text", "label": "Your Message"},
	{
		"fieldname": "source",
		"fieldtype": "Link",
		"label": "Source",
		"options": "CRM Lead Source",
		"default": "Web Form",
		"hidden": 1,
		"read_only": 1,
	},
	{"fieldname": "utm_source", "fieldtype": "Data", "label": "UTM Source", "hidden": 1, "read_only": 1},
	{"fieldname": "utm_medium", "fieldtype": "Data", "label": "UTM Medium", "hidden": 1, "read_only": 1},
	{"fieldname": "utm_campaign", "fieldtype": "Data", "label": "UTM Campaign", "hidden": 1, "read_only": 1},
	{"fieldname": "utm_content", "fieldtype": "Data", "label": "UTM Content", "hidden": 1, "read_only": 1},
	{
		"fieldname": "landing_page",
		"fieldtype": "Small Text",
		"label": "Landing Page",
		"hidden": 1,
		"read_only": 1,
	},
]


def create_inquiry_web_form():
	"""Non-standard (is_standard=0) twin of the code-managed lead-capture-form.

	Standard Web Forms can only be updated by syncing the app's JSON fixture
	through a migrate -- the desk UI refuses direct edits ("duplicate the Web
	Form instead"). This one is a plain, freely-editable record instead, so
	it can be tweaked live without a deploy. Only created once; later edits
	made in the desk are never overwritten by this function.
	"""
	if frappe.db.exists("Web Form", {"route": INQUIRY_WEB_FORM_ROUTE}):
		return

	form = frappe.new_doc("Web Form")
	form.title = "Get in Touch"
	form.route = INQUIRY_WEB_FORM_ROUTE
	form.doc_type = "CRM Lead"
	form.is_standard = 0
	form.published = 1
	form.login_required = 0
	form.anonymous = 1
	form.apply_document_permissions = 0
	form.introduction_text = "<p>Tell us a bit about yourself and we'll get back to you shortly.</p>"
	form.success_message = "Thanks for reaching out! Our team will get back to you shortly."
	form.client_script = INQUIRY_WEB_FORM_CLIENT_SCRIPT
	form.button_label = "Send Message"
	for field in INQUIRY_WEB_FORM_FIELDS:
		form.append("web_form_fields", field)
	form.insert(ignore_permissions=True)


def create_get_in_touch_web_page():
	if not frappe.db.exists("Web Form", {"route": INQUIRY_WEB_FORM_ROUTE}):
		return

	existing = frappe.db.exists("Web Page", {"route": GET_IN_TOUCH_PAGE_ROUTE})
	if existing:
		frappe.db.set_value("Web Page", existing, "main_section_html", GET_IN_TOUCH_PAGE_HTML)
		return

	page = frappe.new_doc("Web Page")
	page.title = "Get in Touch"
	page.route = GET_IN_TOUCH_PAGE_ROUTE
	page.published = 1
	page.show_title = 0
	page.content_type = "HTML"
	page.main_section_html = GET_IN_TOUCH_PAGE_HTML
	page.insert(ignore_permissions=True)
