import bpy, bmesh
import roofeus.models as rfsm
import roofeus.roofeus as rfs
import roofeus.utils as rfsu


def build_target_list(bm):
    """
    Builds roofeus target data from selected blender face
    :param bm: selected object
    :return: roofeus target data and selected blender faces
    """
    rfsm.RFTargetVertex.id_neg = -1
    target_list = []
    uv_layer = bm.loops.layers.uv.verify()
    affected_faces = []
    for face in bm.faces:
        if face.select:
            target = []
            for loop in face.loops:
                coords = loop.vert.co
                uv = loop[uv_layer].uv
                target_vertex = rfsm.RFTargetVertex(coords[0], coords[1], coords[2], uv[0], uv[1])
                target_vertex.bl_vertex = loop.vert
                target.append(target_vertex)

            target_list.append(target)
            affected_faces.append(face)
    return target_list, affected_faces


def create_result_mesh(bm, vertex_list, faces, target, material_index):
    """
    Creates blender data from roofeus output
    :param bm: blender object
    :param vertex_list: roofeus output vertex
    :param faces: roofeus output faces
    :param target: target face
    :param material_index: material index to assign to the new faces
    """
    bvertex_list = []
    for v in vertex_list:
        if v.inside:
            bvertex_list.append(bm.verts.new(v.coords_3d))
        else:
            bvertex_list.append(None)  # Append to preserve index relation

    uv_layer = bm.loops.layers.uv.verify()
    for face in faces:
        bl_face = bm.faces.new([bvertex_list[i] if i >= 0 else target[-1-i].bl_vertex for i in face])
        bl_face.material_index = material_index
        for loop, i in zip(bl_face.loops, face):
            loop[uv_layer].uv = vertex_list[i].coords_2d if i >= 0 else target[-1-i].uvs


def on_template_file_updated(self, context):
    """Executed when template file is updated"""
    props = context.scene.roofeus
    print("Updated Template", str(bpy.path.abspath(props.template_file)))


class RoofeusProperties(bpy.types.PropertyGroup):
    """Roofeus properties"""
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
        target_list, original_faces = build_target_list(bm)

        props = context.scene.roofeus
        template_file = str(bpy.path.abspath(props.template_file))
        if template_file:
            template = rfsu.read_template(template_file)
            if template:
                for target, orig_face in zip(target_list, original_faces):
                    vertex_list, faces = rfs.create_mesh(template, target)
                    create_result_mesh(bm, vertex_list, faces, target, orig_face.material_index)

                bmesh.update_edit_mesh(obj.data)

                bmesh.ops.delete(bm, geom=original_faces, context='FACES_ONLY')
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
