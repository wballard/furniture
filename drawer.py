'''
This creates a laser cut drawer box as an SVG, inline with
jupyter so you can see what is happening as you tweak the parameters.
'''

# %%
import svgwrite
import typing
import math
from enum import Enum
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
width = 40
depth = 80
height = 40

# parameters controlling the drawer details
sheet_thickness = 3.175
floor_inset = 6.35
slide_width = 30
margin = 10
joint_steps = 1

# %%

# now for the nice linear run making the SVG
drawing = svgwrite.Drawing('drawer.svg',
    size=(f'{width + 2*height + margin}mm', f'{depth + 2*height + margin}mm'),
    viewBox=(f'0 0 {width + 2*height + margin} {depth + 2*height + margin}'))


class Point(typing.NamedTuple):
    '''simple subclass to allow operations -- like adding!
    '''

    x: float
    y: float

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)


class Orientation(Enum):
    HORIZONTAL = 1
    VERTICAL = 2


class Alternation(Enum):
    EVEN = 1
    ODD = 2


def finger_notches(start: Point, end: Point, orientation: Orientation, alternation: Alternation, number, amplitude):
    delta = end - start
    buffer = []
    if orientation == Orientation.HORIZONTAL:
        step_x = delta.x / (number * 2 + 1)
        stride = Point(step_x, 0)
        inset = Point(0, amplitude)
    if orientation == Orientation.VERTICAL:
        step_y = delta.y / (number * 2 + 1)
        stride = Point(0, step_y)
        inset = Point(amplitude, 0)
    if alternation == Alternation.EVEN:
        alternations = ['tab', 'notch'] * number + ['tab']
    if alternation == Alternation.ODD:
        alternations = ['notch', 'tab'] * number + ['notch']

    at = start
    for direction in alternations:
        if direction == 'tab':
            buffer.append(at)
            at = at + stride
            buffer.append(at)
        if direction == 'notch':
            buffer.append(at)
            at = at + inset
            buffer.append(at)
            at = at + stride
            buffer.append(at)
            buffer.append(at)
            at = at - inset

    return buffer


def slots(start: Point, end: Point, orientation: Orientation, alternation: Alternation, number, amplitude):

    delta = end - start
    if orientation == Orientation.HORIZONTAL:
        step_x = delta.x / (number * 2 + 1)
        stride = Point(step_x, 0)
        inset = Point(step_x, amplitude)
    if orientation == Orientation.VERTICAL:
        step_y = delta.y / (number * 2 + 1)
        stride = Point(0, step_y)
        inset = Point(amplitude, step_y)
    if alternation == Alternation.EVEN:
        alternations = ['keep', 'notch'] * number + ['keep']
    if alternation == Alternation.ODD:
        alternations = ['notch', 'keep'] * number + ['notch']

    at = start
    for direction in alternations:
        if direction == 'notch':
            drawing.add(drawing.rect(at, inset, stroke='red'))
        at = at + stride


# %%

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
    trace.extend(finger_notches(upper_left, upper_right, Orientation.HORIZONTAL, Alternation.EVEN,
                                joint_steps, sheet_thickness))
    # then a straight side
    lower_right = upper_right + Point(0, depth)
    trace.append(lower_right)
    lower_left = upper_left + Point(0, depth)
    # more notches for the front
    trace.extend(finger_notches(lower_right, lower_left, Orientation.HORIZONTAL, Alternation.EVEN,
                                joint_steps, -sheet_thickness))
    trace.append(upper_left)

    drawing.add(drawing.polyline(trace, stroke='red'))


def draw_back():
    upper_left = Point(margin + height, margin)
    draw_end(upper_left)


def draw_front():
    upper_left = Point(margin + height, margin + height + depth)
    draw_end(upper_left)


def draw_end(upper_left):
    # and end with joinery that connects to the sides
    trace = []
    trace.append(upper_left)
    upper_right = upper_left + Point(width, 0)
    trace.append(upper_right)
    lower_right = upper_right + Point(0, height)
    trace.extend(finger_notches(upper_right, lower_right, Orientation.VERTICAL, Alternation.ODD,
                                joint_steps, -sheet_thickness))
    lower_left = lower_right - Point(width, 0)
    trace.append(lower_left)
    trace.extend(finger_notches(lower_left, upper_left, Orientation.VERTICAL, Alternation.ODD,
                                joint_steps, sheet_thickness))
    drawing.add(drawing.polyline(trace, stroke='red'))


def draw_bottom():
    trace = []
    upper_left = Point(margin + height,
                       margin + height)
    upper_right = upper_left + Point(width, 0)
    trace.extend(finger_notches(upper_left, upper_right,
                                Orientation.HORIZONTAL, Alternation.EVEN, joint_steps, sheet_thickness))
    lower_right = upper_right + Point(0, depth)
    trace.extend(finger_notches(upper_right, lower_right,
                                Orientation.VERTICAL, Alternation.EVEN, joint_steps, -sheet_thickness)),
    lower_left = lower_right - Point(width, 0)
    trace.extend(finger_notches(lower_right, lower_left,
                                Orientation.HORIZONTAL, Alternation.EVEN, joint_steps, -sheet_thickness))
    trace.extend(finger_notches(lower_left, upper_left,
                                Orientation.VERTICAL, Alternation.EVEN, joint_steps, sheet_thickness))
    drawing.add(drawing.polyline(trace, stroke='red'))


def draw_slots():
    back_slots_from = Point(margin + height + sheet_thickness,
                            margin + height - floor_inset - sheet_thickness)
    back_slots_to = back_slots_from + Point(width - 2 * sheet_thickness, 0)
    slots(back_slots_from, back_slots_to, Orientation.HORIZONTAL,
          Alternation.ODD, joint_steps, sheet_thickness)

    front_slots_from = Point(margin + height + sheet_thickness,
                             margin + height + depth + floor_inset)
    front_slots_to = front_slots_from + Point(width - 2 * sheet_thickness, 0)
    slots(front_slots_from, front_slots_to, Orientation.HORIZONTAL,
          Alternation.ODD, joint_steps, sheet_thickness)

    left_slots_from = Point(margin + height - floor_inset - sheet_thickness,
                            margin + height)
    left_slots_to = left_slots_from + Point(0, depth)
    slots(left_slots_from, left_slots_to, Orientation.VERTICAL,
          Alternation.ODD, joint_steps, sheet_thickness)

    right_slots_from = Point(margin + height + width + floor_inset,
                             margin + height)
    right_slots_to = right_slots_from + Point(0, depth)
    slots(right_slots_from, right_slots_to, Orientation.VERTICAL,
          Alternation.ODD, joint_steps, sheet_thickness)


# %%
draw_left()
draw_right()
draw_back()
draw_front()
draw_bottom()
draw_slots()
display(SVG(drawing.tostring()))
drawing.save()