import sys

import numpy as np

from solid import scad_render_to_file, linear_extrude, rotate, translate
from solid.objects import cylinder
from solid.utils import extrude_along_path, arc

from euclid3 import Point2, Point3, Vector3

# Don't compile on GitHub Actions
GH_ACTIONS_DISABLE = True

nom_tube_rad_in = [
    5/32,
    1/4,
    3/16,
    5/16,
]

nom_tube_rad_mm = [25.4*r for r in nom_tube_rad_in]

# Extra clearance for tubes
tube_rads = [r + 0.25 for r in nom_tube_rad_mm]

# Radius of curvature
radius = 100

# Tube geometry
tube_rad = tube_rads[1]
tube_len = 4200

# Extra tube length leading into and out of spiral
tube_extra = radius*2

# Dimensions of dowel rods for part registration
dowel_rad = 3
dowel_len = 30

# Number of tube holding combs
num_combs = 8

def circle_points(rad, num_points):
    angles = np.linspace(0, 2*np.pi, num_points)
    points = list([Point2(rad*np.cos(a), rad*np.sin(a)) for a in angles])
    return points

def helix_pitch(tube_rad):
    # Pitch needs to be slightly higher than tube diameter for printability
    pitch = 2*tube_rad + 1
    return pitch

def helix_points(
        radius, pitch, length,
        helix_segments_per_rev=40, in_out_num_segments=3):
    # Approximate number of turns, rounded down
    num_turns = int(np.floor(length/(2*np.pi*radius)))

    nom_height = num_turns*pitch

    in_z = [0] * in_out_num_segments
    in_x = [radius] * in_out_num_segments
    in_y = list(np.linspace(-tube_extra, -radius/4, in_out_num_segments))

    helix_num_segments = helix_segments_per_rev*num_turns
    helix_default_dz = nom_height/helix_num_segments
    helix_t_end = num_turns*2*np.pi
    helix_t = np.linspace(0, helix_t_end, helix_num_segments)
    helix_x = list(radius*np.cos(helix_t))
    helix_y = list(radius*np.sin(helix_t))

    # Helix pitch needs to be greater at the ends to allow tube to enter and 
    # exit horizontally.
    helix_end_segment_angle = np.arccos(
        (radius - tube_rad/2)/(radius + tube_rad/2)
    )
    helix_extra_pitch = helix_end_segment_angle/(2*np.pi)*pitch
    segments_in_extra = np.floor(
        (2*np.pi - helix_end_segment_angle)/(2*np.pi)*helix_segments_per_rev
    )
    helix_extra_dz = helix_extra_pitch/segments_in_extra

    helix_z = []
    _helix_z = 0
    for t in helix_t:
        helix_z.append(_helix_z)

        if t == helix_t_end:
            break
        if (
                t < 2*np.pi - helix_end_segment_angle
                or t > (num_turns - 1)*2*np.pi + helix_end_segment_angle):
            _helix_z += helix_default_dz + helix_extra_dz
        else:
            _helix_z += helix_default_dz

    out_z = [_helix_z] * in_out_num_segments
    out_x = [radius] * in_out_num_segments
    out_y = list(np.linspace(radius/4, tube_extra, in_out_num_segments))

    x, y, z = (
        in_x + helix_x + out_x,
        in_y + helix_y + out_y,
        in_z + helix_z + out_z,
    )

    helix_points = list([Point3(_x, _y, _z) for _x, _y, _z in zip(x, y, z)])

    return helix_points

def max_span(points, axis):
    _min = getattr(points[0], axis)
    _max = getattr(points[0], axis)
    for p in points:
        pt = getattr(p, axis)
        if pt < _min:
            _min = pt
        if pt > _max:
            _max = pt
    return _max - _min

def assemblies():
    # Calculate comb/part splitting dimensions
    comb_offset_degrees = 360/num_combs
    comb_angle = comb_offset_degrees/2
    sections = num_combs*2

    # Calculate tube geometry and cut out of main cylinder
    tube_profile = circle_points(tube_rad, 30)
    pitch = helix_pitch(tube_rad)
    path = helix_points(radius, pitch, tube_len)
    path_height = max_span(path, "z")
    helix = extrude_along_path(tube_profile, path)
    helix_height = path_height + pitch
    cyl_height = helix_height + (8*dowel_rad)
    helix_offset = (cyl_height - path_height)/2

    # Main cylinder needs to be wide enough to completely contain the tube
    # spiral
    main_cyl = cylinder(r=radius + pitch, h=cyl_height)

    # Cut helix out of main cylinder
    main_cyl -= translate([0, 0, helix_offset])(helix)


    # Calculate core cutout geometry and cut out of main cylinder
    core_cyl = cylinder(r=radius - 4*pitch, h=cyl_height)
    main_cyl -= core_cyl

    # Calculate dowel geometry/positions and cut out of main cylinder
    dowel = rotate([90, 0, 0])(
        cylinder(r=dowel_rad, h=dowel_len, center=True)
    )
    for i in range(sections):
        _d = translate([radius - 3*pitch, 0, 0])(dowel)
        main_cyl -= rotate(i*comb_angle)(
            translate([0, 0, 2*dowel_rad])(_d)
            + translate([0, 0, cyl_height - 2*dowel_rad])(_d)
        )

    ## Calculate the comb geometry and cut out of main cylinder
    #comb_cut_cyl = (
    #    cylinder(r=radius + pitch, h=cyl_height)
    #    - cylinder(r=radius - pitch, h=cyl_height)
    #)
    #comb_cut_arc = linear_extrude(cyl_height)(
    #    arc(rad=radius + pitch, start_degrees=0, end_degrees=comb_angle)
    #)
    #for i in range(num_combs):
    #    comb_cut_cyl -= rotate(i*comb_offset_degrees)(comb_cut_arc)
    #main_cyl -= comb_cut_cyl

    # Split main cylinder into smaller parts for printing
    intersect_arc = linear_extrude(cyl_height)(
        arc(rad=2*radius, start_degrees=0, end_degrees=comb_angle)
    )
    a = []
    for i in range(sections):
        _a = rotate(i*comb_angle)(intersect_arc*main_cyl)
        if i % 2:
            _a *= cylinder(r=radius - pitch, h=cyl_height)
        a.append(_a)

    return a
    #return [main_cyl]

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    asms = assemblies()
    for idx, a in enumerate(asms):
        file_out = scad_render_to_file(a, f"spiral_thing_l{tube_len}_r{tube_rad}_R{radius}_{idx}.scad")
        print(f"{__file__}: SCAD file written to: \n{file_out}")

