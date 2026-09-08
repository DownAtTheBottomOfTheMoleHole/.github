# AI tooling

The reusable [brand-imagery skill](../.github/skills/generate-brand-imagery/SKILL.md) creates
cohesive avatars, banners and logos. It uses available image tools, respects the user's explicit
run/provider choices, and reports real outputs and incomplete work.
The [Copilot prompt](../.github/prompts/generate-brand-imagery.prompt.md) delegates to the skill.

## Discovery

- Copilot loads the canonical skill from `.github/skills/` and the prompt from `.github/prompts/`.
- Codex loads repository guidance from `AGENTS.md` and the relative skill link under `.agents/skills/`.
- The private companion repository holds infrastructure, Azure DevOps and review assets.
  Its organisation agents use root `agents/` for GitHub discovery after merge.
- Select an available model and connect image tools in the client. Repository instructions cannot
  grant tool access, change account limits, or configure authentication automatically.

Try a request such as: “Generate one avatar, logo and banner for DownAtTheBottomOfTheMoleHole,
bronze and gold on black, no text, one run.” Verify the skill is visible in the client's skill
selector and that the output report links to files actually created. If no image tool is connected,
the workflow should produce reusable prompts and identify the missing capability.

To reuse this in another repository, copy the skill directory and the prompt while preserving
`.github/skills/` and `.github/prompts/`. For Codex, also create the matching relative
`.agents/skills/generate-brand-imagery` link. Review existing destination files first.
Use the skill directly in clients that do not support VS Code prompt files.

## Validation

Edit canonical files in `.github/`, then run:

```sh
python3 tools/sync_ai_assets.py
python3 -m pip install -r tools/requirements-dev.txt
python3 tools/validate_ai_assets.py
python3 -m unittest discover -s tests -v
```

The sync command creates missing Codex discovery links and can maintain organisation agent copies
if agents are added. `--check` reports drift without writing. It reports unexpected existing
skill directories and orphan assets for explicit resolution. On Windows, use a Git checkout
with symlink support; text files containing symlink targets do not provide skill discovery.

The `Validate AI assets` workflow runs the offline checks on pull requests and pushes to `main`.
Checks cover metadata, explicit local Markdown links, discovery drift and regression scenarios.
They do not generate images, consume provider credits, or verify live provider authentication.

## Historical image scripts

`assets/scripts/` contains one-off branding experiments, not the reusable skill backend.
Several use fixed output names, machine-specific reference paths or optional local model files.
The old Pollinations download scripts accept downloads by byte count and may overwrite fixed
filenames; byte count does not establish that a response is a valid PNG. Inspect and adapt those
scripts before any reuse. The skill uses connected image tools and collision-safe filenames.
Existing generated assets and historical scripts are preserved.

## Sources

- [Codex skill discovery and symlink support](https://learn.chatgpt.com/docs/build-skills)
- [Codex repository guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Copilot skill locations](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [VS Code prompt file support](https://code.visualstudio.com/docs/agent-customization/prompt-files)
- [GitHub organisation agent discovery](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/prepare-for-custom-agents)
