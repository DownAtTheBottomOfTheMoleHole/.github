---
description: "Generate logo, avatar, and banner assets for a GitHub org/user with iterative MCP image runs"
name: "Generate Brand Imagery"
argument-hint: "target=<org-or-user> kind=<org|user|both> runs=<n> inspirations=<optional image paths/urls> fonts=<optional list> hobbies=<optional list> style=<optional colors + art direction>"
agent: "agent"
---

Generate production-ready brand images for a named GitHub organization and/or named GitHub user.

Use this exact workflow.

## Inputs

Read and normalize the arguments below. If an argument is missing, ask one concise question, then continue.

- `target`: organization or username base name used in output files.
- `kind`: one of `org`, `user`, `both`.
- `runs`: max iteration count.
- `inspirations`: optional list of inspiration image paths or URLs.
- `fonts`: optional list of preferred font family names.
- `hobbies`: optional list of hobbies/interests to influence symbols and motifs.
- `style`: optional style direction including colors, tone, materials, and composition cues.
- `outputDir`: optional output folder, default `assets`.
- `stopOnCreditsExhausted`: default `true`.
- `respectRateLimits`: default `true`.

## Goal

Per run, generate all requested image types:

- avatar
- banner
- logo

Use a combination of all available image generation/editing tools and MCP image servers that are accessible in the current environment.

## Hard Rules

- Never overwrite any existing image.
- Use the file naming convention: `<target>_<imagetype>_<instance>.png`.
- Valid `imagetype` values: `avatar`, `banner`, `logo`.
- `instance` starts at `1` and increments (`2`, `3`, ...).
- If a file already exists, skip that exact filename and choose the next free instance.
- Prefer PNG outputs. If a tool returns JPEG/WebP, convert to PNG while preserving quality.
- Respect platform and provider rate limits. Back off and retry with jitter when needed.
- Stop early if MCP/image credits are exhausted and report partial completion.
- Keep all generated content policy-compliant and avoid direct style mimicry of living artists.
- text is permitted but only from tools that support it natively, and only if explicitly requested in the `style` input. Do not embed text in logos or avatars unless specified.
- When using inspiration images, do not copy distinctive elements that would violate copyright or create confusion with existing brands. Use them as loose references for style and composition instead.
- For logos, focus on strong, simple shapes that scale well. Avoid excessive detail or gradients that may not reproduce clearly at small sizes.
- For avatars, prioritize clear facial features or symbolic representations that read well at small sizes. Avoid cluttered designs.
- For banners, leverage the wider canvas to create more detailed and atmospheric compositions that convey the brand identity and tone. Consider how the banner will look on different screen sizes and ensure key elements are visible and not cropped out.

## Prompt Construction

For each target and image type, build a structured prompt from:

- core identity: org/user name and role
- visual traits: optional hobbies/interests mapped to iconography
- typography: optional font inspirations (do not require exact licensed font use)
- style system: palette, contrast, texture, mood, lighting
- composition: framing suitable for image type (avatar square, banner wide, logo scalable)
- constraints: no embedded text unless explicitly requested

When inspiration images are supplied, use image-to-image or reference-capable tools where supported.

## Iteration Plan

For `runIndex` from 1 to `runs`:

1. Generate candidate avatar/logo/banner set.
2. Save files to the first available non-conflicting names.
3. Validate dimensions and basic quality:
   - avatar: square, recommended >= 1024x1024
   - logo: square or portrait-safe, recommended >= 1024 px on shortest side
   - banner: wide, recommended 1536x640 or better
4. If quality is weak, refine prompt and regenerate only weak outputs in the next run.
5. Check rate-limit and credit status before each tool call group.

## Tooling Strategy

- Prefer parallel generation when safe.
- Diversify across available models/tools to increase variety.
- Reuse successful prompt fragments between runs.
- Log which tool/model produced each file.

## Required Output

Return a concise report with:

- normalized input values
- tools/models used
- files created (full relative paths)
- skipped filenames due to existing files
- run-by-run notes and quality observations
- whether stopped by run limit, success, or credit exhaustion
- next suggested run arguments for improved results

## Example Invocation

`/generate-brand-imagery target=downatthebottomofthemolehole kind=both runs=4 inspirations="assets/reference/org.png,assets/reference/user.png" fonts="Cinzel,Metal Mania" hobbies="mining,metal music,retro games" style="bronze black gold, gritty cinematic, high contrast" outputDir=assets`
