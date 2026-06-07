from enum import Enum

class ResponseSignal(Enum):

    FILE_VALIDATED_SUCCESS = "file_validate_successfully"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    PROCESSING_SUCCESS = "processing_success"
    PROCESSING_FAILED = "processing_failed"
    NO_FILES_ERROR = "not_found_files"
    FILE_ID_ERROR = "no_file_found_with_this_id"
    PROJECT_NOT_FOUND = "project_not_found"
    INSERT_INTO_VECTORDB_SUCCESS = "insert_into_vectordb_success"
    VECTOR_COLLECTION_RETRIEVE_SUCCESS = "vector_collection_retrieve_success"
    VECTOR_COLLECTION_RETRIEVE_FAILED = "vector_collection_retrieve_failed"
    ANSWER_GENERATION_FAILED = "answer_generation_failed"
    ANSWER_GENERATION_SUCCESS = "answer_generation_success"
    NO_RESULTS_FOUND = "no_results_found"