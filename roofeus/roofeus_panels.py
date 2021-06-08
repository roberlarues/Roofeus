import bpy


class RoofeusPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Roofeus"
    bl_idname = "OBJECT_PT_roofeus"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Roofeus"
    bl_context = "mesh_edit"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        roofeus = scene.roofeus

        row = layout.row()
        row.prop(roofeus, "template_file")

        row = layout.row()
        row.operator("mesh.roofeus")


def register():
    bpy.utils.register_class(RoofeusPanel)


def unregister():
    bpy.utils.unregister_class(RoofeusPanel)


if __name__ == "__main__":
    register()
