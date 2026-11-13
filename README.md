# Measles Watch USA

*U.S. Measles Surveillance & Vaccination Vulnerability Dashboard*

[Live Dashboard](https://measles-watch-usa.streamlit.app)

An interactive dashboard examining whether state-level gaps in kindergarten MMR coverage and rising vaccine exemptions track with measles incidence across the U.S., 2024 to 2026.

![Dashboard screenshot](screenshot.png)

## Research question
Across U.S. states, is lower kindergarten MMR vaccination coverage linked to higher measles incidence?

**Hypothesis:** States with MMR coverage below 95% and higher exemption rates have higher measles rates per 100,000 people.

**Design:** Ecological study of 50 states + DC, January 2024 to the latest reported week of 2026, with each case year matched to the kindergarten school year that ends in it (2024 → 2023-24, 2025 → 2024-25, 2026 → 2025-26).

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
| State population | [U.S. Census Bureau, Vintage 2025 estimates (NST-EST2025-ALLDATA)](https://www.census.gov/data/datasets/time-series/demo/popest/2020s-state-total.html) |

## Key findings (data through November 7, 2026)
- Reported measles cases rose from 266 in 2024 to 2,026 in 2025 and 5,073 in 2026 (through MMWR week 44).
- 39 of 49 reporting states had kindergarten MMR coverage below 95% in 2025-26.
- Lower MMR coverage went with higher measles rates in 2025 (Spearman ρ = −0.53, p < 0.001), but not clearly in 2024 (ρ = −0.07) or 2026 (ρ = −0.18). Higher exemption rates showed the same pattern (2025: ρ = 0.43, p = 0.002).
- Both 2025 results stayed significant after Bonferroni correction for six tests.
- Pennsylvania, South Carolina and Utah accounted for 53% of 2026 cases.
- These are state-level (ecological) associations and do not show individual-level risk.

## Methods in brief
Weekly cases are the change in the NNDSS cumulative count; rates are cases per 100,000 July 1 residents (2026 uses the 2025 estimate). The relationship between coverage (or exemptions) and incidence is tested with Spearman rank correlation and two-sided permutation p-values (5,000 permutations), by year and pooled, and states below 95% coverage are compared with those at or above it.

## Definitions
- **MMR coverage**: % of kindergartners up to date with the MMR doses their state requires (usually 2).
- **Exemption rate**: % of kindergartners exempt from **at least one** required vaccine (not MMR-specific).
- **Below 95%**: under the Healthy People 2030 kindergarten MMR target of 95% [1].

## Run it yourself
```bash
pip install -r requirements.txt
python clean_data.py      # downloads and cleans the data
streamlit run app.py      # opens the dashboard
```
Already downloaded the CSVs? Put them in `data/raw/` and run `python clean_data.py --raw data/raw`.

## A note on counting cases
NNDSS's "Current week" column is frozen when first published, so it never picks up late reports. Adding it up gives 676 measles cases for 2025, against the NNDSS cumulative year-to-date total of 2,026. This project defines each week's cases as the increase in the cumulative count, so adding up the weeks reproduces the NNDSS cumulative total exactly.

NNDSS totals still run below CDC's confirmed counts for completed years (266 vs. 285 for 2024; 2,026 vs. 2,289 for 2025, from CDC's measles page), because the weekly tables end with the last week of the year and miss later corrections. The dashboard uses NNDSS for every year, so year-to-year comparisons are like with like.

## Project files
```
measles-watch-usa/
├── app.py                 # Streamlit dashboard (7 tabs)
├── clean_data.py          # download, clean, merge
├── requirements.txt
├── screenshot.png
├── data/
│   ├── measles_cases.csv       # state × week
│   ├── population.csv          # state × year
│   ├── mmr_coverage.csv        # state × school year
│   └── measles_state_year.csv  # merged: 51 states × 3 years = 153 rows
└── .streamlit/config.toml
```

## References
1. Seither R, Yusuf OB, Dramann D, Calhoun K, Mugerwa-Kasujja A, Knighton CL, et al. Coverage with selected vaccines and exemption rates among children in kindergarten — United States, 2023–24 school year. MMWR Morb Mortal Wkly Rep. 2024 Oct 17;73(41):925–32. doi: https://doi.org/10.15585/mmwr.mm7341a3
2. Willens V. 2026 U.S. measles cases surpass 2025 level, highest since declared eliminated in 2000 [Internet]. Baltimore (MD): International Vaccine Access Center, Johns Hopkins Bloomberg School of Public Health; 2026 Jul 22 [cited 2026 Nov 13]. Available from: https://publichealth.jhu.edu/ivac/2026-us-measles-cases-surpass-2025-level
3. Green H. New CDC data shows increase in vaccine exemptions and less vaccine coverage nationally [Internet]. Washington (DC): Center for Children and Families, Georgetown University McCourt School of Public Policy; 2026 Aug 25 [cited 2026 Nov 13]. Available from: https://ccf.georgetown.edu/2026/08/25/new-cdc-data-shows-increase-in-vaccine-exemptions-and-less-vaccine-coverage-nationally/
4. Haelle T. SchoolVaxView offers data and trends on kindergarten vaccination rates [Internet]. Association of Health Care Journalists; 2026 Sep 2 [cited 2026 Nov 13]. Available from: https://healthjournalism.org/blog/2026/09/schoolvaxview-offers-data-and-trends-on-kindergarten-vaccination-rates/
5. Centers for Disease Control and Prevention. NNDSS weekly data [Internet]. Atlanta (GA): CDC; 2026 [updated 2026 Nov 11; cited 2026 Nov 13]. Available from: https://data.cdc.gov/NNDSS/NNDSS-Weekly-Data/x9gk-5huc
6. Centers for Disease Control and Prevention. Vaccination coverage and exemptions among kindergartners [Internet]. Atlanta (GA): CDC; 2026 [updated 2026 Sep 9; cited 2026 Nov 13]. Available from: https://data.cdc.gov/Vaccinations/Vaccination-Coverage-and-Exemptions-among-Kinderga/ijqb-a7ye
7. U.S. Census Bureau. State population totals and components of change: 2020–2025 (Vintage 2025, NST-EST2025-ALLDATA) [Internet]. Washington (DC): U.S. Census Bureau; 2026 Jan [cited 2026 Nov 13]. Available from: https://www.census.gov/data/datasets/time-series/demo/popest/2020s-state-total.html
8. Centers for Disease Control and Prevention. Measles cases and outbreaks [Internet]. Atlanta (GA): CDC; 2026 [updated 2026 Nov 13; cited 2026 Nov 13]. Available from: https://www.cdc.gov/measles/data-research/index.html

## How to cite
Patil S. Measles Watch USA: U.S. measles surveillance and vaccination vulnerability dashboard [Internet]. 2026 [data through 2026 Nov 07]. Available from: https://measles-watch-usa.streamlit.app

## Tools
Python, pandas, Plotly, Streamlit

## Author
**Saloni Patil, MPH, BDS**  
MPH in Epidemiology & Biostatistics, Boston University School of Public Health

[LinkedIn](https://www.linkedin.com/in/salonipatil11/) · [Portfolio](https://salonipatil.com/) · [Research](https://salonipatil.com/research)
