from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException

from app.common.response import Response
from app.utils.logger import logger


def _get_request_user_id(request: Request) -> int | None:
    return getattr(request.state, "user_id", None)


def _get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _set_request_id_header(request: Request, response: JSONResponse):
    request_id = _get_request_id(request)
    if request_id:
        response.headers["X-Request-ID"] = request_id


def _log_error_response(request: Request, response: Response, status_code: int):
    logger.warning(
        "API error response method=%s path=%s request_id=%s user_id=%s "
        "status=%s body=%s",
        request.method,
        request.url.path,
        _get_request_id(request),
        _get_request_user_id(request),
        status_code,
        response.model_dump_json(),
    )


class BusinessException(Exception):

    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code


def business_exception_handler(request: Request, exc: BusinessException):
    response = Response.error(code=exc.code, message=exc.message)
    logger.warning(
        "Business exception method=%s path=%s request_id=%s user_id=%s "
        "error_type=%s error=%s",
        request.method,
        request.url.path,
        _get_request_id(request),
        _get_request_user_id(request),
        type(exc).__name__,
        str(exc),
    )
    _log_error_response(request, response, 200)
    http_response = JSONResponse(
        content=response.model_dump(),
        status_code=200,
    )
    _set_request_id_header(request, http_response)
    return http_response


def http_exception_handler(request: Request, exc: HTTPException):
    response = Response.error(code=exc.status_code, message=exc.detail)
    logger.warning(
        "HTTP exception method=%s path=%s request_id=%s user_id=%s "
        "error_type=%s error=%s",
        request.method,
        request.url.path,
        _get_request_id(request),
        _get_request_user_id(request),
        type(exc).__name__,
        str(exc),
    )
    _log_error_response(request, response, exc.status_code)
    http_response = JSONResponse(
        content=response.model_dump(mode="json"),
        status_code=exc.status_code,
    )
    _set_request_id_header(request, http_response)
    return http_response


def validation_exception_handler(request: Request, _exc: RequestValidationError):
    validation_errors = [
        {
            "location": error.get("loc"),
            "message": error.get("msg"),
            "type": error.get("type"),
        }
        for error in _exc.errors()
    ]
    logger.warning(
        "Request validation exception method=%s path=%s user_id=%s "
        "request_id=%s error_type=%s errors=%s",
        request.method,
        request.url.path,
        _get_request_user_id(request),
        _get_request_id(request),
        type(_exc).__name__,
        validation_errors,
    )
    response = Response.error(code=422, message="请求参数校验错误")
    _log_error_response(request, response, 422)
    http_response = JSONResponse(
        content=response.model_dump(mode="json"),
        status_code=422,
    )
    _set_request_id_header(request, http_response)
    return http_response


def global_exception_handler(request: Request, exc: Exception):
    response = Response.error(code=500, message="服务器内部错误")
    logger.error(
        "Unhandled API exception method=%s path=%s request_id=%s user_id=%s "
        "error_type=%s error=%s response=%s",
        request.method,
        request.url.path,
        _get_request_id(request),
        _get_request_user_id(request),
        type(exc).__name__,
        str(exc),
        response.model_dump_json(),
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    http_response = JSONResponse(
        status_code=500,
        content=response.model_dump(mode="json"),
    )
    _set_request_id_header(request, http_response)
    return http_response


