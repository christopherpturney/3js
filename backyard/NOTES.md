# Backyard model — dimensions and assumptions

Source: `source/backyard.skp` (SketchUp for Web), exported to `source/backyard.stl`.
`extract.py` rebuilds `plan.json` from the STL. Units are feet. `plan-check.png` is a
2D render of plan.json for comparison with the SketchUp view.

## Measured from the model (exact)
| Element | Size |
|---|---|
| Whole site | 83.13 x 53.24 ft |
| Deck | 12.49 x 14.07 ft, 160.5 sq ft, angled notch on the south edge |
| Deck stair (east) | 3 treads, each 0.88 x 3.42 ft (10.5 in deep) |
| Shingled roof block | 13.16 x 14.15 ft, 186.3 sq ft |
| Lawn | 1,221 sq ft |
| Stone pavers | 576.5 sq ft (SketchUp labels it 576.7) |
| Mulch beds | 349 sq ft |
| Concrete | 21.87 x 22.46 ft, 370.2 sq ft |
| Junipers | 14, each 2.15 ft across |
| Trees | 2 circles, 2.97 ft and 2.60 ft across |

## Heights confirmed by Chris (2026-09-30)
- Deck surface 2 ft above grade. The east stair steps down to the ground in four 6 in risers (tread tops at 18, 12 and 6 in).
- The shingled block is a sunroom attached to the main house along its south edge. Shed roof: 10 ft above grade at the north eave, rising to 17 ft where it meets the house.

## Still assumed
- Sunroom floor level with the deck; walls inset 1 ft from the roof outline on the north, east and west sides (no overhang on the house side). Door to the deck is 6'-8".
- Mulch beds about 3 in above the lawn; pavers about 1 in; concrete slab flush with pavers.
- Junipers about 2.5 ft tall. Trees are ponderosa pines (the SketchUp material is "Vegetation Bark Ponderosa"), about 35 ft tall, using each circle as the trunk flare.
- The main house is not drawn in the model, so it is left out; the sunroom's south wall stands in for the house wall.
- The notch in the south edge of the deck is open to the ground (no face was drawn there).
- The house is assumed to lie to the south (plan -y). True north is unknown; the sun angle is chosen for looks.
