# news/context_processors.py

from category.models import Category
from .models import News


def category_context(request):
    return {
        'category': Category.objects.only('id', 'name').order_by('-id')
    }


def breaking_news(request):
    return {
        'breaking_news': News.objects.only('id', 'title').order_by('-created_at')[:15]
    }
