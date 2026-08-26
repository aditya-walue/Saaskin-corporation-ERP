"""Self-contained "Enrich from website" for CRM Deal and CRM Lead.

fcrm ships this as `crm.domain_enrichment` (background crawl + realtime
socket events), but that module only exists on fcrm's develop branch --
it's not in the site's pinned release (see DEAL_ENRICH_FORM_SCRIPT and
LEAD_ENRICH_FORM_SCRIPT in install.py). This is a lighter synchronous
replacement: fetch the record's website homepage once and fill in whichever
of a few fields are still empty.
"""

import re

import frappe
import requests

REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; SaaskinCRM-Enrichment/1.0)"

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_DESC_RE = re.compile(
	r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', re.IGNORECASE
)
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
MAILTO_RE = re.compile(r'href=["\']mailto:([^"\'?]+)', re.IGNORECASE)
TEL_RE = re.compile(r'href=["\']tel:([^"\']+)', re.IGNORECASE)
SOCIAL_PATTERNS = {
	"linkedin": re.compile(r'href=["\'](https?://(?:www\.)?linkedin\.com/[^"\']+)', re.IGNORECASE),
	"twitter": re.compile(r'href=["\'](https?://(?:www\.)?(?:twitter|x)\.com/[^"\']+)', re.IGNORECASE),
	"facebook": re.compile(r'href=["\'](https?://(?:www\.)?facebook\.com/[^"\']+)', re.IGNORECASE),
}
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp")


@frappe.whitelist()
def enrich_deal(deal):
	return _enrich("CRM Deal", deal, organization_field="organization_name")


@frappe.whitelist()
def enrich_lead(lead):
	return _enrich("CRM Lead", lead, organization_field="organization")


def _enrich(doctype, docname, organization_field):
	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("write")

	# Field sets drift across crm app releases (e.g. company_description /
	# social links don't exist on older pinned versions) -- only ever touch
	# fields that actually exist on this site's schema for this doctype.
	valid_fields = {f.fieldname for f in doc.meta.fields}

	website = (doc.website or "").strip()
	if not website:
		frappe.throw(frappe._("Set a Website on this record before enriching."))

	url = website if website.startswith(("http://", "https://")) else f"https://{website}"

	try:
		response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
		response.raise_for_status()
	except requests.RequestException as e:
		return {
			"filled_fields": [],
			"notes": [frappe._("Could not reach {0}: {1}").format(website, str(e))],
			"values": {},
		}

	html = response.text
	text = re.sub(r"<[^>]+>", " ", html)

	values = {}

	if organization_field in valid_fields and not doc.get(organization_field):
		title_match = TITLE_RE.search(html)
		if title_match:
			title = re.sub(r"\s+", " ", title_match.group(1)).strip()
			title = re.split(r"[|\-–]", title)[0].strip()
			if title:
				values[organization_field] = title

	if "company_description" in valid_fields and not doc.get("company_description"):
		desc_match = META_DESC_RE.search(html)
		if desc_match:
			desc = desc_match.group(1).strip()
			if desc:
				values["company_description"] = desc

	if "email" in valid_fields and not doc.get("email"):
		mailto_matches = MAILTO_RE.findall(html)
		if mailto_matches:
			values["email"] = mailto_matches[0].strip()
		else:
			emails = [e for e in EMAIL_RE.findall(text) if not e.lower().endswith(IMAGE_EXTENSIONS)]
			if emails:
				values["email"] = emails[0]

	if "phone" in valid_fields and not doc.get("phone"):
		# Only trust explicit tel: links -- free-text digit scanning on a page
		# throws up too many false positives (dates, version numbers, IDs).
		tel_matches = TEL_RE.findall(html)
		if tel_matches:
			values["phone"] = tel_matches[0].strip()

	for fieldname, pattern in SOCIAL_PATTERNS.items():
		if fieldname not in valid_fields or doc.get(fieldname):
			continue
		match = pattern.search(html)
		if match:
			values[fieldname] = match.group(1)

	if not values:
		return {
			"filled_fields": [],
			"notes": [frappe._("Nothing new found on {0}.").format(website)],
			"values": {},
		}

	for fieldname, value in values.items():
		doc.db_set(fieldname, value, update_modified=False)

	return {"filled_fields": list(values.keys()), "notes": [], "values": values}
