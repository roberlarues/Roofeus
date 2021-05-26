from math import floor
from roofeus.utils import sub_vectors, add_vectors, mul_vector_by_scalar
from roofeus.utils import calc_vector_lineal_combination_params, calculate_vertex_groups


def create_2d_mesh(template, target):
    min_x = floor(min([v.uvs[0] for v in target]))
    max_x = floor(max([v.uvs[0] for v in target]))
    min_y = floor(min([v.uvs[1] for v in target]))
    max_y = floor(max([v.uvs[1] for v in target]))

    projected_mesh = []
    for j in range(min_y, max_y + 1):
        row = []
        for i in range(min_x, max_x + 1):
            projected_quad_vertex = []
            for tv in template.visible_vertex():
                projected_quad_vertex.append((tv.coords[0] + i, tv.coords[1] + j))
            row.append(projected_quad_vertex)
        projected_mesh.append(row)

    _vg, vertex_groups_polygons = calculate_vertex_groups(target)
    for row in projected_mesh:
        for col in row:
            for v in range(0, len(col)):
                found = False
                for polygon in vertex_groups_polygons:
                    if polygon.contains(col[v]):
                        found = True
                if not found:
                    col[v] = ()
    return projected_mesh


def transform_to_3d_mesh(target, mesh_2d):
    def transform_vertex(g, v):
        o = g[0]
        a_t = sub_vectors(g[1].uvs, o.uvs)
        b_t = sub_vectors(g[2].uvs, o.uvs)
        v_t = sub_vectors(v, o.uvs)
        a, b = calc_vector_lineal_combination_params(a_t, b_t, v_t)
        v_a = mul_vector_by_scalar(sub_vectors(g[1].coords, o.coords), a)
        v_b = mul_vector_by_scalar(sub_vectors(g[2].coords, o.coords), b)
        return add_vectors(add_vectors(v_a, v_b), o.coords)

    # Se calculan los subtriangulos de la cara si tiene >3 vértices
    vertex_groups, vertex_groups_polygons = calculate_vertex_groups(target)

    vertex_list = []
    vertex_index = 0

    # Se itera sobre la malla proyectada
    structure = []
    for row in mesh_2d:
        structure_row = []
        for quad in row:
            structure_quad = []
            for v in quad:
                if len(v) == 0:
                    structure_quad.append(None)
                else:
                    # Se itera sobre los subtriangulos de la cara para encontrar los vértices que lo contienen
                    found = False
                    for i in range(0, len(vertex_groups_polygons)):
                        vg_polygon = vertex_groups_polygons[i]
                        if vg_polygon.contains(v):
                            # Se desproyecta el vértice respecto a los 3 vértices del objetivo que lo contienen
                            if not found:
                                vertex_list.append(transform_vertex(vertex_groups[i], v))
                                structure_quad.append(vertex_index)
                                vertex_index += 1
                                found = True
                            else:
                                print("Warn: vértice encontrado en 2 subtriángulos")
                    if not found:
                        structure_quad.append(None)
                        print("Error: Se esperaba que el vértice estuviera contenido en una cara")

            structure_row.append(structure_quad)
        structure.append(structure_row)
    return vertex_list, structure


def get_vertex_list(mesh):
    vertex_list = []
    for row in mesh:
        for quad in row:
            for vertex in quad:
                if len(vertex) > 0:
                    vertex_list.append(vertex)
    return vertex_list


def build_faces(structure, template):
    faces = []
    faces_index = []
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

                if all([i is not None for i in face_vertex]):
                    faces.append(face_vertex)
                    faces_index.append(face_idx)
    return faces, faces_index


def create_mesh(template, target):
    mesh_2d = create_2d_mesh(template, target)
    vertex_list, structure = transform_to_3d_mesh(target, mesh_2d)
    faces, faces_idx = build_faces(structure, template)
    return vertex_list, faces, structure, faces_idx
