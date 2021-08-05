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


def create_result_mesh(bm, vertex_list, faces, target, material_index, bounding_edge_list):
    """
    Creates blender data from roofeus output
    :param bm: blender object
    :param vertex_list: roofeus output vertex
    :param faces: roofeus output faces
    :param target: target face
    :param material_index: material index to assign to the new faces
    :param bounding_edge_list: bounding edges
    """
    bvertex_list = []
    face_vertex_list = [item for sublist in faces for item in sublist]
    bounding_edge_vertex_list = [item for sublist in bounding_edge_list for item in sublist]
    for v in vertex_list:
        if v.inside and (v.index in face_vertex_list or v.index in bounding_edge_vertex_list):
            bvertex_list.append(bm.verts.new(v.coords_3d))
        else:
            bvertex_list.append(None)  # Append to preserve index relation

    uv_layer = bm.loops.layers.uv.verify()
    for face in faces:
        if len(face) >= 3:
            face_vertex_list = []
            for i in face:
                if i >= 0:
                    face_vertex_list.append(bvertex_list[i])
                else:
                    face_vertex_list.append(target[-1-i].bl_vertex)
            bl_face = bm.faces.new(face_vertex_list)
            bl_face.material_index = material_index
            for loop, i in zip(bl_face.loops, face):
                loop[uv_layer].uv = vertex_list[i].coords_2d if i >= 0 else target[-1-i].uvs
        else:
            print("WARN: Incomplete face. len:", len(face))

    # fill uncompleted faces
    bpy.ops.mesh.select_mode(type='EDGE', action='ENABLE')
    bpy.ops.mesh.select_all(action='DESELECT')
    target_vertex = [t.bl_vertex for t in target]
    edges_to_fill = []
    for v in target_vertex:
        for edge in v.link_edges:
            if edge not in edges_to_fill and all([edge_v in target_vertex for edge_v in edge.verts]):
                edge.select = True
                edges_to_fill.append(edge)
    print("Target Edges to fill", len(edges_to_fill))

    for bounding_edge in bounding_edge_list:
        edge_verts = [bvertex_list[v] for v in bounding_edge]
        found_edge = bm.edges.get(edge_verts)
        if not found_edge:
            found_edge = bm.edges.new(edge_verts)

        found_edge.select = True
        edges_to_fill.append(found_edge)
    print("Total Edges to fill", len(edges_to_fill))

    bpy.ops.mesh.fill()
    bpy.ops.mesh.select_all(action='DESELECT')

    # TODO uvs of autogenerated faces



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
                    vertex_list, faces, bounding_edge_list = rfs.create_mesh(template, target)
                    create_result_mesh(bm, vertex_list, faces, target, orig_face.material_index, bounding_edge_list)

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
