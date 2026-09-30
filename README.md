# Cafe sales data cleaning

Cleaning a deliberately messy dataset of 10,000 cafe transactions from 2023, with every decision counted and checked.

**Source:** "Cafe Sales – Dirty Data for Cleaning Training" on Kaggle. (https://www.kaggle.com/datasets/ahmedmohamed2003/cafe-sales-dirty-data-for-cleaning-training)

## Result

| | Rows |
| --- | ---: |
| Transactions in | 10,000 |
| Transactions with at least one invalid value | 6,911 |
| Fully usable after cleaning | 9,500 |
| Kept but flagged for review | 500 |
| Deleted | 0 |

1,951 missing values were recovered by reasoning rather than guessed or dropped. The full breakdown is in [cleaning_log.md](cleaning_log.md).

## What was wrong

Every column mixed real values with three kinds of bad entry: blanks, `ERROR` and `UNKNOWN`. Payment method and location were missing in roughly a third of rows.

## How it was cleaned

1. **Load everything as text first**, so no bad value is silently converted, then count each kind of bad marker per column.
2. **Learn the menu from the data.** Each item has exactly one price (Coffee 2.0, Tea 1.5, and so on). The script confirms this before relying on it.
3. **Recover values by reasoning.** A missing price comes from the item. A missing item comes from the price, but only where that price belongs to a single item; 3.0 (Cake/Juice) and 4.0 (Sandwich/Smoothie) are ambiguous, so those stay unknown. Quantity × price = total held in all 8,544 complete rows, so any one missing amount is recalculated from the other two. The steps repeat, because one recovery can unlock another.
4. **Label what cannot be inferred.** Payment method, location and ambiguous items become `Unknown`. Missing dates are left blank rather than invented.
5. **Flag, don't delete.** Rows still missing an item or an amount get `needs_review = True`.
6. **Check the result.** The script stops if rows were lost, IDs are duplicated, any quantity × price ≠ total, any price disagrees with the menu, or any `ERROR`/`UNKNOWN` text remains.

## A judgement call

141 rows are identical apart from their transaction ID. With only 8 items and one year of dates, the same order on the same day is expected, so these are treated as separate sales and kept.

## Outputs

- `data/clean/cafe_sales_clean.csv` — all 10,000 rows, cleaned, snake_case columns, with a `needs_review` flag.
- `data/clean/cafe_sales_model_ready.csv` — the 9,500 complete rows, with quantity and total spent normalised (z-score) for use in a model.
- `cleaning_log.md` — every step with the number of rows affected.

## Run it

```
pip install -r requirements.txt
python clean_cafe_sales.py
```
