# Licensing and Commercial Use

This page records the current licensing reality and the recommended commercial path for the first
public release candidate.

## Current License

Martenweave Core is currently licensed under the MIT License:

- `LICENSE` contains the MIT License text.
- `pyproject.toml` declares `license = "MIT"`.
- MIT permits commercial use, copying, modification, distribution, sublicensing, and sale, as long
  as the copyright and license notice are included.

This means the current core package cannot honestly be described as non-commercial-only or
source-available. Any public website, release note, package metadata, or pilot document should state
the MIT reality instead of implying that a paid license is required to use the current core.

## Commercial Model Options

### Option A: Keep MIT and monetize services/support/templates

Keep the core package MIT. Charge for facilitated pilots, migration readiness assessments,
implementation support, training, starter templates, review packs, and future hosted or team
collaboration products.

This is the safest current path because it preserves adoption trust and does not change rights for
existing users.

### Option B: Dual license future proprietary additions

Keep the existing core MIT, then place future proprietary add-ons under separate paid commercial
terms. Examples could include a hosted workbench, review queues, branded assessment packs,
enterprise support, or private connector bundles.

This requires clear repository boundaries so MIT code and commercial code are not confused.

### Option C: Move future releases to source-available non-commercial terms

Future releases could use a source-available non-commercial license plus paid commercial terms. This
would be a major project decision, not a release-candidate cleanup task.

If chosen later, it must be explicit, legally reviewed, and communicated as a forward-looking
license change. It should not be implied while `LICENSE` and package metadata remain MIT.

## Recommendation for This Release Candidate

Use Option A for the current release candidate:

- Keep `martenweave-core` under MIT.
- Describe commercial activity as optional paid pilots, facilitation, support, templates, and future
  products.
- Do not claim that company pilots, consulting use, internal production use, or redistribution
  require a paid license under the current MIT core.
- Mark any move to dual licensing or non-commercial source-available terms as an owner decision.

Final license strategy after the first release candidate: **requires owner decision**.
