from dashboard import create_app

app = create_app()

# @app.before_first_request
# def init_db():
#     db.create_all()