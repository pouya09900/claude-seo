"""Run: blender -b rose_optimized.blend --python verify_rose.py"""
import bpy,bmesh,json,math,os
from pathlib import Path
out=Path(__file__).resolve().parent
scene=bpy.data.scenes['Rose_Optimized'];bpy.context.window.scene=scene
petals=[o for o in scene.objects if o.get('anatomy')];assert len(petals)==32
assert {o.get('anatomy') for o in petals}=={'Bud','Middle','Guard'}
assert all(scene.objects.get('Camera_'+v) for v in ['top','perspective','side'])
ob=scene.objects['Rose_Manufacturing_Candidate'];bm=bmesh.new();bm.from_mesh(ob.data)
assert all(e.is_manifold for e in bm.edges);assert bm.calc_volume(signed=True)>0
info={'reopened':True,'blender':bpy.app.version_string,'petal_count':len(petals),'object_count':len(scene.objects),'candidate_vertices':len(bm.verts),'candidate_faces':len(bm.faces),'candidate_boundary_edges':sum(e.is_boundary for e in bm.edges),'candidate_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'candidate_positive_volume':True};bm.free()
# Independent STL round trip into a separate scene: welding on import is enabled by Blender.
test=bpy.data.scenes.new('STL round trip');bpy.context.window.scene=test
bpy.ops.wm.stl_import(filepath=str(out/'rose_manufacturing_candidate.stl'),use_mesh_validate=True)
stl=bpy.context.object;bm=bmesh.new();bm.from_mesh(stl.data)
info['stl_roundtrip']={'vertices':len(bm.verts),'faces':len(bm.faces),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges),'dimensions_mm':[round(v,3) for v in stl.dimensions],'signed_volume_mm3':bm.calc_volume(signed=True)};bm.free()
assert info['stl_roundtrip']['nonmanifold_edges']==0
(out/'reopen_validation.json').write_text(json.dumps(info,indent=2));print('VERIFIED',json.dumps(info),flush=True)
