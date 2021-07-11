import bpy, bmesh
import roofeus.models as rfsm
import roofeus.roofeus as rfs
import roofeus.utils as rfsu


def build_target_list(bm):
    target_list = []
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        if face.select:
            target = []
            for loop in face.loops:
                coords = loop.vert.co
                uv = loop[uv_layer].uv
                target_vertex = rfsm.RFTargetVertex(coords[0], coords[1], coords[2], uv[0], uv[1])
                target.append(target_vertex)

            target_list.append(target)
    print("Target list:", target_list)
    return target_list


def create_result_mesh(bm, vertex_list, faces, structure):
    # vertex_list = rfs.get_vertex_list(structure)
    bvertex_list = []
    for v in vertex_list:
        bvertex_list.append(bm.verts.new(v))

    for face in faces:
        bm.faces.new([bvertex_list[i] for i in face])


def on_template_file_updated(self, context):
    props = context.scene.roofeus
    print("Updated Template", str(bpy.path.abspath(props.template_file)))


class RoofeusProperties(bpy.types.PropertyGroup):
    template_file: bpy.props.StringProperty(name="Template File", subtype="FILE_PATH", update=on_template_file_updated)


class Roofeus(bpy.types.Operator):
    """Mesh generator based on template"""
    bl_idname = "mesh.roofeus"
    bl_label = "Roofeus"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("Begin")
        obj = context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        target_list = build_target_list(bm)

        props = context.scene.roofeus
        template_file = str(bpy.path.abspath(props.template_file))
        if template_file:
            template = rfsu.read_template(template_file)

            if template:  # TODO validate template
                for target in target_list:
                    vertex_list, faces, structure, _faces_idx = rfs.create_mesh(template, target)
                    create_result_mesh(bm, vertex_list, faces, structure)

                bmesh.update_edit_mesh(obj.data)
                print("Done")
            else:
                print("Template not valid")
        else:
            print("No template file selected")

        return {'FINISHED'}


def register():
    bpy.utils.register_class(RoofeusProperties)
    bpy.utils.register_class(Roofeus)
    bpy.types.Scene.roofeus = bpy.props.PointerProperty(type=RoofeusProperties)


def unregister():
    bpy.utils.unregister_class(Roofeus)
    bpy.utils.unregister_class(RoofeusProperties)
    del bpy.types.Scene.roofeus


if __name__ == "__main__":
    register()
