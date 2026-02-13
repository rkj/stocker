# Fixture Dataset

`sample_stock_data.csv` is a deterministic subset extracted from the full historical dataset:
- source: `/mnt/nfs-lithium-public/rkj/all_stock_data.csv`
- symbols: `ED,CVX,GD,BP,IBM,KO`
- window: `1980-01-01` to `1980-12-31`
- max rows requested: `2500`

Actual output summary is tracked in `sample_stock_data.manifest.json`.

Regenerate:

```bash
PYTHONPATH=src python3 -m stocker.tools.fixture_extractor \
  --input-path /mnt/nfs-lithium-public/rkj/all_stock_data.csv \
  --output-path tests/fixtures/sample_stock_data.csv \
  --symbols ED,CVX,GD,BP,IBM,KO \
  --start-date 1980-01-01 \
  --end-date 1980-12-31 \
  --max-rows 2500
```

