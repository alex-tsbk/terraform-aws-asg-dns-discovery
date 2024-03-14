from dataclasses import dataclass, field


@dataclass
class ReconciliationConfig:
    """Model representing the reconciliation configuration for the ASG Service Discovery application."""

    whatif: bool = field(default=False)
    max_concurrency: int = field(default=1)
