.. _ref_sketch:

Sketch
*******

The PyAnsys Geometry :class:`sketch <ansys.geometry.core.sketch>` subpackage is used to build
2D basic shapes. Shapes consist of two fundamental constructs:

* **Edge**: A connection between two or more 2D points along a particular path. An edge represents an open shape
  such as an arc or line.
* **Face**: A set of edges that enclose a surface. A face represents a closed shape such as a circle or triangle.

To initialize a sketch, you first specify the :class:`Plane() <ansys.geometry.core.math.plane>` class, which
represents the plane in space from which other PyAnsys Geometry objects can be located.

This code shows how to initialize a sketch:

.. code:: python

    from ansys.geometry.core.sketch import Sketch

    sketch = Sketch()

You then construct a sketch, which can be done using different approaches.

Functional-style API
====================

A functional-style API is sometimes called a *fluent functional-style api* or *fluent API* in the developer community.
However, to avoid confusion with the Ansys Fluent product, the PyAnsys Geometry documentation refrains from using the latter terms.

One of the key features of a functional-style API is that it keeps an active context based on the previously created
edges to use as a reference starting point for additional objects.

The following code creates a sketch with its origin as a starting point. Subsequent calls create segments,
which take as a starting point the last point of the previous edge.

.. code:: python

    sketch.segment_to_point(Point2D([3, 3]), "Segment2").segment_to_point(
        Point2D([3, 2]), "Segment3"
    )
    sketch.plot()


A functional-style API is also able to get a desired shape of the sketch object by taking advantage
of user-defined labels:

.. code:: python

    sketch.get("<tag>")

.. jupyter-execute::
    :hide-code:

    from ansys.geometry.core.sketch import Sketch
    from ansys.geometry.core.math import Point2D

    sketch = Sketch()
    sketch.segment_to_point(Point2D([3, 3]), "Segment2").segment_to_point(
        Point2D([3, 2]), "Segment3"
    )
    sketch.plot()

Direct API
==========

A direct API is sometimes called an *element-based approach* in the developer community.

This code shows how you can use a direct API to create multiple elements independently
and combine them all together in a single plane:

.. code:: python

    sketch.triangle(
        Point2D([-10, 10]), Point2D([5, 6]), Point2D([-10, -10]), tag="triangle2"
    )
    sketch.plot()

.. jupyter-execute::
    :hide-code:

    from ansys.geometry.core.sketch import Sketch
    from ansys.geometry.core.math import Point2D

    sketch = Sketch()
    sketch.triangle(
        Point2D([-10, 10]), Point2D([5, 6]), Point2D([-10, -10]), tag="triangle2"
    )
    sketch.plot()

For more information on sketch shapes, see the :class:`Sketch() <ansys.geometry.core.sketch>`
subpackage.
