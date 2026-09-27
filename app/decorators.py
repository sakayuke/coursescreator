from functools import wraps

from flask import abort, current_app, request
from flask_login import current_user, login_required


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped_view(*args, **kwargs):
            if current_user.role not in roles:
                current_app.logger.warning(
                    "Role denied: user_id=%s role=%s method=%s path=%s",
                    current_user.id,
                    current_user.role,
                    request.method,
                    request.path,
                )
                abort(403)

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def is_owner(obj, user=None):
    if user is None:
        user = current_user

    return obj.teacher_id == user.id
