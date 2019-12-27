# %%
import numpy as np
import svgwrite
from scipy.spatial import Voronoi, voronoi_plot_2d
import cairosvg
import PIL
import subprocess
import math

# all units in 1pixel == 1mm

# this is the stroke width
width_of_lines = 6

# this is the size of the interior rectangle 
scale = (506, 1256)
HEXAGON = False


# now compute the list of points making the surrounding hexagon
# starting from the far left
frame = []
if HEXAGON:
    a = math.pi / 6
    triangle_height = scale[1] / 2
    triangle_width = math.tan(a) + triangle_height
    frame = [
        (0, triangle_height), # far left
        (triangle_width, 0), # up and right
        (scale[0] - triangle_width, 0), # further right
        (scale[0], triangle_height), # right and down
        (scale[0] - triangle_width, scale[1]), # back left -- and down
        (triangle_width, scale[1]), # back left
    ]
else:
    frame = [
        (0, 0),
        (0, scale[1]),
        (scale[0], scale[1]),
        (scale[0], 0)
    ]

# move the frame -- this makes space for the border
frame = [(f[0] + width_of_lines*2, f[1] + width_of_lines*2) for f in frame]

# and scale up the image to make room for the border
scale = (scale[0] + width_of_lines * 4, scale[1] + width_of_lines * 4)

# all the lines are computed now -- so just expand the size of the canvas a bit

# this is the number of areas to knock out
average_tile = 75 ** 2
tiles = math.floor(scale[0] * scale[1] / average_tile)

# and here is the tesselation
points = np.array([
    (np.random.rand(), np.random.rand()) for i in range(tiles)
])
vor = Voronoi(points)


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

dwg = svgwrite.Drawing('rawpanel.svg', size=scale)

# a big white background
dwg.add(dwg.rect(insert=(0, 0), size=scale, fill="white"))


# path frame -- this is a clipping region
path = "M {x} {y} ".format(x=frame[0][0], y=frame[0][1])
path += " ".join([" L {x} {y} ".format(x=point[0], y=point[1]) for point in frame[1:]])
path += " Z"
# and the actual frame
dwg.add(dwg.path(d=path, stroke='black', stroke_width=width_of_lines, fill="white"))


# all of the lines segments that outlines the cells, this is clipped to the bounding frame
clip_path = dwg.defs.add(dwg.clipPath(id="frame"))
clip_path.add(dwg.path(d=path))
voronoi_lines = dwg.add(dwg.g(id="voronoi", clip_path="url(#frame)", stroke="black", stroke_width=width_of_lines))
for segment in (infinite_segments + finite_segments):
    from_point = segment[0] * scale
    to_point = segment[1] * scale
    voronoi_lines.add(dwg.line(from_point, to_point))




dwg.save()

# this will go in and out of a bitmap to trace the knock out tiles, keeping the black linkes, removing the white
cairosvg.svg2png(url='rawpanel.svg', write_to='rawpanel.png')
png = PIL.Image.open('rawpanel.png')
png.save('panel.bmp')
subprocess.run("potrace --backend dxf panel.bmp --output panel.dxf", shell=True, check=True)
subprocess.run("potrace --backend svg panel.bmp --output panel.svg", shell=True, check=True)
