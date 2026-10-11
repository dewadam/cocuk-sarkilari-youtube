"""Render a short animated Blender test scene for GitHub Actions CPU validation.

This is a pipeline test, not final-quality children's animation.
Run:
  blender --background --python app/blender_animation_smoke.py -- --output output/blender-animation-smoke.mp4
"""
from __future__ import annotations

import sys
from pathlib import Path


def parse_args() -> tuple[Path, Path, bool, int]:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    output = Path("output/blender-animation-smoke.mp4")
    blend_output = Path("output/sheepit-animation-test.blend")
    skip_render = False
    duration_seconds = 2
    for i, value in enumerate(args):
        if value == "--output" and i + 1 < len(args):
            output = Path(args[i + 1])
        elif value == "--save-blend" and i + 1 < len(args):
            blend_output = Path(args[i + 1])
        elif value == "--skip-render":
            skip_render = True
        elif value == "--duration-seconds" and i + 1 < len(args):
            duration_seconds = max(2, int(args[i + 1]))
    return output, blend_output, skip_render, duration_seconds


def main() -> None:
    import bpy
    from mathutils import Vector

    output, blend_output, skip_render, duration_seconds = parse_args()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    def mat(name, color, roughness=0.75):
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*color, 1)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = roughness
        return m

    teal = mat("Character turquoise", (0.05, 0.58, 0.60))
    cream = mat("Eye cream", (1.0, 0.94, 0.79))
    dark = mat("Eyes", (0.025, 0.045, 0.07), 0.3)
    coral = mat("Cheeks and feet", (0.98, 0.25, 0.28))
    green = mat("Garden", (0.12, 0.43, 0.20))
    sky = mat("Sky", (0.30, 0.66, 0.91))
    yellow = mat("Sun", (1.0, 0.68, 0.10))
    pink = mat("Flower pink", (0.98, 0.25, 0.55))

    def sphere(name, loc, scale, material, parent=None):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=loc)
        obj = bpy.context.object
        obj.name = name
        obj.scale = scale
        obj.data.materials.append(material)
        for poly in obj.data.polygons:
            poly.use_smooth = True
        if parent:
            obj.parent = parent
            obj.location = loc
        return obj

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, -0.25))
    floor = bpy.context.object
    floor.name = "Garden floor"
    floor.dimensions = (12, 12, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    floor.data.materials.append(green)
    bevel = floor.modifiers.new("Soft floor edges", "BEVEL")
    bevel.width, bevel.segments = 0.2, 3

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.8, 3))
    backdrop = bpy.context.object
    backdrop.name = "Sky backdrop"
    backdrop.dimensions = (12, 0.2, 8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    backdrop.data.materials.append(sky)

    root = bpy.data.objects.new("Animated character root", None)
    bpy.context.collection.objects.link(root)
    sphere("Character body", (0, 0, 1.35), (0.72, 0.53, 0.88), teal, root)
    sphere("Character head", (0, -0.02, 2.35), (0.82, 0.62, 0.67), teal, root)
    sphere("Left cheek", (-0.44, -0.55, 2.18), (0.15, 0.06, 0.10), coral, root)
    sphere("Right cheek", (0.44, -0.55, 2.18), (0.15, 0.06, 0.10), coral, root)
    for x in (-0.27, 0.27):
        sphere("Eye", (x, -0.61, 2.42), (0.08, 0.05, 0.11), dark, root)
        sphere("Eye glint", (x - 0.02, -0.655, 2.46), (0.022, 0.014, 0.028), cream, root)
    sphere("Smile", (0, -0.64, 2.17), (0.15, 0.035, 0.035), coral, root)

    arms = []
    for side in (-1, 1):
        arm = sphere("Waving arm", (side * 0.98, -0.02, 1.50), (0.18, 0.18, 0.43), teal, root)
        arm.rotation_euler[1] = side * -0.15
        arms.append((arm, side))
    for x in (-0.31, 0.31):
        sphere("Foot", (x, -0.02, 0.46), (0.25, 0.28, 0.16), coral, root)

    for x, flower_mat in [(-1.5, pink), (1.55, yellow)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -0.12, 0.55))
        stem = bpy.context.object
        stem.name = "Flower stem"
        stem.dimensions = (0.06, 0.06, 0.65)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        stem.data.materials.append(green)
        sphere("Flower center", (x, -0.18, 0.91), (0.13, 0.10, 0.13), yellow)
        for dx, dz in [(-0.15, 0), (0.15, 0), (0, -0.14), (0, 0.14)]:
            sphere("Flower petal", (x + dx, -0.17, 0.91 + dz), (0.11, 0.08, 0.11), flower_mat)

    sphere("Sun", (1.9, 3.45, 4.2), (0.43, 0.12, 0.43), yellow)
    world = bpy.data.worlds.new("Soft blue world") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.30, 0.52, 0.72, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.5, 7))
    light = bpy.context.object
    light.data.energy = 750
    light.data.shape = "DISK"
    light.data.size = 5
    light.rotation_euler = (Vector((0, 0, 1.5)) - light.location).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.object.camera_add(location=(0, -10.5, 3.0))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0, 0, 2.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 52

    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE_NEXT" if bpy.app.version >= (4, 2, 0) else "BLENDER_EEVEE"
    scene.render.resolution_x = 320
    scene.render.resolution_y = 568
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = duration_seconds * scene.render.fps
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "Standard"
    scene.camera.data.dof.use_dof = False

    for frame, z in [(1, 0.0), (13, 0.18), (25, 0.0), (37, 0.18), (49, 0.0)]:
        root.location.z = z
        root.keyframe_insert(data_path="location", frame=frame, group="Gentle bounce")
    for arm, side in arms:
        for frame, angle in [(1, side * -0.25), (13, side * 0.25), (25, side * -0.25),
                             (37, side * 0.25), (49, side * -0.25)]:
            arm.rotation_euler[1] = angle
            arm.keyframe_insert(data_path="rotation_euler", frame=frame, group="Wave")
    for action in bpy.data.actions:
        for fcurve in getattr(action, "fcurves", []):
            for key in fcurve.keyframe_points:
                key.interpolation = "BEZIER"
            fcurve.modifiers.new(type="CYCLES")

    output.parent.mkdir(parents=True, exist_ok=True)
    blend_output.parent.mkdir(parents=True, exist_ok=True)
    # Save a self-contained native Blender project for optional SheepIt testing.
    # The render farm receives the .blend file, not this Python generator.
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_output.resolve()))
    if skip_render:
        print("Saved Blender project for render farm: " + str(blend_output.resolve()))
        return

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = str(output.resolve())
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
