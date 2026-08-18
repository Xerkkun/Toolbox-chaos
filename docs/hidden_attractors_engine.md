# Hidden Attractors FO engine integration

## Responsibility boundary

Toolbox Chaos is the visual, no-code product. Hidden Attractors FO is the scientific computation engine. The GUI must not grow a second independent implementation of every numerical method.

```text
Toolbox Chaos
  forms, guided workflows, linked plots, Sprott explorer, export
        |
        v
core.hidden_engine
  capability discovery and GUI-safe adapters
        |
        v
Hidden Attractors FO
  system contracts, solvers, analysis, validation, provenance
```

`hidden-attractors-fo>=1.1,<2` is a normal runtime dependency. The bridge loads
it lazily so an incomplete or incompatible installation can be reported in the
desktop diagnostics instead of aborting during module import. Engine-backed
actions are disabled with that explicit error; there is no alternate solver or
checkout-path fallback.

## Exposed engine capabilities

- safe expression-defined flows and maps;
- structured simulation results;
- no-code Lorenz, Rossler, and logistic-map examples;
- JSON import/export;
- shared Welch PSD and amplitude-spectrum calculations;
- explicit trajectory-only evidence boundary;
- integer-order alignment and covariant-vector adapters where the engine advertises them;
- multi-term Caputo and tempered-history adapters with explicit capability errors;
- integration and UI tests.

Source, wheel, and frozen-application builds resolve the installed Python
distribution. PyInstaller explicitly collects the engine modules and package
metadata. A missing capability fails with its name and version contract rather
than importing code from another checkout.

## Migration rule

New general numerical capabilities should be implemented and validated in Hidden Attractors FO first, then exposed in Toolbox Chaos through a narrow adapter and a guided visual workflow. System-specific educational presentation may remain in the GUI; canonical equations and analysis algorithms should not be duplicated.
