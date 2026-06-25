from typing import Any, Optional
try:
    from flask import Flask, current_app, has_app_context
    from flask_socketio import SocketIO
except Exception:
    Flask = None
    current_app = None
    SocketIO = None

    def has_app_context():
        return False


class SocketIOManager:
    """Flask extension for managing the SocketIO instance and broadcasting events."""

    def __init__(self, app: Optional[Flask] = None):
        self.socketio: Optional[SocketIO] = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> SocketIO:
        """Initializes the SocketIO instance on the Flask application.

        Args:
            app (Flask): The Flask application instance.

        Returns:
            SocketIO: The initialized SocketIO instance.
        """
        self.socketio = SocketIO(
            app,
            async_mode="gevent",
            cors_allowed_origins="*"
        )
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['socket_manager'] = self
        return self.socketio

    @classmethod
    def get_current_instance(cls) -> "SocketIOManager":
        """Retrieves the SocketIOManager instance from the active Flask application context.

        Returns:
            SocketIOManager: The active SocketIOManager instance.

        Raises:
            RuntimeError: If called outside application context or extension is not initialized.
        """
        if not has_app_context():
            raise RuntimeError(
                "Working outside of application context. "
                "Make sure a Flask application is active or use app.app_context()."
            )
        if not hasattr(current_app, "extensions") or "socket_manager" not in current_app.extensions:
            raise RuntimeError(
                "SocketIOManager has not been initialized on this Flask application."
            )
        return current_app.extensions["socket_manager"]


def init_socketio(app: Flask) -> SocketIO:
    """Initializes the SocketIO extension on the Flask application.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        SocketIO: The initialized SocketIO instance.
    """
    manager = SocketIOManager(app)
    return manager.socketio


def get_socketio() -> SocketIO:
    """Retrieves the SocketIO instance from the active Flask application context.

    Returns:
        SocketIO: The active SocketIO instance.

    Raises:
        RuntimeError: If called outside application context or extension is not initialized.
    """
    manager = SocketIOManager.get_current_instance()
    if manager.socketio is None:
        raise RuntimeError(
            "SocketIO has not been initialized. Chame init_socketio() primeiro."
        )
    return manager.socketio


def emit_event(event_name: str, data: Any = None, **kwargs: Any) -> None:
    """Emits an event to connected WebSocket clients.

    Args:
        event_name (str): The name of the event to emit.
        data (any, optional): The payload data for the event. Defaults to None.
        **kwargs: Additional keyword arguments for socketio.emit.
    """
    sio = get_socketio()
    sio.emit(event_name, data, **kwargs)
