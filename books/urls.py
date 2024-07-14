from django.urls import path
from . import views

urlpatterns = [
    path("books/", views.book_list, name="book-list"),
    path("books/add/", views.add_books, name="add-books"),
    path("books/<int:pk>/", views.book_detail, name="book-detail"),
    path("books/<int:book_id>/borrow/", views.borrow_book, name="borrow-book"),
    path(
        "borrowings/<int:borrowing_id>/return/", views.return_book, name="return-book"
    ),
    path("borrowings/history/", views.user_borrowing_history, name="borrowing-history"),
    path("books/search/", views.search_books, name="search-books"),
    path(
        "books/recommendations/",
        views.book_recommendations,
        name="book-recommendations",
    ),
    path("notifications/", views.user_notifications, name="user-notifications"),
    path("reports/", views.generate_report, name="generate-report"),
]
