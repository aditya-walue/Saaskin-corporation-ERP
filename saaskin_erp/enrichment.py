"""Self-contained "Enrich from website" for CRM Deal and CRM Lead.

fcrm ships this as `crm.domain_enrichment` (background crawl + realtime
socket events), but that module only exists on fcrm's develop branch --
it's not in the site's pinned release (see DEAL_ENRICH_FORM_SCRIPT and
LEAD_ENRICH_FORM_SCRIPT in install.py). This is a lighter synchronous
replacement: fetch the record's website homepage once and fill in whichever
of a few fields are still empty.
"""

import json
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

JSONLD_RE = re.compile(
	r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL
)
ADDRESS_TAG_RE = re.compile(r"<address[^>]*>(.*?)</address>", re.IGNORECASE | re.DOTALL)
P_TAG_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
ADDRESS_KEYWORD_RE = re.compile(
	r"\b(road|street|st\.|avenue|ave\.|floor|building|layout|nagar|block|sector|"
	r"lane|drive|blvd|boulevard|highway|hwy|suite|ste\.)\b",
	re.IGNORECASE,
)
POSTAL_CODE_RE = re.compile(r"\b\d{5,6}(?:-\d{4})?\b")
NAME_LIKE_RE = re.compile(r"[A-Za-z .'-]+")

PLAYWRIGHT_TIMEOUT_MS = 15000


def _find_postal_address(node):
	if isinstance(node, dict):
		if node.get("@type") == "PostalAddress":
			parts = [
				node.get("streetAddress"),
				node.get("addressLocality"),
				node.get("addressRegion"),
				node.get("postalCode"),
				node.get("addressCountry"),
			]
			parts = [str(p).strip() for p in parts if p]
			if parts:
				return ", ".join(parts)
		for value in node.values():
			found = _find_postal_address(value)
			if found:
				return found
	elif isinstance(node, list):
		for item in node:
			found = _find_postal_address(item)
			if found:
				return found
	return None


def _extract_address(html):
	# Prefer structured data (schema.org PostalAddress in a JSON-LD block) --
	# far less noisy than scraping visible text. Falls back to a semantic
	# <address> tag if no structured data is present.
	for match in JSONLD_RE.finditer(html):
		try:
			data = json.loads(match.group(1).strip())
		except (ValueError, TypeError):
			continue
		address = _find_postal_address(data)
		if address:
			return address

	tag_match = ADDRESS_TAG_RE.search(html)
	if tag_match:
		text = re.sub(r"<[^>]+>", " ", tag_match.group(1))
		text = re.sub(r"\s+", " ", text).strip()
		if text:
			return text

	# Last resort: plenty of sites just put the address in a plain <p> with no
	# semantic markup at all -- only trust one that both looks like an address
	# (a postal code) and reads like one (a road/street/floor/etc keyword), to
	# avoid grabbing an unrelated paragraph that happens to contain a number.
	for inner in P_TAG_RE.findall(html):
		text = re.sub(r"<[^>]+>", " ", inner)
		text = re.sub(r"\s+", " ", text).strip()
		if not text or len(text) > 200:
			continue
		if POSTAL_CODE_RE.search(text) and ADDRESS_KEYWORD_RE.search(text):
			return text

	return None


def _create_address_doc(raw_text, title):
	# The scraped text is one unstructured line (from a JSON-LD PostalAddress
	# or a scraped tag/paragraph) -- Address requires address_line1/city/
	# country broken out, so this is a best-effort split, not a real parse.
	from saaskin_erp.install import COUNTRY_NAMES

	country = next((c for c in COUNTRY_NAMES if c.lower() in raw_text.lower()), None)
	if not country:
		from saaskin_erp.crm_sync import get_default_company

		country = frappe.get_cached_value("Company", get_default_company(), "country")
	if not country:
		return None

	parts = [p.strip() for p in raw_text.split(",") if p.strip()]
	city = None
	for part in parts:
		if country.lower() in part.lower():
			continue
		if NAME_LIKE_RE.fullmatch(part) and part.lower() != country.lower():
			city = part
	if not city and len(parts) >= 2:
		city = parts[-2]

	address = frappe.new_doc("Address")
	address.address_title = title
	address.address_type = "Billing"
	address.address_line1 = raw_text[:140]
	address.city = (city or title)[:140]
	address.country = country
	address.insert(ignore_permissions=True)
	return address.name


def _fetch_rendered_html(url):
	# Best-effort: sites built on Wix/Squarespace/React etc. render their real
	# content client-side -- a plain HTTP fetch only ever sees the empty page
	# shell. Falls back to a plain request (the caller) if Playwright or its
	# browser isn't installed, so this never blocks enrichment from working.
	try:
		from playwright.sync_api import sync_playwright
	except ImportError:
		return None

	try:
		with sync_playwright() as p:
			browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
			try:
				page = browser.new_page(user_agent=USER_AGENT)
				page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS, wait_until="domcontentloaded")
				page.wait_for_timeout(2000)
				return page.content()
			finally:
				browser.close()
	except Exception:
		return None


def _fetch_html(url):
	rendered_html = _fetch_rendered_html(url)
	if rendered_html is not None:
		return rendered_html

	response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
	response.raise_for_status()
	return response.text


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
		html = _fetch_html(url)
	except requests.RequestException as e:
		return {
			"filled_fields": [],
			"notes": [frappe._("Could not reach {0}: {1}").format(website, str(e))],
			"values": {},
		}

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

	if "address" in valid_fields and not doc.get("address"):
		raw_address = _extract_address(html)
		if raw_address:
			title = doc.get(organization_field) or doc.name
			address_name = _create_address_doc(raw_address, title)
			if address_name:
				values["address"] = address_name

	if not values:
		return {
			"filled_fields": [],
			"notes": [frappe._("Nothing new found on {0}.").format(website)],
			"values": {},
		}

	for fieldname, value in values.items():
		doc.db_set(fieldname, value, update_modified=False)

	return {"filled_fields": list(values.keys()), "notes": [], "values": values}
