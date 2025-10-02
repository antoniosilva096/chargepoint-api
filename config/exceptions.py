from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

STATUS_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: "Bad Request",
    status.HTTP_401_UNAUTHORIZED: "Unauthorized",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    status.HTTP_404_NOT_FOUND: "Not Found",
    status.HTTP_409_CONFLICT: "Conflict",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
}


def api_exception_handler(exc, context):
    """
    Envuelve las respuestas de error en el formato uniforme:
    { code, message, data, errors }
    """
    response = exception_handler(exc, context)
    if response is None:
        return response

    status_code = response.status_code
    detail = response.data

    message = STATUS_MESSAGES.get(status_code, "Error")

    return Response(
        {"code": status_code, "message": message, "data": None, "errors": detail},
        status=status_code,
        headers=response.headers,
    )
