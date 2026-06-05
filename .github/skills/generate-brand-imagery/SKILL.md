---
name: generate-brand-imagery
description: Generate production-ready logo, avatar, and banner assets for a GitHub org/user with iterative multi-provider image runs, strict naming, provider fallback, and concise quality reporting.
---

# Generate Brand Imagery

Use this skill when the user asks to create or iterate brand assets for a GitHub organization, user profile, or both.

## Use When

- User asks to generate GitHub profile branding assets.
- User wants cohesive avatar, logo, and banner sets.
- User wants iterative prompt refinement across multiple runs.
- User wants fallback behavior across image providers when credits/rate limits fail.

## Inputs

Collect and normalize these arguments in this exact order, one concise question at a time:

- `kind`: `org` | `user` | `both`
- `username`: required for `user` or `both`
- `orgname`: required for `org` or `both`
- `brandName`: optional display name for identity text
- `runs`: optional max run count, unlimited if omitted
- `inspirations`: optional list of image paths/URLs
- `fonts`: optional list of preferred font inspirations
- `hobbies`: optional list of interests for motifs
- `style`: optional palette/material/mood/composition direction
- `outputDir`: optional output folder, default `assets/generated`
- `stopOnCreditsExhausted`: default `true`
- `respectRateLimits`: default `true`
- `promptOnProviderCreditExhausted`: default `true`

Treat blank as null unless required by `kind`.
After collecting all inputs, continue without reconfirmation.

## Style Auto-Suggest

If `style` is null:

1. Propose exactly 3 compact style options using available context (`brandName`, `kind`, `hobbies`, `fonts`).
2. Each option must include palette plus art direction.
3. Ask user to pick one or provide custom style text.
4. If still blank, select the most relevant option and continue.

## Naming Resolution

Resolve `targetName` for output filenames:

- Use `brandName` slug when provided.
- Else `orgname` for `kind=org`.
- Else `username` for `kind=user`.
- For `kind=both`, produce separate target sets for org and user.

## Goal

Per run, generate all requested image types:

- `avatar`
- `banner`
- `logo`

Use all accessible image tools/providers available in the current environment.

## Hard Rules

- Never overwrite existing files.
- Filename format: `<target>_<imagetype>_<instance>.png`
- Valid imagetype values: `avatar`, `banner`, `logo`
- `instance` starts at `1` and increments until a free filename is found.
- Prefer PNG; convert JPG/WebP outputs to PNG if needed.
- Respect provider/platform rate limits with backoff + jitter.
- Treat credit exhaustion as provider-scoped, not global.
- If one provider is exhausted, continue with remaining providers unless the user asks to stop.
- On provider credit exhaustion: notify user immediately, include provider name, ask whether to continue.
- Keep all outputs policy-compliant and avoid direct imitation of living artists.
- Embedded text is allowed only when explicitly requested in `style` and supported by provider.
- If text is requested, prefer OpenAI image tooling first for text fidelity, then fallback providers.
- Inspiration images are loose references only; do not copy distinctive copyrighted brand elements.
- Logo quality: strong simple scalable forms; avoid over-detail.
- Avatar quality: clear recognizable silhouette at small size.
- Banner quality: atmospheric wide composition with safe focal framing.
- Keep org image sets stylistically cohesive while adapting composition per format.

## Prompt Construction

Build each prompt from:

- Core identity: `brandName` plus org/user identity and role
- Visual traits: hobbies/interests mapped to motifs/iconography
- Typography: font inspirations (not exact licensed-font replication)
- Style system: palette, contrast, texture, mood, lighting
- Composition: frame per type (square avatar, wide banner, scalable logo)
- Constraints: no text unless explicitly requested

Use reference/image-to-image capable tools when inspiration images are provided.

## Iteration Plan

For each `runIndex` in `1..runs`:

1. Generate candidate avatar/logo/banner set.
2. Save each file to first non-conflicting filename.
3. Validate:
   - Avatar: square, recommended >= 1024x1024
   - Logo: square or portrait-safe, shortest side >= 1024
   - Banner: wide, recommended >= 1536x640
4. If weak quality, refine prompts and regenerate only weak outputs next run.
5. Check rate-limit/credit health before each provider batch.
6. On credit exhaustion, mark provider unavailable for future runs and prompt user to continue.

## Tooling Strategy

- Prefer parallel generation when safe.
- Prefer OpenAI image tooling first for initial generation attempts.
- Use mixed providers/models when available for variety and resilience.
- Provider fallback chain:
  - OpenAI
  - Fal
  - Together
  - EverArt
  - Pollinations
- Reuse successful prompt fragments across runs.
- Log provider and model used for each output file.

## Required Output Report

Always return a concise report containing:

- Normalized inputs
- Tools/models used
- Provider credit status and continue/stop decisions
- Files created (relative paths)
- Skipped filename collisions
- Run-by-run quality notes
- Stop reason: run limit, success, or credit exhaustion
- Suggested next-run arguments
