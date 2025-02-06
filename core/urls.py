from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("create-session/", views.create_session, name="create_session"),
    path(
        "create-session/<str:option>/",
        views.create_session_with_option,
        name="create_session_with_option",
    ),
    path(
        "update-session-title/<int:session_id>/",
        views.update_session_title,
        name="update_session_title",
    ),
    path("session/<int:session_id>/", views.session_detail, name="session_detail"),
    path("session/<int:session_id>/upload/", views.upload_document, name="upload_document"),
    path("delete-session/<int:session_id>/", views.delete_session, name="delete_session"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),


    # extra??
    path("edit-message/<int:query_id>/", views.edit_message, name="edit_message"),
    path("delete-message/<int:query_id>/", views.delete_message, name="delete_message"),
]
