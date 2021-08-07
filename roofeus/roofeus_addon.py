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
    roofeus_id_layer = bm.verts.layers.int.get("roofeus_id") or bm.verts.layers.int.new("roofeus_id")
    uv_layer = bm.loops.layers.uv.verify()
    affected_faces = []
    for face in bm.faces:
        if face.select:
            target = []
            for loop in face.loops:
                coords = loop.vert.co
                uv = loop[uv_layer].uv
                target_vertex = rfsm.RFTargetVertex(coords[0], coords[1], coords[2], uv[0], 1 - uv[1])
                target_vertex.bl_vertex = loop.vert
                target_vertex.bl_vertex[roofeus_id_layer] = target_vertex.ident
                target.append(target_vertex)

            target_list.append(target)
            affected_faces.append(face)
    return target_list, affected_faces


def create_result_mesh(bm, vertex_list, faces, target, material_index, bounding_edge_list, context):
    """
    Creates blender data from roofeus output
    :param bm: blender object
    :param vertex_list: roofeus output vertex
    :param faces: roofeus output faces
    :param target: target face
    :param material_index: material index to assign to the new faces
    :param bounding_edge_list: bounding edges
    """

    props = context.scene.roofeus
    roofeus_id_layer = bm.verts.layers.int.get("roofeus_id") or bm.verts.layers.int.new("roofeus_id")
    uv_layer = bm.loops.layers.uv.verify()

    # Create vertex
    bvertex_list = []
    face_vertex_list = [item for sublist in faces for item in sublist]
    bounding_edge_vertex_list = [item for sublist in bounding_edge_list for item in sublist]
    for v in vertex_list:
        if v.inside and (v.index in face_vertex_list or v.index in bounding_edge_vertex_list):
            new_vertex = bm.verts.new(v.coords_3d)
            new_vertex[roofeus_id_layer] = v.index
            bvertex_list.append(new_vertex)
        else:
            bvertex_list.append(None)  # Append to preserve index relation

    # Create faces
    new_faces = []
    for face in faces:
        if len(face) >= 3:
            face_vertex_list = []
            for i in face:
                if i >= 0:
                    face_vertex_list.append(bvertex_list[i])
                else:
                    face_vertex_list.append(target[-1-i].bl_vertex)
            bl_face = bm.faces.new(face_vertex_list)
            new_faces.append(bl_face)
        else:
            print("WARN: Incomplete face. len:", len(face))

    # fill uncompleted faces
    if props.fill_uncompleted and not props.delete_original_vertex:
        bpy.ops.mesh.select_mode(type='EDGE', action='ENABLE')
        bpy.ops.mesh.select_all(action='DESELECT')
        target_vertex = [t.bl_vertex for t in target]
        for v in target_vertex:
            for edge in v.link_edges:
                if all([edge_v in target_vertex for edge_v in edge.verts]):
                    edge.select = True

        for bounding_edge in bounding_edge_list:
            edge_verts = [bvertex_list[v] for v in bounding_edge]
            edge = bm.edges.get(edge_verts) or bm.edges.new(edge_verts)
            edge.select = True

        bpy.ops.mesh.fill()

    # Delete original vertex if specified
    if props.delete_original_vertex:
        bmesh.ops.delete(bm, geom=[target_vertex.bl_vertex for target_vertex in target], context='VERTS')

    # Select every new face
    bpy.ops.mesh.select_mode(type='FACE', action='ENABLE')
    for face in new_faces:
        face.select = True

    # Setup UVs
    for face in bm.faces:
        if face.select:
            for loop in face.loops:
                v_index = loop.vert[roofeus_id_layer]
                face.material_index = material_index
                if v_index >= 0:
                    loop[uv_layer].uv = (vertex_list[v_index].coords_2d[0],
                                         1 - vertex_list[v_index].coords_2d[1])
                else:
                    loop[uv_layer].uv = (target[-1 - v_index].uvs[0],
                                         1 - target[-1 - v_index].uvs[1])


def on_template_file_updated(self, context):
    """Executed when template file is updated"""
    props = context.scene.roofeus
    print("Updated Template", str(bpy.path.abspath(props.template_file)))


class RoofeusProperties(bpy.types.PropertyGroup):
    """Roofeus properties"""
    template_file: bpy.props.StringProperty(name="Template file",
                                            description="Template file to populate inside target face",
                                            subtype="FILE_PATH",
                                            update=on_template_file_updated)
    fill_uncompleted: bpy.props.BoolProperty(name="Fill uncompleted space",
                                             description="Fills the space between the target and generated faces",
                                             default=True)
    delete_original_vertex: bpy.props.BoolProperty(name="Delete original vertex",
                                                   description="Deletes the target vertex after processing",
                                                   default=False)
    delete_original_face: bpy.props.BoolProperty(name="Delete original face",
                                                 description="Deletes the target face after processing",
                                                 default=True)


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
                    create_result_mesh(bm, vertex_list, faces, target, orig_face.material_index, bounding_edge_list,
                                       context)

                bmesh.update_edit_mesh(obj.data)
                if props.delete_original_face and not props.delete_original_vertex:
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
