# Data Interface

This document describes the expected format of input data used by the **Assaying Anomalies** library.  The code operates on monthly panels of stock returns and firm characteristics derived from CRSP, Compustat and the CRSP/Compustat Merged (CCM) link tables.  Preparing the data correctly ensures that the evaluation pipeline can be applied to your own datasets without modification.

## CRSP monthly data

The CRSP monthly stock file (`msf`) contains security‑level returns and identifiers.  After filtering to common stocks and primary exchange listings, the following columns are required:

| Column   | Description                                                |
|---------|------------------------------------------------------------|
| `permno` | Permanent identifier for each security                    |
| `date`   | Month‑end date (`YYYY-MM-DD`)                             |
| `ret`    | Monthly total return in decimal form (e.g. 0.01 for 1%)   |
| `retx`   | Ex-dividend return                                        |
| `shrout` | Shares outstanding                                         |
| `prc`    | Signed price                                              |
| `vol`    | Monthly trading volume                                    |
| `shrcd`  | Share code                                                |
| `exchcd` | Exchange code (1=NYSE, 2=AMEX, 3=NASDAQ)                 |

These are the fields pulled by the default WRDS query in the library’s `WRDSClient`【220939576088461†L32-L61】.  Returns should be expressed in decimal form, and dates should be converted to the last day of the month.

## Compustat annual fundamentals

The Compustat annual fundamentals file (`funda`) provides firm‑level accounting information.  The library expects the following fields【220939576088461†L32-L61】:

| Column    | Description                                   |
|----------|-----------------------------------------------|
| `gvkey`   | Compustat company identifier                  |
| `fyear`   | Fiscal year                                   |
| `datadate`| Balance-sheet date                            |
| `at`      | Total assets                                  |
| `ceq`     | Shareholder’s equity                          |
| `sale`    | Sales (revenue)                               |
| `cogs`    | Cost of goods sold                            |
| `txdb`    | Deferred taxes and investment tax credit       |

When converting annual fundamentals to monthly frequency, carry forward the most recent value until the next fiscal year.  Lag all characteristics by one period so that information from time *t* is used to predict returns at *t+1*.

## CCM link table

The CCM link tables map CRSP `permno` identifiers to Compustat `gvkey` identifiers.  To merge monthly returns with annual fundamentals, join the CRSP and Compustat datasets using the link tables on the appropriate date ranges.

## Preprocessing steps

1. **Filter CRSP** to common stocks (share codes 10 and 11) and primary exchange listings (`exchcd` ∈ {1, 2, 3}).  Remove rows with missing returns or prices.
2. **Normalise dates** by converting to month-end and dropping any observations outside your desired sample range.
3. **Carry forward fundamentals** from Compustat to each month until the next fiscal year.  Lag these characteristics by one period relative to returns.
4. **Merge using CCM** by matching `permno` to `gvkey` within the appropriate link date intervals.  Only links with `linkprim` equal to "P" or "C" are typically used.
5. **Ensure numeric types** for all metric columns and handle missing values appropriately.  Convert returns to decimal form (percentage divided by 100).

## Example schema

After preprocessing and merging, each row in the final panel should contain the following columns:

| Column               | Type     | Notes                                                              |
|---------------------|---------|--------------------------------------------------------------------|
| `date`              | datetime | Month-end date                                                     |
| `permno`            | int      | CRSP security identifier                                           |
| `gvkey`             | string   | Compustat company identifier                                       |
| `ret`               | float    | One-month ahead return                                             |
| `me`                | float    | Market equity (shares × price)                                     |
| `exchcd`            | int      | Exchange code                                                      |
| `characteristics …` | float    | Lagged firm characteristics (e.g. size, value, momentum, investment, profitability) |

This schema matches the inputs expected by functions such as `univariate_sort`, `double_sort` and `fama_macbeth_full`【22512246537413†L170-L223】.
