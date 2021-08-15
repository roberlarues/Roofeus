from math import floor
from roofeus.utils import sub_vectors, add_vectors, mul_vector_by_scalar
from roofeus.utils import calc_vector_lineal_combination_params, calculate_vertex_groups
from roofeus.models import RFVertexData, RFProjected2dVertex


def create_2d_mesh(template, target):
    """
    Creates a temporal 2d mesh by extending the template covering all the vertex of the target on the UV space
    :param template: RFTemplate - template
    :param target: RFTargetVertex[] - target face
    :return:
        projected_mesh: row[]: column[]; quad[]: vertex: RFProjected2dVertex - projected 2d mesh
    """
    min_x = floor(min([v.uvs[0] for v in target]))
    max_x = floor(max([v.uvs[0] for v in target]))
    min_y = floor(min([v.uvs[1] for v in target]))
    max_y = floor(max([v.uvs[1] for v in target]))

    # Projects vertex
    projected_mesh = []
    for j in range(min_y - 1, max_y + 1):
        row = []
        for i in range(min_x - 1, max_x + 1):
            projected_quad_vertex = []
            for tv in template.visible_vertex():
                projected_quad_vertex.append(RFProjected2dVertex(tv.coords[0] + i, tv.coords[1] + j))
            row.append(projected_quad_vertex)
        projected_mesh.append(row)

    # Check which projected vertex are inside the target
    polygon = calculate_vertex_groups(target)
    for row in projected_mesh:
        for col in row:
            for v in range(0, len(col)):
                if polygon.contains(col[v].coords):
                    col[v].inside = True
    return projected_mesh


def transform_to_3d_mesh(target, mesh_2d):
    """
    Converts the projected mesh to final 3d space
    :param target: RFTargetVertex[] - target face
    :param mesh_2d: row[]: column[]; quad[]: vertex: RFProjected2dVertex - projected 2d mesh
    :return:
        vertex_list: (int, int, int)[] - unprojected vertex to the final space
        structure: row[]: column[]; quad[]: vertice: int - Inner mesh structure, pointing index to vertex_list
    """

    def transform_vertex(g, vert):
        """
        Transforms the v point to 3d coords according the g vertex group that contains it, interpolating from UV space
        to 3d space
        :param g: vertex group
        :param vert: 2d vertex
        :return: 3d vertex
        """
        o = g[0]
        a_t = sub_vectors(g[1].uvs, o.uvs)
        b_t = sub_vectors(g[2].uvs, o.uvs)
        v_t = sub_vectors(vert, o.uvs)
        a, b = calc_vector_lineal_combination_params(a_t, b_t, v_t)
        v_a = mul_vector_by_scalar(sub_vectors(g[1].coords, o.coords), a)
        v_b = mul_vector_by_scalar(sub_vectors(g[2].coords, o.coords), b)
        return add_vectors(add_vectors(v_a, v_b), o.coords)

    vertex_list = []
    vertex_index = 0

    structure = []
    for row in mesh_2d:
        structure_row = []
        for quad in row:
            structure_quad = []
            for v in quad:
                vertex_list.append(RFVertexData(vertex_index, v.coords, transform_vertex(target, v.coords), v.inside))
                structure_quad.append(vertex_index)
                vertex_index += 1
            structure_row.append(structure_quad)
        structure.append(structure_row)
    return vertex_list, structure


def build_faces(structure, template, vertex_list):
    """
    Creates the faces
    :param structure: row[]: column[]; quad[]: vertex: int - inner mesh structure
    :param template: RFTemplate - template
    :param vertex_list: VertexData[] - created vertex
    :return: created faces
    """
    faces = []
    faces_index = []
    bounding_edge_list = []
    for row_index in range(0, len(structure)):
        row = structure[row_index]
        for quad_index in range(0, len(row)):
            for face_idx in range(0, len(template.faces)):
                face = template.faces[face_idx]
                face_vertex = []
                vertex_idx_list = [i.ident for i in face.vertex]
                for vertex_idx in vertex_idx_list:
                    if vertex_idx < template.vertex_count:
                        # Self quad
                        self_quad = row[quad_index]
                        face_vertex.append(self_quad[vertex_idx % template.vertex_count])
                    elif vertex_idx < template.vertex_count * 2:
                        # Right quad
                        if quad_index + 1 < len(row):
                            right_quad = row[quad_index + 1]
                            face_vertex.append(right_quad[vertex_idx % template.vertex_count])
                    elif vertex_idx < template.vertex_count * 3:
                        # Bottom quad
                        if row_index + 1 < len(structure):
                            bottom_quad = structure[row_index + 1][quad_index]
                            face_vertex.append(bottom_quad[vertex_idx % template.vertex_count])
                    else:
                        # Diag quad
                        if quad_index + 1 < len(row) and row_index + 1 < len(structure):
                            diag_quad = structure[row_index + 1][quad_index + 1]
                            face_vertex.append(diag_quad[vertex_idx % template.vertex_count])

                if len(face_vertex) >= 3 and all([vertex_list[i].inside for i in face_vertex]):
                    faces.append(face_vertex)
                    faces_index.append(face_idx)
                elif len(face_vertex) == 2 or not all([not vertex_list[i].inside for i in face_vertex]):
                    vertex_inside = []
                    for v in face_vertex:
                        if vertex_list[v].inside:
                            vertex_inside.append(v)

                    if len(vertex_inside) == 2:
                        bounding_edge_list.append(tuple(vertex_inside))

    return faces, faces_index, bounding_edge_list


def create_mesh(template, target):
    """
    Fills the target with the pattern defined in template
    :param template: RFTemplate - template
    :param target: RFTargetVertex[] - target face
    :return:
        vertex_list:  - Vertex list to create
        faces:  - Face list to create
        structure: - Inner structure data
        faces_idx: - Face indexes (only for print)
    """
    mesh_2d = create_2d_mesh(template, target)
    vertex_list, structure = transform_to_3d_mesh(target, mesh_2d)
    faces, _faces_idx, bounding_edge_list = build_faces(structure, template, vertex_list)
    return vertex_list, faces, bounding_edge_list
