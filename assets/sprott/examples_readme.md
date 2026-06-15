# Synthetic examples

The examples included with Chaos Toolbox are curated synthetic educational
examples. They are not copied from Sprott's original dictionaries such as
`BOOKFIGS.DIC`, `SELECTED.DIC`, or `SPECIAL.DIC`.

Each public example must explain why it exists. A code alone is not enough:
`learning_goal` says what the learner should understand, and `visual_intent`
says what the figure is supposed to show. Typical roles are depth color, banded
color, 4D projection, method comparison, fixed-orbit failure, divergence, or
improving a weak quick plot with more samples and lower alpha.

Reference: Julien C. Sprott, *Strange Attractors: Creating Patterns in Chaos*,
M&T Books, 1993. Chaos Toolbox is an independent educational reimplementation
and does not redistribute Sprott's historical software, disk files,
dictionaries, figures, or long book text.

## Public thumbnail generation

Run this after changing `assets/sprott/examples/synthetic_examples.json`:

```powershell
python tools/generate_sprott_example_thumbnails.py
```

The script simulates every synthetic example, renders a PNG into
`assets/sprott/examples/thumbnails/`, and updates each JSON `thumbnail` field
to `examples/thumbnails/<id>.png`.

## Candidate review workflow

Use the finder to create review material outside public assets:

```powershell
python tools/find_sprott_synthetic_examples.py --kind map --dimension 3 --attempts 120 --count 8
```

It writes `external/sprott_candidate_examples/candidates.json` and optional
review thumbnails. Those files are local review artifacts, not curated public
examples.

After editing a candidate's `learning_goal`, `visual_intent`, parameters, and
style, promote selected records:

```powershell
python tools/promote_sprott_synthetic_examples.py --candidates external/sprott_candidate_examples/candidates.json --ids candidate_i_123456
python tools/generate_sprott_example_thumbnails.py
```

## Local `.DIC` files

Use the Sprott Explorer import and examples tabs to select a local folder
containing references that you have downloaded yourself. The toolbox indexes
those files in place and does not copy them into the repository.

External `.DIC` codes loaded by the user should be treated as local external
references. Images generated from user-local `.DIC` codes should be saved in
the local Sprott gallery under the user's application-data folder, not in this
public `assets/` tree.

## Special Families Implemented

This project implements the following special-function families:
- **Y**: Absolute value maps ($D=4, M=10$).
- **`[`**: Power of absolute value maps ($D=4, M=14$).
- **`\`**: Sine maps ($D=4, M=18$).
- **`]`**: Rotational sine maps ($D=4, M=6$).
- **`^`**: Forced oscillator maps ($D=4, M=9$).
- **Z**: AND/OR special family ($D=4, M=10$) is recognized but remains pending semantics validation.

All implemented special families are simulated using a robust Python/NumPy backend and can be fully analyzed, visualized, and filtered.
