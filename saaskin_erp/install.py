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
			"fieldtype": "Data",
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
	create_label_translations()
	create_lead_assignment_rule()
	align_deal_pipeline_with_business_flow()
	create_purchase_order_approval_workflow()
	create_quotation_finance_approval_workflow()
	create_deal_form_script()
	create_sales_dashboard()
	create_operations_dashboard()
	create_support_dashboard()
	create_delivery_confirmation_custom_fields()
	create_delivery_confirmation_workflow()


def after_migrate():
	create_crm_sales_order_custom_fields()
	create_crm_lead_capture_custom_fields()
	create_label_translations()
	create_lead_assignment_rule()
	align_deal_pipeline_with_business_flow()
	create_purchase_order_approval_workflow()
	create_quotation_finance_approval_workflow()
	create_deal_form_script()
	create_sales_dashboard()
	create_operations_dashboard()
	create_support_dashboard()
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
