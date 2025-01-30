from .routes import Routes
from web_app.internal.routes import account

__routes__ = Routes(routers=(account.router, ))

