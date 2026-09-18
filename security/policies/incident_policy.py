from security.schemas import TokenData

class IncidentPolicy:
    @staticmethod
    def can_resolve_incident(user: TokenData) -> bool:
        if "Admin" in user.roles or "incident.resolve" in user.permissions:
            return True
        return False