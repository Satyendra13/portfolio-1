class AsistLineException(Exception):
    """Base exception for AsistLine AI platform."""
    pass


class TenantFilterRequiredError(AsistLineException):
    """Raised when a query on a tenant-scoped database model lacks explicit tenant_id filtering."""
    def __init__(self, model_name: str):
        super().__init__(f"Tenant safety error: Query on tenant-scoped model '{model_name}' missing required tenant_id filter.")
        self.model_name = model_name


class TenantNotFoundError(AsistLineException):
    """Raised when specified tenant_id does not exist."""
    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant '{tenant_id}' not found.")
        self.tenant_id = tenant_id


class GroundingFailureError(AsistLineException):
    """Raised when grounding guard evaluation fails or returns NO_ANSWER."""
    pass
