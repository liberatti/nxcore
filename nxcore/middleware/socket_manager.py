from flask_socketio import SocketIO

socketio = None


def init_socketio(app):
    global socketio

    socketio = SocketIO(
        app,
        async_mode="gevent",
        cors_allowed_origins="*"
    )

    return socketio


def get_socketio():
    if socketio is None:
        raise RuntimeError(
            "SocketIO não foi inicializado. Chame init_socketio() primeiro."
        )
    return socketio


def emit_event(event_name, data=None, **kwargs):
    sio = get_socketio()
    sio.emit(event_name, data, **kwargs)
