import bpy
import roofeus.roofeus as rfs

class Roofeus(bpy.types.Operator):
    """Mesh generator based on template"""
    bl_idname = "mesh.roofeus"
    bl_label = "Roofeus"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # scene = context.scene
        # for obj in scene.objects:
        #     obj.location.x += 1.0

        # template = ...
        # target = ...
        # rfs.create_mesh(template, target)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(Roofeus)


def unregister():
    bpy.utils.unregister_class(Roofeus)

if __name__ == "__main__":
    register()
