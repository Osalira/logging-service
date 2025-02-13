from flask import Blueprint
from flask_restful import Api
from ..controllers.log_controller import LogController, LogCleanupController, LogStatsController

# Create Blueprint for logging routes
log_bp = Blueprint('logs', __name__)
api = Api(log_bp)

# Register routes
api.add_resource(LogController, '/logs')
api.add_resource(LogCleanupController, '/logs/cleanup')
api.add_resource(LogStatsController, '/logs/stats') 