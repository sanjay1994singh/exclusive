# news/context_processors.py

from category.models import Category
from .models import News
from django.db.models import Max

# def category_context(request):
#     return {
#         'category': Category.objects.all().order_by('-id')
#     }

def category_context(request):
    return {
        'categories': Category.objects.annotate(
            latest_news=Max('news__created_at')
        ).order_by('-latest_news')
    }

def breaking_news(request):
    return {
        'breaking_news': News.objects.filter().order_by('-created_at')
    }
