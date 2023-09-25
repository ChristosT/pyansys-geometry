# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""The plane surface class."""
from functools import cached_property

from beartype import beartype as check_input_types
from beartype.typing import Union
import numpy as np

from ansys.geometry.core.geometry.parameterization import (
    Interval,
    Parameterization,
    ParamForm,
    ParamType,
    ParamUV,
)
from ansys.geometry.core.geometry.surfaces.surface import Surface
from ansys.geometry.core.geometry.surfaces.surface_evaluation import SurfaceEvaluation
from ansys.geometry.core.math import (
    UNITVECTOR3D_X,
    UNITVECTOR3D_Z,
    Matrix44,
    Point3D,
    UnitVector3D,
    Vector3D,
)
from ansys.geometry.core.typing import Real, RealSequence


class Plane(Surface):
    """
    Provides 3D ``Plane`` representation.

    Parameters
    ----------
    origin : Union[~numpy.ndarray, RealSequence, Point3D],
        Centered origin of the torus.
    reference : Union[~numpy.ndarray, RealSequence, UnitVector3D, Vector3D]
        X-axis direction.
    axis : Union[~numpy.ndarray, RealSequence, UnitVector3D, Vector3D]
        X-axis direction.
    """

    def __init__(
        self,
        origin: Union[np.ndarray, RealSequence, Point3D],
        reference: Union[np.ndarray, RealSequence, UnitVector3D, Vector3D] = UNITVECTOR3D_X,
        axis: Union[np.ndarray, RealSequence, UnitVector3D, Vector3D] = UNITVECTOR3D_Z,
    ):
        """Initialize ``Plane`` class."""
        self._origin = Point3D(origin) if not isinstance(origin, Point3D) else origin

        self._reference = (
            UnitVector3D(reference) if not isinstance(reference, UnitVector3D) else reference
        )
        self._axis = UnitVector3D(axis) if not isinstance(axis, UnitVector3D) else axis
        if not self._reference.is_perpendicular_to(self._axis):
            raise ValueError("Plane reference (dir_x) and axis (dir_z) must be perpendicular.")

    @property
    def origin(self) -> Point3D:
        """Origin of the cylinder."""
        return self._origin

    @property
    def dir_x(self) -> UnitVector3D:
        """X-direction of the cylinder."""
        return self._reference

    @property
    def dir_y(self) -> UnitVector3D:
        """Y-direction of the cylinder."""
        return self.dir_z.cross(self.dir_x)

    @property
    def dir_z(self) -> UnitVector3D:
        """Z-direction of the cylinder."""
        return self._axis

    @check_input_types
    def __eq__(self, other: "Plane") -> bool:
        """Check whether two planes are equal."""
        return (
            self._origin == other._origin
            and self._reference == other._reference
            and self._axis == other._axis
        )

    def contains_param(self, param_uv: ParamUV) -> bool:
        """Check whether the plane contains a u and v pair point."""
        raise NotImplementedError("contains_param() is not implemented.")

    def contains_point(self, point: Point3D) -> bool:
        """Check whether the plane contains a 3D point."""
        raise NotImplementedError("contains_point() is not implemented.")

    def parameterization(self) -> tuple[Parameterization, Parameterization]:
        """Return plane parametrization."""
        u = Parameterization(ParamForm.OPEN, ParamType.LINEAR, Interval(np.NINF, np.inf))
        v = Parameterization(ParamForm.OPEN, ParamType.LINEAR, Interval(np.NINF, np.inf))

        return (u, v)

    def project_point(self, point: Point3D) -> SurfaceEvaluation:
        """Evaluate the plane at a given 3D point."""
        origin_to_point = point - self._origin
        u = origin_to_point.dot(self.dir_x)
        v = origin_to_point.dot(self.dir_y)
        return PlaneEvaluation(self, ParamUV(u, v))

    def transformed_copy(self, matrix: Matrix44) -> Surface:
        """Return transformed version of the plane given the transform matrix."""
        new_point = self.origin.transform(matrix)
        new_reference = self._reference.transform(matrix)
        new_axis = self._axis.transform(matrix)
        return Plane(
            new_point,
            UnitVector3D(new_reference[0:3]),
            UnitVector3D(new_axis[0:3]),
        )

    def evaluate(self, parameter: ParamUV) -> "PlaneEvaluation":
        """Evaluate the plane at a given u and v parameter."""
        return PlaneEvaluation(self, parameter)


class PlaneEvaluation(SurfaceEvaluation):
    """
    Provides ``Plane`` evaluation at certain parameters.

    Parameters
    ----------
    plane: ~ansys.geometry.core.primitives.plane.Plane
        The ``Plane`` object to be evaluated.
    parameter: ParamUV
        The parameters (u, v) at which the ``Plane`` evaluation is requested.
    """

    def __init__(self, plane: Plane, parameter: ParamUV) -> None:
        """``SphereEvaluation`` class constructor."""
        self._plane = plane
        self._parameter = parameter

    @property
    def plane(self) -> Plane:
        """The plane being evaluated."""
        return self._plane

    @property
    def parameter(self) -> ParamUV:
        """The parameter that the evaluation is based upon."""
        return self._parameter

    @cached_property
    def position(self) -> Point3D:
        """The point on the surface, based on the evaluation."""
        return (
            self.plane.origin
            + self.parameter.u * self.plane.dir_x
            + self.parameter.v * self.plane.dir_y
        )

    @cached_property
    def normal(self) -> UnitVector3D:
        """The normal to the surface."""
        return self.plane.dir_z

    @cached_property
    def u_derivative(self) -> Vector3D:
        """The first derivative with respect to u."""
        return self.plane.dir_z

    @cached_property
    def v_derivative(self) -> Vector3D:
        """The first derivative with respect to v."""
        return self.plane.dir_y

    @cached_property
    def uu_derivative(self) -> Vector3D:
        """The second derivative with respect to u."""
        return Vector3D([0, 0, 0])

    @cached_property
    def uv_derivative(self) -> Vector3D:
        """The second derivative with respect to u and v."""
        return Vector3D([0, 0, 0])

    @cached_property
    def vv_derivative(self) -> Vector3D:
        """The second derivative with respect to v."""
        return Vector3D([0, 0, 0])

    @cached_property
    def min_curvature(self) -> Real:
        """The minimum curvature."""
        return 0

    @cached_property
    def min_curvature_direction(self) -> UnitVector3D:
        """The minimum curvature direction."""
        return self.plane.dir_x

    @cached_property
    def max_curvature(self) -> Real:
        """The maximum curvature."""
        return 0

    @cached_property
    def max_curvature_direction(self) -> UnitVector3D:
        """The maximum curvature direction."""
        return self.plane.dir_y
