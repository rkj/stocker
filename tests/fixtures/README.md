# Fixture Dataset

`sample_stock_data.csv` is a deterministic synthetic dataset for tests.
It is generated data, not redistributed market data.

CSV schema:
- `Date`
- `Ticker`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume`
- `Dividends`
- `Stock Splits`

Actual output summary is tracked in `sample_stock_data.manifest.json`.

Generate a new fixture from your own input dataset:

```bash
PYTHONPATH=src python3 -m stocker.tools.fixture_extractor \
  --input-path data/market_data.csv \
  --output-path tests/fixtures/sample_stock_data.csv \
  --symbols ED,CVX,GD,BP,IBM,KO \
  --start-date 1980-01-01 \
  --end-date 1980-12-31 \
  --max-rows 2500
```
