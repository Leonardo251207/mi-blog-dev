class DomainException(Exception):
    """Base domain exception"""
    pass

class PageNotFoundError(DomainException):
    def __init__(self, page_id: str):
        super().__init__(f"Page with ID '{page_id}' was not found.")
        self.page_id = page_id

class ArtifactNotFoundError(DomainException):
    def __init__(self, page_id: str):
        super().__init__(f"Artifact for page '{page_id}' was not found.")
        self.page_id = page_id

class ArtifactCorruptedError(DomainException):
    def __init__(self, page_id: str, expected_sha: str, actual_sha: str):
        super().__init__(f"Artifact for page '{page_id}' is corrupted: expected {expected_sha}, got {actual_sha}.")
        self.page_id = page_id
        self.expected_sha = expected_sha
        self.actual_sha = actual_sha

class UnsupportedEngineError(DomainException):
    def __init__(self, engine: str):
        super().__init__(f"Static engine '{engine}' is not supported.")
        self.engine = engine

class BuildExecutionError(DomainException):
    def __init__(self, message: str):
        super().__init__(f"Build failed: {message}")
