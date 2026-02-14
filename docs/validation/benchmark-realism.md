# Benchmark Realism Validation

## Date
2026-02-12

## Inputs
- data source: `/mnt/nfs-lithium-public/rkj/all_stock_data.csv`
- initial capital: `10,000`
- transaction costs: `0 bps`, `0 fixed`, `0 slippage` (for baseline realism check)

## Runs

### 1) Broad top-500 dollar-volume proxy (rejected)
- method: `stocker.validation.benchmark.run_sp500_proxy_streaming`
- window: `1962-01-02` to `2024-11-04`
- config: `top_n=500`, `rolling_window=252`
- output: `docs/validation/sp500_proxy_streaming_result.json`

Result:
- CAGR: `-51.61%`
- Max drawdown: `-100%`

Conclusion:
- This implementation is **not realistic** for an S&P 500 proxy on this raw multi-asset universe.
- It is retained as a diagnostic result, not as the published benchmark path.

### 2) S&P ETF proxy (`SPY`) price-return benchmark (accepted)
- method: simulator run with strategy `explicit_symbols` on `SPY`
- window: `1993-01-29` to `2024-01-02`
- config: `--engine in_memory --price-series-mode raw_reconstructed --contribution-amount 0 --fee-bps 0 --slippage-bps 0`

Result:
- CAGR: `7.98%`
- Final equity from `$10,000`: `107,537.63`
- Annualized volatility: `18.81%`
- Max drawdown: `-56.46%`

Conclusion:
- This aligns with public price-return references near ~`8%` annualized for a comparable S&P 500 window.
- This is the baseline realism reference for price-return comparisons.

## Published Reference Anchors
1. NYU Stern (Damodaran) historical annual returns table:
   - https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html
   - Using the table's compounded stock value (`$100 -> $382,850` from 1928 to 2018), implied long-run CAGR is about `9.49%`.
2. S&P Dow Jones Indices (index return snapshot):
   - https://www.spglobal.com/spdji/en/indices/equity/sp-500/#overview
   - The page reports a 10-year annualized **price** return around `12.85%` (as-of 2025-12-31 on the displayed snapshot).

## Interpretation
- Prior `12.70%` outputs came from double-counting dividends (adjusted close series plus explicit dividend cash credit).
- After correcting the accounting path and using price-only reconstructed closes, results are close to published S&P 500 price-return references.

## Caveats
- `SPY` starts in 1993, so it cannot validate pre-1993 periods.
- The v1 broad top-500 dollar-volume reconstruction is not a faithful S&P 500 index reconstruction and should not be used as the realism anchor.
- Transaction costs are disabled in this benchmark; cost sensitivity should be analyzed separately.
