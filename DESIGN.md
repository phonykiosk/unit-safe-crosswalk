# UnitSafeCrosswalk design and test plan

AI-assisted prototype. No deployment or live consensus claim.

Two immutable, commit-pinned public documentation snapshots describe bounded integer fields. An owner locks a complete bijection between declared source and target fields, positive value domains and supported physical units. Validators independently fetch both byte streams and judge each semantic correspondence, including unit and domain applicability. The output is MATCH / DIFFERENT / UNCERTAIN with source-grounded quotations. All MATCH approves the adapter; any DIFFERENT rejects it; uncertainty never approves. Each input fingerprint can be assessed only once; revocation is terminal.

The useful integration is a deterministic, exact integer adapter. Unit dimensions and rational scale factors are built into the contract, never supplied by an LLM. Conversion rejects fractional integers, overflow, out-of-domain values, bools, missing or extra fields. This deliberately excludes zero sentinels, affine scales, floats, implicit defaults and partial mappings. Evidence establishes documented semantics, not equivalence of executable implementations.

TDD uses the official direct SDK and real pinned curl seconds/milliseconds documentation bytes. First deploy a minimal class and observe behavioral tests fail, then implement. Verify independently recomputed validator outcomes, forged citations, altered sources, bijection and dimension validation, exact 1000x conversion, inverse fractional rejection, field coverage, value bounds, access controls, duplicate fingerprint rejection, uncertainty and terminal revocation. Run the exact official SDK lint, semantic validation and schema generation. No host-side reimplementation of contract conversion is used.
