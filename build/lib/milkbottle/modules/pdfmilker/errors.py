class PDFMilkerError(Exception):
    """
    Base exception for all PDFmilker errors.
    """

    pass


class ExtractionError(PDFMilkerError):
    """
    Raised when extraction of text, images, or metadata fails.
    """

    pass


class ValidationError(PDFMilkerError):
    """
    Raised when validation of assets or hashes fails.
    """

    pass


class RelocationError(PDFMilkerError):
    """
    Raised when relocation of the source PDF fails.
    """

    pass
