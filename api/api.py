from ninja import NinjaAPI

from api.auth.endpoints import auth_router
from api.common.endpoints import common_router
from api.management.endpoints import management_router
from api.utils import ApiKey, AdminApiKey

header_key = ApiKey()
admin_header_key = AdminApiKey()

description = f"""
An API that lets the management manage clients (CRUD) and stores/shows information about the clients' favorite products.

The auth works by checking if the provided `{header_key.param_name}` exists in the database. 
"""

api = NinjaAPI(
    title="Product List API",
    version="1.0.0",
    description=description,
    auth=header_key,
)

api.add_router("/auth", auth_router, tags=["auth"])
api.add_router("/common", common_router, tags=["common"])
api.add_router("/management", management_router, tags=["management"], auth=admin_header_key)
