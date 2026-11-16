# Procedural rose — validation report

## Result and scope

The rose was rebuilt and executed in **Blender 5.0.1**, with 32 independently editable petals, a connected receptacle, studio lighting, and three orthographic cameras. The supplied files remain unchanged. The design is an interpretation of PDF page 1; the reference provides no scale, rear view, underside, or reliable depth measurements. The selected design size, approximately 80 mm across and 43 mm high, is an adjustable assumption, not a recovered physical measurement.

`rose_optimized.blend` contains the visual master and a separate, hidden manufacturing candidate. In the Outliner, expand `ROSEGEN_Editable_Petals` to edit individual petals. The candidate is `Rose_Manufacturing_Candidate` in `ROSEGEN_Manufacturing_Candidate`; enable its viewport visibility and hide the editable petals/receptacle to inspect it alone. It is excluded from the clay renders to avoid double surfaces.

## Input inspection and original diagnosis

All three PDF pages were rasterized before modeling; the original embedded images were also extracted. Page 1 was consulted repeatedly alongside the trial renders. Pages 2 and 3 document the original sparse layering and pointed overlaps.

The installed Blender 4.3.2 could not read the supplied project. A portable official Blender 5.0.1 build opened it with a newer-file warning (file version 503.31). The inspection found exactly 30 petal meshes, each with 837 control vertices and 780 quads, Solidify followed by Subdivision. The source script was also executed successfully under 5.0.1 and rendered with the same gray material, studio rig, and camera direction used for the new rose. This is a source-generated baseline, not a claim that the old project was saved or rendered in its originating Blender version.

Specific mathematical problems:

- **Radius:** the original integrates `sin(a)` from near-vertical centerlines. Negative inner angles decrease the radius; the explicit `max(r, 0.005)` would collapse samples if reached. Direct evaluation of the default source found a minimum radius of 0.011931 BU and **zero samples at that clamp**, so the actual default problem is the near-vertical, narrow cylindrical construction rather than demonstrated clamp collapse. It creates crowded strips rather than a deliberately wound bud.
- **Angular span and width:** the polar patch uses the same width-growth law throughout. Outer rings share nearly identical spans and profiles; the side truncation of the height profile leaves exposed corners and blade-like overlaps.
- **Length and height:** all petals reuse one interpolated length/angle family. Near-vertical inner petals become tall relative to their tiny radius; the common profile does not independently control the outer bowl and middle-petal proportions. The original source, normalized to diameter 2 BU, had a height near 1.325 BU.
- **Curvature:** the integrated tilt primarily changes flare along a strip. It does not independently specify a broad rounded crest, tucked wings, concave bowl, and winding overlap.
- **Spiral and distribution:** golden-angle placement helps the center, but two perfectly spaced eight-petal outer rings reintroduce repeated seams. `ORDER=1` suppresses most outer-ring variation, and some apparent perturbations in the source are explicitly multiplied by zero.
- **Modifiers:** Solidify precedes Subdivision, with tip thickness reduced to 12% of the base. This can soften broad panels while retaining very thin, vulnerable corners. Subdivision cannot repair the underlying profile or nesting.

## Implemented geometry

The new generator uses explicit positive radial distributions and independent bud, middle, and guard-petal parameter families. The bud radius progresses nonlinearly to concentrate its smallest coils; its innermost lips sit slightly below the surrounding bud instead of forming a central spike. Continuous nonuniform divergence avoids explicit uniform rings.

Each surface is a smooth wrapped patch. Its radial path forms a bowl; vertical growth is controlled separately. A broad arch, lowered wings, inward side tuck, and a small radial winding ramp establish overlaps. Low-frequency sculpting, deterministic height/angle variation, and mixed-frequency lip undulation add restrained irregularity. Subdivision precedes Solidify, followed by a small bevel for rounded lips. Solidify uses a constant normal offset; even-offset compensation was disabled after an outline experiment exposed excessive miter offsets near compressed wing roots. The smallest bud petals taper in thickness to avoid crowding the center.

A rounded, flat-bottomed receptacle connects the rooted petals. It supports the candidate union and broadens the bottom silhouette without replacing the visible petal walls.

## Render iterations and visual comparison

Eight preview revisions were executed, using perspective, top, and low side views as appropriate. The available trial renders were visually inspected during refinement. Changes included raising and widening the guards, reducing the radial lip ramp, tucking side wings, broadening the base, increasing gentle rim irregularity, and lowering the innermost bud lips. A compressed-wing outline experiment was rejected after its render exposed a modifier-induced scale error. The final full build uses the corrected normal offset, rounder wing outline, recessed bud profile with nearly level curled lips, and lower guard roots that conceal the receptacle band.

The final top, perspective, and low side images are actual Cycles renders: 1,000 × 1,000 pixels, up to 48 adaptive samples, denoising, neutral gray clay, broad area lights, and controlled orthographic projections. The perspective camera elevation is approximately 32°, and the low side camera elevation approximately 10°. `rose_comparison.png` places the supplied reference and the final perspective render side by side. It is a labeled documentation composition of actual images, using only reference pixels and actual render pixels, without image synthesis or retouching. The comparison uses uniform image resizing; it does not geometrically warp either rose.

Visual judgments:

| Criterion | Result relative to original and reference |
|---|---|
| Center | More closely spaced nested coils and a small, occupied center; the reference still has less regular folded lips. |
| Outer curvature | Deeper upright cup walls and a broader rounded base; the original's exposed flat crossing panels are reduced. |
| Layer density | More continuous nesting, with independent anatomical distributions; some repeated bowl-like arcs remain. |
| Silhouette | Predominantly circular in top view, with about 5% axis variation; reference lobe positions are not replicated individually. |
| Proportions | Chosen height/diameter ratio is approximately 0.54; this is plausible from the photograph, not an exact measurement. |
| Edge softness | Rounded solid lips and subtle waviness replace many thin sharp corners; some side seams remain more geometric than the reference. |

No numerical image-similarity score is asserted. Camera calibration, occlusion, material texture, and lighting are unknown, so a pixel metric would not establish geometric accuracy. The reference's larger irregular folds, local petal dents, asymmetric edge rolling, and rougher surface are not fully reproduced. Hidden geometry is inferred. The final result is visibly fuller and more closely cupped than the source baseline, but it is not an exact sculptural copy.

## Main procedural controls

All controls are in `PARAMS` near the top of `rose_optimized.py`.

| Control | Default | Effect |
|---|---:|---|
| `bud_petals`, `middle_petals`, `guard_petals` | 11, 13, 8 | Independent region counts |
| `diameter_mm`, `height_mm` | 80, 43 | Calibrated envelope; modifier effects introduce a small diameter tolerance |
| `bud_tightness` | 1 | Inverse bud radial scale |
| `petal_length`, `petal_width` | 1, 1 | Relative rise profile and angular breadth |
| `concavity`, `vertical_curvature` | 1, 1 | Radial bowl and vertical progression |
| `edge_curl`, `edge_waviness` | 1, 1 | Rolled rim and irregular lip height |
| `layer_overlap` | 1 | Multiplies angular overlap |
| `organic_variation` | 0.85 | Seeded geometric variation |
| `thickness_mm` | 0.65 | Maximum master thickness; smallest bud petals are thinner |
| `seed` | 23 | Fixed deterministic randomness |
| `resolution_u`, `resolution_v` | 40, 64 | Surface control-grid resolution |
| `subdivision` | 1 | Smooth surface level |
| `manufacturing_voxel_mm` | 0.32 | Candidate union resolution |

Height is normalized after generation, so length/vertical-curvature controls change the relative profile within the specified overall envelope. Very extreme parameter values can create self-intersections; the defaults are the tested configuration. With unchanged parameters and seed, the mathematical generation is deterministic; bit-identical rendering/remeshing across Blender versions or hardware is not promised.

## Mesh and export validation

The evaluated editable master measures **75.984 × 80.032 × 43.000 mm**. Across the evaluated separate solids it has zero boundary and non-manifold edges. Those closed solids intentionally intersect at roots and overlaps; the editable model is not a Boolean union.

For the candidate, evaluated petal thickness is raised to at least 0.48 mm to reduce loss of tiny bud features. Voxel union combines all petal solids and the receptacle at 0.32 mm. Gentle smoothing reduces voxel stepping. 14 secondary eight-vertex shells were removed, leaving the largest connected surface; these were voxel-scale artifacts. Face orientation was recalculated.

Measured candidate findings:

- 784,338 vertices; 784,400 polygons.
- **One connected component**; zero open boundaries, non-manifold edges, wire edges, or detected zero-area faces.
- Positive signed volume: **32,905.744 mm³**, approximately 32.91 mL.
- Envelope: **75.814 × 79.862 × 42.927 mm**.
- STL export: 1,568,800 triangles, with coordinates explicitly scaled to **millimeters**. STL has no embedded unit metadata.

The saved `.blend` was reopened in a separate Blender process. It contained 32 anatomical petals, the candidate, receptacle, three cameras, three lights, and studio floor: 41 generated objects. The exported STL was independently reimported with mesh validation: 784,338 welded vertices, zero non-manifold/boundary edges, the same measured dimensions, and positive volume (32,905.585 mm³; triangulation accounts for the small difference).

The script was also run twice in one Blender process in a no-render preview configuration. Each rebuild contained exactly 40 generated objects (the solid candidate is intentionally skipped in preview mode), with no duplicated petals. Static compilation passed. Raw measurements are included in `mesh_validation.json` and `reopen_validation.json`.

Voxel union removes ordinary overlapping internal petal surfaces, and removing secondary shells avoids enclosed disconnected surfaces. A rigorous computational certificate of no triangle self-intersections, a complete cavity accessibility analysis, and wall-thickness metrology were not performed. Closed manifold topology is therefore the verified claim, rather than unconditional manufacturing suitability.

## Chocolate mold limitations

Deep nested lips, outward curls, and narrow grooves present substantial undercuts for a simple axial pull. A face-normal screen found approximately 37.8% of candidate surface area above the foot facing substantially downward. This includes petal undersides and is an orientation-based warning proxy, not a ray-tested undercut percentage or a draft analysis.

A flexible food-safe silicone mold, split mold, or redesigned draft and relief may be needed. Thin lips, delicate central coils, air traps, chocolate breakage, minimum tooling radii, shrinkage allowance, parting lines, and sanitation of narrow recesses require tooling review. The candidate was separately rendered at 600 × 600 pixels and visually inspected (`rose_manufacturing_preview.png`). The main grooves and cup shape remain visible; small central coils are softened and some lips show voxel-scale irregularity. The finest bud details and grooves can be softened or merged by the 0.32 mm union. Keep the editable master as the visual authority. Do not treat the STL as production approved.

## Rerunning

Use Blender 5.0.1 or a compatible 5.x build (newer versions were not tested):

```sh
blender --background --threads 3 --python rose_optimized.py
```

By default all generated files are written beside the script. Set `ROSE_OUTPUT_DIR` to change the destination. The script creates its own `Rose_Optimized` scene and reserves the `ROSEGEN_` collection prefix; reruns replace those generated collections and that scene while preserving unrelated scenes. Save unrelated work before using reserved generated names.

Fast visual preview:

```sh
ROSE_PREVIEW=1 ROSE_RESOLUTION=720 ROSE_SAMPLES=24 ROSE_VIEWS=perspective blender --background --python rose_optimized.py
```

`ROSE_PREVIEW=1` skips the manufacturing mesh and STL. `ROSE_VIEWS=''` skips rendering for a geometry check. Default output includes all three views, the `.blend`, STL, and machine-readable mesh diagnostics. The labeled comparison and review screenshots are documentation artifacts assembled/captured separately.

## Evidence capture and delivery location

The included review screenshots are browser captures of the actual saved render gallery and reference comparison. Native Blender UI capture under the headless display returned blank frames; those rejected frames are not deliverables. The project was independently opened and its contents validated through Blender itself.

Files were saved in `/workspace/output`, the writable output directory of this execution environment. The chat-configured `/codex/browser/projectless/0003-files-mentioned-by-the-user-uploaded-file-pointe/output` location could not be created because `/codex` is outside the writable operating-system filesystem.
