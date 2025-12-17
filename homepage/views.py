from django.shortcuts import render

from news.models import News
import random

from category.models import Category


# Create your views here.
def homepage(request):
    categories = Category.objects.all()
    news = News.objects.all().order_by('-id')
    context = {
        'news': news,
        'categories': categories,
    }

    return render(request, 'index.html', context)


def news_detail(request, id):
    news = News.objects.get(id=id)
    count = news.count
    number = random.randint(1, 5)
    total_count = int(number + count)
    news.count = total_count
    news.save()
    try:
        absolute_image_url = request.build_absolute_uri(news.featured_image.url)
    except:
        absolute_image_url = ''
    category = Category.objects.all().order_by('-id')
    context = {
        'news': news,
        'absolute_image_url': absolute_image_url,
        'category': category,
    }
    return render(request, 'detail.html', context)


def category_news(request, id):
    category_name = Category.objects.get(id=id)
    all_news = News.objects.filter(category_id=id).order_by('-id')[:30]


    context = {
        'news': all_news,
        'category_name': category_name,
    }
    return render(request, 'category_news.html', context)
