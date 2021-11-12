import sys

import numpy as np

from solid import scad_render_to_file, rotate, translate, linear_extrude, text


def assembly():
    # Message needs to be reversed to be legible from inside of cylinder
    msg = list(reversed("hello"))
    char_width = 3
    radius = 10
    chars_per_circle = int(np.floor(2*np.pi*radius/char_width))
    step_angle = 360/chars_per_circle
    char_thickness = 1
    objs = []
    for i in range(chars_per_circle):
        objs.append(
            rotate(i*step_angle)(
                translate([radius, 0, 0])(
                    rotate([90, 0, -90])(
                        linear_extrude(char_thickness)(
                            text(
                                msg[i % len(msg)],
                                font="Courrier New; Style = Bold",
                                size=char_width,
                                valign="bottom",
                                halign="center"
                            )
                        )
                    )
                )
            )
        )

    return sum(objs)

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    a = assembly()
    file_out = scad_render_to_file(a, out_dir=out_dir, include_orig_code=True)
    print(f"{__file__}: SCAD file written to: \n{file_out}")