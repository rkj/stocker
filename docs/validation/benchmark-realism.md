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

### 2) S&P ETF proxy (`SPY`) with dividend crediting (accepted benchmark)
- method: simulator run with strategy `explicit_symbols` on `SPY`
- window: `1993-01-29` to `2024-11-04`
- output: `docs/validation/sp500_etf_proxy_result.json`

Result:
- CAGR: `12.70%`
- Annualized volatility: `18.66%`
- Max drawdown: `-53.49%`
- Cumulative dividend cash credited: `48,940.80`

Conclusion:
- This path is within a plausible band for the post-1990 U.S. large-cap regime.
- This is the benchmark realism reference for v1.

## Published Reference Anchors
1. NYU Stern (Damodaran) historical annual returns table:
   - https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html
   - Using the table's compounded stock value (`$100 -> $382,850` from 1928 to 2018), implied long-run CAGR is about `9.49%`.
2. S&P Dow Jones Indices (index return snapshot):
   - https://www.spglobal.com/spdji/en/indices/equity/sp-500/#overview
   - The page reports a 10-year annualized **price** return around `12.85%` (as-of 2025-12-31 on the displayed snapshot).

## Interpretation
- Long-run U.S. equity expectations are commonly around ~`9-10%` nominal over very long windows.
- Post-1990 windows can be materially higher, and the observed `12.70%` SPY-proxy CAGR is consistent with that regime.
- Therefore, the simulator's accepted S&P proxy benchmark is considered realistic for the selected period.

## Caveats
- `SPY` starts in 1993, so it cannot validate pre-1993 periods.
- The v1 broad top-500 dollar-volume reconstruction is not a faithful S&P 500 index reconstruction and should not be used as the realism anchor.
- Transaction costs are disabled in this benchmark; cost sensitivity should be analyzed separately.

