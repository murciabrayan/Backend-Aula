from django.urls import path

from .views import (
    my_permission_letters,
    permission_letter_detail,
    permission_letters_collection,
    respond_permission_letter,
)


urlpatterns = [
    path("permission-letters/", permission_letters_collection, name="permission_letters_collection"),
    path("permission-letters/<int:pk>/", permission_letter_detail, name="permission_letter_detail"),
    path("student/permission-letters/", my_permission_letters, name="my_permission_letters"),
    path("student/permission-letters/<int:recipient_id>/respond/", respond_permission_letter, name="respond_permission_letter"),
]
