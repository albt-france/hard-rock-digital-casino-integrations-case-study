# Sources

All public sources were read or downloaded on **2026-11-15**, once, at low frequency (a few seconds between files),
with the sites' `robots.txt` respected. No account was created on any gaming site and no operator site was scraped.

## Company facts (Hard Rock Digital)
| Source | URL | Used for |
|---|---|---|
| Hard Rock Digital home page | https://www.hardrockdigital.com/ | Products (sportsbook, online casino, social games), Seminole Tribe / Hard Rock International relationship, locations, culture |
| Job posting "Product Analyst - Casino Integrations" (posted 2026-11-08) | https://himalayas.app/companies/hard-rock-digital/jobs/product-analyst-casino-integrations | The scope of the role. The page blocks automated requests; its content was read from the posting text |

Only published facts are used. Nothing is said about Hard Rock Digital's providers, contracts, licences or results
beyond what the regulator reports name.

## Regulator data (PUBLIC DATA)
| Source | URL | Derived table |
|---|---|---|
| New Jersey DGE, Monthly Internet Gaming Gross Revenue Reports (form DGE-105), Oct 2024 - Sep 2026 | https://www.njoag.gov/about/divisions-and-offices/division-of-gaming-enforcement-home/financial-and-statistical-information/monthly-internet-gross-revenue-reports/ | `public/nj_internet_gaming_by_licensee.csv` (casino win = "other authorized games", poker = peer-to-peer), `public/nj_hard_rock_skin.csv` ("Hard Rock Bet" skin on the Hard Rock Atlantic City skin-detail page) |
| New Jersey DGE, Internet Gaming Sites | https://www.njoag.gov/about/divisions-and-offices/division-of-gaming-enforcement-home/internet-gaming-sites/ | Sites authorised for Hard Rock Hotel & Casino (hardrock.bet, nj.bet365.com) |
| New Jersey DGE, Slot Laboratory - Technical Services Bureau; Internet Gaming Information (N.J.A.C. 13:69O) | njoag.gov (DGE pages) | Approval process quoted in the compliance checklist |
| Pennsylvania Gaming Control Board, Monthly Interactive Gaming Report, FY 2025-26 and FY 2026-27 | https://gamingcontrolboard.pa.gov/news-and-transparency/revenue | `public/pa_interactive_gaming_by_operator.csv` (slots wagers / won / GGR, tables wagers / GGR, poker revenue by operator, Jul 2025 - Sep 2026) |

Michigan (MGCB) was not used: optional in the plan, and its site blocks scripted downloads.

## Certification standards (reference only)
| Document | Source |
|---|---|
| GLI-19 Standards for Interactive Gaming Systems, v4.0 | https://gaminglabs.com/gli-standards/ |
| GLI-11 Gaming Devices, v3.0; GLI Composite Submission Requirements, v2.0; GLI Change Management Program Guide, v1.0 | same page |

## Reuse
- The raw files (`data/raw/`) are **not committed**: the NJ forms carry signatories' names and the GLI documents are
  GLI's copyright. `python src/download_data.py` downloads them again from the official URLs.
- The derived tables in `data/public/` contain only aggregated public revenue figures and published facts, with their
  source and date.
