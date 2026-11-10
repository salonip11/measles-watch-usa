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

# Colors (validated categorical order; status colors reserved for target flags)
YEAR_COLORS = {2024: "#2a78d6", 2025: "#eb6834", 2026: "#1baf7a"}
BELOW, AT = "#d03b3b", "#0ca30c"
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

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

st.set_page_config(page_title="Measles Watch USA", page_icon="🦠", layout="wide")


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

yr = table[table["year"] == year].copy()
school_year = yr["school_year"].iloc[0]
mcol, mtitle, mfmt = (("rate_per_100k", "Cases per 100k", ".2f") if measure.startswith("Rate")
                      else ("cases", "Cases", ",d"))

st.title("Measles Watch USA")
st.markdown("**Across U.S. states, is lower kindergarten MMR vaccination coverage linked to "
            "higher measles incidence, 2024 to 2026?**")

tabs = st.tabs(["Overview", "Trends", "Vaccination", "State Explorer", "Analysis", "Methods"])

# ---------------------------------------------------------------- 1. Overview
with tabs[0]:
    st.subheader(f"Burden: where is measles worst in {year_label(year)}?")
    # same-week comparison with the previous year
    cum = weekly.groupby(["year", "week"])["cumulative"].sum()
    wk_cmp = int(yr["through_week"].max())
    prev = cum.get((year - 1, min(wk_cmp, 52)), None) if year - 1 in YEARS else None
    total = int(yr["cases"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Measles cases", f"{total:,}",
              None if prev is None else f"{total - prev:+,} vs {year - 1} at week {wk_cmp}",
              delta_color="inverse")
    c2.metric("States reporting cases", f"{(yr['cases'] > 0).sum()} of 51")
    c3.metric("U.S. rate per 100,000", f"{pooled_rate(yr):.2f}")
    rep = yr.dropna(subset=["mmr_coverage"])
    c4.metric(f"States below 95% MMR ({school_year})", f"{int(rep['below_95'].sum())} of {len(rep)}")

    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(us_map(yr, mcol, mtitle, BLUES, mfmt), use_container_width=True)
    with right:
        st.markdown(f"**Top 10 states by rate, {year}**")
        top = (yr.nlargest(10, "rate_per_100k")[["state", "cases", "rate_per_100k", "mmr_coverage"]]
                 .rename(columns={"state": "State", "cases": "Cases", "rate_per_100k": "Per 100k",
                                  "mmr_coverage": "MMR %"}))
        st.dataframe(top, hide_index=True, use_container_width=True,
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
    st.dataframe(summ.rename(columns={"year": "Year"}), hide_index=True, use_container_width=True)
    st.caption("Why it matters: at about 95% MMR coverage, measles cannot find enough susceptible "
               "people to keep spreading. Below that level, outbreaks can grow.")

# ---------------------------------------------------------------- 2. Trends
with tabs[1]:
    st.subheader("Timing: when did cases rise, and is 2026 worse?")
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
    st.plotly_chart(tidy(fig), use_container_width=True)

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
    st.plotly_chart(tidy(fig), use_container_width=True)

    # when did the latest year pass the previous full-year total?
    if len(YEARS) >= 2:
        prev_total = int(nat.loc[nat["year"] == YEARS[-2], "cases"].sum())
        latest = nat[nat["year"] == YEARS[-1]]
        passed = latest[latest["cumulative"] > prev_total]
        if len(passed):
            r = passed.iloc[0]
            st.info(f"{YEARS[-1]} passed {YEARS[-2]}'s full-year total of {prev_total:,} cases in "
                    f"MMWR week {int(r['week'])} (week ending {r['week_ending']:%b %d}).")
    st.caption("Weekly cases are the increase in CDC's cumulative count from one week to the next, so "
               "late reports show up in the week they were added, not the week of illness onset. "
               "A few weeks where CDC removed cases are shown as zero.")

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
    c2.metric("Median state MMR coverage", f"{rep['mmr_coverage'].median():.1f}%")
    c3.metric("Median exemption rate", f"{yr['exemption_rate'].median():.1f}%")
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
        fig.update_layout(xaxis=dict(range=[lo, 100], title="Kindergartners with 2 doses MMR (%)"),
                          yaxis=dict(title=None, tickfont=dict(size=10)), bargap=0.25)
        st.markdown("**MMR coverage by state**")
        st.plotly_chart(tidy(fig, height=900), use_container_width=True)
    with right:
        st.markdown("**Any-exemption rate by state**")
        st.plotly_chart(us_map(yr, "exemption_rate", "Exemptions %", "Oranges", ".1f"),
                        use_container_width=True)
        st.markdown("**Highest exemption rates**")
        ex = (yr.nlargest(10, "exemption_rate")[["state", "exemption_rate", "mmr_coverage"]]
                .rename(columns={"state": "State", "exemption_rate": "Exemptions %", "mmr_coverage": "MMR %"}))
        st.dataframe(ex, hide_index=True, use_container_width=True)
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
              f"{row['exemption_rate'] - yr['exemption_rate'].median():+.1f} vs U.S. median",
              delta_color="inverse")

    w = weekly[weekly["state"] == pick].copy()
    w["Year"] = w["year"].astype(str)
    w["shown"] = w["cases"].clip(lower=0)
    fig = px.bar(w, x="week_ending", y="shown", color="Year",
                 color_discrete_map={str(k): v for k, v in YEAR_COLORS.items()}, custom_data=["week", "cases"])
    fig.update_traces(hovertemplate="Week ending %{x|%b %d, %Y}<br>New cases: %{customdata[1]:,}<extra></extra>")
    fig.update_layout(xaxis_title=None, yaxis_title="New cases that week", bargap=0.15)
    st.markdown(f"**Weekly measles cases, {pick}**")
    st.plotly_chart(tidy(fig, 320), use_container_width=True)

    show = s[["year", "school_year", "cases", "population", "rate_per_100k", "mmr_coverage", "exemption_rate"]].copy()
    show["year"] = show["year"].map(year_label)
    st.dataframe(show.rename(columns={"year": "Year", "school_year": "School year", "cases": "Cases",
                                      "population": "Population", "rate_per_100k": "Per 100k",
                                      "mmr_coverage": "MMR %", "exemption_rate": "Exemptions %"}),
                 hide_index=True, use_container_width=True,
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
    st.plotly_chart(tidy(fig, 460), use_container_width=True)

    # Spearman by year + pooled
    rows = []
    for label, g in [(year_label(y), table[table["year"] == y]) for y in YEARS] + [("All years pooled", table)]:
        rho, p, n = spearman(g[xcol], g["rate_per_100k"])
        rows.append({"Years": label, "Spearman ρ": round(rho, 2), "p-value": "<0.001" if p < 0.001 else f"{p:.3f}", "States (n)": n})
    corr = pd.DataFrame(rows)

    left, right = st.columns(2)
    with left:
        st.markdown(f"**Spearman correlation: {exposure} vs. measles rate**")
        st.dataframe(corr, hide_index=True, use_container_width=True)
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
        st.plotly_chart(tidy(fig, 340), use_container_width=True)

    st.warning("**How to read this.** This is an ecological comparison of states, not people. "
               "Say: *“States with lower kindergarten MMR coverage tended to have higher measles "
               "rates.”* Don't say: *“unvaccinated people got measles”*. State averages hide "
               "under-vaccinated communities, and one large outbreak can dominate a state's rate.")

# ---------------------------------------------------------------- 6. Methods
with tabs[5]:
    st.subheader("Methods")
    st.markdown(f"""
**Design.** Ecological study of 50 states + DC, January 2024 through MMWR week {LAST_WEEK} of
{YEARS[-1]} (week ending {LAST_DATE:%B %d, %Y}). {YEARS[-1]} is year to date.

**Data sources**

| Data | Source | Used |
|---|---|---|
| Weekly measles cases | [CDC NNDSS Weekly Data](https://data.cdc.gov/d/x9gk-5huc) (provisional) | 2024–{YEARS[-1]} |
| MMR coverage & exemptions | [CDC SchoolVaxView: Vaccination Coverage and Exemptions among Kindergartners](https://data.cdc.gov/d/ijqb-a7ye) | 2023-24 to 2025-26 |
| Population | [U.S. Census Bureau, Vintage 2025 (NST-EST2025-ALLDATA)](https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html) | 2024, 2025 |

**Definitions**
- **Cases**: measles, indigenous + imported. New York City is added to New York State.
- **Annual cases**: CDC's cumulative year-to-date count at the last reported week. Each week's
  cases are the increase in that count since the previous week, so adding up the weeks gives
  CDC's total exactly. *Why not add up the "current week" column?* That column is frozen when first
  published and never picks up late reports. For 2025 it adds to 676 cases, against CDC's cumulative 2,026.
- **Rate per 100,000** = annual cases ÷ July 1 population × 100,000. {YEARS[-1]} uses the 2025 population.
- **MMR coverage**: % of kindergartners with 2 doses of MMR. **Exemption rate**: % with any exemption
  (medical or non-medical).
- **Below 95%**: MMR coverage under 95%, roughly the level needed to stop measles spreading.

**Matching school years to case years.** Coverage is measured in the fall, so it describes
children in school during the following calendar year.

| Case year | School year | Population year |
|---|---|---|
| 2024 | 2023-24 | 2024 |
| 2025 | 2024-25 | 2025 |
| 2026 | 2025-26 | 2025 |

**Statistics.** Spearman rank correlation between state coverage (or exemptions) and rate, by year
and pooled, with permutation p-values. Group comparison of median and combined rates for states below
vs. at or above 95%.

**Limitations**
- *Ecological design.* A state can have 96% coverage overall and still have one under-vaccinated
  community where an outbreak takes off. State averages hide those pockets.
- *Association, not cause.* Travel, outbreak timing and local factors also affect where measles appears.
- *Outbreaks are clumpy.* One large outbreak can dominate a whole state's rate.
- *Provisional counts.* NNDSS numbers are revised. Totals may differ from CDC's measles page or final
  annual counts, which also use a different case definition and timing.
- *One age group.* Kindergarten coverage does not describe teenagers or adults.
- *Uneven reporting.* States collect school vaccination data differently, and some skip years.
- *Location.* Cases are counted in the reporting state, which may not be where infection happened.
- *2026 population.* 2026 rates use the 2025 population estimate.
""")
    missing = table[table["mmr_coverage"].isna()][["state", "school_year"]]
    if len(missing):
        st.caption("Coverage not reported: " +
                   "; ".join(f"{a} ({b})" for a, b in missing.values) + ".")
    st.download_button("Download the merged state-year table (CSV)",
                       table.drop(columns=["abbr", "target_status"]).to_csv(index=False),
                       "measles_state_year.csv", "text/csv")
    st.caption("Built with Python, pandas, Plotly and Streamlit.")
