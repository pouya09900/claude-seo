"""Reference-led, editable rose. Tested in Blender 5.0.1; bpy only.
Run: blender --background --python rose_optimized.py
Optional environment: ROSE_OUTPUT_DIR, ROSE_PREVIEW=1 (skip solid), ROSE_SAMPLES,
ROSE_RESOLUTION, ROSE_VIEWS=perspective,top,side. Units: 1 BU = 40 mm by default.
Only the generated Rose_Optimized scene and ROSEGEN_ collections are rebuilt.
"""
import bpy, bmesh, math, random, os, json
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi, sqrt

# -------------------------- artist controls --------------------------
PARAMS = dict(
    bud_petals=11, middle_petals=13, guard_petals=8,
    diameter_mm=80.0, height_mm=43.0,
    bud_tightness=1.0, petal_length=1.0, petal_width=1.0,
    concavity=1.0, vertical_curvature=1.0, edge_curl=1.0,
    edge_waviness=1.0, layer_overlap=1.0, organic_variation=0.85,
    thickness_mm=0.65, seed=23,
    resolution_u=40, resolution_v=64, subdivision=1,
    manufacturing_voxel_mm=0.32,
)
OUTPUT = Path(os.environ.get('ROSE_OUTPUT_DIR', Path(__file__).resolve().parent))
PREVIEW = os.environ.get('ROSE_PREVIEW','0') == '1'
SAMPLES = int(os.environ.get('ROSE_SAMPLES','48'))
RESOLUTION = int(os.environ.get('ROSE_RESOLUTION','1000'))
VIEWS = [v for v in os.environ.get('ROSE_VIEWS','top,perspective,side').split(',') if v]
SCALE_MM = PARAMS['diameter_mm']/2

def log(s): print('[ROSE] '+str(s), flush=True)
def mix(a,b,t): return a+(b-a)*t
def smooth(t): return max(0,min(1,t))**2*(3-2*max(0,min(1,t)))

def collection(name):
    c=bpy.data.collections.new('ROSEGEN_'+name); SCENE.collection.children.link(c); return c

def mesh_object(name,verts,faces,col):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); col.objects.link(ob)
    for f in me.polygons: f.use_smooth=True
    me.materials.append(CLAY)
    return ob

def material(name,color,roughness):
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name); mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=roughness
    return mat

def specifications():
    """Separate anatomical distributions, with a continuous spiral through each.
    Radius is explicit and positive: no centerline clamping or negative-angle collapse.
    """
    rng=random.Random(PARAMS['seed']); result=[]
    regions=[('Bud',PARAMS['bud_petals'],.025,.265,.945,1.015,245,151),
             ('Middle',PARAMS['middle_petals'],.30,.75,.99,.88,153,112),
             ('Guard',PARAMS['guard_petals'],.79,1.01,.86,.70,118,104)]
    phase=.2
    for region,count,rmin,rmax,hmin,hmax,span0,span1 in regions:
        for i in range(count):
            t=i/max(1,count-1); organic=PARAMS['organic_variation']
            rad=mix(rmin,rmax,t**1.55 if region=='Bud' else t)
            if region=='Bud': rad /= PARAMS['bud_tightness']
            # Nonuniform successive divergence avoids aligned seams and explicit rings.
            phase+=math.radians(mix(133,148,rng.random()))
            jitter=lambda a:rng.uniform(-a,a)*organic
            result.append(dict(region=region,r=rad*(1+jitter(.045)),
                h=mix(hmin,hmax,t)+jitter(.027),phi=phase+jitter(.12),
                span=math.radians(mix(span0,span1,t))*PARAMS['petal_width']*PARAMS['layer_overlap']*(1+jitter(.09)),
                phase=rng.uniform(0,2*pi),skew=.06+jitter(.05),
                lean=jitter(.06),wave=jitter(.25)+1))
    return result

def petal(p,index,col):
    """A rounded, wrapped patch: u climbs a concave bowl; v travels across its lip.
    The lip drops and tucks inward at the wings, with a radial spiral ramp for laps.
    Subdivision precedes Solidify, so the rim is smooth without needle-thin tips.
    """
    nu,nv=PARAMS['resolution_u'],PARAMS['resolution_v']; verts=[]; faces=[]
    r,h=p['r'],p['h']; isbud=p['region']=='Bud'
    root_r=max(.006,r*(.72 if p['region']=='Guard' else .48)); root_z=.015 if p['region']=='Guard' else .075
    span=p['span']; phase=p['phase']; wave_amp=(.003 if isbud else .029)*PARAMS['edge_waviness']
    for i in range(nu+1):
        u=i/nu
        for j in range(nv+1):
            v=-1+2*j/nv; av=abs(v)
            # Broad rounded crest; wings terminate below and inward of the crest.
            arch=(1-.025*av**2-.05*av**6) if isbud else .065+.935*sqrt(max(0.0,1-v*v))
            w=u*arch
            bowl=sin(w*pi/2)**(.92*PARAMS['concavity'])
            rad=mix(root_r,r,bowl)
            rad*=1-.32*av**4*smooth(u)
            rad+=r*p['skew']*v*smooth(u) # winding lip, physically overlapped ends
            lip=smooth((u-.76)/.24)
            rad+=r*(.020 if isbud else .065)*PARAMS['edge_curl']*lip*(1-.45*av)
            # Height grows at an independent rate: outer surfaces remain upright cups.
            z=root_z+(h-root_z)*(w**(.83*PARAMS['vertical_curvature']))*PARAMS['petal_length']
            z-=r*.032*PARAMS['edge_curl']*lip*(1-av*av)
            wav=sin(5.1*v+phase)+.36*sin(11.3*v-phase)+.18*sin(19*v+2*phase)
            z+=wave_amp*wav*(u**5)*p['wave']
            rad+=wave_amp*.42*wav*u**4
            # Low-frequency sculpting, no displacement texture concealing shape.
            rad+=PARAMS['organic_variation']*.012*r*sin(3*v+phase+2*u)*sin(pi*u)
            theta=p['phi']+v*span/2*(.42+.58*sin(u*pi/2))+.17*(1-u)+p['lean']*u
            verts.append((rad*cos(theta),rad*sin(theta),z))
    for i in range(nu):
        for j in range(nv):
            a=i*(nv+1)+j; faces.append((a,a+1,a+nv+2,a+nv+1))
    ob=mesh_object(f'{p["region"]}_{index:02d}',verts,faces,col)
    sub=ob.modifiers.new('Smooth sculpted surface','SUBSURF'); sub.levels=PARAMS['subdivision']; sub.render_levels=PARAMS['subdivision']
    sol=ob.modifiers.new('Rounded substantial lip','SOLIDIFY'); sol.thickness=min(PARAMS['thickness_mm']/SCALE_MM, .004+r*.035); sol.offset=0; sol.use_even_offset=False
    bev=ob.modifiers.new('Soft rim','BEVEL'); bev.width=sol.thickness*.28; bev.segments=3
    ob['anatomy']=p['region']; ob['procedural_spec']=json.dumps(p)
    return ob

def base(col):
    verts=[]; faces=[]; n=96
    profile=[(.53,0),(.64,.035),(.67,.09),(.59,.17),(.35,.23),(.04,.27)]
    for r,z in profile:
        for j in range(n):
            a=2*pi*j/n; verts.append((r*cos(a),r*sin(a),z))
    for k in range(len(profile)-1):
        for j in range(n):
            a=k*n+j; b=k*n+(j+1)%n; faces.append((a,b,b+n,a+n))
    faces.append(tuple(reversed(range(n)))); faces.append(tuple((len(profile)-1)*n+j for j in range(n)))
    return mesh_object('Connected_receptacle_flat_base',verts,faces,col)

def evaluated_copy(ob,col):
    sol=next((m for m in ob.modifiers if m.type=='SOLIDIFY'),None)
    original=sol.thickness if sol else 0
    if sol:sol.thickness=max(original,.48/SCALE_MM)
    bpy.context.view_layer.update()
    me=bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    if sol:sol.thickness=original
    bpy.context.view_layer.update()
    new=bpy.data.objects.new('Union_'+ob.name,me); col.objects.link(new); return new

def mesh_stats(ob):
    bm=bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(ob.data)
    seen=set(); sizes=[]
    for v in bm.verts:
        if v in seen: continue
        stack=[v];seen.add(v); n=0
        while stack:
            cur=stack.pop(); n+=1
            for e in cur.link_edges:
                other=e.other_vert(cur)
                if other not in seen: seen.add(other); stack.append(other)
        sizes.append(n)
    stats=dict(vertices=len(bm.verts),faces=len(bm.faces),boundary_edges=sum(e.is_boundary for e in bm.edges),
        nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),wire_edges=sum(e.is_wire for e in bm.edges),
        degenerate_faces=sum(f.calc_area()<1e-12 for f in bm.faces),components=len(sizes),component_vertices=sorted(sizes,reverse=True),
        signed_volume_mm3=bm.calc_volume(signed=True)*SCALE_MM**3,
        dimensions_mm=[round(v*SCALE_MM,3) for v in ob.dimensions])
    # Approximate release-direction screen: down-facing exposed surfaces above the foot.
    under=[f for f in bm.faces if f.normal.z < -.15 and f.calc_center_median().z>.13]
    stats['downward_face_area_fraction_above_base']=sum(f.calc_area() for f in under)/sum(f.calc_area() for f in bm.faces)
    bm.free(); return stats

def manufacture(objects,col):
    log('Consolidating evaluated solids with voxel union')
    copies=[evaluated_copy(o,col) for o in objects]
    bpy.ops.object.select_all(action='DESELECT')
    for o in copies:o.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]; bpy.ops.object.join(); ob=bpy.context.object; ob.name='Rose_Manufacturing_Candidate'
    rem=ob.modifiers.new('Voxel union 0.32mm','REMESH'); rem.mode='VOXEL'; rem.voxel_size=PARAMS['manufacturing_voxel_mm']/SCALE_MM; rem.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    # Drop sealed internal cavities and detached voxel dust, keeping the largest shell.
    bm=bmesh.new();bm.from_mesh(ob.data); unseen=set(bm.verts); shells=[]
    while unseen:
        seed=unseen.pop(); todo=[seed]; shell=[seed]
        while todo:
            v=todo.pop()
            for e in v.link_edges:
                q=e.other_vert(v)
                if q in unseen:unseen.remove(q);todo.append(q);shell.append(q)
        shells.append(shell)
    shells.sort(key=len,reverse=True)
    removed=[len(s) for s in shells[1:]]
    if removed:bmesh.ops.delete(bm,geom=[v for s in shells[1:] for v in s],context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    sm=ob.modifiers.new('Gentle voxel relaxation','SMOOTH');sm.factor=.3;sm.iterations=2;bpy.ops.object.modifier_apply(modifier=sm.name)
    stats=mesh_stats(ob);stats['removed_secondary_shell_sizes']=removed;stats['minimum_candidate_petal_thickness_mm']=.48
    # Blender STL exporter writes explicit millimeters; STL itself carries no unit metadata.
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    if stats['nonmanifold_edges']==0 and stats['components']==1 and stats['signed_volume_mm3']>0:
        bpy.ops.wm.stl_export(filepath=str(OUTPUT/'rose_manufacturing_candidate.stl'),export_selected_objects=True,global_scale=SCALE_MM,apply_modifiers=True)
        stats['stl_exported']=True
    else:stats['stl_exported']=False
    ob['validation']=json.dumps(stats);ob.hide_render=True;ob.hide_set(True)
    log(stats);return stats

def aim(ob,target): ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def setup_studio(col):
    sc=SCENE;sc.render.engine='CYCLES'; sc.cycles.samples=SAMPLES;sc.cycles.use_denoising=True;sc.cycles.use_adaptive_sampling=True;sc.cycles.adaptive_threshold=.035;sc.cycles.adaptive_min_samples=8
    sc.render.resolution_x=RESOLUTION;sc.render.resolution_y=RESOLUTION;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
    sc.world=bpy.data.worlds.new('Rose studio world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.32,.32,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    sc.view_settings.view_transform='AgX'
    floor=mesh_object('Studio_floor',[(-200,-200,-.025),(200,-200,-.025),(200,200,-.025),(-200,200,-.025)],[(0,1,2,3)],col)
    floor.data.materials.clear();floor.data.materials.append(material('Rose neutral backdrop',(.28,.28,.28),.82))
    for name,loc,power,size in [('Key',(-3,-4,6),430,4),('Fill',(4,-1,3),170,3),('Rim',(1,4,5),330,3)]:
        dat=bpy.data.lights.new(name,'AREA');dat.energy=power;dat.shape='DISK';dat.size=size
        ob=bpy.data.objects.new(name,dat);col.objects.link(ob);ob.location=loc;aim(ob,(0,0,.45))
    cameras={}
    for name,loc,scale,target in [('top',(0,0,6),2.30,(0,0,.5)),('perspective',(2,-4,3.3),2.30,(0,0,.48)),('side',(2,-4,1.30),2.30,(0,0,.49))]:
        dat=bpy.data.cameras.new('Camera_'+name);dat.type='ORTHO';dat.ortho_scale=scale;dat.lens=55
        ob=bpy.data.objects.new('Camera_'+name,dat);col.objects.link(ob);ob.location=loc;aim(ob,target);cameras[name]=ob
    return cameras

def main():
    global SCENE,CLAY
    OUTPUT.mkdir(parents=True,exist_ok=True);log('Blender '+bpy.app.version_string)
    old=bpy.data.scenes.get('Rose_Optimized')
    if old:
        bpy.context.window.scene=bpy.data.scenes.new('Rose_rebuild_temp');bpy.data.scenes.remove(old)
    for c in list(bpy.data.collections):
        if c.name.startswith('ROSEGEN_'):
            for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
            bpy.data.collections.remove(c)
    SCENE=bpy.data.scenes.new('Rose_Optimized');bpy.context.window.scene=SCENE
    
    for tmp in list(bpy.data.scenes):
        if tmp.name.startswith('Rose_rebuild_temp'):bpy.data.scenes.remove(tmp)
    SCENE.unit_settings.system='METRIC';SCENE.unit_settings.scale_length=SCALE_MM/1000;SCENE.unit_settings.length_unit='MILLIMETERS'
    CLAY=material('Rose gray clay',(.37,.37,.37),.64)
    edit=collection('Editable_Petals');found=collection('Receptacle');solid=collection('Manufacturing_Candidate');studio=collection('Studio')
    specs=specifications();objects=[petal(p,i,edit) for i,p in enumerate(specs)];objects.append(base(found))
    # Calibrate true evaluated dimensions, including rim thickness and smoothing.
    dg=bpy.context.evaluated_depsgraph_get(); coords=[]
    for ob in objects:
        ev=ob.evaluated_get(dg);me=ev.to_mesh();coords.extend(tuple(v.co) for v in me.vertices);ev.to_mesh_clear()
    mins=[min(v[k] for v in coords) for k in range(3)];maxs=[max(v[k] for v in coords) for k in range(3)]
    log('Unscaled evaluated bounds: '+str((mins,maxs)))
    xy=2/max(maxs[0]-mins[0],maxs[1]-mins[1]); zz=(PARAMS['height_mm']/SCALE_MM)/(maxs[2]-mins[2])
    for ob in objects:
        for v in ob.data.vertices:
            v.co.x*=xy;v.co.y*=xy;v.co.z=(v.co.z-mins[2])*zz
    bpy.context.view_layer.update()
    cameras=setup_studio(studio)
    SCENE['parameters']=json.dumps(PARAMS);SCENE['reference']='converted_images.pdf page 1; single-view interpretation, hidden geometry inferred'
    stats=manufacture(objects,solid) if not PREVIEW else {'skipped':'preview iteration'}
    dg=bpy.context.evaluated_depsgraph_get();points=[]; open_edges=0;bad_edges=0
    for obj in objects:
        ev=obj.evaluated_get(dg); me=ev.to_mesh();points.extend(tuple(v.co) for v in me.vertices)
        bm=bmesh.new();bm.from_mesh(me);open_edges+=sum(e.is_boundary for e in bm.edges);bad_edges+=sum(not e.is_manifold for e in bm.edges);bm.free();ev.to_mesh_clear()
    master_dimensions=[round((max(p[k] for p in points)-min(p[k] for p in points))*SCALE_MM,3) for k in range(3)]
    report=dict(editable_dimensions_mm=master_dimensions,editable_boundary_edges=open_edges,editable_nonmanifold_edges=bad_edges,blender_version=bpy.app.version_string,parameters=PARAMS,petal_count=len(specs),manufacturing=stats)
    (OUTPUT/'mesh_validation.json').write_text(json.dumps(report,indent=2))
    SCENE.camera=cameras['perspective']
    # Frame the editable master in the saved UI.
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_distance=3.3;area.spaces.active.region_3d.view_location=(0,0,.5)
                area.spaces.active.shading.color_type='MATERIAL'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/'rose_optimized.blend'))
    for view in VIEWS:
        SCENE.camera=cameras[view];SCENE.render.filepath=str(OUTPUT/f'rose_{view}.png');log('Rendering '+view);bpy.ops.render.render(write_still=True)
    SCENE.camera=cameras['perspective'];bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/'rose_optimized.blend'))
    log('SUCCESS: saved project, renders and diagnostics to '+str(OUTPUT))

if __name__=='__main__':main()
