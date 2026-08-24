# URL-finder v0 — error analysis (28 listed firms)

- n = 28; hits = 12; abstain = 10; wrong = 6
- hit-rate = 42.9% (Wilson 95% CI 26.5%–60.9%)
- precision among decided = 66.7%
- abstain-rate = 35.7%

n=28 listed manufacturers known to have websites. Not comparable to European 83–88% URL-finding on mixed SME samples. Wilson 95% CI is wide by design. When search is blocked, scores reflect domain-hypothesis + on-page evidence only (not a live SERP URL-finder).

Search was blocked in this environment (HTTP 202 duckduckgo_html). Candidates are domain hypotheses from legal name / aliases / ticker, then checked on the page (tax id, name). This is not a live web-search URL-finder and is not comparable to European 83–88% SME figures.

- candidate sources: {'domain_hypothesis': 28}

| ticker | error_type | predicted | gold | reason |
|--------|------------|-----------|------|--------|
| CSM | wrong_related_domain | https://casumina.com.vn | https://casumina.com | top_clear:name_in_title:100,name_in_body:100,address_tokens:8,domain_tokens:casumina |
| DCM | wrong_related_domain | https://pvcfc.com | https://www.pvcfc.com.vn | top_clear:name_in_title:100,name_in_body:100,address_tokens:3,domain_tokens:pvcfc |
| RAL | wrong_related_domain | https://bongdenrangdong.com | https://rangdong.com.vn | top_clear:name_in_title:84,name_in_body:87,address_tokens:7,domain_tokens:bongdenrangd,bongdenrangdong |
| CSV | wrong_other | https://hoachatvn.com | https://sochemvn.com | top_clear:name_in_body:77,address_tokens:2,domain_tokens:hoacha,fetch_ok |
| DQC | wrong_other | https://dqc.vn | https://dienquang.com | top_clear:tax_id_on_page,name_in_title:100,name_in_body:100,address_tokens:5 |
| VHC | wrong_other | https://vinhgroup.vn | https://vinhhoan.com | top_clear:name_in_body:100,address_tokens:6,tld_prefer:vn,fetch_ok |
| ANV | abstain | — | https://navicorp.com.vn | thin_margin:11.0-11.0<1.0 |
| BFC | abstain | — | https://binhdien.com | thin_margin:16.0-15.25<1.0 |
| BMP | abstain | — | https://binhminhplastic.com.vn | thin_margin:11.0-11.0<1.0 |
| GEE | abstain | — | https://gelex-electric.com | thin_margin:7.5-7.25<1.0 |
| HPG | abstain | — | https://www.hoaphat.com.vn | thin_margin:9.5-9.5<1.0 |
| IDI | abstain | — | https://idiseafood.com | below_min_score:0.5<4.0 |
| NKG | abstain | — | https://tonnamkim.com | thin_margin:5.0-4.25<1.0 |
| POM | abstain | — | http://www.pomina-steel.com | thin_margin:5.0-4.25<1.0 |
| REE | abstain | — | https://reecorp.com | thin_margin:7.25-6.5<1.0 |
| SBT | abstain | — | https://ttcagris.com.vn | thin_margin:4.75-4.5<1.0 |
| AAA | hit | https://anphatbioplastics.com | https://anphatbioplastics.com | top_clear:name_in_title:100,name_in_body:75,address_tokens:8,domain_tokens:anphatbiopla,anphatbioplastics |
| DGC | hit | https://ducgiangchem.vn | https://ducgiangchem.vn | top_clear:name_in_title:100,name_in_body:100,address_tokens:6,domain_tokens:ducgiangchem |
| DPR | hit | https://doruco.com.vn | https://doruco.com.vn | top_clear:name_in_title:100,name_in_body:100,address_tokens:4,domain_tokens:doruco |
| FPT | hit | https://fpt.com.vn | https://fpt.com.vn | ticker_breaks_tie:name_in_title:100,name_in_body:100,address_tokens:4,domain_tokens:fpt |
| GVR | hit | https://vrg.vn | https://vrg.vn | top_clear:name_in_title:100,address_tokens:7,domain_tokens:vrg,tld_prefer:vn |
| HSG | hit | https://hoasengroup.vn | https://hoasengroup.vn | top_clear:name_in_title:100,name_in_body:100,address_tokens:9,domain_tokens:hoasengroup |
| MSN | hit | https://masangroup.com | https://masangroup.com | top_clear:name_in_title:100,name_in_body:100,address_tokens:1,domain_tokens:masangroup |
| PNJ | hit | https://pnj.com.vn | https://pnj.com.vn | top_clear:name_in_title:100,name_in_body:100,address_tokens:2,domain_tokens:pnj |
| QNS | hit | https://qns.com.vn | https://qns.com.vn | top_clear:name_in_title:100,name_in_body:100,address_tokens:9,domain_tokens:qns |
| TLH | hit | https://tienlengroup.vn | https://www.tienlengroup.vn | top_clear:name_in_title:100,name_in_body:100,address_tokens:5,domain_tokens:tienlen |
| TYA | hit | https://taya.com.vn | https://taya.com.vn | top_clear:name_in_title:100,name_in_body:100,address_tokens:8,domain_tokens:taya |
| VNM | hit | https://vinamilk.com.vn | https://vinamilk.com.vn | top_clear:tax_id_on_page,name_in_title:100,name_in_body:100,address_tokens:5 |

## Ghi chú cho buổi gặp GVHD

- Con số này là **URL-finder v0 hypothesis-first**: DuckDuckGo HTML bị chặn (HTTP 202 duckduckgo_html) nên không dùng được SERP live.
- Ứng viên = suy domain từ tên pháp nhân / alias / ticker + kiểm chứng on-page (MST, tên, địa chỉ). Không rò rỉ `website_url` từ seed.
- So với công bố châu Âu 83–88%: mẫu khác (28 DN đã biết có website, không phải SME hỗn hợp) và phương pháp khác (không có search engine ổn định) — **không so trực tiếp**.
- Ca abstain chủ yếu `thin_margin` (hai domain cùng điểm). Ca wrong_related thường là `.com` ↔ `.com.vn` hoặc brand song song (cùng pháp nhân).
- Ca không suy được từ tên (`idiseafood`, `ttcagris`, `tonnamkim`, `sochemvn`) cần search API ở vòng sau — đây là giới hạn có chủ đích của v0.
