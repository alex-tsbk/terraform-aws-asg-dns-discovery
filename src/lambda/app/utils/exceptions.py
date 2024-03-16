from app.config.instrumentation import RUNTIME_CONTEXT


class BusinessException(Exception):
    """Encapsulates an exception that is a business error"""

    pass


class CloudProviderException(Exception):
    """Encapsulates a cloud provider exception from concrete implementation of underlying cloud provider"""

    def __init__(self, underlying_exception: Exception, message: str = "Cloud provider error"):
        self.message = message
        self.underlying_exception = underlying_exception
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.message}: {self.underlying_exception}"

    def __repr__(self) -> str:
        return f"CloudProviderError({self.message}, {self.underlying_exception})"

    def is_aws(self) -> bool:
        """Returns True if the error is an AWS error, False otherwise"""
        if not RUNTIME_CONTEXT.is_aws:
            return False
        from botocore.exceptions import ClientError

        return isinstance(self.underlying_exception, ClientError)
