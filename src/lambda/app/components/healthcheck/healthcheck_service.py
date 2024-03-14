import socket
import urllib.request
from enum import Enum

from app.config.models.health_check_config import HealthCheckConfig, HealthCheckProtocol
from app.config.models.scaling_group_dns_config import ScalingGroupDnsConfigItem
from app.utils.logging import get_logger


class Ec2HealthCheckService:
    """Service for performing health checks on EC2 instances."""

    def __init__(self):
        self.logger = get_logger()

    def check(self, destination: str, asg_dns_config: ScalingGroupDnsConfigItem) -> bool:
        """
        Perform a health check on an EC2 instance.

        Args:
            destination (str): The address of the resource to run health check against.
            path (str): The HTTP path to check, ignored for TCP checks.
            port (int): The port number to check.
            protocol (str): The protocol for the health check ('TCP' or 'HTTP').
            timeout_seconds (int): Timeout for the health check in seconds. Defaults to 60 seconds.

        Returns:
            bool: True if the health check passes, False otherwise.
        """
        protocol: HealthCheckProtocol = asg_dns_config.health_check_config.protocol
        port: int = asg_dns_config.health_check_config.port
        path: str = asg_dns_config.health_check_config.path
        timeout_seconds: int = asg_dns_config.health_check_config.timeout_seconds

        match protocol:
            case HealthCheckProtocol.TCP:
                return self._tcp_check(destination, port, timeout_seconds)
            case HealthCheckProtocol.HTTP | HealthCheckProtocol.HTTPS:
                scheme = asg_dns_config.health_check_config.protocol.value.lower()
                return self._http_check(destination, scheme, port, path, timeout_seconds)
            case _:
                raise ValueError("Unsupported protocol. Only 'TCP' and 'HTTP(S)' are supported.")

    def _tcp_check(self, ip: str, port: int, timeout_seconds: int) -> bool:
        """
        Performs a TCP health check.

        Args:
            ip (str): The IP address to connect to.
            port (int): The port number to connect to.
            timeout_seconds (int): Connection timeout in seconds.

        Returns:
            bool: True if the TCP connection is successful, False otherwise.
        """
        self.logger.info(f"Performing TCP health check on {ip}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout_seconds)
        try:
            result = sock.connect_ex((ip, port))
            return result == 0
        except socket.error as e:
            self.logger.error(f"Socket error: {e}")
            return False
        finally:
            sock.close()

    def _http_check(self, ip: str, scheme: str, port: str, path: str, timeout_seconds: str) -> bool:
        """
        Performs an HTTP health check.

        Args:
            ip (str): The IP address to send the request to.
            scheme (str): The HTTP scheme to use ('http' or 'https').
            port (str): The port number to send the request to.
            path (str): The HTTP path to request.
            timeout_seconds (str): Request timeout in seconds.

        Returns:
            bool: True if the HTTP request returns a 200 status code, False otherwise.
        """
        url = f"{scheme}://{ip}:{port}{path}"
        self.logger.info(f"Sending HTTP request to {url}")
        try:
            response = urllib.request.urlopen(url, timeout=timeout_seconds)
            return response.getcode() == 200
        except Exception as e:
            self.logger.error(f"HTTP check failed: {e}")
            return False
