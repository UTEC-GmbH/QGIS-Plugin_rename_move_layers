"""Module: logs&errors.py

This module contains logging functions and custom error classes.
"""

import inspect
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from qgis.core import Qgis, QgsMessageLog
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import (
    QCoreApplication,  # type: ignore[reportAttributeAccessIssue]
)

iface: QgisInterface | None = None

if TYPE_CHECKING:
    from types import FrameType


def log_debug(message: str, msg_level: Qgis.MessageLevel = Qgis.Info) -> None:
    """Log a debug message.

    :param message: The message to log.
    """
    QgsMessageLog.logMessage(
        message, "Plugin - Rename and Move Layers to gpkg", level=msg_level
    )


def push_message(
    title: str, message: str, level: Qgis.MessageLevel = Qgis.Info
) -> None:
    """Display a message in the QGIS message bar.

    :param title: The title of the message.
    :param message: The message content to display.
    :param level: The message level (e.g., Info, Warning, Critical).
    """
    if iface and (msg_bar := iface.messageBar()):
        msg_bar.pushMessage(title, message, level=level, duration=10)


def log_summary_message(
    successes: int = 0,
    skipped: list | None = None,
    failures: list | None = None,
    not_found: list | None = None,
    action: str = "Operation",
) -> None:
    """Generate a summary message for the user based on operation results.

    This function constructs a user-friendly message summarizing the outcome
    of a plugin operation (e.g., renaming, moving layers). It handles different
    result types (successes, skips, failures, not found) and pluralization
    to create grammatically correct and informative feedback.

    :param plugin: The QGIS plugin interface for interacting with QGIS.
    :param successes: The number of successful operations.
    :param skipped: A list of layer names that were skipped.
    :param failures: A list of tuples detailing failed operations,
                     (e.g., (old_name, new_name, error_message)).
    :param not_found: A list of layer names that could not be found.
    :param action: A string describing the action performed (e.g., "Renamed", "Moved").
    :returns: A tuple containing the summary message (str) and the message level (int).
    """
    message_parts: list[str] = []
    message_level: Qgis.MessageLevel = Qgis.Success

    if successes:
        message_parts.append(
            QCoreApplication.translate(
                "log_summary", "{action} {successes} layer(s)."
            ).format(action=action.lower(), successes=successes)
        )

    if skipped:
        message_level = Qgis.Warning
        message_parts.append(
            QCoreApplication.translate(
                "log_summary", "Skipped {num_skipped} layer(s)."
            ).format(num_skipped=len(skipped))
        )
        for skipped_layer in skipped:
            log_debug(
                QCoreApplication.translate(
                    "log_summary", "Skipped layer '{layer}'"
                ).format(layer=skipped_layer),
                message_level,
            )

    if failures:
        message_level = Qgis.Warning
        message_parts.append(
            QCoreApplication.translate(
                "log_summary", "Failed to {action} {num_failures} layer(s)."
            ).format(action=action.lower(), num_failures=len(failures))
        )
        for failure in failures:
            log_debug(
                QCoreApplication.translate(
                    "log_summary",
                    "Failed to {action} {fail0}: {fail2}",
                ).format(action=action.lower(), fail0=failure[0], fail2=failure[2]),
                message_level,
            )

    if not_found:
        message_level = Qgis.Critical
        message_parts.append(
            QCoreApplication.translate(
                "log_summary", "Could not find {len_not_found} layer(s)."
            ).format(len_not_found=len(not_found))
        )
        for skipped_layer in not_found:  # assuming you have a list of not found layers
            log_debug(
                QCoreApplication.translate(
                    "log_summary", "Could not find '{layer}'"
                ).format(layer=skipped_layer),
                message_level,
            )

    if not message_parts:  # If no operations were reported
        message_level = Qgis.Info
        message_parts.append(
            QCoreApplication.translate(
                "log_summary",
                "No layers processed or "
                "all selected layers already have the desired state.",
            )
        )

    push_message(
        QCoreApplication.translate("log_summary", "Summary"),
        " ".join(message_parts),
        message_level,
    )


class CustomRuntimeError(Exception):
    """Custom exception for runtime errors in the plugin."""


def raise_runtime_error(error_msg: str) -> NoReturn:
    """Log a critical error and raise a RuntimeError.

    This helper function standardizes error handling by ensuring that a critical
    error is raised as a Python exception to halt the current operation.

    :param error_msg: The error message to display and include in the exception.
    :raises RuntimeError: Always raises a RuntimeError with the provided error message.
    """
    frame: FrameType | None = inspect.currentframe()
    if frame and frame.f_back:
        filename: str = Path(frame.f_back.f_code.co_filename).name
        lineno: int = frame.f_back.f_lineno
        error_msg = f"{error_msg} ({filename}: {lineno})"

    push_message(
        QCoreApplication.translate("RuntimeError", "Error"),
        error_msg,
        level=Qgis.Critical,
    )

    QgsMessageLog.logMessage(error_msg, "Error", level=Qgis.Critical)
    raise CustomRuntimeError(error_msg)


class CustomUserError(Exception):
    """Custom exception for user-related errors in the plugin."""


def raise_user_error(error_msg: str) -> NoReturn:
    """Log a warning message and raise a UserError.

    This helper function standardizes error handling by ensuring that a warning
    is raised to halt the current operation because of a user error.

    :param error_msg: The error message to display and include in the exception.
    :raises CustomUserError: Always raises a UserError with the provided error message.
    """

    push_message(
        QCoreApplication.translate("UserError", "Error"), error_msg, level=Qgis.Critical
    )

    QgsMessageLog.logMessage(error_msg, "Error", level=Qgis.Critical)
    raise CustomUserError(error_msg)
