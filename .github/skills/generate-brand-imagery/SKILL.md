---
name: generate-brand-imagery
description: Create or refine cohesive GitHub organization and user avatars, logos, and banners, using available image tools, reference images, bounded iterations, and collision-safe asset names.
---

# Generate Brand Imagery

Create the requested brand assets, inspect the results, and deliver usable image files with concise quality notes. Adapt
to the user's chosen identity, style, tools, and scope.

## Resolve the Request

Use values already supplied in the conversation and repository context. Ask only for missing information that materially
affects the result and cannot be reasonably inferred; batch essential questions together. Optional arguments do not
require an interview or reconfirmation.

| Argument | Meaning and default |
| --- | --- |
| `kind` | `org`, `user`, or `both`; infer from the request and repository owner where clear. |
| `username`, `orgname` | Target account names; required only for the corresponding target when its identity cannot be inferred. |
| `brandName` | Optional display name, independent of the GitHub account name. |
| `types` | Requested subset of `avatar`, `banner`, `logo`; default all three only when no subset was requested. |
| `runs` | Positive maximum number of generation passes; default `1`. Never interpret omission as unlimited. |
| `inspirations` | Optional reference images, paths, or URLs. |
| `fonts`, `hobbies`, `style` | Optional typography, motifs, palette, materials, mood, and composition. |
| `outputDir` | Default `assets/generated`, relative to the repository root. |
| `stopOnCreditsExhausted` | Default `false`: an exhausted provider is skipped; `true` stops further generation at the first confirmed credit exhaustion. |
| `promptOnProviderCreditExhausted` | Default `false`: use an eligible fallback automatically; `true` asks before switching after credit exhaustion. |

Respect any user-specified candidate count, cost limit, dimensions, format, or provider restriction. If a run count is
invalid, resolve it before generation. Provider rate limits always apply; the legacy `respectRateLimits` argument cannot
disable them.

If style is unspecified, derive a coherent direction from existing brand assets and the supplied interests, state the
assumption briefly, and proceed. Offer a few distinct palette/art-direction options when the user asks to explore or
compare styles.

Distinguish references for inspiration from assets the user wants edited or preserved. Inspect accessible references
before using them. If an essential reference cannot be accessed, ask for that reference; proceed on independent assets
where possible. Do not claim to have used an unseen reference.

## Choose Available Tools

- Discover image-generation and editing tools actually available in the current environment. Follow their instructions
  and any applicable installed image skill. Prefer a user-selected provider; otherwise use an available tool suited to
  the required references, text, transparency, and dimensions. OpenAI image tooling is a reasonable default when
  available.
- Use one suitable provider initially. Compare multiple providers only when requested or when doing so resolves a
  concrete quality or capability gap within the user's limits. Do not call every provider just because it is available.
- A fallback must be available, authorized, and capable of the requested operation. Do not assume providers, model IDs,
  credentials, credit-balance APIs, or reference-upload support exist. Do not install tools, buy credits, or upload
  references to an unapproved service as an automatic fallback.
- For edits or identity consistency, use reference-capable tooling and preserve requested features. When a required
  capability is unavailable, explain the limitation and complete any unaffected outputs; do not silently replace an edit
  with an unrelated new image.
- If no suitable image tool is available, deliver reusable prompts for the requested targets and image types, including
  reference requirements and intended dimensions. State which capability is missing and that no images were generated;
  do not present proposed filenames as created files.
- The scripts in `assets/scripts/` are historical, task-specific asset utilities. Inspect their inputs, dependencies,
  output paths, and overwrite behavior before any reuse; they are not the default generation backend.

## Build a Coherent Set

Build prompts from the target identity, meaningful motifs, palette, contrast, texture, and composition. Keep a stable
character or emblem, palette, and rendering style across the target's formats; reuse successful reference images and
prompt details when supported.

- **Avatar:** a recognizable silhouette and clear focal point at small sizes; compose for square and circular crops.
- **Logo:** simple, distinctive forms with clear negative space. Request transparency when needed and supported. A
  raster logo is not a vector master; do not describe it as infinitely scalable.
- **Banner:** a wide composition with room around the focal subject and any requested text so ordinary display cropping
  does not cut them off.

Include embedded text when the user requests it anywhere in the brief, not only through `style`. Preserve the exact
requested wording and check its spelling in the generated image. Font names can guide typography; do not promise a
specific font file was used unless it was. Omit unrequested lettering.

For existing brand assets, follow the requested degree of reuse or transformation. Use inspiration references for the
requested visual traits rather than importing unrelated brand marks or identity details.

## Generate, Inspect, and Refine

Before starting, briefly state the target set, selected style, candidate count, and pass limit. A normal request
produces one candidate per requested image type and target in one pass.

1. Generate the missing candidates using supported sizes and formats. Parallelize only independent calls when the tool
   supports it and filenames and limits remain coordinated.
2. Inspect each actual image and verify its decoded format and dimensions. Save valid outputs using the naming rules
   below. An HTTP success, a filename extension, or a large response body alone does not prove an image is valid.
3. Review identity consistency, visual artifacts, composition, small-size legibility, requested text, and transparency
   where relevant. Prefer square avatars and logo masters around 1024 px or larger, and wide banners around 1536×640 or
   larger, unless the user or destination specifies otherwise. These are working targets, not claimed GitHub upload
   requirements. Use supported generation sizes and preserve composition when adapting to the final aspect ratio.
4. Within the pass limit, refine only missing or weak outputs. Preserve successful candidates and reuse their visual
   direction. Stop when the requested deliverables and quality criteria are met; complete explicitly requested variants
   before stopping.
5. If the limit is reached with unresolved defects, deliver valid partial results with the defects and remaining work
   identified. Do not label an uninspected or visibly defective output production-ready.

### Failures and Stop Conditions

- Honor provider retry guidance, including `Retry-After`, with backoff and jitter where appropriate. Allow at most three
  generation submissions per candidate in a pass, including retries and fallbacks, unless the user specifies a stricter
  limit. Do not restart the budget when changing providers.
- Retry transient errors only. Do not repeatedly submit invalid parameters, authentication failures, or confirmed credit
  exhaustion. Fix a supported parameter issue before retrying; mark unusable providers unavailable for the remainder of
  the run.
- Notify the user once when a provider is confirmed credit-exhausted. If `stopOnCreditsExhausted=true`, stop generation.
  Otherwise, use an eligible fallback within the remaining limits; if `promptOnProviderCreditExhausted=true`, wait for
  the user's answer before switching. No eligible fallback means partial completion, not a retry loop.
- Treat credit status as unknown unless the tool reports it. An ambiguous timeout does not prove the job failed: check
  its status when possible before risking a duplicate generation.
- Stop for completion, the requested limit, an explicit user stop, or a blocking capability/provider failure. Preserve
  completed outputs and report the actual reason.

## Save Without Collisions

Use `<target>_<imagetype>_<instance>.png`, where `imagetype` is `avatar`, `banner`, or `logo`, and `instance` is the
first free positive integer starting at `1`.

- For one target, use the `brandName` slug if supplied, otherwise the account name slug. Use a lowercase, filename-safe
  slug with no path separators.
- For `kind=both`, keep separate target sets. If a shared `brandName` would give them the same slug, use
  `<brand>-org-<orgname>` and `<brand>-user-<username>`. If the account slugs themselves match, prefix them with `org-`
  and `user-`.
- Never overwrite existing images. Serialize filename selection and saving, or use exclusive file creation, so
  concurrent calls cannot select the same instance. Record each target/type-to-file mapping.
- Prefer PNG when supported. Convert another decoded image format only with available tooling and in accordance with
  that tool's instructions; renaming an extension is not conversion. Preserve alpha transparency. If PNG conversion or
  local saving is unavailable, return the actual supported artifact or download link and explain the limitation instead
  of claiming the requested path exists.
- Record the provider, model if reported, effective prompt/reference inputs, dimensions, and pass for each output when
  available. Do not invent provider metadata or expose credentials in the report.

## Deliver

Return the created images or usable file links, the selected candidates, and concise quality notes. Mention material
assumptions, actual tools/models, any fallback or partial completion, and the stop reason. Include next steps only for
unresolved work or requested further exploration.

Creating assets does not itself authorize publishing them or changing a live GitHub profile. If publication was
requested, follow that existing authorization and the available account tooling.
