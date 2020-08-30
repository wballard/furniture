# %%
import numpy as np
import svgwrite
from scipy.spatial import Voronoi, voronoi_plot_2d
import cairosvg
import PIL
import subprocess
import math

# all units in 1pixel == 1mm
# width, height
scale = (900, 100)
width_of_lines = 4
width_of_sides = width_of_lines * 2
# this is the number of areas to knock out
tiles = 200
drill_radius = 1


points = np.array([
    (np.random.rand(), np.random.rand()) for i in range(tiles)
])
vor = Voronoi(points)
print(f"tiles {tiles}")


# borrowed from the internals of voronoi_plot_2d
center = vor.points.mean(axis=0)
ptp_bound = vor.points.ptp(axis=0)
finite_segments = []
infinite_segments = []
for pointidx, simplex in zip(vor.ridge_points, vor.ridge_vertices):
    simplex = np.asarray(simplex)
    if np.all(simplex >= 0):
        finite_segments.append(vor.vertices[simplex])
    else:
        i = simplex[simplex >= 0][0]  # finite end Voronoi vertex

        t = vor.points[pointidx[1]] - vor.points[pointidx[0]]  # tangent
        t /= np.linalg.norm(t)
        n = np.array([-t[1], t[0]])  # normal

        midpoint = vor.points[pointidx].mean(axis=0)
        direction = np.sign(np.dot(midpoint - center, n)) * n
        far_point = vor.vertices[i] + direction * ptp_bound.max()

        infinite_segments.append([vor.vertices[i], far_point])

dwg = svgwrite.Drawing('panel.svg', size=scale)
# overall frame 
# -- remember half of the width will fall off the canvas
dwg.add(dwg.rect((0, 0,), scale, fill='white',
                 stroke='black', stroke_width=width_of_sides*2))
# the sides - -need room to fold a tab
# to serve as a mounting point
dwg.add(dwg.rect((0, 0,), (width_of_sides*3, scale[1]), fill='black'))
dwg.add(dwg.rect((scale[0]-width_of_sides*3, 0,), (scale[0], scale[1]), fill='black'))


# all of the lines segments that outline the cells
for segment in (infinite_segments + finite_segments):
    from_point = segment[0] * scale
    to_point = segment[1] * scale
    dwg.add(dwg.line(from_point, to_point, stroke='black',
                     stroke_width=width_of_lines, stroke_linecap='round'))

# nibble the cornes to allow bends
nibble_size = (width_of_sides * 2 , width_of_lines)
dwg.add(dwg.rect((0, 0,), nibble_size, fill='white'))
dwg.add(dwg.rect((0, scale[1]-nibble_size[1],), nibble_size, fill='white'))
dwg.add(dwg.rect((scale[0]-width_of_sides*2, 0,), nibble_size, fill='white'))
dwg.add(dwg.rect((scale[0]-width_of_sides*2, scale[1]-nibble_size[1],), nibble_size, fill='white'))


# drill holes for attachment, this is done last since the cell strokes can overlap
if drill_radius:
  for y in [scale[1] / 2]:
      for x in [width_of_sides/2, scale[0] - width_of_sides/2]:
          dwg.add(dwg.circle(center=(x, y), r=drill_radius, fill='white'))
dwg.save()

# this will go in and out of a bitmap to trace the knock out tiles, keeping the black linkes, removing the white
cairosvg.svg2png(url='panel.svg', write_to='panel.png')
png = PIL.Image.open('panel.png')
png.save('panel.bmp')
subprocess.run("potrace --backend dxf panel.bmp --output panel.dxf", shell=True, check=True)
subprocess.run("potrace --backend svg panel.bmp --output panel.svg", shell=True, check=True)
