# views.py

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Book, Borrowing, Notification, UserProfile
import requests
from datetime import datetime, timedelta

# Custom permission class
from rest_framework.permissions import BasePermission


class IsLibrarian(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "userprofile")
            and request.user.userprofile.role == "Librarian"
        )


def book_to_dict(book):
    return {
        "id": book.id,
        "isbn_10": book.isbn_10,
        "isbn_13": book.isbn_13,
        "title": book.title,
        "subtitle": book.subtitle,
        "authors": book.authors,
        "publisher": book.publisher,
        "published_date": book.published_date,
        "description": book.description,
        "page_count": book.page_count,
        "categories": book.categories,
        "language": book.language,
        "preview_link": book.preview_link,
        "info_link": book.info_link,
        "small_thumbnail": book.small_thumbnail,
        "thumbnail": book.thumbnail,
        "quantity": book.quantity,
        "available": book.available,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def book_list(request):
    books = Book.objects.all()
    data = [book_to_dict(book) for book in books]
    return Response(data)


@api_view(["POST"])
@permission_classes([IsLibrarian])
def add_books(request):
    isbn_list = request.data.get("isbn_list", [])
    if not isbn_list:
        return Response(
            {"error": "ISBN list is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    added_books = []
    errors = []

    for isbn in isbn_list:
        try:
            # Fetch book details from Google Books API
            response = requests.get(
                f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            )
            if response.status_code != 200:
                errors.append(f"Failed to fetch book details for ISBN {isbn}")
                continue

            book_data = response.json()
            if not book_data.get("items"):
                errors.append(f"Book not found for ISBN {isbn}")
                continue

            volume_info = book_data["items"][0]["volumeInfo"]

            # Create the book
            book = Book.objects.create(
                isbn_13=isbn,
                isbn_10=next(
                    (
                        id["identifier"]
                        for id in volume_info.get("industryIdentifiers", [])
                        if id["type"] == "ISBN_10"
                    ),
                    None,
                ),
                title=volume_info.get("title", ""),
                subtitle=volume_info.get("subtitle", ""),
                authors=", ".join(volume_info.get("authors", [])),
                publisher=volume_info.get("publisher", ""),
                published_date=volume_info.get("publishedDate", ""),
                description=volume_info.get("description", ""),
                page_count=volume_info.get("pageCount"),
                categories=", ".join(volume_info.get("categories", [])),
                language=volume_info.get("language", ""),
                preview_link=volume_info.get("previewLink", ""),
                info_link=volume_info.get("infoLink", ""),
                small_thumbnail=volume_info.get("imageLinks", {}).get(
                    "smallThumbnail", ""
                ),
                thumbnail=volume_info.get("imageLinks", {}).get("thumbnail", ""),
                quantity=1,
                available=1,
            )

            added_books.append(book_to_dict(book))
        except Exception as e:
            errors.append(f"Error adding book with ISBN {isbn}: {str(e)}")

    return Response(
        {
            "message": f"Added {len(added_books)} books successfully.",
            "added_books": added_books,
            "errors": errors,
        },
        status=status.HTTP_201_CREATED,
    )


# @permission_classes([AllowAny])
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == "GET":
        return Response(book_to_dict(book))

    elif request.method in ["PUT", "DELETE"]:
        if not IsLibrarian().has_permission(request, None):
            return Response(
                {"error": "You don't have permission to modify books."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "PUT":
            book.title = request.data.get("title", book.title)
            book.author = request.data.get("author", book.author)
            book.publisher = request.data.get("publisher", book.publisher)
            book.year = request.data.get("year", book.year)
            book.genre = request.data.get("genre", book.genre)
            book.quantity = request.data.get("quantity", book.quantity)
            book.available = request.data.get("available", book.available)
            book.save()
            return Response({"message": "Book updated successfully."})

        elif request.method == "DELETE":
            book.delete()
            return Response(
                {"message": "Book deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def borrow_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    user_profile = request.user.userprofile
    if book.available > 0:
        due_date = datetime.now().date() + timedelta(
            days=14
        )  # 2 weeks borrowing period
        Borrowing.objects.create(user=user_profile, book=book, due_date=due_date)
        book.available -= 1
        book.save()
        return Response(
            {"message": "Book borrowed successfully.", "due_date": due_date}
        )
    return Response(
        {"error": "Book is not available."}, status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def return_book(request, borrowing_id):
    user_profile = request.user.userprofile
    borrowing = get_object_or_404(Borrowing, pk=borrowing_id, user=user_profile)
    if not borrowing.return_date:
        borrowing.return_date = datetime.now().date()
        if borrowing.return_date > borrowing.due_date:
            days_late = (borrowing.return_date - borrowing.due_date).days
            borrowing.late_fee = days_late * 1  # $1 per day late fee
        borrowing.save()

        book = borrowing.book
        book.available += 1
        book.save()

        return Response(
            {"message": "Book returned successfully.", "late_fee": borrowing.late_fee}
        )
    return Response(
        {"error": "This book has already been returned."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_borrowing_history(request):
    user_profile = request.user.userprofile
    borrowings = Borrowing.objects.filter(user=user_profile).order_by("-borrow_date")
    data = [
        {
            "id": b.id,
            "book": b.book.title,
            "borrow_date": b.borrow_date,
            "due_date": b.due_date,
            "return_date": b.return_date,
            "late_fee": b.late_fee,
        }
        for b in borrowings
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_books(request):
    query = request.query_params.get("q", "")
    books = Book.objects.filter(title__icontains=query) | Book.objects.filter(
        author__icontains=query
    )
    data = [
        {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "available": book.available,
        }
        for book in books
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def book_recommendations(request):
    user_profile = request.user.userprofile
    user_genres = (
        Borrowing.objects.filter(user=user_profile)
        .values_list("book__genre", flat=True)
        .distinct()
    )
    recommended_books = (
        Book.objects.filter(genre__in=user_genres)
        .exclude(borrowing__user=user_profile)
        .distinct()[:5]
    )
    data = [
        {"id": book.id, "title": book.title, "author": book.author}
        for book in recommended_books
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_notifications(request):
    user_profile = request.user.userprofile
    notifications = Notification.objects.filter(user=user_profile).order_by(
        "-created_at"
    )
    data = [
        {
            "id": n.id,
            "message": n.message,
            "created_at": n.created_at,
            "is_read": n.is_read,
        }
        for n in notifications
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsLibrarian])
def generate_report(request):
    total_books = Book.objects.count()
    total_borrowings = Borrowing.objects.count()
    overdue_books = Borrowing.objects.filter(
        return_date__isnull=True, due_date__lt=datetime.now().date()
    ).count()
    most_borrowed_books = Book.objects.annotate(
        borrow_count=models.Count("borrowing")
    ).order_by("-borrow_count")[:5]

    report = {
        "total_books": total_books,
        "total_borrowings": total_borrowings,
        "overdue_books": overdue_books,
        "most_borrowed_books": [
            {"title": book.title, "borrow_count": book.borrow_count}
            for book in most_borrowed_books
        ],
    }
    return Response(report)
