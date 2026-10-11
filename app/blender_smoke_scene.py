"""Render a small procedural 3D scene to smoke-test Blender on GitHub Actions.

This is a renderer/runtime proof, not a final-quality character asset or a complete
children's music video. Run with:
  blender --background --python app/blender_smoke_scene.py -- --output output/blender-smoke.png
"""
from __future__ import annotations

import sys
from pathlib import Path


def parse_output() -> Path:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    output = Path("output/blender-smoke.png")
    for index, value in enumerate(args):
        if value == "--output" and index + 1 < len(args):
            output = Path(args[index + 1])
    return output


def create_scene(output: Path) -> None:
    import bpy
    from mathutils import Vector

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.curves, bpy.data.meshes):
        # Unused datablocks are harmless; leave cleanup to Blender.
        pass

    def material(name, color, roughness=0.72):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1.0)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        return mat

    cream = material("Warm cream", (0.98, 0.82, 0.59))
    teal = material("Mascot teal", (0.08, 0.62, 0.62))
    coral = material("Coral accents", (0.98, 0.28, 0.24))
    dark = material("Eye dark", (0.035, 0.055, 0.09), 0.35)
    yellow = material("Sun yellow", (1.0, 0.68, 0.12))
    green = material("Garden green", (0.16, 0.48, 0.22))
    sky = material("Sky blue", (0.42, 0.75, 0.94))
    pink = material("Flower pink", (0.98, 0.28, 0.58))

    def uv_sphere(name, loc, scale, mat, segments=32, rings=20):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
        obj = bpy.context.object
        obj.name = name
        obj.scale = scale
        obj.data.materials.append(mat)
        for poly in obj.data.polygons:
            poly.use_smooth = True
        return obj

    def cube(name, loc, scale, mat, bevel=0.18):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        obj = bpy.context.object
        obj.name = name
        obj.dimensions = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(mat)
        if bevel:
            mod = obj.modifiers.new("Soft rounded edges", "BEVEL")
            mod.width = bevel
            mod.segments = 4
            obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
        return obj

    # Simple stylized garden backdrop and floor.
    cube("Garden floor", (0, 0, -0.25), (14, 14, 0.5), green, 0.25)
    cube("Soft sky backdrop", (0, 3.8, 3.0), (14, 0.25, 8), sky, 0.05)

    # Original toy-like mascot built from primitives (not a copied character).
    uv_sphere("Mascot body", (0, 0, 1.55), (0.82, 0.57, 1.02), teal)
    uv_sphere("Mascot head", (0, -0.03, 2.65), (0.88, 0.66, 0.72), teal)
    uv_sphere("Mascot left cheek", (-0.48, -0.58, 2.43), (0.19, 0.07, 0.12), coral)
    uv_sphere("Mascot right cheek", (0.48, -0.58, 2.43), (0.19, 0.07, 0.12), coral)
    for x in (-0.30, 0.30):
        uv_sphere("Mascot eye", (x, -0.64, 2.73), (0.095, 0.065, 0.13), dark, 20, 12)
        uv_sphere("Eye highlight", (x - 0.025, -0.70, 2.78), (0.025, 0.018, 0.035), cream, 16, 8)
    uv_sphere("Mascot smile", (0, -0.66, 2.48), (0.18, 0.045, 0.045), coral)
    for x in (-0.52, 0.52):
        uv_sphere("Arm", (x * 1.55, -0.01, 1.65), (0.22, 0.22, 0.50), teal)
    for x in (-0.36, 0.36):
        uv_sphere("Foot", (x, -0.02, 0.55), (0.29, 0.34, 0.20), coral)

    # Simple flowers add a readable foreground and depth.
    for x, z, flower_mat in [(-1.5, 0.65, pink), (1.55, 0.75, yellow)]:
        cube("Flower stem", (x, -0.2, z + 0.4), (0.07, 0.07, 0.8), green, 0.03)
        uv_sphere("Flower center", (x, -0.25, z + 0.85), (0.16, 0.12, 0.16), yellow)
        for dx, dz in [(-0.18, 0), (0.18, 0), (0, -0.17), (0, 0.17)]:
            uv_sphere("Flower petal", (x + dx, -0.23, z + 0.85 + dz), (0.13, 0.10, 0.13), flower_mat)

    # Large soft sun in the upper background.
    uv_sphere("Sun", (1.9, 3.45, 4.2), (0.48, 0.12, 0.48), yellow)

    world = bpy.data.worlds.new("Bright soft world") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.52, 0.72, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.5, 7))
    key = bpy.context.object
    key.name = "Large soft key light"
    key.data.energy = 850
    key.data.shape = "DISK"
    key.data.size = 5
    key.rotation_euler = (Vector((0, 0, 1.6)) - key.location).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.object.camera_add(location=(0, -10.5, 3.05))
    camera = bpy.context.object
    camera.name = "Vertical portrait camera"
    camera.rotation_euler = (Vector((0, 0.0, 2.1)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 52
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE_NEXT" if bpy.app.version >= (4, 2, 0) else "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 910
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(output.resolve())
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.color_depth = "8"
    scene.render.resolution_percentage = 100
    scene.camera.data.dof.use_dof = False
    scene.render.filepath = str(output.resolve())
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    create_scene(parse_output())
