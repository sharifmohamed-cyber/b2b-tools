import os
import json
import re
from datetime import datetime
from google import genai
from google.genai import types

# =====================================================================
# CONFIGURATION (Set via GitHub Secrets or Edit Default Links Below)
# =====================================================================
CHECKOUT_URL = os.environ.get(
    "CHECKOUT_URL", 
    "https://your-store.gumroad.com/l/b2b-excel-automation-bundle"
)
SITE_BASE_URL = os.environ.get(
    "SITE_BASE_URL", 
    "https://your-username.github.io/b2b-tools"
)
REGISTRY_FILE = "tools_registry.json"
DOCS_DIR = "docs"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_registry(registry):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

def discover_and_build_tool(client, existing_slugs):
    prompt = f"""
    You are an autonomous B2B Micro-SaaS product architect.
    Existing tool slugs already built (DO NOT REPEAT THESE): {existing_slugs}

    Step 1: Select ONE high-demand, specific B2B calculator, generator, or operational converter needed by SMEs, HR managers, accountants, or operations teams (e.g., End of Service Gratuity Calculator, Overtime & GOSI Payroll Estimator, Leave Balance & Accrual Calculator, Fleet Lease vs Buy ROI Calculator, Project Warranty Certificate Generator, VAT & Invoice Margin Calculator, CSV Attendance to Payroll Converter).

    Step 2: Output a strictly valid JSON object with the following keys:
    - "slug": URL-safe lowercase hyphenated string (e.g., "eosb-gratuity-calculator")
    - "title_en": English title of the web tool
    - "title_ar": Arabic title of the web tool
    - "description_en": 150-character SEO meta description in English
    - "html_code": A COMPLETE, self-contained, single-file `<!DOCTYPE html>` web application using Tailwind CSS CDN (`https://cdn.tailwindcss.com`).
      Requirements for `html_code`:
      1. Bilingual toggle or side-by-side Arabic/English labels (clean RTL/LTR support, Cairo/Inter Google Fonts).
      2. 100% working vanilla JavaScript calculation engine with instant live results, printable/exportable CSV or PDF summary button.
      3. A high-converting sticky banner and results-card CTA button linking to `{CHECKOUT_URL}` offering the "Complete Offline Automated Excel & VBA Master Template ($29)".
      4. A comprehensive 800-word SEO guide, formula breakdown, and FAQ section below the calculator so Google ranks the page.
    """

    response = client.models.generate_content(
    model="gemini-3.8-flash",   # was "gemini-2.5-flash"

        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    return json.loads(response.text)

def rebuild_portal_and_sitemap(registry):
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    # Build Directory Cards
    cards_html = ""
    for item in reversed(registry):
        cards_html += f"""
        <a href="tools/{item['slug']}.html" class="block p-6 bg-white rounded-xl shadow-sm border border-slate-200 hover:shadow-md hover:border-blue-600 transition">
            <div class="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-1">{item['date']}</div>
            <h2 class="text-lg font-bold text-slate-900 mb-1">{item['title_en']}</h2>
            <h3 class="text-md font-semibold text-emerald-700 mb-2" dir="rtl">{item['title_ar']}</h3>
            <p class="text-sm text-slate-600">{item['description_en']}</p>
        </a>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Compass | Free B2B Calculators & Excel Automation Tools</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">
    <header class="bg-slate-900 text-white py-12 px-6 text-center">
        <h1 class="text-3xl md:text-4xl font-extrabold mb-3">Business & HR Automation Hub | بوصلة الأعمال</h1>
        <p class="text-slate-300 max-w-2xl mx-auto mb-6">Free interactive B2B calculators, HR compliance estimators, and financial utilities. Updated automatically every day.</p>
        <a href="{CHECKOUT_URL}" class="inline-block bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition">
            Get the Full Offline Excel & VBA Master Suite ($29) &rarr;
        </a>
    </header>
    <main class="max-w-6xl mx-auto py-10 px-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cards_html}
        </div>
    </main>
</body>
</html>"""

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # Build SEO Sitemap
    urls = [f"<url><loc>{SITE_BASE_URL}/</loc></url>"]
    for item in registry:
        urls.append(f"<url><loc>{SITE_BASE_URL}/tools/{item['slug']}.html</loc></url>")
    
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {"".join(urls)}
</urlset>"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=api_key)
    registry = load_registry()
    existing_slugs = [item["slug"] for item in registry]

    print(f"Existing tools count: {len(existing_slugs)}. Generating new B2B tool...")
    new_tool = discover_and_build_tool(client, existing_slugs)

    slug = re.sub(r"[^a-z0-9-]", "", new_tool["slug"].lower())
    tools_folder = os.path.join(DOCS_DIR, "tools")
    os.makedirs(tools_folder, exist_ok=True)

    tool_path = os.path.join(tools_folder, f"{slug}.html")
    with open(tool_path, "w", encoding="utf-8") as f:
        f.write(new_tool["html_code"])

    registry.append({
        "slug": slug,
        "title_en": new_tool["title_en"],
        "title_ar": new_tool["title_ar"],
        "description_en": new_tool["description_en"],
        "date": datetime.utcnow().strftime("%Y-%m-%d")
    })

    save_registry(registry)
    rebuild_portal_and_sitemap(registry)
    print(f"Successfully deployed: {slug}.html")

if __name__ == "__main__":
    main()
