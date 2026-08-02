# Custom systems: current capability and next gates

Toolbox Chaos now includes a first no-code system editor in the `Crear sistema` tab. The user can define a continuous flow or discrete map with variables, numeric parameters, one expression per state variable, and an initial state. Definitions can be validated, simulated, plotted, imported from JSON, and exported to JSON.

## Security and numerical boundary

Expressions are compiled by Hidden Attractors FO through a restricted syntax tree. The parser does not use `eval`, does not permit imports or attribute access, and only exposes documented arithmetic operators and mathematical functions.

The current integration produces a structured trajectory result. It does not infer chaos, attraction, stability, or hiddenness from the plot. It also does not automatically create a native optimized implementation, equilibrium classifier, Jacobian, or basin contract.

## Current engine relationship

- Toolbox Chaos owns forms, interaction, visualization, project files, and user guidance.
- Hidden Attractors FO owns safe system definitions, flow/map simulation contracts, and scientific analysis.
- The bridge is optional while the engine release and packaging contract are stabilized.
- During development, the Toolbox can discover a sibling checkout; a public release must use a declared compatible package version and a fresh-install test.

## Next gates

1. versioned JSON schema and migration rules;
2. automatic symbolic or finite-difference Jacobian with provenance;
3. numerical equilibrium search and local stability panel;
4. spectral, Poincare, Lyapunov, and bifurcation analyses for compatible custom systems;
5. background execution, cancellation, progress, and stale-result rejection;
6. quick exploration and full scientific modes;
7. persistent user catalog and literature metadata;
8. optional compilation of profiled systems after numerical equivalence tests.

User definitions belong in user-controlled data folders, not the installed application directory. Updates must preserve definitions, generated results, external resource paths, and user-owned Sprott files.
