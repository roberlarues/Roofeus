from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt

import roofeus.roofeus as rfs
import roofeus.models as rfsm
from roofeus.utils import read_template


# Caras con >3 vértices deben de estar en orden para trianglestrip
def prepare_target():
    target = [
        rfsm.RFTargetVertex(0, 0, 0, -1, -1),
        rfsm.RFTargetVertex(0, 1, 1, -1, 1),
        rfsm.RFTargetVertex(1, 0, 0, 1, -1),
        rfsm.RFTargetVertex(1, 1, 1, 1, 1),
    ]
    return target


def plot_template(template):
    fig = plt.figure()
    ax = Axes3D(fig, auto_add_to_figure=False)
    fig.add_axes(ax)
    for face_idx in range(0, len(template.faces)):
        verts = [(v.coords[0], v.coords[1], 0.1) for v in template.faces[face_idx].vertex]
        coll = Poly3DCollection(verts)
        coll.set_color(template.face_colors[face_idx])
        ax.add_collection3d(coll)
    plt.show()


def plot_target(target):
    fig = plt.figure()
    ax = Axes3D(fig, auto_add_to_figure=False)
    fig.add_axes(ax)

    coll = Poly3DCollection([v.coords for v in target])
    coll.set_color((1, 1, 0))
    ax.add_collection3d(coll)
    plt.show()


def plot_mesh_2d(template, target, mesh):
    template_vertex_x = [v.coords[0] for v in template.visible_vertex()]
    template_vertex_y = [v.coords[1] for v in template.visible_vertex()]
    plt.plot(template_vertex_x, template_vertex_y, 'ro-')
    target_uv_x = [v.uvs[0] for v in target]
    target_uv_y = [v.uvs[1] for v in target]
    plt.plot(target_uv_x, target_uv_y, 'bo-')

    projected_vertex_x = []
    projected_vertex_y = []
    for row in mesh:
        for col in row:
            for v in col:
                if len(v) > 0:
                    projected_vertex_x.append(v[0])
                    projected_vertex_y.append(v[1])
    plt.plot(projected_vertex_x, projected_vertex_y, 'yo')
    plt.show()


def plot_faces(vertex_list, face_list, face_index, template):
    coli = 0
    fig = plt.figure()
    ax = Axes3D(fig, auto_add_to_figure=False)
    fig.add_axes(ax)

    for i in range(0, len(face_list)):
        coll = Poly3DCollection([vertex_list[j] for j in face_list[i]])
        coll.set_color(template.face_colors[face_index[i]])
        ax.add_collection3d(coll)
        coli = coli + 1
    plt.show()


if __name__ == '__main__':
    test_template = read_template('test_template.txt')
    test_template.face_colors = [(1, 0, 0), (0, 1, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 1, 0)]
    # plot_template(test_template)

    test_target = prepare_target()
    # plot_target(test_target)

    mesh_2d = rfs.create_2d_mesh(test_template, test_target)
    # plot_mesh_2d(test_template, test_target, mesh_2d)

    vertex_list, structure = rfs.transform_to_3d_mesh(test_target, mesh_2d)
    faces, faces_idx = rfs.build_faces(structure, test_template)
    plot_faces(vertex_list, faces, faces_idx, test_template)
