# news/context_processors.py

from category.models import Category
from .models import News


def category_context(request):
    return {
        'category': Category.objects.all().order_by('-id')
    }


def breaking_news(request):
    return {
        'breaking_news': News.objects.filter().order_by('-created_at')
    }
