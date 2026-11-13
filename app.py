"""Measles Watch USA: U.S. measles surveillance & vaccination vulnerability dashboard.

Run:  streamlit run app.py      (after: python clean_data.py)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
TARGET = 95.0


def neg(x: float, d: int = 2) -> str:
    """Number with a true minus sign, as journals print it."""
    return f"{x:.{d}f}".replace("-", "\u2212")


def r1(x: float) -> str:
    """One decimal place, rounding halves up (4.85 -> 4.9)."""
    return f"{np.floor(x * 10 + 0.5 + 1e-9) / 10:.1f}"

# CDC's confirmed counts for completed years (reference 8, CDC measles page), used only to show how far the
# provisional NNDSS totals fall short for completed years.
CDC_FINAL = {2024: 285, 2025: 2289}

# Colors (validated categorical order; status colors reserved for target flags)
YEAR_COLORS = {2024: "#2a78d6", 2025: "#eb6834", 2026: "#1baf7a"}
BELOW, AT = "#d03b3b", "#0ca30c"
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]  # vaccination
REDS = ["#fbe4e2", "#f5bcb6", "#ec9087", "#de6157", "#c62e3a", "#991f2a", "#66141c"]   # disease

# Theme: "public health bulletin". Measles red = disease, blue = protection.
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"], .stMarkdown, .stText { font-family: 'Inter', sans-serif; }
h1, h2, h3, .hero h1, .card h4, .abstract h3 { font-family: 'Fraunces', Georgia, serif !important; letter-spacing: -0.01em; }
.block-container { padding-top: 1.6rem; max-width: 1280px; }

/* hero banner */
.hero { background: linear-gradient(120deg, #1E2633 0%, #3a1f2b 55%, #C62E3A 120%);
        color: #fff; border-radius: 18px; padding: 30px 34px 26px; margin-bottom: 14px;
        position: relative; overflow: hidden; }
.hero:after { content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px;
        border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,.14) 0 2px, transparent 3px) 0 0/18px 18px; }
.hero .kicker { text-transform: uppercase; letter-spacing: .16em; font-size: .74rem; opacity: .8; font-weight: 600; }
.hero h1 { color: #fff; font-size: 2.6rem; margin: .2rem 0 .3rem; font-weight: 800; line-height: 1.08; }
.hero p { color: rgba(255,255,255,.88); font-size: 1.05rem; max-width: 820px; margin: 0; }
.hero .pill { display: inline-block; margin-top: 14px; margin-right: 8px; padding: 4px 12px; border-radius: 999px;
        background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.25); font-size: .82rem; }
.hero .pill b { color: #ffd2cc; }

/* metric cards */
[data-testid="stMetric"] { background: #fff; border: 1px solid #ebe3d7; border-left: 4px solid #C62E3A;
        border-radius: 12px; padding: 14px 16px 10px; box-shadow: 0 1px 2px rgba(30,38,51,.04); }
[data-testid="stMetricLabel"] p { font-weight: 600; color: #5b6170; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #e6ddcf; }
.stTabs [data-baseweb="tab"] { font-weight: 600; padding: 8px 14px; border-radius: 10px 10px 0 0; }
.stTabs [aria-selected="true"] { background: #fff; }

/* content cards */
.card { background: #fff; border: 1px solid #ebe3d7; border-radius: 14px; padding: 18px 20px; height: 100%;
        box-shadow: 0 1px 2px rgba(30,38,51,.04); }
.card h4 { margin: .1rem 0 .4rem; font-size: 1.15rem; color: #1E2633; }
.card p, .card li { color: #3b4150; font-size: .95rem; line-height: 1.5; }
.card .tag { font-size: .72rem; text-transform: uppercase; letter-spacing: .12em; font-weight: 700; color: #C62E3A; }
.card .big { font-family: 'Fraunces', Georgia, serif; font-size: 2.3rem; font-weight: 800; color: #C62E3A; line-height: 1; margin: .3rem 0 .4rem; }
.card.blue { border-top: 4px solid #256abf; } .card.blue .tag, .card.blue .big { color: #256abf; }
.card.red { border-top: 4px solid #C62E3A; }
.aim { background: #fff; border: 1px solid #ebe3d7; border-radius: 14px; padding: 18px 22px; margin: 6px 0 16px; }
.aim ol { margin: .3rem 0 0 1.1rem; padding: 0; } .aim li { margin: .2rem 0; color: #3b4150; }
.aim .tag { font-size: .72rem; text-transform: uppercase; letter-spacing: .12em; font-weight: 700; color: #C62E3A; }

/* abstract */
.abstract { background: #fff; border: 1px solid #ebe3d7; border-radius: 14px; padding: 26px 30px; }
.abstract h3 { margin-top: 0; font-size: 1.6rem; }
.abstract .meta { color: #7a7f8c; font-size: .85rem; margin-bottom: 14px; }
.abstract p { margin: .5rem 0; line-height: 1.6; color: #2b3140; }
.abstract b.h { color: #C62E3A; text-transform: uppercase; font-size: .78rem; letter-spacing: .12em; margin-right: 6px; }
.abstract .kw { margin-top: 14px; font-size: .85rem; color: #5b6170; }

/* news articles */
a.article { display: block; text-decoration: none !important; background: #fff; border: 1px solid #ebe3d7;
        border-radius: 14px; padding: 16px 18px; height: 100%; transition: transform .15s, box-shadow .15s; }
a.article:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(30,38,51,.10); }
a.article .src { font-size: .72rem; text-transform: uppercase; letter-spacing: .12em; font-weight: 700; color: #C62E3A; }
a.article span { display: block; }
a.article .h5 { font-family: 'Fraunces', Georgia, serif; color: #1E2633; font-size: 1.05rem; font-weight: 600; margin: .35rem 0; line-height: 1.3; }
a.article .p { color: #4a5060; font-size: .88rem; margin: 0; line-height: 1.45; }
a.article .date { color: #C62E3A; font-size: .8rem; font-weight: 600; margin-top: 10px; }
sup a.cite { color: #C62E3A; text-decoration: none; font-weight: 600; font-size: .78em; }
.refs { background: #fff; border: 1px solid #ebe3d7; border-radius: 14px; padding: 20px 26px; margin-top: 18px; }
.refs h3 { margin-top: 0; font-size: 1.3rem; }
.refs ol { padding-left: 1.3rem; margin: 0; } .refs li { margin: .45rem 0; font-size: .88rem; color: #2b3140;
        line-height: 1.5; padding-left: 1.4rem; text-indent: -1.4rem; list-style-position: inside; }
.refs li a { color: #256abf; word-break: break-all; }
.author { background: #1E2633; color: #fff; border-radius: 14px; padding: 20px 24px; margin-top: 18px; }
.author .tag { font-size: .72rem; text-transform: uppercase; letter-spacing: .14em; font-weight: 700; color: #ffb3ab; }
.author .name { font-family: 'Fraunces', Georgia, serif; font-size: 1.45rem; font-weight: 700; margin: .25rem 0 .1rem; }
.author .detail { color: rgba(255,255,255,.82); font-size: .95rem; }
.author .links { margin-top: 10px; font-size: .95rem; }
.author .links a { color: #fff; font-weight: 600; text-decoration: underline; text-underline-offset: 3px; }
.author .links a:hover { color: #ffb3ab; }
.author.compact { padding: 14px 16px; margin-top: 6px; }
.author.compact .name { font-size: 1.1rem; } .author.compact .detail, .author.compact .links { font-size: .82rem; }
.howcite { margin-top: 14px; font-size: .86rem; color: #3b4150; background: #F2ECE3; border-radius: 10px; padding: 10px 14px; }
</style>
"""

ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND",
    "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

# ---------------------------------------------------------------- references (Vancouver)
# Numbered in order of first citation in the abstract. cite(1, 2) -> superscript [1,2].
REFS = [
    ("Seither R, Yusuf OB, Dramann D, Calhoun K, Mugerwa-Kasujja A, Knighton CL, et al. Coverage with "
     "selected vaccines and exemption rates among children in kindergarten — United States, 2023–24 school "
     "year. MMWR Morb Mortal Wkly Rep. 2024 Oct 17;73(41):925–32. doi:",
     "https://doi.org/10.15585/mmwr.mm7341a3"),
    ("Willens V. 2026 U.S. measles cases surpass 2025 level, highest since declared eliminated in 2000 "
     "[Internet]. Baltimore (MD): International Vaccine Access Center, Johns Hopkins Bloomberg School of "
     "Public Health; 2026 Jul 22 [cited 2026 Nov 13]. Available from:",
     "https://publichealth.jhu.edu/ivac/2026-us-measles-cases-surpass-2025-level"),
    ("Green H. New CDC data shows increase in vaccine exemptions and less vaccine coverage nationally "
     "[Internet]. Washington (DC): Center for Children and Families, Georgetown University McCourt School "
     "of Public Policy; 2026 Aug 25 [cited 2026 Nov 13]. Available from:",
     "https://ccf.georgetown.edu/2026/08/25/new-cdc-data-shows-increase-in-vaccine-exemptions-and-less-vaccine-coverage-nationally/"),
    ("Haelle T. SchoolVaxView offers data and trends on kindergarten vaccination rates [Internet]. "
     "Association of Health Care Journalists; 2026 Sep 2 [cited 2026 Nov 13]. Available from:",
     "https://healthjournalism.org/blog/2026/09/schoolvaxview-offers-data-and-trends-on-kindergarten-vaccination-rates/"),
    ("Centers for Disease Control and Prevention. NNDSS weekly data [Internet]. Atlanta (GA): CDC; 2026 "
     "[updated 2026 Nov 11; cited 2026 Nov 13]. Available from:",
     "https://data.cdc.gov/NNDSS/NNDSS-Weekly-Data/x9gk-5huc"),
    ("Centers for Disease Control and Prevention. Vaccination coverage and exemptions among kindergartners "
     "[Internet]. Atlanta (GA): CDC; 2026 [updated 2026 Sep 9; cited 2026 Nov 13]. Available from:",
     "https://data.cdc.gov/Vaccinations/Vaccination-Coverage-and-Exemptions-among-Kinderga/ijqb-a7ye"),
    ("U.S. Census Bureau. State population totals and components of change: 2020–2025 (Vintage 2025, "
     "NST-EST2025-ALLDATA) [Internet]. Washington (DC): U.S. Census Bureau; 2026 Jan [cited 2026 Nov 13]. "
     "Available from:",
     "https://www.census.gov/data/datasets/time-series/demo/popest/2020s-state-total.html"),
    ("Centers for Disease Control and Prevention. Measles cases and outbreaks [Internet]. Atlanta (GA): "
     "CDC; 2026 [updated 2026 Nov 13; cited 2026 Nov 13]. Available from:",
     "https://www.cdc.gov/measles/data-research/index.html"),
]


AUTHOR = {
    "name": "Saloni Patil, MPH, BDS",
    "detail": "MPH in Epidemiology &amp; Biostatistics, Boston University School of Public Health",
    "links": [("LinkedIn", "https://www.linkedin.com/in/salonipatil11/"),
              ("Portfolio", "https://salonipatil.com/"),
              ("Research", "https://salonipatil.com/research")],
}


def author_html(compact: bool = False) -> str:
    links = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{t}</a>' for t, u in AUTHOR["links"])
    cls = "author compact" if compact else "author"
    return (f'<div class="{cls}"><span class="tag">Author</span>'
            f'<div class="name">{AUTHOR["name"]}</div><div class="detail">{AUTHOR["detail"]}</div>'
            f'<div class="links">{links}</div></div>')


def cite(*nums: int) -> str:
    """In-text citation as a superscript linking to the reference list."""
    links = ",".join(f'<a href="#ref-{n}" class="cite">{n}</a>' for n in nums)
    return f"<sup>[{links}]</sup>"


def references_html() -> str:
    items = "".join(f'<li id="ref-{i}">{text} <a href="{url}" target="_blank" rel="noopener">{url}</a></li>'
                    for i, (text, url) in enumerate(REFS, 1))
    return f'<div class="refs"><h3>References</h3><ol>{items}</ol></div>'


st.set_page_config(page_title="Measles Watch USA", page_icon="🦠", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- data
@st.cache_data
def load():
    files = ["measles_state_year.csv", "measles_cases.csv"]
    if not all((DATA / f).exists() for f in files):
        return None, None
    table = pd.read_csv(DATA / "measles_state_year.csv")
    weekly = pd.read_csv(DATA / "measles_cases.csv", parse_dates=["week_ending"])
    table["abbr"] = table["state"].map(ABBR)
    table["target_status"] = np.select(
        [table["mmr_coverage"].isna(), table["mmr_coverage"] < TARGET],
        ["Not reported", "Below 95%"], "At or above 95%")
    return table, weekly


table, weekly = load()
if table is None:
    st.error("Data files not found. Run `python clean_data.py` first, then reload this page.")
    st.stop()

YEARS = sorted(table["year"].unique())
LAST_WEEK = int(weekly.loc[weekly["year"] == YEARS[-1], "week"].max())
LAST_DATE = weekly.loc[(weekly["year"] == YEARS[-1]) & (weekly["week"] == LAST_WEEK),
                       "week_ending"].iloc[0]


def year_label(y: int) -> str:
    return f"{y} (YTD, wk {LAST_WEEK})" if y == YEARS[-1] else str(y)


def spearman(x: pd.Series, y: pd.Series, n_perm: int = 5000, seed: int = 0):
    """Spearman rho with a two-sided permutation p-value (no SciPy needed)."""
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    rx, ry = d["x"].rank().to_numpy(), d["y"].rank().to_numpy()
    rho = float(np.corrcoef(rx, ry)[0, 1])
    rng = np.random.default_rng(seed)
    perms = np.array([np.corrcoef(rx, rng.permutation(ry))[0, 1] for _ in range(n_perm)])
    p = (np.sum(np.abs(perms) >= abs(rho)) + 1) / (n_perm + 1)
    return rho, p, len(d)


def pooled_rate(df: pd.DataFrame) -> float:
    return df["cases"].sum() / df["population"].sum() * 100_000


def us_map(df, col, title, colors, fmt):
    fig = px.choropleth(df, locations="abbr", locationmode="USA-states", scope="usa",
                        color=col, color_continuous_scale=colors,
                        hover_name="state", custom_data=[col])
    fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>" + title + ": %{customdata[0]:" + fmt + "}<extra></extra>",
                      marker_line_color="white", marker_line_width=0.8)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=430,
                      coloraxis_colorbar=dict(title=title, thickness=12, len=0.7),
                      geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)"))
    return fig


def tidy(fig, height=380):
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=height,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
                      hoverlabel=dict(font_size=13))
    fig.update_xaxes(showgrid=False)
    return fig


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🦠 Measles Watch USA")
    st.caption("U.S. Measles Surveillance & Vaccination Vulnerability")
    year = st.radio("Case year", YEARS, index=len(YEARS) - 1, format_func=year_label)
    measure = st.radio("Show states by", ["Rate per 100,000", "Case count"])
    st.divider()
    st.caption(f"Cases: CDC NNDSS (provisional), through MMWR week {LAST_WEEK} of {YEARS[-1]} "
               f"(week ending {LAST_DATE:%b %d, %Y}).  \n"
               "Coverage: CDC SchoolVaxView, matched kindergarten school year.  \n"
               "Population: Census Vintage 2025.")
    st.markdown(author_html(compact=True), unsafe_allow_html=True)

yr = table[table["year"] == year].copy()
school_year = yr["school_year"].iloc[0]
mcol, mtitle, mfmt = (("rate_per_100k", "Cases per 100k", ".2f") if measure.startswith("Rate")
                      else ("cases", "Cases", ",d"))

latest_total = int(table.loc[table["year"] == YEARS[-1], "cases"].sum())
prev_full = int(table.loc[table["year"] == YEARS[-2], "cases"].sum()) if len(YEARS) > 1 else 0
latest_yr = table[table["year"] == YEARS[-1]]
st.markdown(f"""
<div class="hero">
  <div class="kicker">U.S. Measles Surveillance &amp; Vaccination Vulnerability</div>
  <h1>Measles Watch USA</h1>
  <p>Across U.S. states, is lower kindergarten MMR vaccination coverage linked to higher
     measles incidence, 2024 to {YEARS[-1]}?</p>
  <span class="pill"><b>{latest_total:,}</b> cases in {YEARS[-1]} so far</span>
  <span class="pill"><b>{latest_total / max(prev_full, 1):.1f}×</b> the {YEARS[-2]} NNDSS total</span>
  <span class="pill"><b>{int(latest_yr['below_95'].sum())}</b> states below 95% MMR</span>
  <span class="pill">Data through {LAST_DATE:%b %d, %Y}</span>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Trends", "Vaccination", "State Explorer", "Analysis",
                "Methods", "Findings"])

# ---------------------------------------------------------------- 1. Overview
with tabs[0]:
    st.markdown(f"""
<div class="aim">
  <span class="tag">Aim of the project</span>
  <p style="margin:.35rem 0 .2rem;font-size:1.02rem;color:#1E2633">
  U.S. measles cases are at their highest level since the disease was declared eliminated in 2000{cite(2)},
  while kindergarten MMR coverage is slipping and exemptions are rising{cite(3, 4)}. This dashboard tracks where measles is spreading and tests whether
  <b>states with lower kindergarten MMR coverage and higher exemptions carry higher measles rates</b>,
  so that public-health teams can see where the risk is greatest.</p>
  <ol>
    <li><b>Burden</b>: count cases and rates per 100,000 for every state.</li>
    <li><b>Timing</b>: show how the {YEARS[-1]} surge compares with earlier years.</li>
    <li><b>Vulnerability</b>: flag states below the 95% MMR target{cite(1)}.</li>
    <li><b>Relationship</b>: test whether coverage and incidence move together (Spearman).</li>
  </ol>
</div>
""", unsafe_allow_html=True)
    st.subheader(f"Burden: where is measles worst in {year_label(year)}?")
    # same-week comparison with the previous year
    cum = weekly.groupby(["year", "week"])["cumulative"].sum()
    wk_cmp = int(yr["through_week"].max())
    prev = cum.get((year - 1, min(wk_cmp, 52)), None) if year - 1 in YEARS else None
    total = int(yr["cases"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Measles cases", f"{total:,}",
              None if prev is None else f"{total - prev:+,} vs {year - 1} wk {min(wk_cmp, 52)}",
              delta_color="inverse")
    c2.metric("States reporting cases", f"{(yr['cases'] > 0).sum()} of 51")
    c3.metric("U.S. rate per 100,000", f"{pooled_rate(yr):.2f}")
    rep = yr.dropna(subset=["mmr_coverage"])
    c4.metric("Below 95% MMR", f"{int(rep['below_95'].sum())} of {len(rep)}",
              help=f"States reporting kindergarten MMR coverage under 95% in {school_year}. "
                   f"Not reported: {', '.join(yr.loc[yr['mmr_coverage'].isna(), 'state']) or 'none'}.")

    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(us_map(yr, mcol, mtitle, REDS, mfmt), width="stretch")
    with right:
        st.markdown(f"**Top 10 states by rate, {year}**")
        top = (yr.nlargest(10, "rate_per_100k")[["state", "cases", "rate_per_100k", "mmr_coverage"]]
                 .rename(columns={"state": "State", "cases": "Cases", "rate_per_100k": "Per 100k",
                                  "mmr_coverage": "MMR %"}))
        st.dataframe(top, hide_index=True, width="stretch",
                     column_config={"Per 100k": st.column_config.NumberColumn(format="%.2f"),
                                    "Cases": st.column_config.NumberColumn(format="%d"),
                                    "MMR %": st.column_config.NumberColumn(format="%.1f")})

    st.markdown("**All three years**")
    summ = (table.groupby("year")
                 .apply(lambda g: pd.Series({
                     "Cases": int(g["cases"].sum()),
                     "States with cases": int((g["cases"] > 0).sum()),
                     "Rate per 100k": round(pooled_rate(g), 2),
                     "Median state MMR %": g["mmr_coverage"].median(),
                     "States below 95%": int(g["below_95"].sum())}), include_groups=False)
                 .reset_index())
    summ["year"] = summ["year"].map(year_label)
    st.dataframe(summ.rename(columns={"year": "Year"}), hide_index=True, width="stretch")
    st.markdown(f'<p style="font-size:.86rem;color:#6b7080">Why it matters: Healthy People 2030 sets a '
                f'95% target for kindergarten MMR coverage{cite(1)}, about the level at which measles can no '
                f'longer find enough susceptible people to keep spreading{cite(4)}. Below it, outbreaks '
                f'can grow.</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------- 2. Trends
with tabs[1]:
    st.subheader(f"Timing: when did cases rise, and is {YEARS[-1]} worse?")
    nat = weekly.groupby(["year", "week", "week_ending"], as_index=False)[["cases", "cumulative"]].sum()
    nat["Year"] = nat["year"].astype(str)
    nat["shown"] = nat["cases"].clip(lower=0)

    fig = px.bar(nat, x="week_ending", y="shown", color="Year",
                 color_discrete_map={str(k): v for k, v in YEAR_COLORS.items()},
                 custom_data=["week", "cases"])
    fig.update_traces(hovertemplate="Week ending %{x|%b %d, %Y} (MMWR wk %{customdata[0]})"
                                    "<br>New cases: %{customdata[1]:,}<extra></extra>",
                      marker_line_width=0)
    fig.update_layout(bargap=0.15, xaxis_title=None, yaxis_title="New cases reported that week")
    st.markdown("**Epidemic curve: new U.S. cases each week**")
    st.plotly_chart(tidy(fig), width="stretch")

    fig = go.Figure()
    for y in YEARS:
        d = nat[nat["year"] == y]
        fig.add_trace(go.Scatter(x=d["week"], y=d["cumulative"], name=year_label(y), mode="lines",
                                 line=dict(color=YEAR_COLORS.get(y), width=2.5),
                                 hovertemplate=f"{y}, week %{{x}}: %{{y:,}} cases<extra></extra>"))
        fig.add_annotation(x=d["week"].iloc[-1], y=d["cumulative"].iloc[-1], text=f" {y}",
                           showarrow=False, xanchor="left", font=dict(color=YEAR_COLORS.get(y)))
    fig.update_layout(xaxis_title="MMWR week", yaxis_title="Cumulative cases", hovermode="x unified")
    st.markdown("**Running total by week, year over year**")
    st.plotly_chart(tidy(fig), width="stretch")

    # when did the latest year pass the previous full-year total?
    if len(YEARS) >= 2:
        prev_total = int(nat.loc[nat["year"] == YEARS[-2], "cases"].sum())
        latest = nat[nat["year"] == YEARS[-1]]
        passed = latest[latest["cumulative"] > prev_total]
        if len(passed):
            r = passed.iloc[0]
            st.info(f"{YEARS[-1]} passed {YEARS[-2]}'s full-year total of {prev_total:,} cases in "
                    f"MMWR week {int(r['week'])} (week ending {r['week_ending']:%b %d}).")
    st.caption("Weekly cases are the increase in the NNDSS cumulative count from one week to the next, so "
               "late reports show up in the week they were added, not the week of illness onset. "
               "A few weeks where reported cases were later removed are shown as zero.")

# ---------------------------------------------------------------- 3. Vaccination
with tabs[2]:
    st.subheader(f"Vulnerability: which states have the biggest gaps? ({school_year} school year)")
    st.caption(f"Matched to {year} cases. Change the case year in the sidebar to see another school year.")
    rep = yr.dropna(subset=["mmr_coverage"])
    prev_sy = table[table["year"] == year - 1].set_index("state")["mmr_coverage"]
    if year - 1 in YEARS:
        both = rep.set_index("state")["mmr_coverage"].to_frame("now").join(prev_sy.rename("before")).dropna()
        dropped = int((both["now"] < both["before"]).sum())
    else:
        dropped = None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("States below 95% MMR", f"{int(rep['below_95'].sum())} of {len(rep)}")
    c2.metric("Median state MMR coverage", f"{r1(rep['mmr_coverage'].median())}%")
    c3.metric("Median exemption rate", f"{r1(yr['exemption_rate'].median())}%")
    c4.metric("States where coverage fell", "n/a" if dropped is None else f"{dropped}",
              help="Compared with the previous school year, among states reporting both years.")

    left, right = st.columns(2)
    with left:
        d = yr.sort_values("mmr_coverage", na_position="first")
        fig = px.bar(d, x="mmr_coverage", y="state", orientation="h", color="target_status",
                     color_discrete_map={"Below 95%": BELOW, "At or above 95%": AT, "Not reported": "#9a9893"},
                     custom_data=["exemption_rate"])
        fig.update_traces(hovertemplate="<b>%{y}</b><br>MMR: %{x:.1f}%<br>"
                                        "Exemptions: %{customdata[0]:.1f}%<extra></extra>")
        fig.add_vline(x=TARGET, line_dash="dash", line_color="#52514e",
                      annotation_text="95% target", annotation_position="top")
        lo = np.floor(d["mmr_coverage"].min()) - 2
        fig.update_layout(xaxis=dict(range=[lo, 100], title="Kindergartners up to date with MMR (%)"),
                          yaxis=dict(title=None, tickfont=dict(size=10)), bargap=0.25)
        st.markdown("**MMR coverage by state**")
        st.plotly_chart(tidy(fig, height=900), width="stretch")
    with right:
        st.markdown("**Any-exemption rate by state** (exempt from at least one required vaccine)")
        st.plotly_chart(us_map(yr, "exemption_rate", "Exemptions %", BLUES, ".1f"),
                        width="stretch")
        st.markdown("**Highest exemption rates**")
        ex = (yr.nlargest(10, "exemption_rate")[["state", "exemption_rate", "mmr_coverage"]]
                .rename(columns={"state": "State", "exemption_rate": "Exemptions %", "mmr_coverage": "MMR %"}))
        st.dataframe(ex, hide_index=True, width="stretch")
        missing = yr.loc[yr["mmr_coverage"].isna(), "state"].tolist()
        if missing:
            st.caption("Not reported this school year: " + ", ".join(missing) + ".")

# ---------------------------------------------------------------- 4. State Explorer
with tabs[3]:
    st.subheader("Local profile")
    states = sorted(table["state"].unique())
    default = yr.loc[yr["cases"].idxmax(), "state"]
    pick = st.selectbox("Choose a state", states, index=states.index(default))
    s = table[table["state"] == pick].sort_values("year")
    row = s[s["year"] == year].iloc[0]
    rank = int(yr["rate_per_100k"].rank(ascending=False, method="min")[yr["state"] == pick].iloc[0])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"Cases, {year_label(year)}", f"{int(row['cases']):,}")
    c2.metric("Rate per 100,000", f"{row['rate_per_100k']:.2f}")
    c3.metric("Rank by rate", f"{rank} of 51")
    c4.metric(f"MMR coverage ({row['school_year']})",
              "Not reported" if pd.isna(row["mmr_coverage"]) else f"{row['mmr_coverage']:.1f}%",
              None if pd.isna(row["mmr_coverage"]) else f"{row['mmr_coverage'] - TARGET:+.1f} vs 95%",
              delta_color="normal")
    c5.metric("Exemption rate",
              "Not reported" if pd.isna(row["exemption_rate"]) else f"{row['exemption_rate']:.1f}%",
              None if pd.isna(row["exemption_rate"]) else
              f"{row['exemption_rate'] - yr['exemption_rate'].median():+.1f} vs state median",
              delta_color="inverse")

    w = weekly[weekly["state"] == pick].copy()
    w["Year"] = w["year"].astype(str)
    w["shown"] = w["cases"].clip(lower=0)
    fig = px.bar(w, x="week_ending", y="shown", color="Year",
                 color_discrete_map={str(k): v for k, v in YEAR_COLORS.items()}, custom_data=["week", "cases"])
    fig.update_traces(hovertemplate="Week ending %{x|%b %d, %Y}<br>New cases: %{customdata[1]:,}<extra></extra>")
    fig.update_layout(xaxis_title=None, yaxis_title="New cases that week", bargap=0.15)
    st.markdown(f"**Weekly measles cases, {pick}**")
    st.plotly_chart(tidy(fig, 320), width="stretch")

    show = s[["year", "school_year", "cases", "population", "rate_per_100k", "mmr_coverage", "exemption_rate"]].copy()
    show["year"] = show["year"].map(year_label)
    st.dataframe(show.rename(columns={"year": "Year", "school_year": "School year", "cases": "Cases",
                                      "population": "Population", "rate_per_100k": "Per 100k",
                                      "mmr_coverage": "MMR %", "exemption_rate": "Exemptions %"}),
                 hide_index=True, width="stretch",
                 column_config={"Population": st.column_config.NumberColumn(format="localized"),
                                "Per 100k": st.column_config.NumberColumn(format="%.2f")})

# ---------------------------------------------------------------- 5. Analysis
with tabs[4]:
    st.subheader("Relationship: do lower-coverage states have more measles?")
    a1, a2, a3 = st.columns([2, 2, 1])
    exposure = a1.radio("Exposure", ["MMR coverage", "Exemption rate"], horizontal=True)
    which = a2.radio("Years", ["All years"] + [str(y) for y in YEARS], horizontal=True)
    log_y = a3.toggle("Log scale", help="Hides states with zero cases.")
    xcol = "mmr_coverage" if exposure == "MMR coverage" else "exemption_rate"

    d = table.dropna(subset=[xcol]).copy()
    if which != "All years":
        d = d[d["year"] == int(which)]
    if log_y:
        d = d[d["rate_per_100k"] > 0]
    d["Year"] = d["year"].astype(str)

    fig = px.scatter(d, x=xcol, y="rate_per_100k", color="Year", log_y=log_y,
                     color_discrete_map={str(k): v for k, v in YEAR_COLORS.items()},
                     hover_name="state", custom_data=["cases", "year"])
    fig.update_traces(marker=dict(size=10, opacity=0.85, line=dict(width=1.5, color="white")),
                      hovertemplate="<b>%{hovertext}</b> (%{customdata[1]})<br>" + exposure +
                                    ": %{x:.1f}%<br>Rate: %{y:.2f} per 100k<br>Cases: %{customdata[0]:,}<extra></extra>")
    if xcol == "mmr_coverage":
        fig.add_vline(x=TARGET, line_dash="dash", line_color="#52514e",
                      annotation_text="95% target", annotation_position="top")
    fig.update_layout(xaxis_title=f"{exposure} (%), matched school year",
                      yaxis_title="Measles cases per 100,000")
    st.plotly_chart(tidy(fig, 460), width="stretch")

    # Spearman by year + pooled
    rows = []
    for label, g in [(year_label(y), table[table["year"] == y]) for y in YEARS] + [("All years pooled (state-years)", table)]:
        rho, p, n = spearman(g[xcol], g["rate_per_100k"])
        rows.append({"Years": label, "Spearman ρ": round(rho, 2),
                     "p-value": "<0.001" if p < 0.001 else f"{p:.3f}", "n": n})
    corr = pd.DataFrame(rows)

    left, right = st.columns(2)
    with left:
        st.markdown(f"**Spearman correlation: {exposure} vs. measles rate**")
        st.dataframe(corr, hide_index=True, width="stretch")
        st.caption("Spearman compares the ranking of states, so one very large outbreak cannot "
                   "dominate. p-values come from a 5,000-permutation test. The pooled row counts each "
                   "state three times, so its p-value is optimistic.")
        sign = "negative" if xcol == "mmr_coverage" else "positive"
        st.markdown(f"If the hypothesis holds, ρ is **{sign}**: "
                    + ("lower coverage goes with higher rates." if sign == "negative"
                       else "higher exemptions go with higher rates."))
    with right:
        g = table.dropna(subset=["mmr_coverage"]).copy()
        g["Group"] = np.where(g["below_95"] == 1, "Below 95%", "At or above 95%")
        comp = (g.groupby(["year", "Group"])
                  .apply(lambda x: pd.Series({"Median state rate": x["rate_per_100k"].median(),
                                              "Combined rate": pooled_rate(x),
                                              "States": len(x)}), include_groups=False)
                  .reset_index())
        stat = st.radio("Compare", ["Median state rate", "Combined rate"], horizontal=True,
                        help="Median: the typical state in each group. Combined: all cases in the "
                             "group ÷ all people in the group.")
        comp["Year"] = comp["year"].map(year_label)
        fig = px.bar(comp, x="Year", y=stat, color="Group", barmode="group",
                     color_discrete_map={"Below 95%": BELOW, "At or above 95%": AT},
                     custom_data=["States"])
        fig.update_traces(hovertemplate="%{x}<br>%{y:.2f} per 100k<br>%{customdata[0]} states<extra></extra>")
        fig.update_layout(xaxis=dict(title=None, type="category"), yaxis_title="Cases per 100,000",
                          bargap=0.3, bargroupgap=0.08)
        st.markdown("**States below vs. at or above 95% MMR coverage**")
        st.plotly_chart(tidy(fig, 340), width="stretch")

    st.warning("**How to read this.** This is an ecological comparison of states, not people. "
               "Say: *“In years with a clear link, states with lower kindergarten MMR coverage had "
               "higher measles rates.”* Don't say: *“unvaccinated people got measles”*. State averages hide "
               "under-vaccinated communities, and one large outbreak can dominate a state's rate.")

# ---------------------------------------------------------------- 6. Methods
with tabs[5]:
    st.subheader("Methods")
    fr = weekly.groupby("year")[["cases", "cases_first_reported"]].sum()
    demo_y = YEARS[-2] if len(YEARS) > 1 else YEARS[-1]
    final_gap = "; ".join(f"{int(fr.loc[y, 'cases']):,} vs. {c:,} for {y}"
                          for y, c in CDC_FINAL.items() if y in fr.index) or "see CDC's measles page"
    match_rows = "\n".join(
        f"| {y} | {sy} | {py} |" for y, sy, py in
        table[["year", "school_year", "pop_year"]].drop_duplicates().sort_values("year").itertuples(index=False))
    st.markdown(f"""
**Design.** Ecological study of the 50 states and the District of Columbia, January {YEARS[0]} through
MMWR week {LAST_WEEK} of {YEARS[-1]} (week ending {LAST_DATE:%B %d, %Y}). MMWR weeks are CDC's
standard Sunday-to-Saturday reporting weeks. {YEARS[-1]} is year to date.

**Data sources**

| Data | Source | Used |
|---|---|---|
| Weekly measles cases | CDC NNDSS Weekly Data, provisional{cite(5)} | {YEARS[0]}–{YEARS[-1]} |
| MMR coverage and exemptions | CDC SchoolVaxView, Vaccination Coverage and Exemptions among Kindergartners{cite(6)} | {table["school_year"].min()} to {table["school_year"].max()} |
| Population | U.S. Census Bureau, Vintage 2025 (NST-EST2025-ALLDATA){cite(7)} | {table["pop_year"].min()}–{table["pop_year"].max()} |

**Definitions**
- **Cases**: measles, indigenous plus imported. New York City is reported separately in NNDSS and is
  added to New York State.
- **Annual cases**: the NNDSS cumulative year-to-date count at the last reported week. Each week's cases are
  the increase in that count since the previous week, so the weekly values add up to the NNDSS total exactly.
  The "current week" column is not used for totals because it keeps each week's count as first
  published and never picks up late reports. For {demo_y} it adds up to {int(fr.loc[demo_y, "cases_first_reported"]):,}
  cases, against the NNDSS cumulative total of {int(fr.loc[demo_y, "cases"]):,}.
- **Rate per 100,000** = annual cases ÷ July 1 resident population × 100,000.
- **MMR coverage**: percentage of kindergartners up to date with the MMR doses their state requires for
  school entry. That is two doses in most states, but a few states differ{cite(1)}.
- **Exemption rate**: percentage of kindergartners with an exemption (medical or nonmedical) from
  **at least one** required vaccine. It is not specific to MMR{cite(1)}.
- **Below 95%**: MMR coverage under the Healthy People 2030 target of 95%{cite(1)}.
- SchoolVaxView also lists "NY-City of New York" and "TX-City of Houston" separately. The statewide
  "New York" and "Texas" rows already include them, so the statewide rows are used.

**Matching school years to case years.** Each school year runs from late summer to early summer, so most
of it falls in the second calendar year. Each case year is therefore matched to the school year that ends in
it (for example, 2024-25 coverage is matched to 2025 cases). {YEARS[-1]} uses the latest Census estimate.

| Case year | School year | Population year |
|---|---|---|
{match_rows}

**Joins.** Cases are joined to population on state and population year (many-to-one), and then to
coverage on state and school year (one-to-one). The cleaning script stops with an error if any key is
duplicated, and it checks that the 51-state totals equal CDC's national "U.S. residents" total each year.
The result is 51 states × {len(YEARS)} years = {len(table)} rows.

**Statistics.** Spearman rank correlation between state coverage (or exemptions) and rate, by year and
pooled, with two-sided permutation p-values (5,000 permutations). Because six year-specific tests were run
(three years, two exposures), results are also checked against a Bonferroni-adjusted threshold of
p < 0.0083. States below 95% are compared with
states at or above 95% using the median state rate and the combined rate (all cases ÷ all population).

**Limitations**
- *Ecological design.* A state can have 96% coverage overall and still have one under-vaccinated
  community where an outbreak takes off. State averages hide those pockets.
- *Association, not cause.* Travel, outbreak timing and local factors also affect where measles appears.
- *Outbreaks are clumpy.* One large outbreak can dominate a whole state's rate.
- *Provisional counts.* NNDSS figures are revised over time and can differ from CDC's measles page,
  which is compiled separately. For example, CDC's page reported 5,412 confirmed 2026 cases as of
  November 12, 2026, including 18 among international visitors{cite(8)}. NNDSS totals also run below
  CDC's confirmed counts for completed years ({final_gap}){cite(8)}, because the weekly tables end with the
  last week of the year and miss later corrections. All year-to-year comparisons here use NNDSS for every
  year, so they compare like with like.
- *Six states report all-vaccine completion.* Florida, Georgia, Iowa, Mississippi, New Hampshire and New
  Jersey did not assess coverage for individual vaccines; their figure is the share of kindergartners with
  all required vaccines, which can understate MMR coverage{cite(6, 8)}.
- *Exemption measure.* The exemption rate covers any required vaccine, not MMR alone.
- *One age group.* Kindergarten coverage does not describe older children or adults.
- *Uneven reporting.* States collect school vaccination data differently, and some skip years.
- *Location.* Cases are counted in the reporting state, which may not be where infection happened.
- *{YEARS[-1]} population.* {YEARS[-1]} rates use the {int(table["pop_year"].max())} population estimate.
""", unsafe_allow_html=True)
    missing = table[table["mmr_coverage"].isna()][["state", "school_year"]]
    if len(missing):
        st.caption("MMR coverage not reported: " +
                   "; ".join(f"{a} ({b})" for a, b in missing.values) + ".")
    st.markdown(references_html(), unsafe_allow_html=True)
    st.download_button("Download the merged state-year table (CSV)",
                       table.drop(columns=["abbr", "target_status"]).to_csv(index=False),
                       "measles_state_year.csv", "text/csv")
    st.caption("Built with Python, pandas, Plotly and Streamlit.")

# ---------------------------------------------------------------- 7. Findings
def strength(r: float) -> str:
    a = abs(r)
    return "weak" if a < 0.2 else "modest" if a < 0.4 else "moderate" if a < 0.6 else "strong"


with tabs[6]:
    tot = table.groupby("year")["cases"].sum()
    with_cases = table.groupby("year")["cases"].apply(lambda c: int((c > 0).sum()))
    first, last = YEARS[0], YEARS[-1]
    growth = tot[last] / max(tot[first], 1)

    stats = {}
    for y in YEARS:
        g = table[table["year"] == y]
        rho, p, n = spearman(g["mmr_coverage"], g["rate_per_100k"])
        rho_e, p_e, _ = spearman(g["exemption_rate"], g["rate_per_100k"])
        rep_y = g.dropna(subset=["mmr_coverage"])
        lo, hi = rep_y[rep_y["below_95"] == 1], rep_y[rep_y["below_95"] == 0]
        stats[y] = dict(rho=rho, p=p, n=n, rho_e=rho_e, p_e=p_e,
                        r_lo=pooled_rate(lo), r_hi=pooled_rate(hi),
                        m_lo=lo["rate_per_100k"].median(), m_hi=hi["rate_per_100k"].median(),
                        ratio=pooled_rate(lo) / pooled_rate(hi) if pooled_rate(hi) > 0 else np.nan,
                        n_lo=len(lo), n_rep=len(rep_y))
    best = min(YEARS, key=lambda y: stats[y]["rho"])
    pooled_rho, pooled_p, pooled_n = spearman(table["mmr_coverage"], table["rate_per_100k"])
    ly = table[table["year"] == last].sort_values("cases", ascending=False)
    top3, top3_share = ly["state"].head(3).tolist(), ly["cases"].head(3).sum() / max(ly["cases"].sum(), 1)
    sy = table.groupby("school_year")[["mmr_coverage", "exemption_rate"]].median()
    sy0, sy1 = sy.index[0], sy.index[-1]
    f1 = lambda x: f"{np.floor(x * 10 + 0.5 + 1e-9) / 10:.1f}"
    fmt_p = lambda p: "p &lt; 0.001" if p < 0.001 else f"p = {p:.3f}"
    s_last = stats[last]
    # week in which the latest year passed the previous year's full-year total
    natc = weekly.groupby(["year", "week"])["cumulative"].sum()
    passed = natc.loc[last][natc.loc[last] > tot[YEARS[-2]]] if len(YEARS) > 1 else natc.loc[last].iloc[:0]
    passed_txt = (f"{last} passed {YEARS[-2]}'s full-year total in MMWR week {int(passed.index[0])}."
                  if len(passed) else f"{last} has not yet passed {YEARS[-2]}'s total.")

    # which single years show a clear negative link (p < 0.05); the conclusion is written from this,
    # so it stays true when the data are refreshed
    def join_years(ys, word="and"):
        ys = [str(y) for y in ys]
        return ys[0] if len(ys) == 1 else ", ".join(ys[:-1]) + f" {word} " + ys[-1]
    sig = [y for y in YEARS if stats[y]["p"] < 0.05 and stats[y]["rho"] < 0]
    not_sig = [y for y in YEARS if y not in sig]
    by_year = "; ".join(f"{y}: ρ = {neg(stats[y]['rho'])}, {fmt_p(stats[y]['p'])}" for y in YEARS)
    if len(sig) == len(YEARS):
        concl = "States with lower kindergarten MMR coverage had higher measles rates in every year studied."
    elif sig:
        concl = (f"States with lower kindergarten MMR coverage had clearly higher measles rates in "
                 f"{join_years(sig)}, but not in {join_years(not_sig, "or")}. The link varied from year to year; one "
                 f"likely reason is that a few large, localized outbreaks can dominate state rates.")
    else:
        concl = ("No single year showed a clear link between state MMR coverage and measles rates; a few "
                 "large, localized outbreaks may dominate state rates.")
    sb = stats[best]
    n_tests = 2 * len(YEARS)                      # MMR and exemptions, each year
    thr = 0.05 / n_tests
    by_year_e = "; ".join(f"{y}: ρ = {neg(stats[y]['rho_e'])}, {fmt_p(stats[y]['p_e'])}" for y in YEARS)
    sig_e = [y for y in YEARS if stats[y]["p_e"] < 0.05 and stats[y]["rho_e"] > 0]
    exempt_txt = (f"Higher exemption rates went with higher measles rates in {join_years(sig_e)} ({by_year_e})."
                  if sig_e else f"Exemption rates showed no clear link with measles rates in any year ({by_year_e}).")
    n_sig = len(sig) + len(sig_e)
    n_keep = sum(stats[y]["p"] < thr for y in sig) + sum(stats[y]["p_e"] < thr for y in sig_e)
    bonf_txt = ("" if n_sig == 0 else
                f"After Bonferroni correction for {n_tests} year-specific tests (p &lt; {thr:.4f}), "
                f"{n_keep} of {n_sig} significant results remained significant.")

    st.markdown(f"""
<div class="abstract">
  <h3>Lower kindergarten MMR coverage and measles incidence across U.S. states, {first}–{last}</h3>
  <div class="meta">Structured abstract · Ecological study · Data through MMWR week {LAST_WEEK},
  {last} (week ending {LAST_DATE:%B %d, %Y}) · Figures recalculate each time the data files are refreshed
  with clean_data.py</div>
  <p><b class="h">Background</b>Kindergarten MMR coverage of at least 95% is the Healthy People 2030 target{cite(1)}
  and roughly the level needed to stop measles spreading{cite(4)}. U.S. measles cases in 2026 reached their
  highest level since elimination was declared in 2000{cite(2)}, while kindergarten MMR coverage has fallen
  and exemptions have risen{cite(3, 4)}.</p>
  <p><b class="h">Objective</b>To test whether U.S. states with lower kindergarten MMR coverage, or
  higher vaccine exemption rates, had higher measles incidence from {first} to {last}.</p>
  <p><b class="h">Methods</b>CDC NNDSS provisional measles counts (indigenous plus imported){cite(5)}
  for the 50 states and DC were linked with CDC SchoolVaxView kindergarten MMR coverage and exemption rates
  for the matching school year{cite(6)} and with Census Vintage 2025 population estimates{cite(7)}. That gives
  51 states × {len(YEARS)} years = {len(table)} state-years. Annual cases were taken from the NNDSS cumulative
  year-to-date counts. The exemption rate counts exemptions from any required vaccine, not MMR alone{cite(1)}.
  Rates per 100,000 and Spearman rank correlations with permutation p-values were calculated, and states
  below 95% coverage were compared with those at or above it.</p>
  <p><b class="h">Results</b>Reported cases rose from {tot[first]:,} in {first} ({with_cases[first]} states)
  to {tot[YEARS[1]]:,} in {YEARS[1]} and {tot[last]:,} in {last} through week {LAST_WEEK}
  ({with_cases[last]} states), a {growth:.0f}-fold increase with {last} still incomplete. Median state MMR coverage moved from
  {f1(sy.loc[sy0, 'mmr_coverage'])}% ({sy0}) to {f1(sy.loc[sy1, 'mmr_coverage'])}% ({sy1}), and the median
  exemption rate from {f1(sy.loc[sy0, 'exemption_rate'])}% to {f1(sy.loc[sy1, 'exemption_rate'])}%;
  {s_last['n_lo']} of {s_last['n_rep']} reporting states were below 95% in {sy1}.
  The coverage–incidence association was clear in {len(sig)} of {len(YEARS)} years ({by_year}).
  It was strongest in {best} (n = {sb['n']}), when states below 95% had a combined rate
  {sb['ratio']:.1f}× that of states at or above 95% ({sb['r_lo']:.2f} vs. {sb['r_hi']:.2f} per 100,000;
  median state {sb['m_lo']:.2f} vs. {sb['m_hi']:.2f}). Only {sb['n_rep'] - sb['n_lo']}
  reporting states were at or above 95%, so these ratios are unstable. In {last} the association was
  {strength(s_last['rho'])}; {", ".join(top3[:-1])} and {top3[-1]} accounted for {top3_share:.0%} of cases.
  Pooled across years, ρ = {neg(pooled_rho)} ({fmt_p(pooled_p)}, n = {pooled_n} state-years); this p-value
  is optimistic because each state appears once per year. {exempt_txt} {bonf_txt}</p>
  <p><b class="h">Conclusions</b>{concl} State averages also hide under-vaccinated communities.
  These are ecological associations and do not show individual-level risk, and a state-level analysis
  cannot show that raising coverage in a given state would lower its measles rate. The findings are
  consistent with the Healthy People 2030 goal of 95% kindergarten MMR coverage{cite(1)}.</p>
  <div class="kw"><b>Keywords:</b> measles · MMR vaccination · vaccine exemptions · kindergarten ·
  surveillance · NNDSS · ecological study · United States</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("### Key findings")
    cards = [
        ("red", "Surge", f"{growth:.0f}×",
         f"Measles cases, {first} → {last}",
         f"{tot[first]:,} cases in {first} became {tot[last]:,} in {last} (through week {LAST_WEEK}). "
         f"{passed_txt}"),
        ("blue", "Vulnerability", f"{s_last['n_lo']} of {s_last['n_rep']}",
         f"States below 95% MMR ({sy1})",
         f"Median state coverage is {f1(sy.loc[sy1, 'mmr_coverage'])}%. The median exemption rate "
         f"rose from {f1(sy.loc[sy0, 'exemption_rate'])}% ({sy0}) to {f1(sy.loc[sy1, 'exemption_rate'])}%."),
        ("red", "Relationship", f"{len(sig)} of {len(YEARS)}",
         "Years with a clear coverage link",
         f"Clearest in {best} (ρ = {neg(sb['rho'])}, {fmt_p(sb['p'])}): states below 95% had "
         f"{sb['r_lo']:.2f} vs. {sb['r_hi']:.2f} cases per 100k combined, and {sb['m_lo']:.2f} vs. "
         f"{sb['m_hi']:.2f} for the typical (median) state."
         + (f" No clear link in {join_years(not_sig, "or")}." if not_sig else "")),
        ("blue", "Clustering", f"{top3_share:.0%}",
         f"Of {last} cases in three states",
         f"{', '.join(top3)}. A few big outbreaks drive the totals, which can weaken state-level "
         f"correlations (ρ = {neg(s_last['rho'])} in {last})."),
    ]
    cols = st.columns(4)
    for col, (tone, tag, big, title, body) in zip(cols, cards):
        col.markdown(f'<div class="card {tone}"><span class="tag">{tag}</span>'
                     f'<div class="big">{big}</div><h4>{title}</h4><p>{body}</p></div>',
                     unsafe_allow_html=True)

    st.markdown("### In the news")
    articles = [
        ("Johns Hopkins IVAC [2]", "Jul 22, 2026",
         "2026 U.S. measles cases surpass 2025 level, highest since declared eliminated in 2000",
         "2,295 confirmed cases by July 21, 2026, already past 2025's 2,289. The most since 1991.",
         "https://publichealth.jhu.edu/ivac/2026-us-measles-cases-surpass-2025-level"),
        ("Georgetown CCF [3]", "Aug 25, 2026",
         "New CDC data shows increase in vaccine exemptions and less vaccine coverage nationally",
         "Kindergarten MMR coverage fell to 92.4% in 2025-26, and exemptions rose to 4.2% (about 155,000 children).",
         "https://ccf.georgetown.edu/2026/08/25/new-cdc-data-shows-increase-in-vaccine-exemptions-and-less-vaccine-coverage-nationally/"),
        ("AHCJ [4]", "Sep 2, 2026",
         "SchoolVaxView offers data and trends on kindergarten vaccination rates",
         "A reporter's guide to CDC's school vaccination data. Exemptions from at least one vaccine rose 17% in 2025-26.",
         "https://healthjournalism.org/blog/2026/09/schoolvaxview-offers-data-and-trends-on-kindergarten-vaccination-rates"),
        ("CDC [8]", "Updated Nov 13, 2026",
         "Measles cases and outbreaks",
         "CDC's official confirmed-case count (5,412 in 2026 as of Nov 12), plus outbreaks, ages and vaccination status.",
         "https://www.cdc.gov/measles/data-research/index.html"),
    ]
    cols = st.columns(4)
    for col, (src, date, title, blurb, url) in zip(cols, articles):
        col.markdown(f'<a class="article" href="{url}" target="_blank" rel="noopener">'
                     f'<span class="src">{src}</span><span class="h5">{title}</span>'
                     f'<span class="p">{blurb}</span><span class="date">{date} · Read ↗</span></a>',
                     unsafe_allow_html=True)
    st.caption("National totals in news reports come from CDC's measles page and can differ from "
               "the provisional NNDSS counts used in this dashboard. See Methods.")
    st.markdown(references_html() +
                f'<div class="howcite"><b>How to cite this dashboard:</b> Patil S. Measles Watch USA: U.S. measles '
                f'surveillance and vaccination vulnerability dashboard [Internet]. {LAST_DATE:%Y} '
                f'[data through {LAST_DATE:%Y %b %d}]. Available from: '
                f'<a href="https://measles-watch-usa.streamlit.app" target="_blank">https://measles-watch-usa.streamlit.app</a></div>'
                + author_html(), unsafe_allow_html=True)
