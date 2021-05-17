from models.RFTemplateVertex import RFTemplateVertex


class RFTemplate:
    def __init__(self):
        self.vertex_count = 0
        self.total_vertex_count = 0
        self.vertex = []
        self.faces = []
        self.face_colors = []

    def calculateIds(self):
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
        return self.vertex[:self.vertex_count]
