class RFTargetVertex:
    """
    Existing vertex of the face that will be filled with the new mesh
    """
    id_neg = -1

    def __init__(self, x, y, z, u, v):
        self.ident = RFTargetVertex.id_neg  # int
        RFTargetVertex.id_neg -= 1
        self.coords = (x, y, z)  # (float, float, float)
        self.uvs = (u, v)  # (float, float)


class RFTemplate:
    """
    Template data that will be used as base to generate the new mesh
    """
    def __init__(self):
        self.vertex_count = 0  # int
        self.total_vertex_count = 0  # int
        self.vertex = []  # RFTemplateVertex[]
        self.faces = []  # RFTemplateFace[]
        self.face_colors = []  # (r,g,b)[]

    def calculate_ids(self):
        self.total_vertex_count = 0
        right_vertex = []
        bottom_vertex = []
        diag_vertex = []
        for v in self.vertex:
            v.ident = self.total_vertex_count
            vr = RFTemplateVertex(v.coords[0] + 1.0, v.coords[1])
            vb = RFTemplateVertex(v.coords[0], v.coords[1] + 1.0)
            vd = RFTemplateVertex(v.coords[0] + 1.0, v.coords[1] + 1.0)
            right_vertex.append(vr)
            bottom_vertex.append(vb)
            diag_vertex.append(vd)
            self.total_vertex_count += 1
        self.vertex_count = self.total_vertex_count

        for v in right_vertex:
            v.ident = self.total_vertex_count
            self.vertex.append(v)
            self.total_vertex_count += 1

        for v in bottom_vertex:
            v.ident = self.total_vertex_count
            self.vertex.append(v)
            self.total_vertex_count += 1

        for v in diag_vertex:
            v.ident = self.total_vertex_count
            self.vertex.append(v)
            self.total_vertex_count += 1

    def get_vertex_right(self, v):
        return self.vertex[v.ident + self.vertex_count]

    def get_vertex_bottom(self, v):
        return self.vertex[v.ident + self.vertex_count * 2]

    def get_vertex_diag_quad(self, v):
        return self.vertex[v.ident + self.vertex_count * 3]

    def visible_vertex(self):
        return self.vertex[:self.vertex_count] if self.vertex_count > 0 else self.vertex


class RFTemplateFace:
    """
    Face of the template
    """
    def __init__(self, a, b, c):
        self.vertex = (a, b, c)  # (int, int, int)


class RFTemplateVertex:
    """
    Vertex (2d) of the template
    """
    def __init__(self, x, y):
        self.ident = -1  # int
        self.coords = (x, y)  # (float, float)


class RFProjected2dVertex:
    """
    Temporal vertex that represents a projection of a template vertex on the target UV space
    """
    def __init__(self, x, y):
        self.coords = (x, y)  # (float, float)
        self.inside = False  # boolean


class RFVertexData:
    """
    Data of a roofeus output vertex that will be created in blender
    """
    def __init__(self, index, coords_2d, coords_3d, inside):
        self.index = index  # number
        self.coords_2d = coords_2d  # (float, float)
        self.coords_3d = coords_3d  # (float, float, float)
        self.inside = inside  # boolean
