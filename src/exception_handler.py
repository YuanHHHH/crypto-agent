from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from src.utils.exceptions import APIError,InvalidCoinError

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(APIError)
    def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail":f"上游 API 错误: {exc}"}
        )

    @app.exception_handler(InvalidCoinError)
    def handle_invalid_coin(request: Request, exc: InvalidCoinError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail":f"找不到币种: {exc}"}
        )