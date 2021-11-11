__app_name__ = "notebooktester"
__version__ = "0.1.0"

(
    SUCCESS,
    NOTEBOOK_NOT_FOUND,
    IO_ERROR,
    INCONSISTENT_SOURCE,
    SOURCE_OUTDATED,
    TEST_FAILED,
    NOTEBOOK_JSON_ERROR,
    PROCESSING_FAILURE,
    INIT_ALLREADY_DONE
) = range(9)

ERRORS = {
    NOTEBOOK_NOT_FOUND: "The source notebook was not found",
    IO_ERROR: "Error opening accessing files",
    INCONSISTENT_SOURCE : "The source notebook is not consistent.",
    SOURCE_OUTDATED : "The source notebook is newer than the metadata timestamp.",
    TEST_FAILED: "The Embedded tests failed",
    NOTEBOOK_JSON_ERROR: "There was a problem parsing the notebook content.",
    PROCESSING_FAILURE: "Failure to process the notebook",
    INIT_ALLREADY_DONE: "The notebook has allready been initialized. Use --force to update."
}