import roofeus.models as rfsm
import math


def add_vectors(v1, v2):
    """
    Adds 2 vector
    :param v1: vector 1
    :param v2: vector 2
    :return: v1 + v2
    """
    return tuple([v1[i] + v2[i] for i in range(0, len(v1))])


def sub_vectors(v1, v2):
    """
    Subtracts v2 to v1
    :param v1: vector 1
    :param v2: vector 2
    :return: v1 - v2
    """
    return tuple([v1[i] - v2[i] for i in range(0, len(v1))])


def size_vector(v):
    """
    Returns the l2 norm of a vector
    :param v: vector
    :return: norm l2
    """
    return math.sqrt(sum([i * i for i in v]))


def calc_intersection(r1, r2):
    """
    Calculates the intersection of 2 rects
    Maths from https://es.wikipedia.org/wiki/Intersecci%C3%B3n_de_dos_rectas
    :param r1:
    :param r2:
    :return:
    """
    p1, p2, p3, p4 = r1[0], r1[1], r2[0], r2[1]

    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    x3, y3 = p3[0], p3[1]
    x4, y4 = p4[0], p4[1]
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None  # parallel
    else:
        tmp_x = (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
        tmp_y = (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)
        return tuple([tmp_x / denom, tmp_y / denom])


def has_intersection(r1, r2, threshold=0.001):
    """
    Checks if 2 segments of different rects intersects
    :param r1: segment 1
    :param r2: segment 2
    :param threshold: threshold to consider no intersection
    :return: true if intersects
    """
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
    """
    Multiplies a vector by a scalar
    :param vector: vector
    :param scalar: scalar
    :return: vector * scalar
    """
    return tuple([value * scalar for value in vector])


def calc_vector_lineal_combination_params(a_t, b_t, v_t):
    """
    Calculates the linear combination of 2 vector (a_t and b_t) to be a third (v_t).
    :param a_t: vector 1
    :param b_t: vector 2
    :param v_t: target vector
    :return: a, b values that makes a * a_t + b * b_t == v_t
    """
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
    """
    Returns polygon data from a target face
    :param target: target face
    :return: polygon
    """
    return Polygon([v.uvs for v in target])


def check_positive_normal(v1, v2, v3):
    """
    Checks if the given order makes the normal positive
    :param v1: vertex 1
    :param v2: vertex 2
    :param v3: vertex 3
    """

    def cross_product_positive(a, b):
        return a[0] * b[1] - a[1] * b[0] >= 0

    v12 = sub_vectors(v2, v1)
    v13 = sub_vectors(v3, v1)
    return cross_product_positive(v13, v12)


def get_polygon_subtriangle_for_index(vlist, index):
    return [vlist[0], vlist[index + 1], vlist[index + 2]]


class Polygon:
    """
    2D convex Polygon
    For >3 vertices, vertex_list must be in cycle order
    """

    def __init__(self, vertex_list):
        self.vertex_list = vertex_list
        self.sub_polygons = []
        if len(self.vertex_list) > 3:
            for i in range(0, len(self.vertex_list) - 2):
                self.sub_polygons.append(Polygon(get_polygon_subtriangle_for_index(self.vertex_list, i)))

    def contains(self, vertex):
        """
        Checks if the vertex is inside the polygon
        :param vertex: vertex
        :return:
         - true if the vertex is inside
         - triangle vertex that contains the vertex. None if outside
        """
        found = True
        container_triangle_index = 0
        if len(self.vertex_list) == 3:
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
                    break
        else:
            found = False
            for pol in self.sub_polygons:
                inside, _inside_triangle = pol.contains(vertex)
                if inside:
                    found = True
                    break
                else:
                    container_triangle_index += 1

        return found, container_triangle_index


def read_template(filename):
    """
    Reads a template from file
    :param filename: filename of the template
    :return: template data
    """
    template = rfsm.RFTemplate()
    with open(filename) as f:
        content = f.readlines()

        all_vertex_read = False
        for line in content:
            line = line.strip()
            if line == 'f':
                all_vertex_read = True
                template.calculate_ids()
            elif not all_vertex_read:
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
                        v_idx.append(template.get_vertex_diag_cell(template.vertex[int(f_el.strip('d'))]))
                    else:
                        v_idx.append(template.vertex[int(f_el)])
                f = rfsm.RFTemplateFace(v_idx[0], v_idx[1], v_idx[2])
                template.faces.append(f)
    return template


def write_template(filename, template):
    """
    Writes a template to a file
    :param filename: filename of the template
    :param template: template to save
    """
    with open(filename, 'w') as f:
        for v in template.visible_vertex():
            f.write(f"{v.coords[0]},{v.coords[1]}\n")
        f.write("f\n")

        def get_vertex_ref_text(vertex):
            text = ""
            if vertex.ident < template.vertex_count:
                text = str(vertex.ident)
            elif vertex.ident < template.vertex_count * 2:
                text = f"{vertex.ident % template.vertex_count}r"
            elif vertex.ident < template.vertex_count * 3:
                text = f"{vertex.ident % template.vertex_count}b"
            elif vertex.ident < template.vertex_count * 4:
                text = f"{vertex.ident % template.vertex_count}d"
            return text

        for face in template.faces:
            v1_txt = get_vertex_ref_text(face.vertex[0])
            v2_txt = get_vertex_ref_text(face.vertex[1])
            v3_txt = get_vertex_ref_text(face.vertex[2])
            if check_positive_normal(face.vertex[0].coords, face.vertex[1].coords, face.vertex[2].coords):
                f.write(f"{v1_txt},{v2_txt},{v3_txt}\n")
            else:
                # Change order to flip normal
                f.write(f"{v1_txt},{v3_txt},{v2_txt}\n")
        f.close()
