import roofeus.models as rfsm


def add_vectors(v1, v2):
    return tuple([v1[i] + v2[i] for i in range(0, len(v1))])


def sub_vectors(v1, v2):
    return tuple([v1[i] - v2[i] for i in range(0, len(v1))])


def mul_vector_by_scalar(vector, scalar):
    return tuple([value * scalar for value in vector])


def calc_vector_lineal_combination_params(a_t, b_t, v_t):
    a = (b_t[0] * v_t[1] - b_t[1] * v_t[0]) / (a_t[1] * b_t[0] - a_t[0] * b_t[1])
    if not b_t[0] == 0:
        b = (v_t[0] - a * a_t[0]) / b_t[0]
    else:
        b = (v_t[1] - a * a_t[1]) / b_t[1]
    return a, b


class Polygon:
    def __init__(self, vertex_list):
        self.vertex_list = vertex_list
        min_x = min([v[0] for v in vertex_list])
        min_y = min([v[0] for v in vertex_list])
        self.outer_vertex = (min_x - 1, min_y - 1)

    def contains(self, vertex):
        count_cross = 0
        b_v = sub_vectors(self.outer_vertex, vertex)
        for i in range(0, len(self.vertex_list)):
            a_v = sub_vectors(self.vertex_list[(i + 1) % len(self.vertex_list)], self.vertex_list[i])
            v_v = sub_vectors(vertex, self.vertex_list[i])
            a, b = calc_vector_lineal_combination_params(a_v, b_v, v_v)
            if 0 <= a <= 1 and b >= 0:
                count_cross += 1
        return count_cross % 2 == 1


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
