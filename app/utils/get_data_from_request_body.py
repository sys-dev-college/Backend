from starlette.datastructures import UploadFile


def get_data_from_request_body(body: dict) -> dict:
    return {
        k: (v if not isinstance(v, (bytes, UploadFile)) else "binary") for k, v in body.items()
    }
