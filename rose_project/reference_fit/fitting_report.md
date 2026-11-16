# Reference-fitting revision

## Status
This is a further fitting study, not an exact reconstruction. The required “same flower” fidelity has not been achieved. The reference still has more compressed folds, less cylindrical bud walls, broader irregular rolled lips, and different individual occlusion boundaries. No exact count of hidden petals or physical dimensions can be recovered from this single image.

## Changes
The prior generator interpolated all petals through three radial distributions with nearly golden-angle divergence. That enforces an orderly widening and repeating arc spacing regardless of the photograph. Its common wing profile and nearly equal bud lips create open concentric cups.

The replacement uses a table of 24 individually specified radii, crest heights, azimuths, angular spans and rim tilts, plus five explicit transition folds. Placement is no longer governed by a golden-angle sequence. The front guard, back silhouette petals and middle walls have different heights and overlap. Dimensions are an assumed 80 mm envelope and 48 mm height.

The camera faces the foreground directly with an approximately 40-degree elevation. This is a visually chosen view, not a solved camera calibration. The original reference is packed in the blend as a front camera background overlay at 45% opacity. Select Camera_perspective and enter camera view to compare. The reference is not rendered onto the mesh.

## Executed refinement passes
1. Explicit 24-petal arrangement and revised camera. Render inspected: too much separation and shallow foreground overlap.
2. Compressed bud radius and broadened middle spans. Render inspected: some gaps reduced, but individual walls remained too tall and exposed.
3. Raised wing profiles, broader guard spans and offset foreground guard. Render inspected: more continuous walls, but repeated rim arcs still apparent.
4. Five independently placed transition folds added around the bud and middle region to close observed gaps. Final reference and top views saved separately.

The comparison sheet includes the reference and all four rendered passes. These are actual Blender renders; no image synthesis or retouching is used. Improvements are local and qualitative. No numerical similarity claim is made, and the final study should not be represented as meeting the requested literal reconstruction criterion.

## Run
Blender 5.0.1 was used. Run `blender --background --python rose_reference_fit.py`. Keep reference.jpeg beside the script. Default output uses the script directory. `ROSE_RESOLUTION`, `ROSE_SAMPLES`, `ROSE_VIEWS`, and `ROSE_OUTPUT_DIR` control rendering. The default fitting settings are the final revision; earlier previews are retained as evidence.

This revision is a visual master only. The previous manufacturing STL has not been regenerated for this changed geometry and must not be treated as its manufacturing counterpart. Original delivered files are preserved outside this new directory.
