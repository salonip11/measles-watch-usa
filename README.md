# Measles Watch USA

*U.S. Measles Surveillance & Vaccination Vulnerability Dashboard*

[Live Dashboard](https://measles-watch-usa.streamlit.app) <!-- replace with your real link -->

An interactive dashboard examining whether state-level gaps in kindergarten MMR coverage and rising vaccine exemptions track with measles incidence across the U.S., 2024 to 2026.

![Dashboard screenshot](screenshot.png) <!-- add a screenshot named screenshot.png -->

## Research question
Across U.S. states, is lower kindergarten MMR vaccination coverage linked to higher measles incidence?

**Hypothesis:** States with MMR coverage below 95% and higher exemption rates have higher measles rates per 100,000 people.

**Design:** Ecological study of 50 states + DC, January 2024 to the latest reported week of 2026, with each case year matched to the preceding kindergarten school year (2024 → 2023-24, 2025 → 2024-25, 2026 → 2025-26).

## What's inside
- **Overview:** national totals and a U.S. map of cases or cases per 100,000
- **Trends:** weekly epidemic curve and year-over-year cumulative cases
- **Vaccination:** state MMR coverage against the 95% target, and exemption rates
- **State Explorer:** a profile for any state
- **Analysis:** MMR coverage (or exemptions) vs. measles incidence, Spearman correlation, below-vs-above-95% comparison
- **Methods:** data sources, definitions, and limitations
- **Findings:** a structured abstract (numbers update with the data), key-finding cards, and related news articles

## Data sources
| Data | Source |
|---|---|
| Weekly measles cases | [CDC National Notifiable Diseases Surveillance System (NNDSS)](https://data.cdc.gov/d/x9gk-5huc), provisional |
| MMR coverage and exemptions | [CDC SchoolVaxView, kindergarten vaccination coverage and exemptions](https://data.cdc.gov/d/ijqb-a7ye) |
| State population | [U.S. Census Bureau, Vintage 2025 estimates (NST-EST2025-ALLDATA)](https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html) |

## Definitions
- **MMR coverage**: % of kindergartners up to date with the MMR doses their state requires (usually 2).
- **Exemption rate**: % of kindergartners exempt from **at least one** required vaccine (not MMR-specific).
- **Below 95%**: under the Healthy People 2030 kindergarten MMR target of 95% (Seither et al., 2024).

## Run it yourself
```bash
pip install -r requirements.txt
python clean_data.py      # downloads and cleans the data
streamlit run app.py      # opens the dashboard
```
Already downloaded the CSVs? Put them in `data/raw/` and run `python clean_data.py --raw data/raw`.

## A note on counting cases
NNDSS's "Current week" column is frozen when first published, so it never picks up late reports. Adding it up gives 676 measles cases for 2025, against CDC's cumulative year-to-date total of 2,026. This project defines each week's cases as the increase in the cumulative count, so adding up the weeks reproduces CDC's total exactly.

## Project files
```
measles-watch-usa/
├── app.py                 # Streamlit dashboard (6 tabs)
├── clean_data.py          # download, clean, merge
├── requirements.txt
├── data/
│   ├── measles_cases.csv       # state × week
│   ├── population.csv          # state × year
│   ├── mmr_coverage.csv        # state × school year
│   └── measles_state_year.csv  # merged: 51 states × 3 years = 153 rows
└── .streamlit/config.toml
```

## References
1. Seither, R., et al. (2024). Coverage with selected vaccines and exemption rates among children in kindergarten — United States, 2023–24 school year. *MMWR, 73*(41), 925–932. https://doi.org/10.15585/mmwr.mm7341a3
2. Willens, V. (2026, July 22). *2026 U.S. measles cases surpass 2025 level, highest since declared eliminated in 2000*. Johns Hopkins IVAC. https://publichealth.jhu.edu/ivac/2026-us-measles-cases-surpass-2025-level
3. Center for Children and Families. (2026, August 25). *New CDC data shows increase in vaccine exemptions and less vaccine coverage nationally*. Georgetown University. https://ccf.georgetown.edu/2026/08/25/new-cdc-data-shows-increase-in-vaccine-exemptions-and-less-vaccine-coverage-nationally/
4. Haelle, T. (2026, September 2). *SchoolVaxView offers data and trends on kindergarten vaccination rates*. AHCJ. https://healthjournalism.org/blog/2026/09/schoolvaxview-offers-data-and-trends-on-kindergarten-vaccination-rates
5. CDC. (2026). *NNDSS weekly data* [Data set]. https://data.cdc.gov/d/x9gk-5huc
6. CDC. (2026). *Vaccination coverage and exemptions among kindergartners* [Data set]. https://data.cdc.gov/d/ijqb-a7ye
7. U.S. Census Bureau. (2026). *State population totals and components of change: 2020–2025* (NST-EST2025-ALLDATA) [Data set]. https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html
8. CDC. (2026, October 16). *Measles cases and outbreaks*. https://www.cdc.gov/measles/data-research/index.html

## Tools
Python, pandas, Plotly, Streamlit

## Author
**Saloni Patil, MPH, BDS**  
MPH in Epidemiology & Biostatistics, Boston University School of Public Health

[LinkedIn](https://www.linkedin.com/in/salonipatil11/) · [Portfolio](https://salonipatil.com/) · [Research](https://salonipatil.com/research)
