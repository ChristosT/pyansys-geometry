# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Modeling: Tessellation of two bodies
#
# This example shows how to create two stacked bodies and return the tessellation
# as two merged bodies.

# ## Perform required imports
#
# Perform the required imports.

# +
from pint import Quantity

from ansys.geometry.core import Modeler
from ansys.geometry.core.math import Point2D, Point3D, Plane
from ansys.geometry.core.misc import UNITS
from ansys.geometry.core.plotting import Plotter
from ansys.geometry.core.sketch import Sketch

# -

# ## Create design
#
# Create the basic sketches to be tessellated and extrude the sketch in the
# required plane. For more information on creating a component and extruding a
# sketch in the design, see the [Rectangular plate with multiple bodies](plate_with_hole.mystnb)
# example.
#
# Here is a typical situation in which two bodies, with different sketch planes,
# merge each body into a single dataset. This effectively combines all the faces
# of each individual body into a single dataset without separating faces.

# +
modeler = Modeler()

sketch_1 = Sketch()
box = sketch_1.box(
    Point2D([10, 10], unit=UNITS.m), width=Quantity(10, UNITS.m), height=Quantity(5, UNITS.m)
)
circle = sketch_1.circle(
    Point2D([0, 0], unit=UNITS.m), radius=Quantity(25, UNITS.m)
)

design = modeler.create_design("TessellationDesign")
comp = design.add_component("TessellationComponent")
body = comp.extrude_sketch("Body", sketch=sketch_1, distance=10 * UNITS.m)

# Create the second body in a plane with a different origin
sketch_2 = Sketch(Plane([0, 0, 10]))
box = sketch_2.box(Point2D(
    [10, 10], unit=UNITS.m), width=Quantity(10, UNITS.m), height=Quantity(5, UNITS.m)
)
circle = sketch_2.circle(
    Point2D([0, 10], unit=UNITS.m), radius=Quantity(25, UNITS.m)
)

body = comp.extrude_sketch("Body", sketch=sketch_2, distance=10 * UNITS.m)
# -

# ## Tessellate component as two merged bodies
#
# Tessellate the component and merge each body into a single dataset. This effectively
# combines all the faces of each individual body into a single dataset without
# separating faces.

dataset = comp.tessellate(merge_bodies=True)
dataset

# If you want to tessellate the body and return the geometry as triangles, single body tessellation
# is possible. If you want to merge the individual faces of the tessellation, enable the
# ``merge`` option so that the body is rendered into a single mesh. This preserves the number of
# triangles and only merges the topology.
#
# **Code without merging the body**

dataset = body.tessellate()
dataset

# **Code with merging the body**

mesh = body.tessellate(merge=True)
mesh

# ## Plot design
#
# Plot the design.

design.plot()
