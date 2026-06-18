# Custom Systems Future Scope

Fyskode Chaotic Systems Toolbox 0.1.0 is developed by Maria Fernanda Moreno Lopez (Fer Moreno) and distributed under the MIT License.

This version does not implement complete creation or registration of new chaotic systems from the main UI. The main toolbox uses a closed catalog of systems supported by the application and by the numerical backend. Users can modify parameters, initial conditions, integration options, and visualization controls for the systems already available.

## Existing Exception

The Sprott Explorer can load local `.DIC` files selected by the user for personal exploration. This is not the same as registering a new complete system in the main toolbox. Local `.DIC` files are not redistributed, not copied into the installed package, and not treated as bundled runtime assets.

## Planned Future Scope

Custom-system support is planned for a future version and should include:

- equation editor from the UI;
- variable and dimension definition;
- configurable parameters;
- initial conditions;
- syntax validation;
- generic numerical integration;
- automatic 2D portraits;
- optional 3D attractor support when dimension equals 3;
- time series for arbitrary dimension;
- configurable bifurcation diagrams;
- YAML/JSON import and export;
- clear warning when custom systems do not use the optimized C backend initially.

## Packaging Impact

Future custom-system definitions should live in user configuration or user data folders, not in the installed application directory. Updates must preserve those definitions, generated results, external resource paths, and local Sprott files.

Numerical results are computational evidence, not automatic mathematical proof.
