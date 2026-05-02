# Governance

This document describes how DownAtTheBottomOfTheMoleHole repositories are maintained,
how decisions are made, and how contributors can take on broader responsibility.

## Scope

This governance model applies to the organization-level standards in this repository
and to repositories that inherit these defaults unless a repository documents a more
specific policy.

## Roles

### Organization Owner

The organization owner has final responsibility for:

- repository creation, archival, and transfer
- security-sensitive changes and disclosure decisions
- branch protection, secrets, and org-wide automation
- appointing or removing maintainers

### Maintainers

Maintainers are trusted contributors with day-to-day responsibility for one or more
repositories. Maintainers are expected to:

- review pull requests in their area of ownership
- keep issues, labels, and milestones in usable shape
- enforce the contribution, security, and release standards defined in this repo
- escalate security, abuse, or policy concerns to the organization owner

### Contributors

Contributors may propose changes through issues, discussions, and pull requests.
Contributors are expected to follow the guidance in [CONTRIBUTING.md](CONTRIBUTING.md)
and the standards in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Decision Making

- Routine changes can be merged after maintainer review and successful checks.
- Changes to shared automation, labels, templates, security policy, release policy,
  or org-wide standards should receive review from the organization owner or an
  explicitly delegated maintainer.
- In the event of disagreement, the organization owner makes the final decision.

## Security and Sensitive Changes

Security issues must follow [SECURITY.md](SECURITY.md). Secrets, credentials,
access-control changes, and disclosure timing are handled privately until a safe
resolution is available.

## Becoming a Maintainer

There is no fixed checklist, but maintainers are typically contributors who have
shown consistent technical judgment, constructive review behaviour, and reliability
across multiple changes.

Potential maintainers are usually invited after they have demonstrated that they can:

- submit high-signal pull requests
- review changes carefully and communicate clearly
- respect project standards and contributor expectations
- handle routine maintenance without close supervision

## Changes to This Policy

Changes to this governance document should be proposed by pull request and reviewed
with the same care as other organization-wide standards.
