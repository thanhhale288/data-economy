# Epic 3 Task #33 — website detector + marketplace URL audit

**Generated (UTC):** 2026-07-25T15:49:14Z
**Counts:** tickers=28, website_ok=19, website_fail=9, website_unknown=0, has_checkout=11, checkout_unknown=9, flag_url_mismatch=0, db_mismatch=0, marketplace_urls=8

| stock_code | website_ok | has_checkout | shopee_url | tiktok_url | flag_vs_url_mismatch | db_mismatch | detect_detail |
|------------|-----------|--------------|------------|------------|----------------------|-------------|---------------|
| RAL | true | true | https://shopee.vn/rangdong_official |  | - | - | ok |
| HPG | true | false |  |  | - | - | ok |
| VNM | true | true | https://shopee.vn/vinamilk_official | https://www.tiktok.com/@vinamilk | - | - | ok |
| FPT | true | true | https://shopee.vn/fpt_official |  | - | - | ok |
| GVR | true | false |  |  | - | - | ok |
| DGC | true | true |  |  | - | - | ok |
| MSN | true | false | https://shopee.vn/masan_consumer |  | - | - | ok |
| PNJ | true | false | https://shopee.vn/pnj_official | https://www.tiktok.com/@pnj | - | - | ok |
| REE | true | true |  |  | - | - | ok |
| BMP | true | false |  |  | - | - | ok |
| VHC | true | true |  |  | - | - | ok |
| ANV | true | false |  |  | - | - | ok |
| IDI | false | unknown |  |  | - | - | error:ConnectError:[Errno 8] nodename nor servname provided, or not known |
| SBT | false | unknown |  |  | - | - | error:ConnectError:[Errno 8] nodename nor servname provided, or not known |
| QNS | true | true |  |  | - | - | ok |
| HSG | true | true |  |  | - | - | ok |
| NKG | false | unknown |  |  | - | - | error:ConnectTimeout:timed out |
| POM | false | unknown |  |  | - | - | error:ConnectError:[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: EE certificate key too weak (_ssl.c:1032) |
| TLH | false | unknown |  |  | - | - | error:ConnectError:[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1032) |
| DQC | true | true | https://shopee.vn/dienquang_officialstore |  | - | - | ok |
| GEE | false | unknown |  |  | - | - | error:ConnectError:[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1032) |
| TYA | true | false |  |  | - | - | ok |
| DPR | false | unknown |  |  | - | - | error:ConnectError:[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1032) |
| CSM | true | true |  |  | - | - | ok |
| AAA | true | true |  |  | - | - | ok |
| DCM | false | unknown |  |  | - | - | error:ConnectError:[Errno 54] Connection reset by peer |
| BFC | true | false |  |  | - | - | ok |
| CSV | false | unknown |  |  | - | - | error:ConnectError:[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'hcb.com.vn'. (_ssl.c:1032) |

`unknown` = HTTP block/timeout or detection skipped — **not** a false. Checkout is never inferred from a failed fetch.

`flag_vs_url_mismatch` empty (`-`) = `digital_channels` agrees with `digital_presence` URLs. `db_mismatch` compares DB rows against seed; re-run with `--fix-db` to sync missing/stale URLs.

