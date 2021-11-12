import sys

import numpy as np

from solid import scad_render_to_file, linear_extrude, rotate
from solid.objects import cylinder
from solid.utils import extrude_along_path, arc

from euclid3 import Point2, Point3, Vector3


radius = 10
tube_rad = 1
tube_len = 500

# Extra tube length leading into and out of spiral
tube_extra = radius*2


# Approximate number of turns, rounded down
num_turns = int(np.floor(tube_len/(2*np.pi*radius)))

# Pitch needs to be slightly higher than tube diameter for geometry to resolve
pitch = 2*tube_rad*1.01

# Cylinder needs to be slightly longer than helix for geometry to resolve
cyl_height_extra = 0.01

nom_height = num_turns*pitch

in_num_segments = 3
in_z = [tube_rad + cyl_height_extra] * in_num_segments
in_x = [radius] * in_num_segments
in_y = list(np.linspace(-tube_extra, -radius/4, in_num_segments))



helix_segments_per_rev = 40
helix_num_segments = helix_segments_per_rev*num_turns
helix_default_dz = nom_height/helix_num_segments
helix_t_end = num_turns*2*np.pi
helix_t = np.linspace(0, helix_t_end, helix_num_segments)
helix_x = list(radius*np.cos(helix_t))
helix_y = list(radius*np.sin(helix_t))

# Helix pitch needs to be greater at the ends to allow tube to enter and exit
# horizontally.
helix_end_segment_angle = np.arccos((radius - tube_rad/2)/(radius + tube_rad/2))
helix_extra_pitch = helix_end_segment_angle/(2*np.pi)*pitch
segments_per_rev = helix_num_segments/num_turns
segments_in_extra = np.floor(
    (2*np.pi - helix_end_segment_angle)/(2*np.pi)*segments_per_rev)
helix_extra_dz = helix_extra_pitch/segments_in_extra

helix_z = []
_helix_z = tube_rad + cyl_height_extra
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

out_num_segments = 3
out_z = [_helix_z] * out_num_segments
out_x = [radius] * out_num_segments
out_y = list(np.linspace(radius/4, tube_extra, out_num_segments))

x, y, z = (
    in_x + helix_x + out_x,
    in_y + helix_y + out_y,
    in_z + helix_z + out_z,
)

helix_points = list([Point3(_x, _y, _z) for _x, _y, _z in zip(x, y, z)])

cyl_height = _helix_z + tube_rad + cyl_height_extra

def circle_points(rad, num_points):
    angles = np.linspace(0, 2*np.pi, num_points)
    points = list([Point2(rad*np.cos(a), rad*np.sin(a)) for a in angles])
    return points

def assembly():
    circle = circle_points(tube_rad, 100)
    path = helix_points
    helix = extrude_along_path(circle, path)

    main_cyl = cylinder(r=radius + pitch, h=cyl_height)

    cut_cyl = (
        cylinder(r=radius + pitch, h=cyl_height)
        - cylinder(r=radius - pitch, h=cyl_height)
    )
    cut_arc = linear_extrude(cyl_height)(
        arc(rad=radius + pitch, start_degrees=0, end_degrees=45)
    )
    for i in range(4):
        cut_cyl -= rotate(i*90)(cut_arc)

    return main_cyl - cut_cyl - helix

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    a = assembly()
    file_out = scad_render_to_file(a, out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{file_out}")