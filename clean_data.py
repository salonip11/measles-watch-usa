"""Measles Watch USA: download and clean the three source datasets.

    python clean_data.py               # download from CDC / Census, then clean
    python clean_data.py --raw data/raw  # use CSVs you already downloaded

Writes to data/:
    measles_cases.csv       state, year, week, week_ending, cases, cases_first_reported, cumulative
    population.csv          state, year, population
    mmr_coverage.csv        state, school_year, mmr_coverage, exemption_rate
    measles_state_year.csv  the merged analysis table (51 states x 3 years = 153 rows)

About "cases": NNDSS's weekly column (m1) is frozen as first reported, so cases
reported late are never added back. Summing m1 gives 676 measles cases for 2025,
but the NNDSS cumulative total (m3) is 2,026. We therefore define each week's
cases as the increase in the cumulative year-to-date count (m3) since the
previous week. Summing those weeks reproduces the NNDSS cumulative total
exactly. m1 is kept as cases_first_reported for reference. (CDC's measles page
reports slightly higher final counts for past years, e.g. 2,289 for 2025.)
"""
import argparse
import io
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
CASE_YEARS = [2024, 2025, 2026]
MEASLES_LABELS = ["Measles, Indigenous", "Measles, Imported"]

# --- sources --------------------------------------------------------------
NNDSS_API = "https://data.cdc.gov/resource/x9gk-5huc.csv"          # filtered query (small)
NNDSS_CSV = "https://data.cdc.gov/api/v3/views/x9gk-5huc/export.csv?accessType=DOWNLOAD"  # full (~280 MB)
VAX_CSV = "https://data.cdc.gov/api/v3/views/ijqb-a7ye/export.csv?accessType=DOWNLOAD"
POP_CSV = ("https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/"
           "state/totals/NST-EST2025-ALLDATA.csv")

# Column names differ between the API and the CSV export; map both to API names.
NNDSS_COLS = {"Reporting Area": "states", "Current MMWR Year": "year", "MMWR WEEK": "week",
              "Label": "label", "Current week": "m1", "Cumulative YTD Current MMWR Year": "m3"}
VAX_COLS = {"Vaccine/Exemption": "vaccine", "Dose": "dose", "Geography Type": "geography_type",
            "Geography": "geography", "School Year": "year_season",
            "Estimate (%)": "coverage_estimate"}

STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois",
    "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
    "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah",
    "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
]
# NNDSS spells states in capitals in some years and Title Case in others.
# Upper-casing everything keeps every year; NYC is folded into New York State.
NNDSS_TO_STATE = {s.upper(): s for s in STATES} | {"NEW YORK CITY": "New York"}


# --- helpers --------------------------------------------------------------
def to_num(s: pd.Series) -> pd.Series:
    """'1,161' -> 1161; blanks, 'NR', 'NReq' -> NaN."""
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False), errors="coerce")


def fetch_csv(url: str, **kw) -> pd.DataFrame:
    print(f"  downloading {url[:90]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "measles-watch-usa"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return pd.read_csv(io.BytesIO(r.read()), dtype=str, **kw)


def find_raw(raw: Path | None, pattern: str) -> Path | None:
    if raw is None:
        return None
    hits = sorted(raw.glob(pattern))
    return hits[-1] if hits else None


def mmwr_week_ending(year: int, week: int) -> date:
    """Saturday that ends MMWR week `week` of `year` (week 1 contains Jan 4)."""
    jan4 = date(year, 1, 4)
    week1_sunday = jan4 - timedelta(days=(jan4.weekday() + 1) % 7)
    return week1_sunday + timedelta(weeks=week - 1, days=6)


def check(name: str, df: pd.DataFrame) -> None:
    n = df["state"].nunique()
    print(f"  {name:<24} {len(df):>6} rows  {n} states {'[OK]' if n == 51 else '[CHECK]'}")


# --- 1. measles cases -----------------------------------------------------
def load_nndss(raw: Path | None) -> pd.DataFrame:
    local = find_raw(raw, "NNDSS*.csv")
    if local:
        print(f"  reading {local.name}")
        df = pd.read_csv(local, dtype=str, usecols=list(NNDSS_COLS)).rename(columns=NNDSS_COLS)
    else:
        labels = ",".join(f"'{l}'" for l in MEASLES_LABELS)
        query = {"$select": "states,year,week,label,m1,m3",
                 "$where": f"label in({labels}) AND year >= '{min(CASE_YEARS)}'",
                 "$limit": "500000"}
        try:
            df = fetch_csv(NNDSS_API + "?" + urllib.parse.urlencode(query))
        except Exception as e:  # fall back to the full export
            print(f"  filtered query failed ({e}); downloading full file")
            df = fetch_csv(NNDSS_CSV, usecols=list(NNDSS_COLS)).rename(columns=NNDSS_COLS)
    return df


def national_totals(df: pd.DataFrame) -> pd.Series:
    """CDC's national row ('U.S. Residents, excluding U.S. Territories') at the last week of each year."""
    us = df[df["label"].isin(MEASLES_LABELS)
            & df["states"].str.upper().str.replace(".", "", regex=False).str.strip().str.startswith("US RESIDENTS")].copy()
    us["year"], us["week"], us["m3"] = us["year"].astype(int), us["week"].astype(int), to_num(us["m3"]).fillna(0)
    us = us[us["week"] == us.groupby("year")["week"].transform("max")]
    return us.groupby("year")["m3"].sum().astype(int)


def clean_cases(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["label"].isin(MEASLES_LABELS)].copy()
    df["state"] = df["states"].str.strip().str.upper().map(NNDSS_TO_STATE)
    df = df.dropna(subset=["state"])  # drops regions, territories, U.S. totals
    df["year"] = df["year"].astype(int)
    df["week"] = df["week"].astype(int)
    df = df[df["year"].isin(CASE_YEARS)]
    df["m1"] = to_num(df["m1"]).fillna(0)  # blank count = zero cases
    # blank cumulative = 0 (CDC also blanks it when all of a state's cases are removed;
    # treating blanks as 0 is what makes the totals match CDC's published YTD figures)
    df["m3"] = to_num(df["m3"]).fillna(0)

    # imported + indigenous, and NY + NYC -> one row per state-week
    wk = (df.groupby(["state", "year", "week"], as_index=False)[["m1", "m3"]].sum()
            .rename(columns={"m1": "cases_first_reported", "m3": "cumulative"}))

    # full grid so every state has every reported week
    weeks = wk[["year", "week"]].drop_duplicates()
    grid = weeks.merge(pd.DataFrame({"state": STATES}), how="cross")
    wk = grid.merge(wk, on=["state", "year", "week"], how="left").fillna(0)
    wk = wk.sort_values(["state", "year", "week"])
    # weekly cases = increase in the cumulative count. When CDC removes or reassigns a
    # case the cumulative drops, so a few weeks are negative; keeping them makes the
    # weekly sum equal CDC's official year-to-date total.
    wk["cases"] = wk.groupby(["state", "year"])["cumulative"].diff().fillna(wk["cumulative"])

    wk["week_ending"] = [mmwr_week_ending(y, w) for y, w in zip(wk["year"], wk["week"])]
    for c in ["cases", "cases_first_reported", "cumulative"]:
        wk[c] = wk[c].astype(int)
    return wk[["state", "year", "week", "week_ending", "cases",
               "cases_first_reported", "cumulative"]].reset_index(drop=True)


# --- 2. population ----------------------------------------------------------
def load_population(raw: Path | None) -> pd.DataFrame:
    local = find_raw(raw, "*NST-EST2025*.csv")
    if local:
        print(f"  reading {local.name}")
        return pd.read_csv(local, dtype=str, encoding="latin-1")
    return fetch_csv(POP_CSV, encoding="latin-1")


def clean_population(pop: pd.DataFrame) -> pd.DataFrame:
    pop = pop[(pop["SUMLEV"] == "040") & pop["NAME"].isin(STATES)]
    years = [y for y in CASE_YEARS if f"POPESTIMATE{y}" in pop.columns]
    long = pop.melt(id_vars="NAME", value_vars=[f"POPESTIMATE{y}" for y in years],
                    var_name="year", value_name="population")
    long["year"] = long["year"].str[-4:].astype(int)
    long["population"] = to_num(long["population"]).astype(int)
    return long.rename(columns={"NAME": "state"}).sort_values(["state", "year"])


# --- 3. MMR coverage and exemptions ------------------------------------------
def load_vax(raw: Path | None) -> pd.DataFrame:
    local = find_raw(raw, "*Kindergartners*.csv")
    if local:
        print(f"  reading {local.name}")
        return pd.read_csv(local, dtype=str).rename(columns=VAX_COLS)
    return fetch_csv(VAX_CSV).rename(columns=VAX_COLS)


def school_year_for(case_year: int) -> str:
    """2025 -> '2024-25' (coverage measured in fall describes kids in school that year)."""
    return f"{case_year - 1}-{str(case_year)[-2:]}"


def clean_vax(v: pd.DataFrame) -> pd.DataFrame:
    v = v[(v["geography_type"] == "States") & v["geography"].isin(STATES)].copy()
    v["pct"] = to_num(v["coverage_estimate"])
    keys = ["geography", "year_season"]
    mmr = v[v["vaccine"] == "MMR"][keys + ["pct"]].rename(columns={"pct": "mmr_coverage"})
    exm = (v[(v["vaccine"] == "Exemption") & (v["dose"] == "Any Exemption")][keys + ["pct"]]
           .rename(columns={"pct": "exemption_rate"}))
    out = mmr.merge(exm, on=keys, how="outer", validate="one_to_one").rename(
        columns={"geography": "state", "year_season": "school_year"})
    out = out[out["school_year"].isin([school_year_for(y) for y in CASE_YEARS])]
    # every state x school year, blank where the state did not report
    grid = pd.MultiIndex.from_product(
        [STATES, [school_year_for(y) for y in CASE_YEARS]],
        names=["state", "school_year"]).to_frame(index=False)
    # Note: SchoolVaxView's "New York" and "Texas" rows are statewide (they include the
    # separately listed "NY-City of New York" and "TX-City of Houston"), so we use them as is.
    return grid.merge(out, on=["state", "school_year"], how="left", validate="one_to_one")


# --- 4. merge (same steps as the analysis plan) ---------------------------------
def merge(cases: pd.DataFrame, pop: pd.DataFrame, vax: pd.DataFrame) -> pd.DataFrame:
    # 1. weekly to yearly
    df = cases.groupby(["state", "year"], as_index=False).agg(
        cases=("cases", "sum"), through_week=("week", "max"))
    # 2. add population (2026 borrows 2025)
    df["pop_year"] = df["year"].clip(upper=pop["year"].max())
    df = df.merge(pop.rename(columns={"year": "pop_year"}), on=["state", "pop_year"],
                  how="left", validate="many_to_one")  # fails loudly on duplicate keys
    # 3. add the matching school year: 2025 -> "2024-25"
    df["school_year"] = df["year"].map(school_year_for)
    df = df.merge(vax, on=["state", "school_year"], how="left", validate="one_to_one")
    # 4. the rate and the 95% flag (blank when coverage was not reported)
    df["rate_per_100k"] = (df["cases"] / df["population"] * 100_000).round(3)
    df["below_95"] = (df["mmr_coverage"] < 95).astype("Int64").mask(df["mmr_coverage"].isna())
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, help="folder with already-downloaded source CSVs")
    raw = ap.parse_args().raw
    DATA.mkdir(exist_ok=True)

    print("Measles cases (CDC NNDSS)")
    nndss = load_nndss(raw)
    cases = clean_cases(nndss)
    us_total = national_totals(nndss)
    print("Population (Census NST-EST2025)")
    pop = clean_population(load_population(raw))
    print("MMR coverage & exemptions (CDC SchoolVaxView)")
    vax = clean_vax(load_vax(raw))
    table = merge(cases, pop, vax)

    print("\nWrote data/:")
    for name, df in [("measles_cases.csv", cases), ("population.csv", pop),
                     ("mmr_coverage.csv", vax), ("measles_state_year.csv", table)]:
        df.to_csv(DATA / name, index=False)
        check(name, df)

    # sanity checks from the analysis plan
    ok = len(table) == 51 * len(CASE_YEARS) and table["population"].notna().all()
    print(f"\nMerged table: {len(table)} rows, blank population: "
          f"{table['population'].isna().sum()}, blank coverage: {table['mmr_coverage'].isna().sum()}"
          f"  {'[OK]' if ok else '[CHECK]'}")
    if us_total.empty:
        print("  [CHECK] No 'U.S. residents' rows found in NNDSS, so the national cross-check was skipped.")
    for y, g in table.groupby("year"):
        match = us_total.get(y)
        flag = "" if match is None else ("  = CDC U.S. total [OK]" if match == g["cases"].sum()
                                         else f"  vs CDC U.S. total {match:,} [CHECK]")
        print(f"  {y}: {g['cases'].sum():>5,} cases through MMWR week {g['through_week'].max()}, "
              f"{(g['cases'] > 0).sum()} states with cases{flag}")
    missing = table[table["mmr_coverage"].isna()][["state", "school_year"]]
    if len(missing):
        print("  coverage not reported:", "; ".join(f"{s} {y}" for s, y in missing.values))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
