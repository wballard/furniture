'''
This creates a laser cut drawer box as an SVG, inline with
jupyter so you can see what is happening as you tweak the parameters.
'''

# %%
import svgwrite
import typing
import math
from IPython.core.display import display, SVG

# %%
'''
Here are the parameters, a drawer is a relatively simple
open top box, with relief cuts for concealed ball bearing
slides under the drawer bottom.

A traditional tool cut drawer box has a groove cut to accept the
drawer bottom, this design differs in that the drawer bottom
joins the sides using modified box joints, so no additional
cuts or grooves are required.

All units are in millimeters unless otherwise noted.
'''

# overall bounds of the drawer
width = 150
depth = 300
height = 50

# parameters controlling the drawer details
sheet_thickness = 12.7
floor_inset = 12.7
slide_width = 30
margin = 10
joint_steps = 4

# %%


class Point(typing.NamedTuple):
    '''simple subclass to allow operations -- like adding!
    '''

    x: float
    y: float

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)


def horizontal_finger_notches(start: Point, end: Point, number, amplitude):
    delta = end - start
    buffer = []
    step_x = delta.x / (number * 2 + 1)

    # now alternate tab and notching -- we'll have number+1 tabs
    # and number notches -- tab, notch
    alternations = ['tab', 'notch'] * number + ['tab']
    at = start
    for direction in alternations:
        if direction == 'tab':
            buffer.append(at)
            at = at + Point(step_x, 0)
            buffer.append(at)
        if direction == 'notch':
            buffer.append(at)
            at = at + Point(0, amplitude)
            buffer.append(at)
            at = at + Point(step_x, 0)
            buffer.append(at)
            buffer.append(at)
            at = at - Point(0, amplitude)

    return buffer


# %%
# now for the nice linear run making the SVG
drawing = svgwrite.Drawing(
    size=(f'{width + 2*height + margin}px', f'{depth + 2*height + margin}px'))

# the actual cuts will be a series of poly-lines, which are just
# a series of points -- let's start with the left side
# this will be a bit of a connect the dots activity


def draw_left():
    upper_left = Point(margin, margin + height)
    draw_side(upper_left)

def draw_right():
    upper_left = Point(margin + height + width, margin + height)
    draw_side(upper_left)

def draw_side(upper_left):
    # a side with notches for joinery
    trace = []
    # start at the upper left corner, let's draw clockwise
    # to the upper right
    upper_right = upper_left + Point(height, 0)
    trace.extend(horizontal_finger_notches(upper_left, upper_right,
                         joint_steps, sheet_thickness))
    # then a straight side
    lower_right = upper_right + Point(0, depth)                     
    trace.append(lower_right)
    lower_left = upper_left + Point(0, depth)
    # more notches for the front
    trace.extend(horizontal_finger_notches(lower_right, lower_left,
                         joint_steps, -sheet_thickness))
    trace.append(upper_left)

    drawing.add(drawing.polyline(trace, stroke='red'))


draw_left()
draw_right()
print(drawing.tostring())
display(SVG(drawing.tostring()))
