import socket
import urllib.request

from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.healthcheck.models.health_check_result_model import (
    HealthCheckResultModel,
    EndpointHealthCheckResultModel,
)
from app.config.models.health_check_config import HealthCheckProtocol
from app.config.models.scaling_group_dns_config import ScalingGroupConfiguration
from app.utils.logging import get_logger


class HealthCheckService(HealthCheckInterface):
    """Service for performing health check."""

    def __init__(self):
        self.logger = get_logger()

    def check(self, destination: str, sg_dns_config: ScalingGroupConfiguration) -> HealthCheckResultModel:
        """
        Performs a health check on a specified destination in accordance to given Scaling Group configuration.

        Args:
            destination (str): The address of the resource to run health check against. Can be IP, DNS name, etc.
            sg_dns_config (ScalingGroupConfiguration): The Scaling Group DNS configuration item.


        Returns:
            HealthCheckResultModel: The model that represents the result of the health check.
        """
        protocol: HealthCheckProtocol = sg_dns_config.health_check_config.protocol
        port: int = sg_dns_config.health_check_config.port
        path: str = sg_dns_config.health_check_config.path
        timeout_seconds: int = sg_dns_config.health_check_config.timeout_seconds

        match protocol:
            case HealthCheckProtocol.TCP:
                return self._tcp_check(destination, port, timeout_seconds)
            case HealthCheckProtocol.HTTP | HealthCheckProtocol.HTTPS:
                scheme = sg_dns_config.health_check_config.protocol.value.lower()
                return self._http_check(destination, scheme, port, path, timeout_seconds)
            case _:
                raise ValueError("Unsupported protocol. Only 'TCP' and 'HTTP(S)' are supported.")

    def _tcp_check(
        self,
        ip: str,
        port: int,
        timeout_seconds: int,
    ) -> HealthCheckResultModel:
        """
        Performs a TCP health check.

        Args:
            ip (str): The IP address to connect to.
            port (int): The port number to connect to.
            timeout_seconds (int): Connection timeout in seconds.

        Returns:
            HealthCheckResultModel: Model representing the result of the health check.
        """
        self.logger.info(f"Performing TCP health check on {ip}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout_seconds)
        try:
            result = sock.connect_ex((ip, port))
            return HealthCheckResultModel(
                [
                    EndpointHealthCheckResultModel(
                        healthy=result == 0,
                        protocol="TCP",
                        endpoint=f"{ip}:{port}",
                    )
                ]
            )
        except socket.error as e:
            msg = f"Socket error: {e}"
            self.logger.error(msg)
            return HealthCheckResultModel(
                [
                    EndpointHealthCheckResultModel(
                        healthy=False,
                        protocol="TCP",
                        endpoint=f"{ip}:{port}",
                        message=msg,
                    )
                ]
            )
        finally:
            sock.close()

    def _http_check(
        self,
        ip: str,
        scheme: str,
        port: str,
        path: str,
        timeout_seconds: str,
    ) -> HealthCheckResultModel:
        """
        Performs an HTTP health check.

        Args:
            ip (str): The IP address to send the request to.
            scheme (str): The HTTP scheme to use ('http' or 'https').
            port (str): The port number to send the request to.
            path (str): The HTTP path to request.
            timeout_seconds (str): Request timeout in seconds.

        Returns:
            HealthCheckResultModel: Model representing the result of the health check.
        """
        url = f"{scheme}://{ip}:{port}{path}"
        self.logger.info(f"Sending HTTP request to {url}")
        try:
            response = urllib.request.urlopen(url, timeout=timeout_seconds)
            return HealthCheckResultModel(
                [
                    EndpointHealthCheckResultModel(
                        healthy=response.getcode() == 200,
                        endpoint=ip,
                        protocol=scheme,
                        status=response.getcode(),
                        time_taken_s=response.getheader("X-Response-Time", 0),
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"HTTP check failed: {e}")
            return HealthCheckResultModel.UNHEALTHY()
