# UnitSafeCrosswalk

AI-assisted, unaudited GenLayer prototype for a public integration problem: two documentation sets may describe the same integer quantity using different units. Consensus approves the documented correspondence; the contract then performs exact, bounded unit conversion. This independently reusable IC was not extracted from a Project. No funds, personal identity or private data are involved.

## Behavior and interface

Deploy only `unit_safe_crosswalk.py`. Constructor arguments are `[]`; deployer becomes owner. The pinned runner is `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.

| Method | Purpose |
|---|---|
| `register(adapter_id,spec_json) -> fingerprint` | Owner locks source/target URL+SHA256 and 1..8 complete field pairs. Pair keys appear in `fixtures/demo-spec.json`. IDs are bounded ASCII. |
| `assess(adapter_id)` | Anyone can assess a LOCKED adapter once. All MATCH -> APPROVED; any DIFFERENT -> REJECTED; otherwise UNCERTAIN. |
| `transform(adapter_id,payload_json) -> object` | View: only APPROVED adapters. Exact declared source field set, true integers, positive domain bounds and exact target integers required. |
| `revoke(adapter_id)` | Owner invalidates an APPROVED adapter permanently. |
| `get_adapter(adapter_id)` | Inspect locked spec, input fingerprint, result, timestamps and current status. |

Field pairs form a bijection: neither source nor target field names repeat. Every input field maps to exactly one output; there are no omitted, defaulted or extra fields. Supported unit dimensions are time (`s`, `ms`, `us`), bytes (`B`, `KiB`), count (`count`), and ratios (`one`, `bp`). The conversion is `input * source_scale / target_scale`, using contract-defined integer scales. Dimensions must match. Bounds are integers from 1 to 9007199254740991; bools, floats, duplicate JSON keys, zero sentinels and negative quantities reject. A fractional target rejects instead of rounding. An entire declared source domain need not map inside the target domain: each call checks the target bound too. Units are multiplicative, with no affine temperatures, locale parsing or implicit defaults.

Canonical pair sorting makes the same input fingerprint unavailable under another adapter ID or pair order. Successful assessment is terminal, including DIFFERENT and UNCERTAIN. Transport/model errors revert and leave LOCKED, since no assessment was obtained. These are input-specific results; altered documents or field definitions require a new explicit version. The contract cannot stop another deployment or a substantively changed input from requesting a new assessment.

## Consensus and trust boundary

Leader and validators independently fetch both sources, verify their exact registered SHA256, and independently evaluate every ordered correspondence. Each evaluates quantity, behavior, units, integer type and whole positive domain applicability. Equal names or schema shape are insufficient. Candidate decisions must match the validator's own decisions; both candidate citations must be exact substrings of the validator's freshly fetched documents. The LLM cannot set conversion factors, dimensions, bounds, status, mappings or arithmetic.

URLs must be public `https://raw.githubusercontent.com/<owner>/<repo>/<40-lowercase-hex-commit>/<path>` without query, fragment, credentials, ports, empty or dot path segments. Source responses must be HTTP 200, UTF-8, 1..48000 bytes and match SHA256. The exact SDK has no redirect/final-URL control or pre-download size limit: requested URLs are checked and byte bounds apply after receipt. GitHub, transport/DNS/TLS, availability and correlated model errors remain assumptions.

Documents and field names are untrusted data in the prompt. Independent substantive re-evaluation and grounded quotes reduce leader trust but do not mathematically prove semantic equivalence or immunity to prompt injection. Owner controls admission and revocation. A third-party consumer should bind contract address, chain, adapter fingerprint and finalized current APPROVED state, and inspect the declared domains. This attests documented behavior; it does not execute or verify the external libraries themselves. Approval remains valid for the pinned document version and has no claim of current compatibility with later software releases.

## Real demonstration

`fixtures/sources.json` records actual curl documentation fetched at commit `8f143e852f2c5ef5a10a9af20ac04617e5dfef83`. `curl-seconds.md` describes `CURLOPT_CONNECTTIMEOUT`; `curl-milliseconds.md` describes `CURLOPT_CONNECTTIMEOUT_MS`, explicitly referencing the corresponding option in the other unit. Original bytes are retained with curl's permission notice in `fixtures/UPSTREAM-COPYING.txt`. No upstream software/documentation text was modified.

Register `curl` using the JSON string in `fixtures/demo-spec.json`, then assess it. If consensus approves, `transform("curl", "{\"CURLOPT_CONNECTTIMEOUT\":2}")` returns `{"CURLOPT_CONNECTTIMEOUT_MS":2000}`. The example excludes zero because libcurl uses it as a default sentinel. A reverse adapter with source `ms` and target `s` rejects 1500 ms as a fractional target integer. A live model may return UNCERTAIN; the local test does not claim a live model issued MATCH.

## Reproduce and evidence

Python 3.12+ in a dedicated environment:

```text
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe tools/verify.py
```

Linux/macOS use `.venv/bin/python`. `verify.py` downloads the official exact SDK v0.2.12, executes this deployable source through official direct tests, and runs full SDK lint/semantic validation and schema extraction. Results and source hash are in `evidence/verification.json`; all logs are retained. The test-only `conftest.py` addresses gltest 0.29.2 Windows temporary stdin cleanup and deterministic warp metadata refresh; it does not replace contract storage, consensus, fetching or arithmetic.

**The initial suite had 18 passing tests; the current complete suite has 25.** Initial minimal-contract red evidence is `evidence/tdd-red.log` (17 failures). The added order-bypass regression first failed in `tdd-order-red.log`, then passed. Tests use actual pinned fixture bytes with mocked HTTP/model boundaries, exercise actual contract transitions and `run_validator`, and never reproduce the production conversion in a host-side oracle. Independent disagreement, altered bytes, fake quotes, inverse fractional conversion, strict payload/domain checks, bijection/dimension checks, access and revocation are covered.

The constructor is FINALIZED/SUCCESS at `0x1E83D28d6F08217F90e250542f5059Da17ad94E7` on Studio 61999, with normal majority consensus, zero value and on-chain bytes matching the tested source. See evidence/deployment.json. Full live field assessment, transformation, GenVM HTTP/model behavior and production integration remain unverified; no audit, production users or endorsement is claimed.

References checked: [official boilerplate](https://github.com/genlayerlabs/genlayer-project-boilerplate), [direct test API](https://github.com/genlayerlabs/genlayer-testing-suite/blob/main/docs/direct-runner.md), [exact GenVM release](https://github.com/genlayerlabs/genvm/releases/tag/v0.2.12). Original source/tests MIT; upstream fixture notice is separate.


## Commit locator namespace repair (2026-10-21)

The prior local source SHA256 `0c39ecc55474dc3b14724ecf46fdfbcce412e15b2848668bf3ea6c9da87531d2` is superseded by `281bb3919461fe000110260f65071903372ae462cebcad198b7c6e591029fe9e`. Literal repository `.` and `..` segments are now rejected before registration or fetching, alongside the existing path restrictions. Legitimate `.github`, `repo.name` and `_repo` names remain accepted. The previous defect concerned the declared repository/commit locator under dot-segment URL normalization; exact expected SHA256 byte checks remained effective. No arbitrary-byte bypass is claimed.

The actual public SDK API regression first produced 4 failures and 3 valid-name passes. The repaired full suite has 25 passing tests, full semantic validation and schema extraction succeed on GenVM v0.2.12, and the extracted public schema is byte-identical. See `evidence/namespace-fix.json`, `namespace-red.log` and the current `verification-*.log`. Previous counts/reviews describe their frozen historical candidates; Root independently reviewed this narrow correction and closed it after the fix; see `evidence/namespace-final-review.json`. The constructor deployment is recorded separately in evidence/deployment.json; a full live namespace/source assessment flow remains unverified.
