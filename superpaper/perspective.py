"""
Display rotation correcting perspective transforms for Superpaper.

Having displays in a multi monitor setup both tilted and swiveled will
shear the wallpaper in disjoint pieces where lines are not preserved.
This module will research into alleviating or fixing this issue by applying
perspective corrections that aim to undo these effects caused by the rotations
of the displays relative to each other.

Written by Henri Hänninen, copyright 2020 under MIT licence.
"""

import math
from math import pi
import numpy as np

import superpaper.sp_logging as sp_logging

def get_backprojected_display_system(crops, persp_data, plot=False):
    """
    Return a back-projected quadrilateral and associated projection
    transformation coefficients for each display in the DisplaySystem.

    Displays are initialized in a flat plane in homogeneous coordinates
    front of the viewer using the size and offset data from DisplaySystem.
    These represent the display as they would be without any swivels or tilts.
    Then each display is rotated in 3D around a swivel axis and a tilt axis
    to get a 3D representation of the display setup.

    From this geometric setup, perspective corrections are computed by back-
    projecting the display corners back onto the initial common plane which
    represents the image plane. This produces stretched quadrilaterals that
    are used to compute the perspective correction coefficients that are used
    with Pillow to perform the perspective transformation on the source image.
    """
    # get_ppi_norm_crops: [(0, 695, 3840, 2855), (3943, 0, 5940, 3550)]
    # central_disp = 0
    # viewer_pos_wrt_central = (0, 0, 500/25.4 * 163) # (lateral, vert, depth)
    # crops = [(0, 695, 3840, 2855), (3943, 0, 5940, 3550)] # left, top, right, bottom
    # sizes = [(crp[2] - crp[0], crp[3] - crp[1]) for crp in crops]
    # swivels = (
    #     ("right", 0*pi/8, 0, 0),
    #     # ("left", 0*pi/16, 0, 0)
    #     ("left", 1.8*pi/8, 0, 0)
    # )
    # tilts = (
    #     # (0/360 * 2*pi, 0, 0),
    #     # (0/360 * 2*pi, 0, 0)
    #     # (1/360 * 2*pi, 0, 0),
    #     # (1/360 * 2*pi, 0, 0)
    #     (-2/360 * 2*pi, 0, 50/25.4 * 163),
    #     (-2/360 * 2*pi, 0, 50/25.4 * 163)
    # )

    sizes = [(crp[2] - crp[0], crp[3] - crp[1]) for crp in crops]
    central_disp = persp_data["central_disp"]
    viewer_pos_wrt_central = persp_data["viewer_pos"] # (lateral, vert, depth)
    swivels = persp_data["swivels"]
    tilts = persp_data["tilts"]
    sp_logging.G_LOGGER.info("swivs: %s", swivels)
    sp_logging.G_LOGGER.info("tilts: %s", tilts)

    disp_positions, init_plane_basis = position_displays_viewer(
        central_disp, viewer_pos_wrt_central, crops
    )
    init_plane_point = disp_positions[central_disp]

    projected_quads = []
    for sz, pos, swiv, tilt in zip(sizes, disp_positions, swivels, tilts):
        p_quad = get_backprojected_display(sz, pos, swiv, tilt,
                                           init_plane_basis, init_plane_point)
        projected_quads.append(p_quad)
    leftmost_corner = min(
        [corner[0] for quad in projected_quads for corner in quad])
    bottommost_corner = min(
        [corner[1] for quad in projected_quads for corner in quad])
    translated_quads = []
    for quad in projected_quads:
        work_quad = []
        for corner in quad:
            work_quad.append(
                (
                    int(round(corner[0] - leftmost_corner)),
                    int(round(corner[1] - bottommost_corner))
                )
            )
        translated_quads.append(work_quad)
    sp_logging.G_LOGGER.info("translated_quads: %s", translated_quads)
    ordered_quads = [(tquad[2], tquad[3], tquad[1], tquad[0])
                     for tquad in translated_quads]
    sp_logging.G_LOGGER.info("ordered_quads: %s", ordered_quads)
    ordered_crops = [crop_from_quad(ordqu) for ordqu in ordered_quads]
    sp_logging.G_LOGGER.info("ordered_crops: %s", ordered_crops)
    ppi_norm_corners = [
        (
            (crop[0], crop[1]),
            (crop[2], crop[1]),
            (crop[2], crop[3]),
            (crop[0], crop[3])
        )
        for crop in crops
    ]
    # print("ppi_norm_corners", ppi_norm_corners)
    projected_coeffs = []
    for ordquad, ppi_norm_quad in zip(ordered_quads, ppi_norm_corners):
        coeffs = find_coeffs(ordquad, ppi_norm_quad)
        projected_coeffs.append(coeffs)

    if plot:
        import matplotlib.pyplot as plt
        data = (ppi_norm_corners[0], ppi_norm_corners[1], ordered_quads[0], ordered_quads[1])
        colors = ("red", "orange", "blue", "cyan")
        # groups = ("orig", "rotated")

        fig = plt.figure()
        # ax = fig.add_subplot(1, 1, 1, facecolor="1.0")
        # for dat, color, group in zip(data, colors, groups):
        for dat, color in zip(data, colors):
            for corner in dat:
                # print(corner)
                x, y = corner
                # ax.scatter(x,    y, alpha=0.8, c=color, edgecolors='none', s=30)
                plt.plot(x, y, c=color, marker='o', linestyle='dashed', linewidth=2, markersize=6)
        plt.title('rot test')
        # plt.legend(loc=2)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.gca().invert_yaxis()
        plt.show()

    return (ordered_crops, projected_coeffs)


def position_displays_viewer(central_disp, viewer_pos_wrt_central, crops):
    """Return display positions in viewer coordinates and a basis for the
    initialized plane."""
    centers = [((crp[2] + crp[0]) / 2, (crp[3] + crp[1]) / 2) for crp in crops]
    view_lat_off, view_ver_off, view_dist = viewer_pos_wrt_central
    # Translate centers so that central_disp center is at (0, 0)
    cd_cent = centers[central_disp]
    transl_cents = [
        (
            cent[0] - cd_cent[0] + view_lat_off,
            cent[1] - cd_cent[1] + view_ver_off
        ) for cent in centers
    ]
    homog_cents = [
        np.array(
            (tracen[0], tracen[1], view_dist, 1)
        )
        for tracen in transl_cents
    ]
    basis = [
        np.array([1, 0, 0, 1]),
        np.array([0, 1, 0, 1]),
        np.array([0, 0, 1, 1]),
    ]
    return homog_cents, basis

def crop_from_quad(quad):
    """Return (left, top, right, bottom) from a list of 4 corners."""
    leftmost = min([corner[0] for corner in quad])
    topmost = min([corner[1] for corner in quad])
    rightmost = max([corner[0] for corner in quad])
    bottommost = max([corner[1] for corner in quad])
    return (leftmost, topmost, rightmost, bottommost)


def get_backprojected_display(display_size, display_center,
                              swivel_ax_ang_off, tilt_ang_off,
                              bproj_pln_basis, bproj_pln_point):
    """
    Return a quadrilateral that is produced then a display is back projected
    onto the plane of the assumed wallpaper, to be called 'poster plane'.

    Arguments needed are:
        - swivel angle & axis & axis offset from display edge in ppi norm res
        - tilt angle & axis offset from display surface horizontal mid line
        - distance of viewer in ppi norm res
        - height of viewer relative to the display. assume this to be 1/2?
            - lateral pos is assumed to be 1/2, centered to the display
        - display size (physical / ppi normalized resolution)

    Viewer (point camera) is taken to be at the origo of the world coordinates.
    The display is placed on the z-axis, centering it to (0, 0, view_dist).
    """

    swiv_ax, swiv_ang, swiv_loff, swiv_depth = swivel_ax_ang_off
    if swiv_ax == 0:
        # No swivel; keep code simpler by performing rotation of 0 degrees
        swiv_ax = "left"
        swiv_ang = 0
        swiv_loff = 0
        swiv_depth = 0
    elif swiv_ax == 1:
        swiv_ax = "left"
    elif swiv_ax == 2:
        swiv_ax = "right"
    tilt_ang, tilt_voff, tilt_depth = tilt_ang_off
    # convert angles to radians
    swiv_ang *= -1*2*pi/360 # something causes swivels go the wrong way; maybe the y-axis flip?
    tilt_ang *= 2*pi/360

    display_plane = XYPlaneRectangle(display_center, display_size)
    display_normal = display_plane.normal()
    display_basis = display_plane.basis()
    display_center = display_plane.center
    axis_swivel = display_plane.swivel_axis(swiv_ax,
                                            depth_offset=swiv_depth,
                                            lateral_offset=swiv_loff)
    axis_tilt = display_plane.tilt_axis(depth_offset=tilt_depth,
                                        vertical_offset=tilt_voff)

    # Swivel and tilt each corner of the display, specifically in this order
    disp_corners = display_plane.corners
    rotated_corners = tuple(
        swivel_and_tilt(corner, axis_tilt, tilt_ang, axis_swivel, swiv_ang)
        for corner in disp_corners
    )

    posterplane_normal = bproj_pln_basis[2]
    posterplane_basis = bproj_pln_basis[:-1]
    posterplane_center = bproj_pln_point

    # Back project display plane corners onto poster plane
    proj_corners = tuple(
        backproject_point_to_plane(
            crnr,
            posterplane_center,
            posterplane_normal)
        for crnr in rotated_corners)

    # Convert corners into poster plane coordinates
    poster_plane_corners = convert_to_plane_basis(
        proj_corners,
        posterplane_basis,
        posterplane_center
    )
    # print("disp_corners", disp_corners)
    # print("proj_corners", proj_corners)
    # print("display_plane.corners_2d", display_plane.corners_2d())
    # print("poster_plane_corners", poster_plane_corners)

    return poster_plane_corners


class XYPlaneRectangle():
    """Represent a rectangle in viewer coordinates."""
    def __init__(self, center, size):
        self.center = center
        self.size = size
        self.corners = self.get_corners()

    def get_corners(self):
        """Return rect corners as top left, top right, bot left, bot right."""
        width, height = self.size
        cent_x, cent_y, cent_z, cent_w = self.center
        corners = (
            np.array([cent_x - width/2, cent_y + height/2, cent_z, 1]),
            np.array([cent_x + width/2, cent_y + height/2, cent_z, 1]),
            np.array([cent_x - width/2, cent_y - height/2, cent_z, 1]),
            np.array([cent_x + width/2, cent_y - height/2, cent_z, 1]),
        )
        return corners

    def corners_2d(self):
        """Return plane corners in its own coordinates."""
        width, height = self.size
        corners = (
            (0, 0),
            (width, 0),
            (0, height),
            (width, height)
        )
        return corners

    def side_middle_pt(self, side):
        """Return the midpoint of side (left/right)."""
        if side == "left":
            mid = (self.corners[0]+self.corners[2]) / 2
        elif side == "right":
            mid = (self.corners[1]+self.corners[3]) / 2
        return mid

    def swivel_axis(self, side, depth_offset=0, lateral_offset=0):
        """Return swivel axis.

        Points from side midpoint to top side top corner."""
        side_mid = self.side_middle_pt(side)
        if side == "left":
            axis_end = self.corners[0]
        elif side == "right":
            axis_end = self.corners[1]
        axis = axis_end - side_mid
        pt_on_line = side_mid
        pt_on_line[0] += lateral_offset
        pt_on_line[2] += depth_offset
        return (axis, pt_on_line)

    def tilt_axis(self, side="left", depth_offset=0, vertical_offset=0):
        """Return tilt axis, including optional offsets.

        Choose positive rotation to tilt display upwards."""
        side_mid = self.side_middle_pt(side)
        if side == "left":
            axis = side_mid - self.center
        elif side == "right":
            axis = self.center - side_mid
        pt_on_line = side_mid
        pt_on_line[1] += vertical_offset
        pt_on_line[2] += depth_offset
        return (axis, pt_on_line)

    def normal(self):
        """Return the normal vector of the rectangle placed at the center.

        Take length 1 and points to -z direction."""
        normal = np.array(
            [
                self.center[0],
                self.center[1],
                self.center[2]-1,
                self.center[3],
            ]
        )
        return normal

    def basis(self):
        """Return homogenous crd vectors that parametrize the display
        plane up and right.

        Put the origo to the center of the display."""
        top_mid = (self.corners[0] + self.corners[1]) / 2
        right_mid = self.side_middle_pt("right")
        basis_x = right_mid
        basis_y = top_mid
        return (basis_x, basis_y)

def swivel_and_tilt(vector, axis_tilt, tilt, axis_swivel, swivel):
    """Swivel and tilt a vector around given axii."""
    swivel_vec = rotate_point_around_line(vector, axis_swivel, swivel)
    tilt_swiveled_vec = rotate_point_around_line(swivel_vec, axis_tilt, tilt)
    return tilt_swiveled_vec

def rotate_point_around_line(point, axis_with_pt, theta):
    """Return a point in homogenous coordinates that results in
    the rotation around a line.

    Point is the one to be rotated, axis is the direction of the line
    and point_on_line is a point on the line where to move the origo
    for the duration of the rotation.

    Analytical form of the translation + rotation in homogenous coordinates
    is
    M = [[R, p-Rp], [0^T, 1]]
    """
    axis, point_on_line = axis_with_pt
    ax_3d = np.array([axis[0], axis[1], axis[2]])
    rot_m = rotation_matrix(ax_3d, theta)
    p = np.array(
        [
            point_on_line[0],
            point_on_line[1],
            point_on_line[2]
        ]
    )
    p_rp = p - np.dot(rot_m, p)
    col_p_rp = np.array([[p_rp[0]], [p_rp[1]], [p_rp[2]]])

    zeros_transp = np.array([0, 0, 0])

    transl_and_rot = np.block([[rot_m, col_p_rp],
                               [zeros_transp, 1]])

    return np.dot(transl_and_rot, point)


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.

    Rodrigues' rotation formula.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])


def backproject_point_to_plane(point, point_on_plane, plane_normal):
    """Back-project a point along it's ray to a point on a plane
    parametrized with a normal and point."""
    norm = plane_normal - point_on_plane
    n_dot_r = np.dot(norm, point_on_plane)
    transform = np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [norm[0]/n_dot_r, norm[1]/n_dot_r, norm[2]/n_dot_r, 0]
        ]
    )
    projected_p = np.dot(transform, point)
    cartes_projected_p = projected_p / projected_p[3]
    return cartes_projected_p


def convert_to_plane_basis(points, basis, origo):
    """Covert homogenous coordinate points into 2d plane basis set at origo."""
    # pick cartesian part of basis
    base_x = (basis[0])[:-1]
    base_y = (basis[1])[:-1]
    # normalize to unit lenght
    unit_basis_vecs = (
        base_x/math.sqrt(np.dot(base_x, base_x)),
        base_y/math.sqrt(np.dot(base_y, base_y))
    )
    plane_coords = []
    for pnt in points:
        x = np.dot(unit_basis_vecs[0], (pnt - origo)[:-1])
        y = np.dot(unit_basis_vecs[1], (pnt - origo)[:-1])
        plane_coords.append((round(x), round(y)))
    return plane_coords


def find_coeffs(source_coords, target_coords):
    """Compute the perspective transfomation coefficients from source and
    target quadrilaterals.

    Quad corner order needs to be TOP LEFT, TOP RIGHT, BOTTOM RIGHT, BOTTOM LEFT.
    """
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
    A = np.matrix(matrix, dtype=np.float)
    B = np.array(source_coords).reshape(8)
    # res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    res = np.linalg.solve(A, B)
    return np.array(res).reshape(8)



# if __name__ == "__main__":
    # from PIL import Image

    # RESOLUTION_ARRAY = [(3840, 2160), (1440, 2560)]
    # DISPLAY_OFFSET_ARRAY = [(0, 200), (3840, 0)]

    # file = "~/Pictures/triangles.jpg"
    # img = Image.open(file)
    # cropped_images = []

    # get_backprojected_display_system(plot=True)

    # canvas_tuple_eff = tuple(compute_working_canvas(crop_tuples))
    # img_workingsize = resize_to_fill(img, canvas_tuple_eff)

    # for coeffs, res in zip(persp_coeffs, RESOLUTION_ARRAY):
    #     persp_crop = img_workingsize.transform(res, Image.PERSPECTIVE, coeffs,
    #                                             Image.LANCZOS)
    #     cropped_images.append(persp_crop)
    #     persp_crop.show()
