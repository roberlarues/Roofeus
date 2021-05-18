from math import floor
from roofeus.utils import sub_vectors, add_vectors, mul_vector_by_scalar, calc_vector_lineal_combination_params, Polygon


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

    polygon = Polygon([v.uvs for v in target])
    for row in projected_mesh:
        for col in row:
            for v in range(0, len(col)):
                if not polygon.contains(col[v]):
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
    vertex_groups = []
    for i in range(0, len(target) - 2):
        vertex_groups.append((target[i], target[i + 1], target[i + 2]))
    vertex_groups_polygons = [Polygon([v.uvs for v in group]) for group in vertex_groups]

    # Se itera sobre la malla proyectada
    mesh_3d = []
    for row in mesh_2d:
        row_3d = []
        for quad in row:
            quad_3d = []
            for v in quad:
                if len(v) == 0:
                    quad_3d.append(())
                else:
                    # Se itera sobre los subtriangulos de la cara para encontrar los vértices que lo contienen
                    for i in range(0, len(vertex_groups_polygons)):
                        vg_polygon = vertex_groups_polygons[i]
                        if vg_polygon.contains(v):
                            # Se desproyecta el vértice respecto a los 3 vértices del objetivo que lo contienen
                            quad_3d.append(transform_vertex(vertex_groups[i], v))
            row_3d.append(quad_3d)
        mesh_3d.append(row_3d)
    return mesh_3d


def build_faces(mesh_3d, template):
    faces = []
    faces_index = []
    for row_index in range(0, len(mesh_3d)):
        row = mesh_3d[row_index]
        for quad_index in range(0, len(row)):
            for face_idx in range(0, len(template.faces)):
                face = template.faces[face_idx]
                face_vertex = []
                vertex_idx_list = [i.ident for i in face.vertex]
                for vertex_idx in vertex_idx_list:
                    if vertex_idx < template.vertex_count:
                        # Self quad
                        self_quad = row[quad_index]
                        face_vertex.append(self_quad[vertex_idx])
                    elif vertex_idx < template.vertex_count * 2:
                        # Right quad
                        if quad_index + 1 < len(row):
                            right_quad = row[quad_index + 1]
                            face_vertex.append(right_quad[vertex_idx % template.vertex_count])
                    elif vertex_idx < template.vertex_count * 3:
                        # Bottom quad
                        if row_index + 1 < len(mesh_3d):
                            bottom_quad = mesh_3d[row_index + 1][quad_index]
                            face_vertex.append(bottom_quad[vertex_idx % template.vertex_count])
                    else:
                        # Diag quad
                        if quad_index + 1 < len(row) and row_index + 1 < len(mesh_3d):
                            diag_quad = mesh_3d[row_index + 1][quad_index + 1]
                            face_vertex.append(diag_quad[vertex_idx % template.vertex_count])

                if all([len(i) > 0 for i in face_vertex]):
                    faces.append(face_vertex)
                    faces_index.append(face_idx)
    return faces, faces_index


def create_mesh(template, target):
    mesh_2d = create_2d_mesh(template, target)
    mesh = transform_to_3d_mesh(target, mesh_2d)
    faces, faces_idx = build_faces(mesh, template)
    return mesh, faces, faces_idx
