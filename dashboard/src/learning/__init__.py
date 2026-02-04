from flask import Blueprint

from dashboard.src.learning.routes.cards import cards_bp
from dashboard.src.learning.routes.checklists import checklists_bp
from dashboard.src.learning.routes.prints import prints_bp
from dashboard.src.learning.routes.quizzes import quizzes_bp
from dashboard.src.learning.routes.reminders import reminders_bp
from dashboard.src.learning.routes.routines import routines_bp
from dashboard.src.learning.routes.subjects import subjects_bp
from dashboard.src.learning.routes.topics import topics_bp

learning = Blueprint("learning", __name__, url_prefix="/learning")

# Register all sub-blueprints
learning.register_blueprint(cards_bp)
learning.register_blueprint(topics_bp)
learning.register_blueprint(subjects_bp)
learning.register_blueprint(checklists_bp)
learning.register_blueprint(routines_bp)
learning.register_blueprint(reminders_bp)
learning.register_blueprint(prints_bp)
learning.register_blueprint(quizzes_bp)
