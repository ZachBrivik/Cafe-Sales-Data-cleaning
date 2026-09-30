# Cleaning log

Rows in: 10,000 · Rows out: 10,000 (none deleted)
Rows with at least one invalid value before cleaning: 6,911
Rows fully usable after cleaning: 9,500
Rows kept but flagged for review: 500

| Step | Column | Rows | Action |
| --- | --- | ---: | --- |
| Invalid value found | item | 969 | 333 blank, 292 ERROR, 344 UNKNOWN |
| Invalid value found | quantity | 479 | 138 blank, 170 ERROR, 171 UNKNOWN |
| Invalid value found | price_per_unit | 533 | 179 blank, 190 ERROR, 164 UNKNOWN |
| Invalid value found | total_spent | 502 | 173 blank, 164 ERROR, 165 UNKNOWN |
| Invalid value found | payment_method | 3,178 | 2579 blank, 306 ERROR, 293 UNKNOWN |
| Invalid value found | location | 3,961 | 3265 blank, 358 ERROR, 338 UNKNOWN |
| Invalid value found | transaction_date | 460 | 159 blank, 142 ERROR, 159 UNKNOWN |
| Recovered from menu | price_per_unit | 479 | price looked up from item |
| Recovered from menu | item | 489 | item identified from its unique price |
| Recalculated | total_spent | 479 | quantity x price |
| Recalculated | quantity | 456 | total / price |
| Recalculated | price_per_unit | 48 | total / quantity |
| Not recoverable | item | 480 | labelled "Unknown" |
| Not recoverable | payment_method | 3,178 | labelled "Unknown" |
| Not recoverable | location | 3,961 | labelled "Unknown" |
| Not recoverable | transaction_date | 460 | left blank |
| Flagged for review | needs_review | 500 | item or an amount still missing; row kept |
| Checked, kept | all columns | 141 | identical except ID; separate sales of the same order, not duplicates |
