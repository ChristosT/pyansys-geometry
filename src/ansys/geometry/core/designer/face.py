"""Provides the ``Face`` class module."""

from enum import Enum, unique

from ansys.api.geometry.v0.edges_pb2 import EdgeIdentifier
from ansys.api.geometry.v0.edges_pb2_grpc import EdgesStub
from ansys.api.geometry.v0.faces_pb2 import (
    EvaluateFaceRequest,
    FaceIdentifier,
    GetFaceLoopsRequest,
    GetFaceNormalRequest,
)
from ansys.api.geometry.v0.faces_pb2_grpc import FacesStub
from ansys.api.geometry.v0.models_pb2 import Edge as GRPCEdge
from beartype.typing import TYPE_CHECKING, List
from pint import Quantity

from ansys.geometry.core.connection import GrpcClient
from ansys.geometry.core.designer.edge import CurveType, Edge
from ansys.geometry.core.errors import protect_grpc
from ansys.geometry.core.math import Point3D, UnitVector3D
from ansys.geometry.core.misc import SERVER_UNIT_AREA, SERVER_UNIT_LENGTH

if TYPE_CHECKING:  # pragma: no cover
    from ansys.geometry.core.designer.body import Body


@unique
class SurfaceType(Enum):
    """Provides an enum holding the possible values for surface types by the Geometry service."""

    SURFACETYPE_UNKNOWN = 0
    SURFACETYPE_PLANE = 1
    SURFACETYPE_CYLINDER = 2
    SURFACETYPE_CONE = 3
    SURFACETYPE_TORUS = 4
    SURFACETYPE_SPHERE = 5
    SURFACETYPE_NURBS = 6
    SURFACETYPE_PROCEDURAL = 7


@unique
class FaceLoopType(Enum):
    """Provides an enum holding the possible values for face loop types."""

    INNER_LOOP = "INNER"
    OUTER_LOOP = "OUTER"


class FaceLoop:
    """Provides an internal class holding the face loops defined by the server side.

    Notes
    -----
    This class is to be used only when parsing server side results. It is not
    intended to be instantiated by a user.

    Parameters
    ----------
    type : FaceLoopType
        Type of loop.
    length : Quantity
        Length of the loop.
    min_bbox : Point3D
        Minimum point of the bounding box containing the loop.
    max_bbox : Point3D
        Maximum point of the bounding box containing the loop.
    edges : List[Edge]
        Edges contained in the loop.
    """

    def __init__(
        self,
        type: FaceLoopType,
        length: Quantity,
        min_bbox: Point3D,
        max_bbox: Point3D,
        edges: List[Edge],
    ):

        self._type = type
        self._length = length
        self._min_bbox = min_bbox
        self._max_bbox = max_bbox
        self._edges = edges

    @property
    def type(self) -> FaceLoopType:
        """Type of the face loop."""
        return self._type

    @property
    def length(self) -> Quantity:
        """Length of the loop."""
        return self._length

    @property
    def min_bbox(self) -> Point3D:
        """Minimum point of the bounding box containing the loop."""
        return self._min_bbox

    @property
    def max_bbox(self) -> Point3D:
        """Maximum point of the bounding box containing the loop."""
        return self._max_bbox

    @property
    def edges(self) -> List[Edge]:
        """Edges contained in the loop."""
        return self._edges


class Face:
    """
    Represents a single face of a body within the design assembly.

    This class synchronizes to a design within a supporting Geometry service instance.

    Parameters
    ----------
    id : str
        Server-defined ID for the body.
    surface_type : SurfaceType
        Type of surface that the face forms.
    body : Body
        Parent body that the face constructs.
    grpc_client : GrpcClient
        Active supporting Geometry service instance for design modeling.
    """

    def __init__(self, id: str, surface_type: SurfaceType, body: "Body", grpc_client: GrpcClient):
        """Constructor method for the ``Face`` class."""

        self._id = id
        self._surface_type = surface_type
        self._body = body
        self._grpc_client = grpc_client
        self._faces_stub = FacesStub(grpc_client.channel)
        self._edges_stub = EdgesStub(grpc_client.channel)

    @property
    def id(self) -> str:
        """Face ID."""
        return self._id

    @property
    def _grpc_id(self) -> FaceIdentifier:
        """gRPC face ID."""
        return FaceIdentifier(id=self._id)

    @property
    def body(self) -> "Body":
        """Body that the face belongs to."""
        return self._body

    @property
    @protect_grpc
    def area(self) -> Quantity:
        """Calculated area of the face."""
        self._grpc_client.log.debug("Requesting face area from server.")
        area_response = self._faces_stub.GetFaceArea(self._grpc_id)
        return Quantity(area_response.area, SERVER_UNIT_AREA)

    @property
    def surface_type(self) -> SurfaceType:
        """Surface type of the face."""
        return self._surface_type

    @property
    @protect_grpc
    def edges(self) -> List[Edge]:
        """Get all edges of the face."""
        self._grpc_client.log.debug("Requesting face edges from server.")
        edges_response = self._faces_stub.GetFaceEdges(self._grpc_id)
        return self.__grpc_edges_to_edges(edges_response.edges)

    @property
    @protect_grpc
    def loops(self) -> List[FaceLoop]:
        """Get all face loops of the face."""
        self._grpc_client.log.debug("Requesting face loops from server.")
        grpc_loops = self._faces_stub.GetFaceLoops(GetFaceLoopsRequest(face=self.id)).loops
        loops = []
        for grpc_loop in grpc_loops:
            type = FaceLoopType(grpc_loop.type)
            length = Quantity(grpc_loop.length, SERVER_UNIT_LENGTH)
            min = Point3D(
                [
                    grpc_loop.boundingBox.min.x,
                    grpc_loop.boundingBox.min.y,
                    grpc_loop.boundingBox.min.z,
                ],
                SERVER_UNIT_LENGTH,
            )
            max = Point3D(
                [
                    grpc_loop.boundingBox.max.x,
                    grpc_loop.boundingBox.max.y,
                    grpc_loop.boundingBox.max.z,
                ],
                SERVER_UNIT_LENGTH,
            )
            grpc_edges = [
                self._edges_stub.GetEdge(EdgeIdentifier(id=edge_id)) for edge_id in grpc_loop.edges
            ]
            edges = self.__grpc_edges_to_edges(grpc_edges)
            loops.append(
                FaceLoop(type=type, length=length, min_bbox=min, max_bbox=max, edges=edges)
            )

        return loops

    @protect_grpc
    def face_normal(self, u: float = 0.5, v: float = 0.5) -> UnitVector3D:
        """Get the normal direction to the face evaluated at certain UV coordinates.

        Notes
        -----
        To properly use this method, you must handle UV coordinates. Thus, you must
        know how these relate to the underlying Geometry service. It is an advanced
        method for Geometry experts only.

        Parameters
        ----------
        u : float, default: 0.5
            First coordinate of the 2D representation of a surface in UV space.
            The default is the center of the surface.
        v : float, default: 0.5
            Second coordinate of the 2D representation of a surface in UV space.
            The default is the center of the surface.

        Returns
        -------
        UnitVector3D
            The :class:`UnitVector3D <ansys.geometry.core.math.vector.unitVector3D>`
            object evaluated at the given U and V coordinates.
            This :class:`UnitVector3D <ansys.geometry.core.math.vector.unitVector3D>`
            object is perpendicular to the surface at the given UV coordinates.
        """
        self._grpc_client.log.debug(f"Requesting face normal from server with (u,v)=({u},{v}).")
        response = self._faces_stub.GetFaceNormal(
            GetFaceNormalRequest(id=self.id, u=u, v=v)
        ).direction
        return UnitVector3D([response.x, response.y, response.z])

    @protect_grpc
    def face_point(self, u: float = 0.5, v: float = 0.5) -> Point3D:
        """Get a point of the face evaluated at certain UV coordinates.

        Notes
        -----
        To properly use this method, you must handle UV coordinates. Thus, you must
        know how these relate to the underlying Geometry service. It is an advanced
        method for Geometry experts only.

        Parameters
        ----------
        u : float, default: 0.5
            First coordinate of the 2D representation of a surface in UV space.
            The default is the center of the surface.
        v : float, default: 0.5
            Second coordinate of the 2D representation of a surface in UV space.
            The default is the center of the surface.

        Returns
        -------
        Point
            The :class:`Point3D <ansys.geometry.core.math.point.Point3D>`
            object evaluated at the given UV coordinates.
        """
        self._grpc_client.log.debug(f"Requesting face point from server with (u,v)=({u},{v}).")
        response = self._faces_stub.EvaluateFace(EvaluateFaceRequest(face=self.id, u=u, v=v)).point
        return Point3D([response.x, response.y, response.z], SERVER_UNIT_LENGTH)

    def __grpc_edges_to_edges(self, edges_grpc: List[GRPCEdge]) -> List[Edge]:
        """Transform a list of gRPC edge messages into actual ``Edge`` objects.

        Parameters
        ----------
        edges_grpc : List[GRPCEdge]
            List of gRPC messages of type ``Edge``.

        Returns
        -------
        List[Edge]
            ``Edge`` objects to obtain from gRPC messages.
        """
        edges = []
        for edge_grpc in edges_grpc:
            edges.append(
                Edge(edge_grpc.id, CurveType(edge_grpc.curve_type), self._body, self._grpc_client)
            )
        return edges
