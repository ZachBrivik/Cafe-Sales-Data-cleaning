"""
Clean the Kaggle "dirty cafe sales" dataset (10,000 transactions).

Approach: recover missing values by reasoning wherever the data allows it,
flag what cannot be recovered, and never delete a transaction. Every step
is counted and written to cleaning_log.md, and the script finishes with
checks that stop it if the cleaned data breaks a rule.

Run:  python clean_cafe_sales.py
"""
from pathlib import Path
import pandas as pd

RAW = Path("data/raw/dirty_cafe_sales.csv")
OUT = Path("data/clean")
BAD_MARKERS = ["", "ERROR", "UNKNOWN"]
log = {}  # (step, column, action) -> rows affected; repeats are added up


def note(step, column, n, action):
    key = (step, column, action)
    log[key] = log.get(key, 0) + int(n)
    print(f"{step:<28} {column:<16} {int(n):>6}  {action}")


# 1. Load everything as text so nothing is silently converted -------------
raw = pd.read_csv(RAW, dtype=str, keep_default_na=False)
df = raw.copy()
df.columns = [c.lower().replace(" ", "_") for c in df.columns]
n_rows = len(df)

# 2. Count and replace the bad markers --------------------------------------
for col in df.columns:
    counts = {m: (df[col] == m).sum() for m in BAD_MARKERS}
    if sum(counts.values()):
        detail = f"{counts['']} blank, {counts['ERROR']} ERROR, {counts['UNKNOWN']} UNKNOWN"
        note("Invalid value found", col, sum(counts.values()), detail)
    df[col] = df[col].mask(df[col].isin(BAD_MARKERS))

# 3. Convert to proper types --------------------------------------------------
for col in ["quantity", "price_per_unit", "total_spent"]:
    df[col] = pd.to_numeric(df[col])
df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="%Y-%m-%d")

# 4. Learn the menu from complete rows and confirm it is consistent ---------
pairs = df.dropna(subset=["item", "price_per_unit"])
prices_per_item = pairs.groupby("item")["price_per_unit"].nunique()
assert (prices_per_item == 1).all(), "An item has more than one price"
menu = pairs.groupby("item")["price_per_unit"].first().to_dict()
items_per_price = pd.Series(menu).reset_index().groupby(0)["index"].apply(list)
unique_price_item = {p: i[0] for p, i in items_per_price.items() if len(i) == 1}
shared = {p: i for p, i in items_per_price.items() if len(i) > 1}
print("Menu:", menu)
print("Prices shared by two items (item cannot be inferred):", shared)

# 5. Recover missing values. Repeat, because one fix can unlock another ----
for _ in range(3):
    m = df["price_per_unit"].isna() & df["item"].notna()
    df.loc[m, "price_per_unit"] = df.loc[m, "item"].map(menu)
    if m.sum(): note("Recovered from menu", "price_per_unit", m.sum(), "price looked up from item")

    m = df["item"].isna() & df["price_per_unit"].isin(unique_price_item)
    df.loc[m, "item"] = df.loc[m, "price_per_unit"].map(unique_price_item)
    if m.sum(): note("Recovered from menu", "item", m.sum(), "item identified from its unique price")

    q, p, t = df["quantity"], df["price_per_unit"], df["total_spent"]
    m = t.isna() & q.notna() & p.notna()
    df.loc[m, "total_spent"] = q[m] * p[m]
    if m.sum(): note("Recalculated", "total_spent", m.sum(), "quantity x price")

    m = q.isna() & t.notna() & p.notna()
    df.loc[m, "quantity"] = t[m] / p[m]
    if m.sum(): note("Recalculated", "quantity", m.sum(), "total / price")

    m = p.isna() & t.notna() & q.notna()
    df.loc[m, "price_per_unit"] = t[m] / q[m]
    if m.sum(): note("Recalculated", "price_per_unit", m.sum(), "total / quantity")

# 6. Fields that cannot be inferred -----------------------------------------
for col in ["item", "payment_method", "location"]:
    n = df[col].isna().sum()
    df[col] = df[col].fillna("Unknown")
    note("Not recoverable", col, n, 'labelled "Unknown"')

n = df["transaction_date"].isna().sum()
note("Not recoverable", "transaction_date", n, "left blank")

core = ["quantity", "price_per_unit", "total_spent"]
df["needs_review"] = df[core].isna().any(axis=1) | (df["item"] == "Unknown")
note("Flagged for review", "needs_review", df["needs_review"].sum(),
     "item or an amount still missing; row kept")

df["quantity"] = df["quantity"].astype("Int64")

# 7. Checked but deliberately not changed -----------------------------------
look_alikes = raw.drop(columns="Transaction ID").duplicated().sum()
note("Checked, kept", "all columns", look_alikes,
     "identical except ID; separate sales of the same order, not duplicates")

# 8. Final checks. The script stops if any of these fail --------------------
full = df.dropna(subset=core)
assert len(df) == n_rows, "Rows were lost"
assert df["transaction_id"].is_unique, "Duplicate transaction IDs"
assert ((full["quantity"] * full["price_per_unit"] - full["total_spent"]).abs() < 1e-9).all(), "Arithmetic broken"
known = df[df["item"] != "Unknown"].dropna(subset=["price_per_unit"])
assert (known["price_per_unit"] == known["item"].map(menu)).all(), "Price does not match menu"
assert not df.isin(["ERROR", "UNKNOWN"]).any().any(), "Bad markers remain"
print("All checks passed.")

# 9. Model-ready copy: complete rows only, amounts normalised ----------------
model = df[~df["needs_review"]].copy()
for col in ["quantity", "total_spent"]:
    model[f"{col}_scaled"] = ((model[col] - model[col].mean()) / model[col].std()).round(4)

# 10. Save outputs -----------------------------------------------------------
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "cafe_sales_clean.csv", index=False, date_format="%Y-%m-%d")
model.to_csv(OUT / "cafe_sales_model_ready.csv", index=False, date_format="%Y-%m-%d")

before = raw.isin(BAD_MARKERS).any(axis=1).sum()
lines = [
    "# Cleaning log",
    "",
    f"Rows in: {n_rows:,} · Rows out: {len(df):,} (none deleted)",
    f"Rows with at least one invalid value before cleaning: {before:,}",
    f"Rows fully usable after cleaning: {len(model):,}",
    f"Rows kept but flagged for review: {df['needs_review'].sum():,}",
    "",
    "| Step | Column | Rows | Action |",
    "| --- | --- | ---: | --- |",
] + [f"| {s} | {c} | {n:,} | {a} |" for (s, c, a), n in log.items()]
Path("cleaning_log.md").write_text("\n".join(lines) + "\n")
print("Wrote cleaning_log.md and data/clean/")
