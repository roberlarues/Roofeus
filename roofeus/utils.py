import roofeus.models as rfsm
import math


def add_vectors(v1, v2):
    return tuple([v1[i] + v2[i] for i in range(0, len(v1))])


def sub_vectors(v1, v2):
    return tuple([v1[i] - v2[i] for i in range(0, len(v1))])


def size_vector(v):
    return math.sqrt(sum([i * i for i in v]))


# https://es.wikipedia.org/wiki/Intersecci%C3%B3n_de_dos_rectas
def calc_intersection(r1, r2):
    p1 = r1[0]
    p2 = r1[1]
    p3 = r2[0]
    p4 = r2[1]

    x1 = p1[0]
    y1 = p1[1]
    x2 = p2[0]
    y2 = p2[1]
    x3 = p3[0]
    y3 = p3[1]
    x4 = p4[0]
    y4 = p4[1]
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        # Son paralelas
        return None
    else:
        tmp_x = (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
        tmp_y = (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)
        return tuple([tmp_x / denom, tmp_y / denom])


def has_intersection(r1, r2, threshold=0.01):
    intersection_point = calc_intersection(r1, r2)
    if intersection_point is None:
        return False

    mult = 1 + threshold
    to_intersection_r1_1 = sub_vectors(intersection_point, r1[0])
    to_intersection_r1_2 = sub_vectors(intersection_point, r1[1])
    to_intersection_r2_1 = sub_vectors(intersection_point, r2[0])
    to_intersection_r2_2 = sub_vectors(intersection_point, r2[1])
    r1_size = size_vector(sub_vectors(r1[1], r1[0]))
    r2_size = size_vector(sub_vectors(r2[1], r2[0]))
    return size_vector(to_intersection_r1_1) <= r1_size * mult and size_vector(to_intersection_r1_2) <= r1_size * mult \
        and size_vector(to_intersection_r2_1) <= r2_size * mult and size_vector(to_intersection_r2_2) <= r2_size * mult


def mul_vector_by_scalar(vector, scalar):
    return tuple([value * scalar for value in vector])


def calc_vector_lineal_combination_params(a_t, b_t, v_t):
    divider = (a_t[1] * b_t[0] - a_t[0] * b_t[1])
    if divider == 0:
        divider_2 = (v_t[1] * b_t[0] - v_t[0] * b_t[1])
        if not divider_2 == 0:
            a = v_t[0] / b_t[0]
        else:
            print("Vectors not combinable")
            a = 0
    else:
        a = (b_t[0] * v_t[1] - b_t[1] * v_t[0]) / divider

    if not b_t[0] == 0:
        b = (v_t[0] - a * a_t[0]) / b_t[0]
    else:
        b = (v_t[1] - a * a_t[1]) / b_t[1]
    return a, b


def calculate_vertex_groups(target):
    vertex_groups_polygons = [Polygon([v.uvs for v in target])]
    return [target], vertex_groups_polygons


class Polygon:
    def __init__(self, vertex_list):
        self.vertex_list = vertex_list

    def contains(self, vertex):
        found = True
        for i in range(0, len(self.vertex_list)):
            v = self.vertex_list[i]
            va = self.vertex_list[(i + 1) % len(self.vertex_list)]  # Next
            vb = self.vertex_list[(i + len(self.vertex_list) - 1) % len(self.vertex_list)]  # Previous
            a_v = sub_vectors(va, v)
            b_v = sub_vectors(vb, v)
            v_v = sub_vectors(vertex, v)
            a, b = calc_vector_lineal_combination_params(a_v, b_v, v_v)
            if not (0 <= a <= 1 and b >= -0.01):
                found = False
        return found


def generate_test_template():
    template = rfsm.RFTemplate()
    v1 = rfsm.RFTemplateVertex(0.5, 0.2)
    v2 = rfsm.RFTemplateVertex(0.2, 0.8)
    v3 = rfsm.RFTemplateVertex(0.8, 0.8)

    template.vertex.append(v1)
    template.vertex.append(v2)
    template.vertex.append(v3)

    template.calculate_ids()

    template.faces.append(rfsm.RFTemplateFace(v1, v2, v3))
    template.faces.append(rfsm.RFTemplateFace(v1, template.get_vertex_right(v1), v3))
    template.faces.append(rfsm.RFTemplateFace(v3, template.get_vertex_right(v1), template.get_vertex_right(v2)))
    template.faces.append(rfsm.RFTemplateFace(v2, v3, template.get_vertex_bottom(v1)))
    template.faces.append(rfsm.RFTemplateFace(v3, template.get_vertex_right(v2), template.get_vertex_diag_quad(v1)))
    template.faces.append(rfsm.RFTemplateFace(v3, template.get_vertex_bottom(v1), template.get_vertex_diag_quad(v1)))

    template.face_colors = [(1, 0, 0), (0, 1, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 1, 0)]

    return template


def read_template(filename):
    template = rfsm.RFTemplate()
    with open(filename) as f:
        content = f.readlines()

        all_vertex_readed = False
        for line in content:
            line = line.strip()
            if line == 'f':
                all_vertex_readed = True
                template.calculate_ids()
            elif not all_vertex_readed:
                v_pos = line.split(',')
                v = rfsm.RFTemplateVertex(float(v_pos[0]), float(v_pos[1]))
                template.vertex.append(v)
            else:
                face_idx = line.split(',')
                v_idx = []
                for f_el in face_idx:
                    if 'r' in f_el:
                        v_idx.append(template.get_vertex_right(template.vertex[int(f_el.strip('r'))]))
                    elif 'b' in f_el:
                        v_idx.append(template.get_vertex_bottom(template.vertex[int(f_el.strip('b'))]))
                    elif 'd' in f_el:
                        v_idx.append(template.get_vertex_diag_quad(template.vertex[int(f_el.strip('d'))]))
                    else:
                        v_idx.append(template.vertex[int(f_el)])
                f = rfsm.RFTemplateFace(v_idx[0], v_idx[1], v_idx[2])
                template.faces.append(f)
    return template
