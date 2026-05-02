# Contributing to DownAtTheBottomOfTheMoleHole

Thank you for your interest in contributing! This document outlines the conventions and
workflows used across all org repositories.

## Table of Contents

- [Contributing to DownAtTheBottomOfTheMoleHole](#contributing-to-downatthebottomofthemolehole)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [Getting Started](#getting-started)
  - [Branch Naming](#branch-naming)
  - [Commit Messages](#commit-messages)
  - [Pull Requests](#pull-requests)
  - [Reporting Issues](#reporting-issues)
  - [Security Vulnerabilities](#security-vulnerabilities)

## Code of Conduct

All contributors are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository.
2. Clone your fork locally.
3. Create a branch using the naming convention below.
4. Make your changes, ensuring they pass linting and tests.
5. Commit using conventional commit messages.
6. Open a pull request against `main` using the appropriate PR template.

## Branch Naming

Use the format `<type>/<short-description>` — for example:

| Type | Example |
| --- | --- |
| `feat/` | `feat/add-oauth-support` |
| `fix/` | `fix/null-pointer-on-empty-input` |
| `docs/` | `docs/update-setup-guide` |
| `refactor/` | `refactor/extract-auth-middleware` |
| `chore/` | `chore/update-dependencies` |
| `ci/` | `ci/add-scorecard-scan` |
| `release/` | `release/v2.1.0` |

## Commit Messages

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/)
specification. Gitmojis are encouraged but optional.

**Format:** `<gitmoji> <type>(<scope>): <short description>`

```text
✨ feat(api): add rate-limiting middleware
🐛 fix(auth): handle expired token refresh correctly
📝 docs(readme): add environment variable reference
```

| Gitmoji | Type | When to use |
| --- | --- | --- |
| ✨ | `feat` | New feature |
| 🐛 | `fix` | Bug fix |
| 📝 | `docs` | Documentation only |
| 💄 | `style` | Formatting, no logic change |
| ♻️ | `refactor` | Refactoring, no feature/fix |
| ⚡ | `perf` | Performance improvement |
| ✅ | `test` | Adding or fixing tests |
| 📦 | `build` | Build system changes |
| 👷 | `ci` | CI/CD pipeline changes |
| 🔧 | `chore` | Miscellaneous maintenance |
| ⏪ | `revert` | Revert a previous commit |
| 🔒 | `security` | Security fix |
| 💥 | `feat!` | Breaking change (append `!` after type) |

**Rules:**

- Subject line must not exceed 100 characters.
- Use the imperative mood: _"add feature"_ not _"added feature"_.
- Do not end the subject with a period.
- Add a blank line before the body and footer.
- Reference issues in the footer: `Closes #123`

## Pull Requests

- Select the appropriate PR template from the `.github/PULL_REQUEST_TEMPLATE/` directory
  by appending `?template=<type>.md` to the PR URL, or use the default template.
- Keep PRs focused — one logical change per PR.
- Ensure all status checks pass before requesting review.
- Squash commits when merging unless the commit history is meaningful.

Available named templates:

| Template | URL parameter |
| --- | --- |
| Feature | `?template=feat.md` |
| Bug fix | `?template=fix.md` |
| Documentation | `?template=docs.md` |
| Refactor | `?template=refactor.md` |
| Chore / CI / Build | `?template=chore.md` |

## Reporting Issues

Use [GitHub Issues](../../issues/new/choose) and select the appropriate issue template.
Please search for existing issues before opening a new one.

## Security Vulnerabilities

Do **not** open a public issue for security vulnerabilities. Review our
[Security Policy](SECURITY.md) for responsible disclosure instructions.
