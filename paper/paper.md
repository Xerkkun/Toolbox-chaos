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

Existing specialized computational ecosystems cover important parts of this workflow. Packages like `XPPAUT` [@ermentrout2002xpp] and `AUTO-07P` are highly established for numerical bifurcation analysis and continuation. `MATCONT` offers comprehensive MATLAB-based continuation workflows, while `PyDSTool` supports hybrid modeling and analysis in Python [@clewley2012pydstool]. In Julia, `DynamicalSystems.jl` provides a performant, modular library for nonlinear dynamics and chaos [@datseris2018dynamicalsystems].

`Fyskode Chaotic Systems Toolbox` does not compete with nor intend to replace these advanced mathematical toolsets. General-purpose libraries like `SciPy` [@virtanen2020scipy] or `DynamicalSystems.jl` require writing scripts or notebook pipelines, which can pose a steep learning curve for students and educators. Similarly, bifurcation tools like `AUTO-07P` require manual script setup and compilation.

The contribution of `Fyskode Chaotic Systems Toolbox` is complementary and focused: it packages an interactive, offline desktop educational interface organized around a closed, curated catalog of dynamical systems, literature-referenced materials, and built-in numerical diagnostics. This structure is specifically geared toward the study of multistability, hidden oscillations, coexisting attractors, no-equilibrium systems, and chaotic flows from the literature [@sprott1993strange; @sprott1994simple; @wang2021chaotic]. It provides a rapid prototyping environment for reproducing figures, verifying initial configurations, and inspecting numerical results without the overhead of programming custom scripts.

# Software design

The software is structured as a Python/PyQt6 desktop application with a separate numerical core. This design choice favors a local GUI, offline classroom use, and clean packaging. The registry-backed system catalog separates system equations, default parameters, dimensions, and visual configurations from the UI orchestrator. A compiled native C library backend (`core/csrc/chaos_core.c`) is used to accelerate trajectory integrations and grid-based basin calculations where available, while Python components manage UI plotting, diagnostics, documentation rendering, and figure export.

The primary scientific contribution is the local numerical environment centered on a closed catalog of chaotic systems. It allows users to estimate Lyapunov exponent spectra, sweep parameters for bifurcation screening, perform Fast Fourier Transform (FFT) analysis, identify coexisting attractors, and visualize trajectory portraits in 2D or 3D. The current mathematical language is deliberately conservative: the toolbox produces numerical approximations that serve as computational evidence, but it does not claim automatic mathematical proof or formal certification of hidden attractors or chaotic states.

Complementing this, the Sprott Explorer acts as an educational and computational preservation tool. It modernizes the exploration of historical chaotic models inspired by Julien C. Sprott's publications. The Sprott Explorer can parse and simulate equations defined in user-local `.DIC` dictionary files. This module strictly respects copyright: no proprietary book disk files, databases, book figures, or executables are redistributed.

Planned future extensions include a controlled UI editor to register arbitrary custom systems, support for fractional-order chaotic dynamics, and native installer builds for macOS and Linux (which currently rely on build scripts). These planned features are treated as future scope and are not promised as present capabilities.

# Research impact statement

The Fyskode Chaotic Systems Toolbox has been utilized in dynamic systems research workflows and manuscripts as an auxiliary tool to generate dynamic visualizations and compute numerical diagnostics, including phase space portraits, time series, FFT spectra, Lyapunov exponent estimations, bifurcation diagrams, and coexisting basins of attraction. Its primary research impact is practical and scientific: it provides a standardized, reproducible platform for inspecting and comparing chaotic systems documented in the literature, particularly in the study of multistability and hidden attractors [@leonov2013hidden; @dudkowski2016hidden]. 

By providing a frozen release snapshot archived on the Open Science Framework (OSF) with persistent DOI [@moreno2026fyskode], researchers can reference a specific computational state of the toolbox, enhancing the reproducibility of numerical figures in chaotic literature. 

The software package contains an automated test suite verifying UI construction, Sprott parsing rules, catalog extraction, and packaging metadata. Comprehensive documentation guides are provided for installation, reviewer workflows, research use, reproducible examples, and platform packaging. GitHub serves as the active development repository for review, issue tracking, and testing history (archived at DOI [10.17605/OSF.IO/GQMJR](https://doi.org/10.17605/OSF.IO/GQMJR)).

# AI usage disclosure

Generative AI tools, including OpenAI ChatGPT and Codex-style coding assistance, were used to support refactoring, documentation drafting, packaging scaffolding, test scaffolding, and review of wording. The author reviewed and edited the AI-assisted outputs, retained responsibility for scientific claims and licensing decisions, and verified code changes through local tests and repository-specific validation commands. AI tools were not used to make independent scientific judgements about whether an attractor is mathematically certified as hidden or chaotic.

# Acknowledgements

The toolbox builds on open-source scientific Python and Qt software. The Sprott Explorer is an independent educational reimplementation inspired by Julien C. Sprott's published work and does not redistribute original protected disk files, dictionaries, executables, or book figures. No external funding is declared in this draft.

# References
