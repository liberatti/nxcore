from flask_socketio import SocketIO

socketio = None


def init_socketio(app):
    global socketio
    socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
    socketio.init_app(app)
    return socketio


def get_socketio():
    if socketio is None:
        raise RuntimeError(
            "SocketIO não foi inicializado. Chame init_socketio() primeiro."
        )
    return socketio


def emit_event(event_name, data=None, **kwargs):
    if socketio:
        socketio.emit(event_name, data, **kwargs)
