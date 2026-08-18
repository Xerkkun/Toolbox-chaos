# Custom-system editor

The `Crear sistema` tab defines continuous flows or discrete maps with named
variables, numeric parameters, one expression per state variable, and an
initial state. Definitions can be validated, simulated, plotted, imported from
JSON, and exported to JSON.

## Security and numerical boundary

Hidden Attractors FO compiles expressions through a restricted syntax tree.
The parser does not use `eval`, permit imports or attribute access, or expose
arbitrary Python execution. Only documented arithmetic operators and
mathematical functions are available.

The current interface returns a structured trajectory. It does not infer
chaos, attraction, stability, or hiddenness from a plot, and it does not
automatically create a native implementation, equilibrium
classifier, Jacobian, basin contract, Lyapunov analysis, or bifurcation sweep.
Those controls stay unavailable for a custom definition rather than silently
substituting a different calculation.

Toolbox Chaos owns the forms, interaction, visualization, project files, and
user guidance. The installed `hidden-attractors-fo>=1.1,<2` distribution owns
safe system definitions and flow/map simulation contracts. If that dependency
or a requested API capability is unavailable, the tab displays a compatibility
error and does not search another checkout.

User definitions belong in user-controlled data folders, not the installed
application directory. Application updates preserve those definitions,
generated results, external-resource paths, and user-owned Sprott files.
