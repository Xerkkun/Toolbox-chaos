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

The bridge loads lazily so the desktop window can start even when the optional engine is unavailable. The GUI displays the availability result instead of silently falling back to scientifically different behavior.

## First implemented slice

- safe expression-defined flows and maps;
- structured simulation results;
- no-code Lorenz, Rossler, and logistic-map examples;
- JSON import/export;
- shared Welch PSD and amplitude-spectrum calculations;
- explicit trajectory-only evidence boundary;
- integration and UI tests.

## Release requirement

The development checkout can discover the sibling repository. This is not a distribution strategy. Before shipping this feature, Hidden Attractors FO must publish a version containing the required API, Toolbox Chaos must declare the compatible dependency range, and the pair must pass installation and execution in a clean environment on every supported platform.

## Migration rule

New general numerical capabilities should be implemented and validated in Hidden Attractors FO first, then exposed in Toolbox Chaos through a narrow adapter and a guided visual workflow. System-specific educational presentation may remain in the GUI; canonical equations and analysis algorithms should not be duplicated.
