# needGit — Product libs (crawl + ML)

## 4. sdmx1 (OECD) — trong requirements

`import sdmx` — không dùng `pandasdmx` (xung đột pydantic).  
Code: `crawlers/oecd/sdmx_client.py`. Không invent số.

## 5. statsmodels ARIMA — trong requirements

`ml/models/trainer.py` → ARIMA/SARIMAX thật.

## 6. Playwright — trong requirements

```bash
pip install playwright && playwright install chromium
```

Marketplace / website DN nặng JS.
