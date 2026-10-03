# How the APCO layout was drafted

1. `measurements/1-7.webp`: Google Maps "Measure distance" screenshots from Chris (2026-10-02).
   1: west line 400.36 ft, 2: Route 130 frontage 308.00, 3: east line 355.65,
   4: Municipal Dr frontage 359.64, 5: building SW corner to property SW corner 149.53,
   6: building west face 132.75, 7: along the building's north side 199.12.
2. `markers.json`: measurement endpoint pixels. Images 2-7 share one scale (2.424 px/ft, within 0.3%),
   image 1 is 2.797 px/ft. The red pin tip is the common anchor between screenshots.
3. `mosaic.py`: stitches the screenshots into one scaled aerial, rotated 33.6 deg so the
   building's west face is vertical. `corners.py` least-squares fits the four property corners
   to the four measured sides (corners moved under 2 ft).
4. `../layout.py` holds the traced polygons (building, islands, walks, landscape, drives) -> `../site.json`.
   `../build_plan.py` renders `../index.html`.

Scripts expect the scratch paths they were written with; adjust paths before re-running.
The aerial underlay is Google imagery: fine for internal checking, do not publish it.
