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
    '''orientation of slots and tabs'''
    HORIZONTAL = 1
    VERTICAL = 2


class Alternation(Enum):
    '''alternation pattern of slots and tabs'''
    EVEN = 1
    ODD = 2

# %%


class LaserBox:
    '''
    A relatively simple open top box. 

    A traditional tool cut drawer box has a groove cut to accept the
    drawer bottom, this design differs in that the drawer bottom
    joins the sides using modified box joints, so no additional
    cuts or grooves are required.

    The floor can be inset to provide relief for ball bearing slides.

    All units are in millimeters unless otherwise noted.
    '''

    def __init__(self, filename='box.svg'):

        self.configure()
        # now for the nice linear run making the SVG
        # the viewbox is the magic to allow all units to be mm
        self.drawing = svgwrite.Drawing(filename,
                                        size=(f'{self.image_width}mm',
                                              f'{self.image_height}mm'),
                                        viewBox=(f'0 0 {self.image_width} {self.image_height}'))

        self.draw()

    def configure(self):
        '''configure the overall dimensions'''
        # overall bounds of the drawer
        self.width = 40
        self.depth = 80
        self.height = 35

        # parameters controlling the drawer details
        self.sheet_thickness = 3.175
        self.floor_inset = 6.35
        self.slide_width = 30
        self.joint_steps = 1

        # overall image size
        self.image_width = self.width + 2*self.height
        self.image_height = self.depth + 2*self.height


    def finger_notches(self, start: Point, end: Point, orientation: Orientation, alternation: Alternation, number, amplitude):
        '''create a buffer of square notched line segments'''
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


    def slots(self, start: Point, end: Point, orientation: Orientation, alternation: Alternation, number, amplitude):
        '''cut a series of slots from start to end'''

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
                self.drawing.add(self.drawing.rect(at, inset, stroke='red'))
            at = at + stride

    def draw_side(self, upper_left):
        '''draw a single side with notches for joinery'''
        trace = []
        # start at the upper left corner, let's draw clockwise
        # to the upper right
        upper_right = upper_left + Point(self.height, 0)
        trace.extend(self.finger_notches(upper_left, upper_right, Orientation.HORIZONTAL, Alternation.EVEN,
                                    self.joint_steps, self.sheet_thickness))
        # then a straight side
        lower_right = upper_right + Point(0, self.depth)
        trace.append(lower_right)
        lower_left = upper_left + Point(0, self.depth)
        # more notches for the front
        trace.extend(self.finger_notches(lower_right, lower_left, Orientation.HORIZONTAL, Alternation.EVEN,
                                    self.joint_steps, -self.sheet_thickness))
        trace.append(upper_left)

        self.drawing.add(self.drawing.polyline(trace, stroke='red'))


    def draw_end(self, upper_left):
        # and end with joinery that connects to the sides
        trace = []
        trace.append(upper_left)
        upper_right = upper_left + Point(self.width, 0)
        trace.append(upper_right)
        lower_right = upper_right + Point(0, self.height)
        trace.extend(self.finger_notches(upper_right, lower_right, Orientation.VERTICAL, Alternation.ODD,
                                    self.joint_steps, -self.sheet_thickness))
        lower_left = lower_right - Point(self.width, 0)
        trace.append(lower_left)
        trace.extend(self.finger_notches(lower_left, upper_left, Orientation.VERTICAL, Alternation.ODD,
                                    self.joint_steps, self.sheet_thickness))
        self.drawing.add(self.drawing.polyline(trace, stroke='red'))

    def draw_left(self):
        upper_left = Point(0, self.height)
        self.draw_side(upper_left)

    def draw_right(self):
        upper_left = Point(self.height + self.width, self.height)
        self.draw_side(upper_left)

    def draw_back(self):
        upper_left = Point(self.height, 0)
        self.draw_end(upper_left)

    def draw_front(self):
        upper_left = Point(self.height, self.height + self.depth)
        self.draw_end(upper_left)

    def draw_bottom(self):
        trace = []
        upper_left = Point(self.height, self.height)
        upper_right = upper_left + Point(self.width, 0)
        trace.extend(self.finger_notches(upper_left, upper_right,
                                    Orientation.HORIZONTAL, Alternation.EVEN, self.joint_steps, self.sheet_thickness))
        lower_right = upper_right + Point(0, self.depth)
        trace.extend(self.finger_notches(upper_right, lower_right,
                                    Orientation.VERTICAL, Alternation.EVEN, self.joint_steps, -self.sheet_thickness)),
        lower_left = lower_right - Point(self.width, 0)
        trace.extend(self.finger_notches(lower_right, lower_left,
                                    Orientation.HORIZONTAL, Alternation.EVEN, self.joint_steps, -self.sheet_thickness))
        trace.extend(self.finger_notches(lower_left, upper_left,
                                    Orientation.VERTICAL, Alternation.EVEN, self.joint_steps, self.sheet_thickness))
        self.drawing.add(self.drawing.polyline(trace, stroke='red'))


    def draw_slots(self):
        back_slots_from = Point(self.height, self.height - self.floor_inset - self.sheet_thickness)
        back_slots_to = back_slots_from + Point(self.width, 0)
        self.slots(back_slots_from, back_slots_to, Orientation.HORIZONTAL,
            Alternation.ODD, self.joint_steps, self.sheet_thickness)

        front_slots_from = Point(self.height, self.height + self.depth + self.floor_inset)
        front_slots_to = front_slots_from + Point(self.width, 0)
        self.slots(front_slots_from, front_slots_to, Orientation.HORIZONTAL,
            Alternation.ODD, self.joint_steps, self.sheet_thickness)

        left_slots_from = Point(self.height - self.floor_inset - self.sheet_thickness, self.height)
        left_slots_to = left_slots_from + Point(0, self.depth)
        self.slots(left_slots_from, left_slots_to, Orientation.VERTICAL,
            Alternation.ODD, self.joint_steps, self.sheet_thickness)

        right_slots_from = Point(self.height + self.width + self.floor_inset, self.height)
        right_slots_to = right_slots_from + Point(0, self.depth)
        self.slots(right_slots_from, right_slots_to, Orientation.VERTICAL,
            Alternation.ODD, self.joint_steps, self.sheet_thickness)

    def draw(self):
        self.draw_left()
        self.draw_right()
        self.draw_back()
        self.draw_front()
        self.draw_bottom()
        self.draw_slots()
        self.drawing.save()


#%%
drawer = LaserBox('drawer.svg')
display(SVG(drawer.drawing.tostring()))