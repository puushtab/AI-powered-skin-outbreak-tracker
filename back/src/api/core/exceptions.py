from fastapi import HTTPException

class ModelNotAvailableError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=503,
            detail="Model file is currently unavailable."
        )

class InvalidFileTypeError(HTTPException):
    def __init__(self, content_type: str):
        super().__init__(
            status_code=415,
            detail=f"Invalid file type '{content_type}'. Please upload JPG, PNG, or BMP."
        )

class DatabaseError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=500,
            detail=f"Database error: {detail}"
        )

class AnalysisError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=500,
            detail=f"Analysis error: {detail}"
        ) 