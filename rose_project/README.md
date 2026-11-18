# Procedural rose project

Reference-led rose built and tested in Blender 5.0.1, with 32 editable petals and a separate consolidated manufacturing candidate.

## Downloads and files

- [Complete final ZIP](output/rose_project_final.zip)
- [Editable Blender project](output/rose_optimized.blend)
- [Blender Python generator](output/rose_optimized.py)
- [Top render](output/rose_top.png), [three-quarter render](output/rose_perspective.png), and [low side render](output/rose_side.png)
- [Reference comparison](output/rose_comparison.png) and [before/after comparison](output/rose_before_after.png)
- [Manufacturing candidate STL](output/rose_manufacturing_candidate.stl)
- [Validation report and limitations](output/validation_report.md)
- [Machine-readable mesh validation](output/mesh_validation.json) and [project/STL round-trip check](output/reopen_validation.json)

GitHub may show a download button rather than previewing the larger binary files.

## Rebuild

```sh
blender --background --python rose_project/output/rose_optimized.py
```

The script writes generated outputs beside itself by default; set `ROSE_OUTPUT_DIR` for another destination. It uses Blender's bundled Python and bpy without additional Python packages.

## Validation and manufacturing limits

The saved project was reopened in Blender, and the exported STL was reimported. The candidate has one connected component and zero boundary/non-manifold edges. Its measured size is approximately 75.814 x 79.862 x 42.927 mm. The visual master and candidate were rendered separately and inspected.

The single reference image does not determine hidden geometry or physical scale exactly. Deep grooves, thin lips, and undercuts need a separate mold-release/tooling review; the candidate is not production approved. See the full validation report.

All files under `output/` were copied byte-for-byte from the completed rose output folder, including the original input copies, render review screenshots, diagnostic logs, and ZIP bundles. No pre-existing repository file was changed.
