from math import floor
from roofeus.utils import sub_vectors, add_vectors, mul_vector_by_scalar, has_intersection, calc_intersection, Polygon
from roofeus.utils import calc_vector_lineal_combination_params, check_positive_normal, calculate_vertex_groups, size_vector
from roofeus.models import RFVertexData, RFProjected2dVertex


def create_2d_mesh(template, target):
    """
    Creates a temporal 2d mesh by extending the template covering all the vertex of the target on the UV space
    :param template: RFTemplate - template
    :param target: RFTargetVertex[] - target face
    :return:
        projected_mesh: row[]: column[]; cell[]: vertex: RFProjected2dVertex - projected 2d mesh
    """
    min_x = floor(min([v.uvs[0] for v in target]))
    max_x = floor(max([v.uvs[0] for v in target]))
    min_y = floor(min([v.uvs[1] for v in target]))
    max_y = floor(max([v.uvs[1] for v in target]))

    # Project vertices
    projected_mesh = []
    for j in range(min_y - 1, max_y + 2):
        row = []
        for i in range(min_x - 1, max_x + 2):
            projected_cell_vertex = []
            for tv in template.visible_vertex():
                projected_cell_vertex.append(RFProjected2dVertex(tv.coords[0] + i, tv.coords[1] + j))
            row.append(projected_cell_vertex)
        projected_mesh.append(row)

    # Check which projected vertices are inside the target
    polygon = calculate_vertex_groups(target)
    for row in projected_mesh:
        for col in row:
            for v in range(0, len(col)):
                if polygon.contains(col[v].coords):
                    col[v].inside = True
    return projected_mesh


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


def transform_to_3d_mesh(target, mesh_2d):
    """
    Converts the projected mesh to final 3d space
    :param target: RFTargetVertex[] - target face
    :param mesh_2d: row[]: column[]; cell[]: vertex: RFProjected2dVertex - projected 2d mesh
    :return:
        vertex_list: (int, int, int)[] - unprojected vertex to the final space
        structure: row[]: column[]; cell[]: vertice: int - Inner mesh structure, pointing index to vertex_list
    """

    vertex_list = []
    vertex_index = 0

    structure = []
    for row in mesh_2d:
        structure_row = []
        for cell in row:
            structure_cell = []
            for v in cell:
                vertex = get_nearest_target_vertex(target, v.coords, 0.001)
                if not vertex or vertex in vertex_list:
                    vertex = RFVertexData(vertex_index, v.coords, transform_vertex(target, v.coords), v.inside)
                    vertex_list.append(vertex)
                    vertex_index += 1
                structure_cell.append(vertex.index)
            structure_row.append(structure_cell)
        structure.append(structure_row)
    return vertex_list, structure


def ensure_good_normal_order(v1, v2, v3):  # TODO borrar
    if check_positive_normal(v1.coords_2d, v2.coords_2d, v3.coords_2d):
        return [v1.index, v2.index, v3.index]
    else:
        return [v1.index, v3.index, v2.index]


def get_nearest_target_vertex(target, intersection, threshold=0.005):
    target_vertex = None
    vertex = None
    for tv in target:
        if size_vector(sub_vectors(intersection, tv.uvs)) <= threshold:
            target_vertex = tv
            break
    if target_vertex:
        vertex = RFVertexData(target_vertex.ident, intersection, transform_vertex(target, intersection), True)
    return vertex


def get_face_vertex(template, structure, row_index, cell_index, face):
    row = structure[row_index]
    face_vertex = []
    vertex_idx_list = [i.ident for i in face.vertex]
    for vertex_idx in vertex_idx_list:
        if vertex_idx < template.vertex_count:
            # Self cell
            self_cell = row[cell_index]
            face_vertex.append(self_cell[vertex_idx % template.vertex_count])
        elif vertex_idx < template.vertex_count * 2:
            # Right cell
            if cell_index + 1 < len(row):
                right_cell = row[cell_index + 1]
                face_vertex.append(right_cell[vertex_idx % template.vertex_count])
        elif vertex_idx < template.vertex_count * 3:
            # Bottom cell
            if row_index + 1 < len(structure):
                bottom_cell = structure[row_index + 1][cell_index]
                face_vertex.append(bottom_cell[vertex_idx % template.vertex_count])
        else:
            # Diag cell
            if cell_index + 1 < len(row) and row_index + 1 < len(structure):
                diag_cell = structure[row_index + 1][cell_index + 1]
                face_vertex.append(diag_cell[vertex_idx % template.vertex_count])
    return face_vertex


def build_border_vertices(target, vertex_list, face_vertex, border_vertex, border_vertex_index):
    face_border_vertex = []
    for fi in range(0, len(face_vertex)):
        v1 = face_vertex[fi]
        for v2 in face_vertex[fi+1:]:
            for i in range(0, len(target)):
                r1 = (vertex_list[v1].coords_2d, vertex_list[v2].coords_2d)
                r2 = (target[i].uvs, target[(i + 1) % len(target)].uvs)
                if has_intersection(r1, r2, 0):
                    intersection = calc_intersection(r1, r2)
                    existing_vertex = list(
                        filter(lambda ev: ev.iv == v1 and ev.ov == v2 and ev.edge_index == i,
                               border_vertex))
                    if len(existing_vertex) > 0:
                        vertex = existing_vertex[0]
                    else:
                        vertex = get_nearest_target_vertex(target, intersection)

                        if not vertex or vertex.index in face_border_vertex:
                            # TODO asume target triangulo
                            vertex = RFVertexData(border_vertex_index, intersection,
                                                  transform_vertex(target, intersection), True)
                            border_vertex_index += 1
                            border_vertex.append(vertex)
                        vertex.ov = v2
                        vertex.iv = v1
                        vertex.edge_index = i
                    face_border_vertex.append(vertex.index)
    return border_vertex, border_vertex_index, face_border_vertex


def build_borders(target, vertex_list, faces, faces_index, face_idx, face_vertex, border_vertex, border_vertex_index):
    border_vertex, border_vertex_index, face_border_vertex = build_border_vertices(target, vertex_list, face_vertex,
                                                                                   border_vertex, border_vertex_index)

    face_polygon = Polygon([vertex_list[v].coords_2d for v in face_vertex])
    for vt in target:
        if face_polygon.contains(vt.uvs) and vt.ident not in face_border_vertex:
            face_border_vertex.append(vt.ident)

    for fv in face_vertex:
        if vertex_list[fv].inside and fv not in face_border_vertex:
            face_border_vertex.append(fv)

    faces.append(face_border_vertex)
    faces_index.append(face_idx)

    return border_vertex, border_vertex_index


def build_faces(structure, template, vertex_list, target, fill_uncompleted='border'):
    """
    Creates the faces
    :param structure: row[]: column[]; cell[]: vertex: int - inner mesh structure
    :param template: RFTemplate - template
    :param vertex_list: VertexData[] - created vertex
    :param target: RFTargetVertex[] - target face
    :param fill_uncompleted: Fills the space that template faces are not completely inside the target
    :return: created faces
    """
    faces = []
    faces_index = []
    bounding_edge_list = []
    border_vertex = []
    border_vertex_index = len(vertex_list)
    for row_index in range(0, len(structure) - 1):
        row = structure[row_index]
        for cell_index in range(0, len(row) - 1):
            for face_idx in range(0, len(template.faces)):
                face = template.faces[face_idx]
                face_vertex = get_face_vertex(template, structure, row_index, cell_index, face)

                if len(face_vertex) != 3:  # Shouldn't happen, the projected vertex covers all the target
                    continue

                if all([vertex_list[i].inside for i in face_vertex]):
                    # All faces are inside the target
                    faces.append(face_vertex)
                    faces_index.append(face_idx)
                elif str(fill_uncompleted) == 'border':
                    border_vertex, border_vertex_index = build_borders(target, vertex_list, faces,
                                                                       faces_index, face_idx, face_vertex,
                                                                       border_vertex, border_vertex_index)
                elif str(fill_uncompleted) == 'vertex':
                    if not all([not vertex_list[i].inside for i in face_vertex]):
                        inside = list(filter(lambda fvertex: vertex_list[fvertex].inside, face_vertex))
                        if len(inside) == 2:
                            bounding_edge_list.append(tuple(inside))
    return faces, faces_index, bounding_edge_list, border_vertex


def create_mesh(template, target, fill_uncompleted):
    """
    Fills the target with the pattern defined in template
    :param template: RFTemplate - template
    :param target: RFTargetVertex[] - target face
    :param fill_uncompleted: Fills the space that template faces are not completely inside the target
    :return:
        vertex_list:  - Vertex list to create
        faces:  - Face list to create
        structure: - Inner structure data
        faces_idx: - Face indexes (only for print)
    """
    mesh_2d = create_2d_mesh(template, target)
    vertex_list, structure = transform_to_3d_mesh(target, mesh_2d)
    faces, _faces_idx, bounding_edge_list, border_vertex = build_faces(structure, template, vertex_list, target,
                                                                       fill_uncompleted)
    vertex_list.extend(border_vertex)
    return vertex_list, faces, bounding_edge_list
