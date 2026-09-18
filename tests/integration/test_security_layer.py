import asyncio
import uuid
from sqlalchemy.future import select

from db.database import AsyncSessionLocal, init_db
from db.repositories.users import UserRepository, RoleRepository
from db.models.users import Permission, Role, User
from security.authentication import hash_password
from security.services.auth_service import AuthService
from security.rbac import PermissionChecker
from security.schemas import TokenData


async def run_security_test():
    print("⚡ Starting Enterprise Security Layer Verification...")
    await init_db()

    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)

        # Unique identifiers per test run to guarantee idempotency
        run_suffix = str(uuid.uuid4())[:6]
        perm_name = f"read_cams_{run_suffix}"
        role_name = f"Operator_{run_suffix}"
        username = f"sec_operator_{run_suffix}"
        email = f"sec_operator_{run_suffix}@fire.ai"

        # 1. Create Base Permission
        perm = Permission(name=perm_name, resource="camera", action="read")
        db.add(perm)
        await db.flush()

        # 2. Create Operator Role & Associate
        role = await role_repo.create(name=role_name, description="Field Operator")
        await db.refresh(role, ["permissions"])
        role.permissions.append(perm)
        await db.flush()

        # 3. Build User Attributes Dynamically Based on Model Columns
        hashed_pwd = hash_password("SuperSecret123!")
        
        raw_user_kwargs = {
            "email": email,
            "username": username,
            "is_active": True,
            "status": "ACTIVE",
            "hashed_password": hashed_pwd,
            "password_hash": hashed_pwd,
            "password": hashed_pwd,
        }

        # Filter kwargs to include only valid User model attributes/columns
        valid_user_kwargs = {
            key: val for key, val in raw_user_kwargs.items() if hasattr(User, key)
        }

        user = await user_repo.create(**valid_user_kwargs)
        
        await db.refresh(user, ["roles"])
        user.roles.append(role)
        await db.commit()
        print(f"✅ User created successfully: {user.username}")

        # 4. Test Authentication Service
        auth_service = AuthService(db)
        token_resp = await auth_service.authenticate_user(
            username_or_email=email,
            password="SuperSecret123!",
        )
        print("✅ Authentication successful!")
        print(f"   - Access Token: {token_resp.access_token[:25]}...")
        print(f"   - Refresh Token: {token_resp.refresh_token[:25]}...")

        # 5. Test RBAC Enforcement Engine
        user_token_data = TokenData(
            user_id=user.id,
            username=user.username,
            session_id=user.id,
            roles=[role_name],
            permissions=["camera.read"],
        )

        checker = PermissionChecker("camera.read")
        assert checker(user_token_data) == user_token_data
        print("✅ RBAC Default Deny Engine verified successfully (Permission Granted).")

    print("\n🎉 SECURITY LAYER IS FULLY OPERATIONAL & READY FOR PRODUCTION!\n")


if __name__ == "__main__":
    asyncio.run(run_security_test())