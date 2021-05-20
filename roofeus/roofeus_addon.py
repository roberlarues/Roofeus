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


def create_result_mesh(bm, mesh):
    vertex_list = rfs.get_vertex_list(mesh)
    for v in vertex_list:
        bm.verts.new(v)


class Roofeus(bpy.types.Operator):
    """Mesh generator based on template"""
    bl_idname = "mesh.roofeus"
    bl_label = "Roofeus"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("Begin")
        obj = bpy.context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        target_list = build_target_list(bm)
        template = rfsu.generate_test_template()  # TODO leer de fichero
        for target in target_list:
            mesh, faces, faces_idx = rfs.create_mesh(template, target)
            create_result_mesh(bm, mesh)

        bmesh.update_edit_mesh(obj.data)
        print("Done")

        return {'FINISHED'}


def register():
    bpy.utils.register_class(Roofeus)


def unregister():
    bpy.utils.unregister_class(Roofeus)


if __name__ == "__main__":
    register()
