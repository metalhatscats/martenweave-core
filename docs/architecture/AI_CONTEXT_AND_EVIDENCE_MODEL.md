# AI Context And Evidence Model

## Purpose

AI context should help agents explain, propose, and review model changes without exposing unnecessary data or bypassing validation.

## Include

- object IDs, types, names, statuses;
- relationship summaries;
- validation results;
- impact summaries;
- evidence references;
- compact dataset profile metadata;
- file paths to source material.

## Exclude By Default

- raw dataset rows;
- secrets and credentials;
- ignored local files;
- full generated indexes;
- unrelated docs or examples;
- long object bodies when a summary is enough.

## Evidence

Evidence can be a canonical `Evidence` object, an issue, a decision, a dataset profile, a file reference, or a human note. Evidence supports a proposal or decision but does not replace validation or approval.

## Privacy

Dataset and AI context workflows must minimize, redact, or exclude sensitive-looking values. If a task requires raw sensitive values, stop and ask the human.
