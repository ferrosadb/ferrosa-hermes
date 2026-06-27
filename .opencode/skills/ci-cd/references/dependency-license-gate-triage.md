# Dependency License Gate Triage

Use this when `cargo deny check` or another dependency-license gate blocks CI hardening/release work.

## Principle

Do not make CI green by silently broadening the license allowlist. First prove what uses the license and whether it fits the repository's distribution posture. If it is incompatible or ambiguous, rework/remove/feature-gate the dependent functionality.

## Rust/cargo-deny workflow

```bash
# Identify failing license check directly
cargo deny check licenses

# Find reverse dependency paths for crates named in the deny output
cargo tree -i CRATE_NAME
cargo tree -i CRATE_NAME --target all

# Inspect direct dependency declarations
grep -R "CRATE_OR_STACK" -n --include Cargo.toml .
```

When allowing an additional license:

1. Confirm the exact SPDX identifier and version, e.g. `CDLA-Permissive-2.0` vs `CDLA-Permissive-2.1` or `CDLA-Sharing-*`.
2. Identify the exact crates and dependency path.
3. Confirm the license is compatible with the repo's own license and release/distribution model.
4. Add a focused comment next to the allowlist entry explaining the crate/path and rationale.
5. Re-run the license gate and the full dependency gate.

## Example: WebPKI root certificates

`webpki-roots` / `webpki-root-certs` may appear via `ureq`/Rustls HTTPS stacks and use `CDLA-Permissive-2.0` for Mozilla/WebPKI root certificate data. If the repo policy accepts CDLA-Permissive-2.0, keep the allowlist comment specific to certificate root data and state that it is not CDLA-Sharing and not 2.1.

## Reporting

Report:

- license identifier and version
- crates using it
- reverse dependency path to direct dependencies
- whether the allowlist already had the license
- exact gate output after the change, e.g. `licenses ok`
