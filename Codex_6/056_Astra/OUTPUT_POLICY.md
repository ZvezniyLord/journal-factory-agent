# OUTPUT_POLICY.md

## Production journal destination

A production build must never choose an output location ad hoc.

The conference number is derived deterministically from trusted run inputs, primarily the Excel/registry metadata or archive/file naming when unambiguous.

For each conference:
- create a dedicated conference-number folder under the configured journal output root;
- never overwrite an existing source archive, Excel registry or template;
- write the finished journal only after release QA;
- keep run/audit artifacts inside the Astra workspace, not mixed with the final journal folder unless explicitly configured;
- if the conference number cannot be resolved uniquely, status is BLOCKED;
- if the output root is not configured or unavailable, status is BLOCKED;
- if a destination file already exists, create a versioned/new filename unless explicit overwrite approval exists.

The physical output root is configured in `config/output_paths.yaml`.
Hermes may resolve the conference number and orchestrate the build, but Astra code owns directory creation and final file placement.
