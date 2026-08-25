"""Lead Scoring + Qualification for the CRM Lead pipeline.

Bridges the "Lead Management" step of Saaskin's business flow:
Lead Capture -> Data Enrichment -> Lead Scoring -> Qualification -> Sales Assignment.

Runs on every CRM Lead save (after fcrm's own enrichment has had a chance to
fill in organization/industry/employee-count fields), scores the lead, and --
only for leads still in an untriaged status -- routes it to "Qualified" or
"Nurture". Sales Assignment itself is handled by a standard Frappe Assignment
Rule (see install.create_lead_assignment_rule) that fires once status becomes
"Qualified"; fcrm's own ToDo hooks then sync the assignment onto lead_owner.
"""

QUALIFY_THRESHOLD = 50

AUTO_TRIAGE_STATUSES = {"New", "Contacted"}

HIGH_VALUE_EMPLOYEE_TIERS = {"51-200", "201-500", "501-1000", "1000+"}
HIGH_VALUE_ANNUAL_REVENUE = 1_000_000

SCORE_WEIGHTS = {
	"email": 20,
	"mobile_no": 15,
	"organization": 15,
	"website": 10,
	"job_title": 10,
	"industry": 10,
}


def score_and_qualify_lead(doc, method=None):
	if doc.get("converted"):
		return

	doc.lead_score = compute_lead_score(doc)

	if doc.status not in AUTO_TRIAGE_STATUSES:
		return

	doc.status = "Qualified" if doc.lead_score >= QUALIFY_THRESHOLD else "Nurture"


def compute_lead_score(doc):
	score = sum(weight for fieldname, weight in SCORE_WEIGHTS.items() if doc.get(fieldname))

	if doc.get("no_of_employees") in HIGH_VALUE_EMPLOYEE_TIERS:
		score += 10

	if (doc.get("annual_revenue") or 0) >= HIGH_VALUE_ANNUAL_REVENUE:
		score += 10

	return min(score, 100)
