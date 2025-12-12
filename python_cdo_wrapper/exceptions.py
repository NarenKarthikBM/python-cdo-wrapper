"""Exception hierarchy for python-cdo-wrapper v1.0.0+."""

from __future__ import annotations

from typing import Any


class CDOError(Exception):
    """Base exception for all CDO errors in v1.0.0+ API."""

    pass


class CDOExecutionError(CDOError):
    """CDO command execution failed."""

    def __init__(
        self,
        message: str,
        command: str,
        returncode: int,
        stdout: str,
        stderr: str,
    ):
        """
        Initialize CDOExecutionError.

        Args:
            message: Error message.
            command: The CDO command that failed.
            returncode: Process exit code.
            stdout: Standard output from CDO.
            stderr: Standard error from CDO.
        """
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self) -> str:
        """Return formatted error message."""
        return (
            f"{super().__str__()}\n"
            f"Command: {self.command}\n"
            f"Return code: {self.returncode}\n"
            f"Stderr: {self.stderr}"
        )


class CDOValidationError(CDOError):
    """Invalid parameters provided to an operator."""

    def __init__(
        self,
        message: str,
        parameter: str,
        value: Any,
        expected: str,
    ):
        """
        Initialize CDOValidationError.

        Args:
            message: Error message.
            parameter: Parameter name that failed validation.
            value: The invalid value provided.
            expected: Description of expected value/format.
        """
        super().__init__(message)
        self.parameter = parameter
        self.value = value
        self.expected = expected

    def __str__(self) -> str:
        """Return formatted error message."""
        return (
            f"{super().__str__()}\n"
            f"Parameter: {self.parameter}\n"
            f"Value: {self.value}\n"
            f"Expected: {self.expected}"
        )


class CDOFileNotFoundError(CDOError):
    """Input file does not exist."""

    def __init__(self, message: str, file_path: str):
        """
        Initialize CDOFileNotFoundError.

        Args:
            message: Error message.
            file_path: Path to the file that was not found.
        """
        super().__init__(message)
        self.file_path = file_path

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"{super().__str__()}\nFile: {self.file_path}"


class CDOParseError(CDOError):
    """Failed to parse CDO output."""

    def __init__(self, message: str, raw_output: str):
        """
        Initialize CDOParseError.

        Args:
            message: Error message.
            raw_output: The raw output that failed to parse.
        """
        super().__init__(message)
        self.raw_output = raw_output

    def __str__(self) -> str:
        """Return formatted error message."""
        output_preview = (
            self.raw_output[:200] + "..."
            if len(self.raw_output) > 200
            else self.raw_output
        )
        return f"{super().__str__()}\nOutput: {output_preview}"
