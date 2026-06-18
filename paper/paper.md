---
title: "Fyskode Chaotic Systems Toolbox: a desktop environment for reproducible exploration of chaotic dynamical systems"
tags:
  - Python
  - PyQt6
  - chaos theory
  - dynamical systems
  - hidden attractors
  - multistability
  - scientific visualization
authors:
  - name: Maria Fernanda Moreno Lopez
    affiliation: 1
affiliations:
  - name: Independent researcher
    index: 1
date: 14 June 2026
bibliography: paper.bib
repository: https://github.com/Xerkkun/Toolbox-chaos
---

# Summary

Chaos Toolbox is an open-source desktop application for simulating, analyzing,
validating, and visualizing chaotic dynamical systems. It provides an educational
graphical interface for exploring trajectories, projections, time series,
spectra, bifurcation diagrams, equilibrium information, attraction basins where
supported, Lyapunov diagnostics, and exportable figures. The current software
targets reproducible numerical exploration of integer-order systems and a
curated catalog of systems from the chaos literature, while fractional-order
systems and arbitrary user-defined models are explicitly planned as future
extensions rather than presented as complete current capabilities.

# Statement of need

Research and teaching in nonlinear dynamics often require moving between
equations, numerical simulation, visual diagnostics, and documentation. General
numerical libraries such as SciPy [@virtanen2020scipy] provide high-quality
integration routines, and continuation packages such as AUTO-07P
[@doedel2007auto] and MATCONT [@dhooge2003matcont] support advanced bifurcation
workflows. These tools are powerful, but they are not organized around a
curated, GUI-driven catalog of hidden-attractor and multistability examples for
teaching, inspection, and reproducible figure generation.

Chaos Toolbox fills this gap by combining a closed catalog of supported systems,
documentation, native numerical routines, and interactive visualization panels.
The target users are students, instructors, and researchers who need a practical
environment for reproducing published systems, comparing numerical behavior, and
creating documented exploratory materials without turning each system into a
separate script or notebook.

# State of the field

Existing tools cover important parts of this workflow. XPPAUT [@ermentrout2002xpp]
and AUTO-07P are established for differential equations and continuation.
MATCONT offers MATLAB-based continuation workflows. PyDSTool supports hybrid
models and dynamical-system analysis in Python [@clewley2012pydstool].
DynamicalSystems.jl provides a broad Julia ecosystem for nonlinear dynamics and
chaos [@datseris2018dynamicalsystems]. Chaos Toolbox is not intended to replace
these packages. Its contribution is narrower and complementary: it packages a
desktop educational interface around selected chaotic systems, reference
materials, reproducible graphics, and literature-oriented organization focused
on multistability, coexisting attractors, no-equilibrium systems, stable
equilibrium cases, line or surface equilibrium examples, multiscroll systems,
and Sprott-style polynomial examples [@sprott1993strange; @sprott1994simple;
@wang2021chaotic].

# Software design

The software is implemented as a Python/PyQt6 desktop application with a
separate numerical core. This design favors a rich local GUI, offline teaching
use, and packaging as a desktop application. The registry-backed system catalog
keeps system metadata, defaults, dimensions, and plotting behavior separate from
tab-level UI code. A local C backend is used for performance-sensitive
trajectories and basin calculations where available, while Python components
handle orchestration, diagnostics, documentation views, and export workflows.

The current interface exposes parameters, initial conditions, visualization
controls, FFT, bifurcation, Lyapunov, coexistence, PDF documentation, and a
Sprott Explorer. The Sprott Explorer can load user-local `.DIC` files for
personal exploration, but those files are not redistributed and this mechanism
does not register new systems in the main toolbox. Current hidden-attractor
language is deliberately conservative: the software can reproduce, screen, and
visualize candidates and published examples, but it does not claim automatic
mathematical certification of hidden attractors.

Planned work includes a controlled editor for user-defined systems, YAML/JSON
import and export of new models, more complete fractional-order workflows,
expanded validation contracts, and broader platform packaging. These items are
documented as future scope, not current functionality.

# Research impact statement

Chaos Toolbox is at a pre-submission preparation stage for JOSS. It does not yet
claim external citations or broad external adoption. Its credible near-term
significance comes from the combination of reproducible examples, tests,
packaging work, and documentation already present in the repository. The project
contains tests for UI construction, Sprott code parsing and examples, gallery
behavior, package metadata, and Wang-system catalog extraction. It also includes
Markdown documentation for installation, packaging, licensing, updates, runtime
resources, distribution restrictions, and future custom-system support.
GitHub is the active repository for JOSS review, issues, source code, tests, and
development history. OSF is planned as the persistent archive for the frozen
release snapshot; the archive DOI is pending and will be added only after OSF
assigns it.

The expected impact is practical: instructors can demonstrate chaotic behavior
with a GUI; researchers can inspect and reproduce numerical examples from the
literature; and generated plots can be exported with consistent configuration.
The emphasis on hidden attractors and multistability follows the modern
literature on hidden oscillations and coexisting attractors
[@leonov2013hidden; @dudkowski2016hidden], while maintaining clear separation
between numerical evidence and mathematical proof.

# AI usage disclosure

Generative AI tools, including OpenAI ChatGPT and Codex-style coding assistance,
were used to support refactoring, documentation drafting, packaging scaffolding,
test scaffolding, and review of wording. The author reviewed and edited the
AI-assisted outputs, retained responsibility for scientific claims and licensing
decisions, and verified code changes through local tests and repository-specific
validation commands. AI tools were not used to make independent scientific
judgements about whether an attractor is mathematically certified as hidden or
chaotic.

# Acknowledgements

The toolbox builds on open-source scientific Python and Qt software. The Sprott
Explorer is an independent educational reimplementation inspired by Julien C.
Sprott's published work and does not redistribute original protected disk files,
dictionaries, executables, or book figures. No external funding is declared in
this draft.

# References
