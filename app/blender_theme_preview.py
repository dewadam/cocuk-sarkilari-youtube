"""Render a short theme-specific procedural 3D preview for a song topic.

This is a visual prototype: each TR topic gets a different hero character and set.
It intentionally uses Blender primitives so the pipeline needs no paid assets.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

def args():
    values = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out, song, seconds = Path("output/theme-preview.mp4"), "TR001", 5
    for i, v in enumerate(values):
        if v == "--output" and i+1 < len(values): out = Path(values[i+1])
        elif v == "--song-id" and i+1 < len(values): song = values[i+1]
        elif v == "--duration-seconds" and i+1 < len(values): seconds = max(3, int(values[i+1]))
    return out, song, seconds

def main():
    import bpy
    from mathutils import Vector
    output, song_id, seconds = args()
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.materials, bpy.data.curves, bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
        pass

    def material(name, color, roughness=.68):
        m = bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*color,1)
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=roughness
        return m
    floaters = []
    mats = {
      "blue": material("Sky blue",(.12,.48,.86)), "navy": material("Deep space",(.025,.035,.16)),
      "green": material("Garden green",(.12,.48,.22)), "grass": material("Bright grass",(.28,.68,.22)),
      "cream": material("Warm cream",(1,.88,.65)), "white": material("Soft white",(.96,.96,.91)),
      "black": material("Charcoal details",(.045,.055,.075),.35), "pink": material("Coral pink",(.98,.23,.40)),
      "yellow": material("Sunshine yellow",(1,.68,.08)), "red": material("Tomato red",(.88,.12,.12)),
      "orange": material("Tangerine",(1,.34,.06)), "purple": material("Friendly violet",(.42,.22,.80)),
      "teal": material("Ocean teal",(.02,.58,.58)), "brown": material("Warm brown",(.38,.20,.10)),
      "silver": material("Robot silver",(.62,.70,.78),.35), "tooth": material("Pearl tooth",(1,.99,.88)),
      "wood": material("Toy wood",(.64,.35,.13)), "blue2": material("Toy blue",(.08,.32,.92)),
    }
    def uv(name, loc, scale, mat, parent=None):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=loc)
        o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(mat)
        for p in o.data.polygons: p.use_smooth=True
        if parent: o.parent=parent
        elif any(token in name.casefold() for token in ("floating", "balloon", "bubble", "flower", "planet", "star", "fruit", "leaf", "toy block")): floaters.append(o)
        return o
    def cube(name, loc, scale, mat, bevel=.08):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        o=bpy.context.object; o.name=name; o.dimensions=scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.data.materials.append(mat)
        if bevel:
            mod=o.modifiers.new("Rounded child-friendly edges","BEVEL"); mod.width=bevel; mod.segments=3
        if any(token in name.casefold() for token in ("floating", "toy block")): floaters.append(o)
        return o
    def cone(name, loc, radius, depth, mat):
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radius, depth=depth, location=loc)
        o=bpy.context.object; o.name=name; o.data.materials.append(mat)
        bevel=o.modifiers.new("Soft edges","BEVEL"); bevel.width=.06; bevel.segments=2
        if "floating" in name.casefold(): floaters.append(o)
        return o
    def cylinder(name, loc, radius, depth, mat):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth, location=loc)
        o=bpy.context.object; o.name=name; o.data.materials.append(mat)
        bevel=o.modifiers.new("Soft edges","BEVEL"); bevel.width=.04; bevel.segments=2
        if any(token in name.casefold() for token in ("flower", "plant leaf", "shared fruit")): floaters.append(o)
        return o
    def eyes(parent, z=2.35, y=-.57, spacing=.24, size=.075):
        for x in (-spacing, spacing):
            uv("Eye", (x,y,z),(size,.04,size*1.25),mats["black"],parent)
            uv("Eye sparkle",(x-.018,y-.04,z+.025),(size*.25,.018,size*.28),mats["white"],parent)
        uv("Smile",(0,y-.025,z-.20),(.12,.025,.035),mats["pink"],parent)
    # Floor and background change by theme.
    themed = {
      "TR001": ("Renkler Bahçesi","green","teal"),
      "TR002": ("Hayvan Dostlarım","grass","cream"),
      "TR003": ("Fırça Fırça, Pırıl Pırıl","blue","tooth"),
      "TR004": ("Oyuncaklar Evlerine","wood","yellow"),
      "TR005": ("Minik Roket Uzayda","navy","silver"),
      "TR006": ("Şekiller Dans Ediyor","purple","yellow"),
      "TR007": ("Minik Bahçıvanlar","green","orange"),
      "TR008": ("Paylaşınca Çoğalan","grass","pink"),
    }
    title, floor_key, hero_key = themed.get(song_id,("Neşeli Çocuk Dünyası","green","teal"))
    floor=cube("Theme floor",(0,0,-.28),(12,12,.5),mats[floor_key],.12)
    wall=cube("Colorful studio backdrop",(0,3.6,3.1),(12,.2,8),mats["navy" if song_id=="TR005" else "blue"],.05)
    root=bpy.data.objects.new("Theme hero animated root",None); bpy.context.collection.objects.link(root)
    # Theme-specific silhouette, body, face, accessories.
    if song_id == "TR002": # proper fluffy lamb with hanging ears and four attached legs
        # Pear-shaped fleece body and a rounded, clearly separate lamb face.
        uv("Lamb fleece body",(0,0,1.35),(.70,.52,.76),mats["white"],root)
        uv("Lamb face",(0,-.39,2.03),(.48,.32,.52),mats["cream"],root)
        # Distinct wool curls around the silhouette; all are part of the animated character.
        for x,z,s in [
            (-.48,1.72,.20),(-.58,1.42,.19),(-.46,1.12,.18),
            (-.24,.92,.18),(0,.88,.19),(.24,.92,.18),(.47,1.12,.18),
            (.58,1.42,.19),(.48,1.72,.20),(-.28,1.86,.18),
            (0,1.91,.19),(.28,1.86,.18),(-.34,2.20,.16),
            (-.16,2.36,.17),(0,2.40,.18),(.17,2.35,.17),(.34,2.19,.16)
        ]:
            uv("Individual fluffy wool curl",(x,-.05,z),(s,.19,s*.92),mats["white"],root)
        # Long, soft, visibly drooping ears, with pink inner-ear insets.
        for side in (-1,1):
            ear=uv("Long floppy lamb ear",(side*.51,-.34,2.10),(.17,.13,.32),mats["cream"],root)
            ear.rotation_euler[1]=side*-.30
            inner=uv("Pink inner ear",(side*.535,-.455,2.10),(.095,.035,.235),mats["pink"],root)
            inner.rotation_euler[1]=side*-.30
        # Eyes and muzzle are positioned on the forward-facing surface of the face.
        for x in (-.19,.19):
            uv("Lamb eye",(x,-.685,2.10),(.060,.035,.078),mats["black"],root)
            uv("Lamb eye sparkle",(x-.015,-.718,2.125),(.018,.012,.022),mats["white"],root)
        uv("Soft lamb muzzle",(0,-.705,1.91),(.15,.055,.105),mats["white"],root)
        for x in (-.045,.045):
            uv("Tiny nostril",(x,-.755,1.94),(.018,.012,.015),mats["brown"],root)
        # Four separate short legs, attached to the root so they stay with the body.
        for side_x in (-.38,.38):
            for depth_y in (-.24,.24):
                leg=uv("Lamb short leg",(side_x,depth_y,.66),(.115,.13,.34),mats["cream"],root)
                uv("Lamb dark hoof",(side_x,depth_y-.015,.43),(.13,.14,.105),mats["brown"],root)
        # Small tail and a gentle farm meadow dressing.
        uv("Lamb tail",(.68,.18,1.25),(.16,.16,.18),mats["white"],root)
        for x in (-1.5,1.5):
            uv("Farm flower",(x,-.1,.48),(.18,.16,.18),mats["yellow"])
            cylinder("Farm flower stem",(x,-.1,.29),.025,.38,mats["green"])
    elif song_id == "TR003": # smiling tooth
        cube("Tooth crown",(0,0,1.65),(1.05,.68,1.25),mats["tooth"],.26).parent=root
        for x in (-.31,.31): cylinder("Tooth root",(x,0,.95),.19,.70,mats["tooth"]).parent=root
        eyes(root,1.95,-.37,.22,.07)
        for x in (-1.5,1.5): uv("Bubble",(x,0,1.6),(.16,.16,.16),mats["white"])
        cylinder("Toothbrush handle",(1.05,-.3,1.0),.10,.9,mats["pink"])
        cube("Brush head",(1.05,-.3,1.48),(.36,.16,.18),mats["white"],.05)
    elif song_id == "TR004": # toy train engine
        cube("Train body",(0,0,1.3),(1.25,.72,.68),mats["red"],.15).parent=root
        cube("Train cabin",(-.22,0,1.85),(.62,.62,.55),mats["blue2"],.12).parent=root
        cylinder("Train chimney",(.28,0,2.0),.13,.38,mats["yellow"]).parent=root
        for x in (-.42,.35): cylinder("Train wheel",(x,-.39,.78),.22,.13,mats["black"]).rotation_euler[0]=math.pi/2
        uv("Friendly face",(0,-.4,1.43),(.25,.07,.20),mats["cream"],root); eyes(root,1.48,-.48,.13,.05)
        for x in (-1.35,1.45): cube("Toy block",(x,0,.45),(.48,.48,.48),mats["yellow" if x<0 else "purple"],.08)
    elif song_id == "TR005": # robot astronaut
        uv("Robot head",(0,0,2.05),(.57,.48,.54),mats["silver"],root)
        cube("Robot torso",(0,0,1.25),(.85,.55,.78),mats["teal"],.16).parent=root
        for x in (-.22,.22): uv("LED eye",(x,-.48,2.12),(.10,.05,.12),mats["yellow"],root)
        uv("Robot smile",(0,-.50,1.91),(.12,.03,.035),mats["black"],root)
        for x in (-.65,.65): cylinder("Robot antenna",(x,0,2.42),.045,.35,mats["silver"]).parent=root; uv("Antenna light",(x,0,2.61),(.10,.10,.10),mats["pink"],root)
        uv("Planet",(1.45,.8,2.4),(.52,.52,.52),mats["purple"])
        bpy.ops.mesh.primitive_torus_add(major_radius=.75, minor_radius=.045, major_segments=32, minor_segments=8, location=(1.45,.8,2.4), rotation=(.5,.2,.2)); bpy.context.object.data.materials.append(mats["yellow"])
        for x,z in [(-1.3,2.7),(1.7,3.3),(-1.6,1.6)]: uv("Star",(x,.5,z),(.10,.10,.10),mats["yellow"])
    elif song_id == "TR006": # dancing geometric friends
        uv("Circle character",(-.8,0,1.45),(.47,.4,.47),mats["pink"],root)
        cube("Square character",(.15,0,1.45),(.78,.55,.78),mats["yellow"],.05).parent=root
        cone("Triangle character",(1.05,0,1.45),.48,.8,mats["teal"]).parent=root
        # eyes on the foreground of each shape
        for x,z in [(-.92,1.5),(-.68,1.5),(.04,1.5),(.26,1.5),(.98,1.55),(1.15,1.55)]:
            uv("Shape eye",(x,-.43,z),(.055,.035,.075),mats["black"],root)
    elif song_id == "TR007": # little gardener with plant
        uv("Child head",(-.35,0,2.12),(.48,.43,.49),mats["cream"],root)
        uv("Hair",(-.35,.02,2.43),(.49,.43,.25),mats["brown"],root)
        cube("Gardener overalls",(-.35,0,1.35),(.68,.45,.8),mats["orange"],.12).parent=root
        eyes(root,2.12,-.42,.18,.06)
        cylinder("Plant stem",(1.0,0,1.15),.07,1.05,mats["green"])
        for x,z in [(.75,1.35),(1.25,1.55),(1.22,1.05)]: uv("Plant leaf",(x,0,z),(.28,.12,.12),mats["grass"])
        cylinder("Plant pot",(1.0,0,.48),.36,.5,mats["red"])
    elif song_id == "TR008": # two friends and shared picnic
        uv("Friend A head",(-.55,0,2.0),(.42,.38,.45),mats["cream"],root)
        uv("Friend A hair",(-.55,.02,2.29),(.44,.39,.23),mats["brown"],root)
        cube("Friend A shirt",(-.55,0,1.3),(.6,.45,.72),mats["teal"],.12).parent=root
        uv("Friend B head",(.55,0,2.0),(.42,.38,.45),mats["cream"],root)
        uv("Friend B hair",(.55,.02,2.29),(.44,.39,.23),mats["orange"],root)
        cube("Friend B shirt",(.55,0,1.3),(.6,.45,.72),mats["purple"],.12).parent=root
        uv("Shared fruit",(0,-.55,.7),(.28,.25,.26),mats["red"])
        for x in (-.7,.7): uv("Eye",(x,-.36,2.05),(.055,.04,.08),mats["black"])
    else: # TR001: original colorful balloon character
        uv("Balloon body",(0,0,1.55),(.62,.52,.78),mats["teal"],root)
        uv("Balloon head",(0,-.02,2.25),(.67,.54,.58),mats["teal"],root)
        eyes(root,2.3,-.52,.23,.07)
        cone("Balloon knot",(0,0,.72),.13,.25,mats["pink"]).parent=root
        for x, mat_key in [(-1.35,"red"),(1.35,"yellow")]:
            uv("Floating balloon",(x,.0,2.45),(.34,.30,.42),mats[mat_key])
            cylinder("Balloon string",(x,0,1.98),.012,.55,mats["white"])
    # Shared animated arms and stage props, with distinct palette per topic.
    arms=[]
    if song_id not in ("TR002","TR004","TR006","TR008"):
        for side in (-1,1):
            arm=uv("Animated arm",(side*.76,-.02,1.45),(.15,.16,.38),mats[hero_key if hero_key in mats else "teal"],root)
            arms.append((arm,side))
    for x, key in [(-1.65,"yellow"),(1.65,"pink")]:
        uv("Floating accent",(x,.1,3.05),(.16,.13,.16),mats[key])
    world=bpy.data.worlds.new("Theme world") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world=world; world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.16,.25,.40,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=.5
    bpy.ops.object.light_add(type="AREA", location=(-3.5,-4.5,7))
    light=bpy.context.object; light.data.energy=650; light.data.shape="DISK"; light.data.size=5
    light.rotation_euler=(Vector((0,0,1.5))-light.location).to_track_quat("-Z","Y").to_euler()
    bpy.ops.object.camera_add(location=(0,-10.5,2.8))
    camera=bpy.context.object; camera.rotation_euler=(Vector((0,0,1.85))-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type="ORTHO"; camera.data.ortho_scale=5.2
    scene=bpy.context.scene; scene.camera=camera
    # Gentle camera choreography: subtle push-in and lateral drift over the whole shot.
    # Keep the movement restrained so preschool viewers can follow the character comfortably.
    scene.frame_start=1
    scene.frame_end=seconds*24
    camera_frames = [1, max(2, round(scene.frame_end * 0.33)),
                     max(3, round(scene.frame_end * 0.66)), scene.frame_end]
    camera_x = [0.0, -0.10, 0.10, 0.0]
    camera_scale = [5.2, 5.05, 4.95, 5.0]
    for frame, x_pos, scale in zip(camera_frames, camera_x, camera_scale):
        camera.location.x = x_pos
        camera.keyframe_insert(data_path="location", frame=frame, group="Gentle camera drift")
        camera.data.ortho_scale = scale
        camera.data.keyframe_insert(data_path="ortho_scale", frame=frame, group="Gentle camera push-in")
    scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version >= (4,2,0) else "BLENDER_EEVEE"
    scene.render.resolution_x=320; scene.render.resolution_y=568; scene.render.resolution_percentage=100
    scene.render.fps=24; scene.frame_start=1; scene.frame_end=seconds*24
    scene.view_settings.view_transform="Standard"
    scene.render.image_settings.color_mode="RGB"
    # Animate across the entire selected duration. Earlier versions keyed only
    # the first 49 frames, which made 5s/8s previews hold still near the end.
    # The final pose matches the first pose so the movement loops cleanly.
    last_frame = scene.frame_end
    quarter = max(2, round((last_frame - 1) / 4))
    loop_frames = [1, 1 + quarter, 1 + 2 * quarter, 1 + 3 * quarter, last_frame]
    bounce_values = [0.0, 0.13, 0.0, 0.13, 0.0]
    for frame, z in zip(loop_frames, bounce_values):
        root.location.z = z
        root.keyframe_insert(data_path="location", frame=frame, group="Bounce")
    for arm, side in arms:
        wave_values = [side * -0.18, side * 0.22, side * -0.18, side * 0.22, side * -0.18]
        for frame, angle in zip(loop_frames, wave_values):
            arm.rotation_euler[1] = angle
            arm.keyframe_insert(data_path="rotation_euler", frame=frame, group="Wave")
    # Small set props gently bob at staggered phases so the whole frame feels
    # alive rather than only the hero moving. All curves span the full duration.
    for index, prop in enumerate(floaters):
        base_z = prop.location.z
        phase = index % 2
        values = [0.0, 0.07 if phase == 0 else -0.035, 0.0,
                  -0.035 if phase == 0 else 0.07, 0.0]
        for frame, offset in zip(loop_frames, values):
            prop.location.z = base_z + offset
            prop.keyframe_insert(data_path="location", frame=frame, group="Floating set props")
    # Keyframe interpolation is sufficient because the key poses span the full
    # preview duration; avoid version-specific Action F-Curve APIs.
    for action in bpy.data.actions:
        for fc in getattr(action, "fcurves", []):
            for key in fc.keyframe_points:
                key.interpolation = "BEZIER"
    output.parent.mkdir(parents=True,exist_ok=True)
    scene.render.image_settings.file_format="FFMPEG"; scene.render.ffmpeg.format="MPEG4"
    scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"
    scene.render.filepath=str(output.resolve())
    bpy.ops.render.render(animation=True)
    # Save a representative still for quick visual inspection.
    scene.frame_set(1); scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(output.with_suffix(".png").resolve())
    bpy.ops.render.render(write_still=True)
    report={"song_id":song_id,"theme":title,"duration_seconds":seconds,"resolution":"320x568",
            "fps":24,"distinct_theme_scene":True,"youtube_uploaded":False}
    output.with_suffix(".json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__": main()
