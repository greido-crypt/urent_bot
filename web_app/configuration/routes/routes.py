from fastapi import FastAPI
from dataclasses import dataclass


@dataclass(frozen=True)
class Routes:
    routers: tuple

    def register_routes(self, app: FastAPI) -> None:
        for router in self.routers:
            app.include_router(router=router)
