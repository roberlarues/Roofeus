from math import floor

import roofeus.models
from roofeus.utils import sub_vectors, add_vectors, mul_vector_by_scalar, size_vector, has_intersection
from roofeus.utils import calc_vector_lineal_combination_params, calculate_vertex_groups
from roofeus.models import RFVertexData, RFProjected2dVertex

# import matplotlib.pyplot as plt  # TODO quitar


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


def build_faces(structure, template, target, vertex_list):
    """
    Creates the faces
    :param structure: row[]: column[]; quad[]: vertex: int - inner mesh structure
    :param template: RFTemplate - template
    :param target: RFTargetVertex[] - target face
    :param vertex_list: VertexData[] - created vertex
    :return: created faces
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
        """A in-out vertex pair of an incomplete face"""
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
        """Edge of the target face"""
        def __init__(self, v1, v2, index):
            self.v1 = v1
            self.v2 = v2
            self.attached_in_outs = []
            self.size = size_vector(sub_vectors(v2.uvs, v1.uvs))
            self.index = index

    edge_list = []
    for i in range(0, len(target)):
        edge_list.append(Edge(target[i], target[(i + 1) % len(target)], i))

    # Part 2.3 - Calculate nearest edge of each pair
    def calc_nearest_edge(edges, io_data):
        """
        Calculates the nearest edge of the in-out pair
        :param edges: edge list
        :param io_data: in out pair
        :return: nearest edge
        """
        nearest = None
        inside_point = vertex_list[io_data.inside].coords_2d
        outside_point = vertex_list[io_data.outside].coords_2d
        for e in edges:
            if has_intersection((e.v1.uvs, e.v2.uvs), (inside_point, outside_point), 0.01):
                nearest = e
        return nearest

    # Plot target for test purpose
    # colors = ['ro-', 'go-', 'bo-', 'yo-']
    # for i in range(0, len(target)):
    #     plt.plot([target[i].uvs[0], target[(i + 1) % len(target)].uvs[0]],
    #              [target[i].uvs[1], target[(i + 1) % len(target)].uvs[1]], 'yo-')

    for in_out in pairs_in_out:
        nearest_edge = calc_nearest_edge(edge_list, in_out)
        # inside_p = vertex_list[in_out.inside].coords_2d
        # outside_p = vertex_list[in_out.outside].coords_2d
        if nearest_edge is None:
            print('IO pair with no nearest edge')
            # plt.plot([inside_p[0], outside_p[0]], [inside_p[1], outside_p[1]], 'yo-')
            continue
        # BEGIN PLOT
        # plt.plot([inside_p[0], outside_p[0]], [inside_p[1], outside_p[1]], colors[nearest_edge.index])
        # END PLOT
        contains = False
        for io in nearest_edge.attached_in_outs:
            if io.inside == in_out.inside:
                contains = True
                break
        if not contains:
            nearest_edge.attached_in_outs.append(in_out)
    # plt.show()

    # Part 2.4 - Build pending faces
    def build_pending_faces(v1, v2, pending_list):
        """
        Builds recursively faces from vertex v1, v2 and pending vertex list (only if they are visible
        :param v1: RFTargetVertex|int - vertex 1
        :param v2: RFTargetVertex|int - vertex 2
        :param pending_list:  InOut[] - pending vertex list
        :return: face list of
        """
        def is_visible(ref_coords, vertex, added_list):
            """
            Check if ref_coords are not occluded by added_list from vertex. In other words, checks if a imaginary ray
            traced from ref_coords to vertex intersects with the path formed by every vertex of added_list
            :param ref_coords: coords to check
            :param vertex: coords from
            :param added_list: already added vertex list
            :return: true if is visible
            """
            visible = True
            if len(added_list) > 1:
                for i in range(0, len(added_list) - 1):
                    if has_intersection((vertex_list[added_list[i]].coords_2d, vertex_list[added_list[i + 1]].coords_2d),
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
        ordered_vertex_list = sorted(edge.attached_in_outs, key=lambda x: size_vector(sub_vectors(edge.v1.uvs,
                                                                                                  vertex_list[x.inside].coords_2d)))
        p_faces, p_face_idx = build_pending_faces(edge.v1, edge.v2, ordered_vertex_list)
        faces.extend(p_faces)
        faces_index.extend(p_face_idx)
    return faces, faces_index


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
    faces, _faces_idx = build_faces(structure, template, target, vertex_list)
    return vertex_list, faces
