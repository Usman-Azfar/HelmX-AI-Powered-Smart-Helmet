# Security policy

## Supported versions

Only the latest revision of the active repository branch receives security fixes. Historical
checkpoints and experiment snapshots are research artifacts and are not supported releases.

## Reporting a vulnerability

Use the repository's **Security > Report a vulnerability** workflow to open a private GitHub
Security Advisory. If private reporting is unavailable, contact a repository maintainer without
including exploit details in a public issue.

Do not disclose a vulnerability publicly before a fix or documented mitigation is available.

Include the affected commit, environment, reproduction steps, impact, and any proposed mitigation.
Maintainers will acknowledge the report when available, assess it, and coordinate disclosure after
a fix exists. This volunteer research project does not promise a fixed response-time service level.

## Scope

This policy covers vulnerabilities in:

- the camera runtime and alert path;
- training, export, quantization, and offline inference;
- dependencies and packaging configuration;
- archive extraction, manifest paths, and downloaded model assets;
- unintended retention or disclosure of camera-derived data.

Public model-quality disagreements, research limitations, and feature requests are not security
vulnerabilities; use the regular issue templates for those topics.

## Safety boundary

HelmX is a driver-monitoring research system, not a certified safety-critical product. A security
fix does not imply automotive, medical, regulatory, or operational certification.
