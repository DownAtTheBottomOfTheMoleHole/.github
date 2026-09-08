---
description: "Create or refine cohesive GitHub avatars, logos, and banners with available image tools"
name: "Generate Brand Imagery"
argument-hint: "kind=<org|user|both> username=<optional> orgname=<optional> brandName=<optional> types=<avatar,banner,logo> runs=<positive max passes; default 1> inspirations=<paths/urls> fonts=<optional> hobbies=<optional> style=<optional> outputDir=<optional>"
agent: "agent"
---

Follow the [Generate Brand Imagery skill](../skills/generate-brand-imagery/SKILL.md) for this request. The skill is the
source of truth for inputs, available-tool selection, iteration limits, quality checks, filenames, and failure handling.

Use the user's arguments and conversation context. Infer optional details, ask only for essential missing information,
and create only the requested targets and image types. The default is one generation pass.

Example:

```text
/generate-brand-imagery kind=both username=rolfmoleman orgname=downatthebottomofthemolehole brandName="Mole Hole Foundry" types=avatar,banner runs=1 style="bronze, black, and gold; cinematic underground forge" outputDir=assets/generated
```
