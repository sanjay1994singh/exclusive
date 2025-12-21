# news/context_processors.py

from category.models import Category
from .models import News
from django.db.models import Max


# def category_context(request):
#     return {
#         'category': Category.objects.all().order_by('-id')
#     }

# def category_context(request):
#     return {
#         'categories': Category.objects.annotate(
#             latest_news=Max('news__created_at')
#         ).order_by('-latest_news')
#     }

# def category_context(request):
#     return {
#         'categories': Category.objects
#             .filter(news__isnull=False)
#             .annotate(latest_news=Max('news__created_at'))
#             .order_by('-latest_news')
#             .distinct()
#     }
def category_context(request):
    categories = Category.objects.annotate(
        latest_news_time=Max('news__created_at')
    ).order_by('-latest_news_time', 'id')  # Categories without news go last

    return {
        'categories': categories
    }


def breaking_news(request):
    return {
        'breaking_news': News.objects.filter().order_by('-created_at')
    }
