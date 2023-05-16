"""This module provides a connection object between PyGeometry and the Geometry API
server."""


import io
import os

from ansys.api.geometry.v0.admin_pb2 import LogsRequest, LogsTarget, PeriodType
from ansys.api.geometry.v0.admin_pb2_grpc import AdminStub
from grpc import Channel

class Admin:
    """
    Provides a connection object between PyGeometry and the Geometry API server.

    Parameters
    ----------
    channel:
        gRPC channel for initializing the ``AdminStub`` object.
    """

    def __init__(self, grpc_channel: Channel):
        """Creates the ``Admin`` object and the ``AdminStub`` objects."""
        self._grpc_channel = grpc_channel
        if grpc_channel is not None and isinstance(grpc_channel, Channel):
            self._admin = AdminStub(grpc_channel)
        else:
            raise Exception("Invalid gRPC channel.")

    def get_current_log(self):
        """
        Get the current log content.

        Returns
        -------
        ansys.api.geometry.v0.admin_pb2.LogsResponse[]
            In the case of the current log, the array contains only one
            ``LogResponse`` object.

            An array of objects containing:

            - log_name : str
                Name of the log file.
            - relative_path : str
                Relative path of the log's parent folder, starting from the
                server's root logs directory.
            - log_chunk : bytes[]
                Raw log data.

        Examples
        --------
        >>> from ansys.geometry.core.launcher import launch_local_modeler
        >>> client = launch_local_modeler()
        INFO -  -  connection - connect - Connection: gRPC channel created.
        INFO -  -  connection - wait_for_transient_failure - Connection: idle.
        INFO -  -  connection - wait_for_transient_failure - Connection: connecting.
        INFO -  -  connection - wait_for_transient_failure - Connection: ready.
        INFO -  -  connection - connect - Connection: connected to: 127.0.0.1:50055
        INFO - localhost:51454 -  geometry - _initialize_stubs - Ansys Geometry API client initialization...
        INFO - 127.0.0.1:50055 -  geometry - _initialize_stubs - Ansys Geometry API client initialization done.
        <grpc._channel.Channel object at 0x000002A331830DA0>
        >>> current_log= client.admin.get_current_log()
        >>> current_log[0].log_name
        'Application.log'
        >>> current_log[0].log_chunk
        b'2022-07-05 18:18:07,205 [...]
        >>> current_log[0].relative_path
        '20220705.1818.82388\\Logs\\'
        """
        result = []
        request = LogsRequest(
            period_type=PeriodType.CURRENT,
            target=LogsTarget.CLIENT,
            null_path=None,
            null_period=None,
        )
        response_iterator = self._admin.GetLogs(request)
        for response in response_iterator:
            result.append(response)
        return result

    def get_all_logs(self):
        """
        Get an array containing all server logs.

        Returns
        -------
        ansys.api.geometry.v0.admin_pb2.LogsResponse[]
            An array of objects containing:

            - log_name : str
                Name of the log file.
            - relative_path : str
                Relative path of the log's parent folder, starting from the
                server's root logs directory.
            - log_chunk : bytes[]
                Raw log data.

        Examples
        --------
        >>> from ansys.geometry.core.launcher import launch_geometry
        >>> client = launch_geometry()
        INFO -  -  connection - connect - Connection: gRPC channel created.
        INFO -  -  connection - wait_for_transient_failure - Connection: idle.
        INFO -  -  connection - wait_for_transient_failure - Connection: connecting.
        INFO -  -  connection - wait_for_transient_failure - Connection: ready.
        INFO -  -  connection - connect - Connection: connected to: 127.0.0.1:50055
        INFO - localhost:50055 -  geometry - _initialize_stubs - Ansys Geometry API client initialization...
        INFO - 127.0.0.1:50055 -  geometry - _initialize_stubs - Ansys Geometry API client initialization done.
        <grpc._channel.Channel object at 0x000002A331830DA0>
        >>> all_logs = client.admin.get_all_logs()
        >>> all_logs[1].log_name
        'Application.log'
        >>> all_logs[2].log_name
        'Ansys Geometry_7_4_2022_74524.log'
        >>> all_logs[2].relative_path
        '\\20220704.1119.74524\\Logs\\'
        """
        result = []
        request = LogsRequest(
            period_type=PeriodType.ALL, target=LogsTarget.CLIENT, null_path=None, null_period=None
        )
        response_iterator = self._admin.GetLogs(request)
        for response in response_iterator:
            result.append(response)
        return result

    def export_current_log(self, output_folder):
        """
        Export the current log file for the server and its relative folder hierarchy to
        an output folder.

        Parameters
        ----------
        output_folder : str
            Folder to copy the current log file for the server and its relative folder hierarchy to.

        Returns
        -------
        ansys.api.geometry.v0.admin_pb2.LogsResponse[]
            An array of objects containing:

            - log_name : str
                Name of the log file.
            - relative_path : str
                Relative path of the log's parent folder, starting from the
                server's root logs directory.
            - log_chunk : bytes[]
                Raw log data.

        Examples
        --------
        >>> from ansys.geometry.core.launcher import launch_geometry
        >>> client = launch_geometry()
        INFO -  -  connection - connect - Connection: gRPC channel created.
        INFO -  -  connection - wait_for_transient_failure - Connection: idle.
        INFO -  -  connection - wait_for_transient_failure - Connection: connecting.
        INFO -  -  connection - wait_for_transient_failure - Connection: ready.
        INFO -  -  connection - connect - Connection: connected to: 127.0.0.1:50055
        INFO - 127.0.0.1:50055 -  geometry - _initialize_stubs - Ansys Geometry API client initialization...
        INFO - 127.0.0.1:50055 -  geometry - _initialize_stubs - Ansys Geometry API client initialization done.
        <grpc._channel.Channel object at 0x000001F2D9FF0E48>
        >>> all_log = client.admin.export_current_log(r"D:\Tests\Copied Logs")
        """
        self.check_and_make_output_folder(output_folder)

        result = self.get_current_log()
        self.write_output_logs(output_folder, result)
        return result

    def export_all_logs(self, output_folder):
        """
        Export all log files for the server and their relative folder hierarchies to an
        output folder.

        Parameters
        ----------
        output_folder : str
            Folder to copy all log files for the server and their relative folder hierarchies to.

        Returns
        -------
        ansys.api.geometry.v0.admin_pb2.LogsResponse[]
            An array of objects containing:

            - log_name : str
                Name of the log file.
            - relative_path : str
                Relative path of the log's parent folder, starting from the
                server's root logs directory.
            - log_chunk : bytes[]
                Raw log data.

        Examples
        --------
        >>> from ansys.geometry.core.launcher import launch_geometry
        >>> client = launch_geometry()
        INFO -  -  connection - connect - Connection: gRPC channel created.
        INFO -  -  connection - wait_for_transient_failure - Connection: idle.
        INFO -  -  connection - wait_for_transient_failure - Connection: connecting.
        INFO -  -  connection - wait_for_transient_failure - Connection: ready.
        INFO -  -  connection - connect - Connection: connected to: 127.0.0.1:50055
        INFO - 127.0.0.1:50055 -  geometry - _initialize_stubs - Ansys Geometry API client initialization...
        INFO - 127.0.0.1:50055 -  geometry - _initialize_stubs - Ansys Geometry API client initialization done.
        <grpc._channel.Channel object at 0x000001F2D9FF0E48>
        >>> all_log = client.admin.export_all_logs(r"D:\Tests\Copied Logs")
        """
        self.check_and_make_output_folder(output_folder)
        result = self.get_all_logs()
        self.write_output_logs(output_folder, result)
        return result

    def write_output_logs(self, output_folder, logs):
        """Write all output logs in the given folder."""
        if logs is not None and len(logs) > 0:
            for log in logs:
                folder = output_folder
                folder = folder + log.relative_path
                if not os.path.isdir(folder):
                    os.makedirs(folder)

                complete_path = os.path.join(folder, log.log_name)
                logBytes = io.BytesIO(bytes(log.log_chunk))
                f = open(complete_path, "wb")
                f.write(logBytes.read())
                f.close()

    def check_and_make_output_folder(self, output_folder):
        """
        Check if the output folder exists and write the log outputs.

        If an output folder does not exist in the given path, a new folder is created.
        """
        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)
