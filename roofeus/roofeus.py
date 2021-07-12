from math import floor

import roofeus.models
from roofeus.utils import sub_vectors, add_vectors, mul_vector_by_scalar, size_vector, has_intersection
from roofeus.utils import calc_vector_lineal_combination_params, calculate_vertex_groups
from roofeus.models import RFVertexData, RFProjected2dVertex

# import matplotlib.pyplot as plt  # TODO quitar

def create_2d_mesh(template, target):
    """
    Crea una malla extendiendo el patrón definido en template dentro de la cara definida en target, atendiendo a los UVs
    de cada vértice
    :param template: RFTemplate - patrón a extender
    :param target: RFTargetVertex[] - cara sobre la que extender el patrón
    :return:
        projected_mesh: fila[]: columna[]; cuadrante[]: vertice: RFProjected2dVertex - malla proyectada en el espacio 2d (UVs)
    """
    min_x = floor(min([v.uvs[0] for v in target]))
    max_x = floor(max([v.uvs[0] for v in target]))
    min_y = floor(min([v.uvs[1] for v in target]))
    max_y = floor(max([v.uvs[1] for v in target]))

    # Se proyecta el patrón sobre un cuadrilatero que contiene las UVs de la cara objetivo, dejando un margen de +-1
    projected_mesh = []
    for j in range(min_y - 1, max_y + 1):
        row = []
        for i in range(min_x - 1, max_x + 1):
            projected_quad_vertex = []
            for tv in template.visible_vertex():
                projected_quad_vertex.append(RFProjected2dVertex(tv.coords[0] + i, tv.coords[1] + j))
            row.append(projected_quad_vertex)
        projected_mesh.append(row)

    # Se marcan aquellos que quedan dento del triángulo definido por los vértices de la cara
    _vg, vertex_groups_polygons = calculate_vertex_groups(target)
    for row in projected_mesh:
        for col in row:
            for v in range(0, len(col)):
                for polygon in vertex_groups_polygons:
                    if polygon.contains(col[v].coords):
                        col[v].inside = True
    return projected_mesh


def transform_to_3d_mesh(target, mesh_2d):
    """
    Convierte la malla proyectada al espacio 3d final
    :param target: RFTargetVertex[] - cara en el espacio 3d final
    :param mesh_2d: fila[]: columna[]; cuadrante[]: vertice: (int, int) - malla proyectada en el espacio 2d (UVs)
    :return:
        vertex_list: (int, int, int)[] - coordenadas de cada punto de la malla desproyectado en el espacio 3d final
        structure: fila[]: columna[]; cuadrante[]: vertice: int - estructura interna de la malla, haciendo referencia
                   mediante el índice de los puntos desproyectados de vertex_list
    """

    def transform_vertex(g, v):
        """
        Transforma el punto v a coordenadas 3D respecto al grupo de vertices g que lo contiene, interpolando el punto
        de coordenadas UVs a coordenadas reales
        :param g: grupo de vertices que contiene al vertice
        :param v: vértice en 2d
        :return: vértice en 3d
        """
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
    # vertex_list_2d = []
    vertex_index = 0

    # Se itera sobre la malla proyectada
    structure = []
    for row in mesh_2d:
        structure_row = []
        for quad in row:
            structure_quad = []
            for v in quad:
                # if len(v) == 0:
                # Se itera sobre los subtriangulos de la cara para encontrar los vértices que lo contienen
                found = False
                for i in range(0, len(vertex_groups_polygons)):
                    # Se desproyecta el vértice respecto a los 3 vértices del objetivo que lo contienen
                    if not found:
                        # vertex_list_2d.append(v.coords)
                        vertex_list.append(RFVertexData(vertex_index, v.coords,
                                                        transform_vertex(vertex_groups[i], v.coords), v.inside))
                        # structure_quad.append(RFProjectedQuadVertex(vertex_index, v.inside))
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


def build_faces(structure, template, target, vertex_list):
    """
    Crea las caras para la estructura y patrón indicados
    :param structure: fila[]: columna[]; cuadrante[]: vertice: int - estructura interna de la malla
    :param template: RFTemplate - patrón a extender
    :param target: RFTargetVertex[] - cara en el espacio 3d final
    :param target: RFProjected2dVertex[] -lista de vértices creados en el espacio 2D
    :return:
    """

    # Part 1 - Create full template faces
    faces = []
    faces_index = []
    faces_half = []
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

                if all([vertex_list[i].inside for i in face_vertex]):
                    faces.append(face_vertex)
                    faces_index.append(face_idx)
                elif not all([not vertex_list[i].inside for i in face_vertex]):
                    faces_half.append(face_vertex)

    # Part 2 - Fill between unconnected vertex and target

    # Part 2.1 - Fill in-out pairs
    class InOut:
        def __init__(self, i, o):
            self.inside = i
            self.outside = o
            self.nearest_vertex = None

    pairs_in_out = []
    for half_face in faces_half:
        face_inside = []
        outside = None
        for v in half_face:
            if vertex_list[v].inside:
                face_inside.append(v)
            else:
                outside = v

        for inside in face_inside:
            pairs_in_out.append(InOut(inside, outside))

    # Part 2.2 - Find edges
    class Edge:
        def __init__(self, v1, v2, index):
            self.v1 = v1
            self.v2 = v2
            self.attached_in_outs = []
            self.size = size_vector(sub_vectors(v2.uvs, v1.uvs))
            self.index = index

    edge_list = []
    # TODO Asumo triángulos, pero podrán ser quads
    for i in range(0, len(target)):
        edge_list.append(Edge(target[i], target[(i + 1) % len(target)], i))

    # Part 2.3 - foreach io in pairs_in_out -> calcPOF()
    def calc_nearest_edge(edges, io):
        nearest = None
        inside_p = vertex_list[io.inside].coords_2d
        outside_p = vertex_list[io.outside].coords_2d
        edge_index = 0
        for edge in edges:
            if has_intersection((edge.v1.uvs, edge.v2.uvs), (inside_p, outside_p), 0.01):
                nearest = edge
            edge_index += 1
        return nearest

    # colors = ['ro-', 'go-', 'bo-']
    # for i in range(0, 3):
    #     plt.plot([target[i].uvs[0], target[(i + 1) % 3].uvs[0]], [target[i].uvs[1], target[(i + 1) % 3].uvs[1]], 'yo-')

    for in_out in pairs_in_out:
        nearest_edge = calc_nearest_edge(edge_list, in_out)
        # inside_p = vertex_list_2d[in_out.inside]
        # outside_p = vertex_list_2d[in_out.outside]
        if nearest_edge is None:
            print('IO pair with no nearest edge')
            # plt.plot([inside_p[0], outside_p[0]], [inside_p[1], outside_p[1]], 'yo-')
            continue
        # BEGIN PLOT
        # plt.plot([inside_p[0], outside_p[0]], [inside_p[1], outside_p[1]], colors[nearest_edge.index])
        # END PLOT
        # in_out.nearest_vertex = calc_nearest_vertex(nearest_edge, in_out)
        contains = False
        for io in nearest_edge.attached_in_outs:
            if io.inside == in_out.inside:
                contains = True
                break
        if not contains:
            nearest_edge.attached_in_outs.append(in_out)
    # plt.show()

    # Part 2.4 - foreach z in Z -> fillZ
    def order_from_distance_to(vertex_target_coords, io_list):
        return sorted(io_list,
                      key=lambda io: size_vector(sub_vectors(vertex_target_coords, vertex_list[io.inside].coords_2d)))

    def build_pending_faces(v1, v2, pending_list):
        def is_visible(ref_coords, vertex, added):
            visible = True
            if len(added) > 1:
                for i in range(0, len(added) - 1):
                    if has_intersection((vertex_list[added[i]].coords_2d, vertex_list[added[i + 1]].coords_2d),
                                        (ref_coords, vertex), -0.05):
                        visible = False
                        break
            return visible

        v1_coords = v1.uvs if type(v1) is roofeus.models.RFTargetVertex else vertex_list[v1].coords_2d
        v1_index = v1.ident if type(v1) is roofeus.models.RFTargetVertex else v1
        v2_index = v2.ident if type(v2) is roofeus.models.RFTargetVertex else v2
        pending = []
        added = []
        last = None
        v_count = 0
        pending_faces = []
        pending_face_idx = []
        for v in pending_list:
            v_count += 1
            if is_visible(v1_coords, vertex_list[v.inside].coords_2d, added):
                if len(pending) > 0:
                    pf, pfi = build_pending_faces(last, v.inside, pending)
                    pending_faces.extend(pf)
                    pending_face_idx.extend(pfi)
                    pending = []
                if last is not None:
                    pending_faces.append([last, v1_index, v.inside])
                    pending_face_idx.append(0)  # No importa
                if v_count == len(pending_list):
                    pending_faces.append([v1_index, v2_index, v.inside])
                    pending_face_idx.append(0)  # No importa
                last = v.inside
                added.append(v.inside)
            else:
                pending.append(v)

        if len(pending) > 0:
            pf, pfi = build_pending_faces(last, v2, pending)
            pending_faces.extend(pf)
            pending_face_idx.extend(pfi)
            pending_faces.append([v1_index, v2_index, last])
            pending_face_idx.append(0)  # No importa
        return pending_faces, pending_face_idx

    for edge in edge_list:
        ordered_vertex_list = order_from_distance_to(edge.v1.uvs, edge.attached_in_outs)
        pending_faces, pending_face_idx = build_pending_faces(edge.v1, edge.v2, ordered_vertex_list)
        faces.extend(pending_faces)
        faces_index.extend(pending_face_idx)
    return faces, faces_index


def create_mesh(template, target):
    """
    Llena la cara (target) con el patrón definido en la plantilla (template)
    :param template: RFTemplate - patrón de puntos
    :param target: RFTargetVertex[] - cara a rellenar
    :return:
        vertex_list:  - Lista de vértices a crear
        faces:  - Lista de caras a crear
        structure: - Datos internos de estructura
        faces_idx: - Índices de las caras (?)
    """
    mesh_2d = create_2d_mesh(template, target)
    vertex_list, structure = transform_to_3d_mesh(target, mesh_2d)
    faces, faces_idx = build_faces(structure, template, target, vertex_list)
    return vertex_list, faces, structure, faces_idx
