# Public Documentation Policy

This policy defines how public documentation for Fyskode Chaotic Systems Toolbox should be written, reviewed, and maintained.

The goal is to keep public-facing documentation neutral, useful, and current. Public documentation should describe the present state of the toolbox, not the internal development history, research strategy, unfinished editorial plans, or private implementation discussions.

## Scope

This policy applies to public or repository-visible documentation, including:

- `README.md`
- release notes and changelogs
- files under `docs/`
- packaging notes intended for users
- public website content
- GitHub release descriptions
- public examples and tutorials

It does not prevent private planning notes, local development logs, or unpublished research notes from existing outside public documentation. Those materials should remain local, ignored, or clearly separated from user-facing documentation.

## Core Rule

Public documentation must answer one of these user-facing questions:

- What is this software?
- What can it do now?
- How do I install or run it?
- What systems, tools, or workflows are currently supported?
- What files are included in the public repository or release package?
- What are the scientific, numerical, legal, or distribution limits that users need to know?
- How should the software be cited, licensed, or redistributed?

If a paragraph does not help a user install, run, understand, cite, or safely use the current toolbox, it should not be in public documentation.

## Allowed Content

Public documentation may include:

- a concise project description;
- current features and supported modules;
- installation and execution commands;
- current repository structure when it helps users navigate the project;
- supported systems and numerical diagnostics;
- distribution and packaging policy;
- copyright, license, and citation information;
- limitations needed for correct scientific or legal interpretation;
- examples that run with the current public repository;
- links to maintained documentation and release artifacts.

## Prohibited Content

Public documentation must not include:

- internal development conversations;
- AI/Codex/ChatGPT prompts or traces;
- editorial strategy for papers, journals, or submissions;
- historical explanations of previous repository states unless required for migration;
- obsolete folder descriptions;
- local absolute paths or private machine paths;
- references to untracked local folders as if they were public content;
- internal audit counts, freeze-audit numbers, or CI details unless they are part of a dedicated technical validation record;
- repeated warnings that do not add new information;
- overclaims about mathematical proof, scientific certification, or reproduction;
- undocumented future promises presented as current functionality.

## Scientific Wording

The toolbox is a numerical and visual tool for chaotic dynamical systems. Numerical diagnostics should be described as computational evidence, not as automatic mathematical certification.

Use neutral language such as:

> The toolbox provides numerical diagnostics for trajectory exploration, bifurcation screening, Lyapunov estimation, spectral analysis, and attraction-basin visualization where supported.

Avoid overclaims such as:

> The toolbox proves chaos.
>
> The toolbox certifies hidden attractors.
>
> The toolbox reproduces all published systems.
>
> A plotted attractor is formal proof.

A single scope statement is enough in most user-facing documents:

> Numerical outputs produced by the toolbox are computational evidence and do not represent automatic mathematical proof.

Do not repeat the same warning in every section.

## Current-State Writing

Describe the current project state directly.

Prefer:

> The toolbox includes trajectory views, time series, FFT panels, bifurcation sweeps, Lyapunov diagnostics, attraction-basin grids where supported, and the Sprott Explorer.

Avoid:

> The project was previously reorganized to include...
>
> Earlier versions used...
>
> This was added after an audit...
>
> The next paper will...

Historical notes should be kept only when they are necessary for migration, compatibility, or release interpretation.

## Public Website Policy

Website pages should be shorter and more user-centered than technical repository files.

A public website page may include:

- what the toolbox is;
- who it is for;
- supported workflows;
- screenshots or visual examples;
- download or installation links;
- links to documentation and GitHub;
- license and distribution boundaries;
- a short scientific scope note.

A public website page should not include:

- internal cleanup notes;
- long repository hygiene details;
- paper or journal strategy;
- development audit history;
- private folder names;
- repeated warnings;
- detailed CI or test-count narratives.

## Release Notes Policy

Release notes should be concise and technical.

Recommended structure:

```markdown
## Summary

Short description of the release.

## Added

- New user-visible feature.

## Changed

- User-visible change.

## Fixed

- User-visible fix.

## Notes

- Relevant compatibility or distribution note.
```

Release notes should not mention private plans, editorial strategy, or local development history.

## Distribution And Third-Party Material

The toolbox must not redistribute third-party material unless the license explicitly permits it and the repository records the permission clearly.

For the Sprott Explorer and related educational material:

- do not bundle original copyrighted disk files, `.DIC` databases, book figures, proprietary code, or long book excerpts;
- allow users to load their own local `.DIC` files only for personal runtime exploration;
- do not copy local `.DIC` files into the installed package or repository;
- include only generated, licensed, or permitted assets in public releases.

## Documentation Review Checklist

Before committing public documentation, check:

- Does this describe the current public project state?
- Does this help a user install, run, understand, cite, or safely use the toolbox?
- Are all paths public and repository-relative?
- Are claims scientifically conservative?
- Are warnings centralized instead of repeated?
- Are third-party materials described without redistributing restricted content?
- Are future features clearly marked as planned or omitted?
- Is the language neutral and free of internal development history?

## Standard Instruction For Documentation Edits

Use this instruction when asking an automated coding assistant to modify documentation:

```text
Apply the public documentation policy before editing.
Describe only the current public state of the project.
Do not include internal conversations, AI/Codex/ChatGPT traces, editorial strategy, journal plans, obsolete folder descriptions, private paths, or repeated warnings.
Keep scientific claims conservative and user-facing.
If a warning is necessary, write it once in a scope or limitations section.
If a note is only useful for internal planning, do not place it in public documentation.
```
