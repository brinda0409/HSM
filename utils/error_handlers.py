from flask import jsonify
from utils.logger import logger

def register_error_handlers(app):
    """
    Registers standardized JSON error handlers for Flask application.
    """
    @app.errorhandler(400)
    def bad_request(error):
        message = getattr(error, 'description', 'Bad Request')
        logger.warning(f"400 Bad Request: {message}")
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(message)
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        message = getattr(error, 'description', 'Resource Not Found')
        logger.warning(f"404 Not Found: {message}")
        return jsonify({
            "success": False,
            "error": "NOT_FOUND",
            "message": str(message)
        }), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"500 Internal Server Error: {error}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred. Please check system logs."
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        logger.error(f"Unhandled Exception: {error}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "UNHANDLED_EXCEPTION",
            "message": str(error)
        }), 500
