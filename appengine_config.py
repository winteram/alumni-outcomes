from gaesessions import SessionMiddleware
def webapp_add_wsgi_middleware(app):
    app = SessionMiddleware(app, cookie_key="tZ0l_HB64ShicoHi-JIYz8iXufIiSpP2pCwj_XqqNPokioUKt5FyI6")
    return app