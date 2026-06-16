import json
from datetime import timedelta
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from news.models import News
import random

from category.models import Category


# Create your views here.
PUBLICATION_NAME = 'Exclusive Bulletin'


def absolute_url(request, path):
    return request.build_absolute_uri(path)


def image_url(request, news):
    if news.featured_image:
        return request.build_absolute_uri(news.featured_image.url)
    return request.build_absolute_uri('/static/images/logo.jpeg')


def clean_description(text, words=32):
    if not text:
        return 'Latest verified news update from Exclusive Bulletin.'
    plain = ' '.join(str(text).split())
    return ' '.join(plain.split()[:words])


def homepage(request):
    categories = Category.objects.all()
    news = News.objects.select_related('category').all().order_by('-id')[:12]
    featured_news = news[0] if news else None
    context = {
        'news': news,
        'categories': categories,
        'featured_news': featured_news,
        'canonical_url': absolute_url(request, reverse('homepage')),
    }

    return render(request, 'index.html', context)


def news_detail(request, id):
    news = get_object_or_404(News.objects.select_related('category'), id=id)
    count = news.count
    number = random.randint(1, 5)
    total_count = int(number + count)
    news.count = total_count
    news.save()
    absolute_image_url = image_url(request, news)
    category = Category.objects.all().order_by('-id')
    canonical_url = absolute_url(request, reverse('news_detail', args=[news.id]))
    article_schema = {
        '@context': 'https://schema.org',
        '@type': 'NewsArticle',
        'headline': news.title,
        'description': clean_description(news.text),
        'image': [absolute_image_url],
        'datePublished': news.created_at.isoformat(),
        'dateModified': news.updated_at.isoformat() if news.updated_at else news.created_at.isoformat(),
        'author': {
            '@type': 'Person',
            'name': news.reporter or PUBLICATION_NAME,
        },
        'publisher': {
            '@type': 'Organization',
            'name': PUBLICATION_NAME,
            'logo': {
                '@type': 'ImageObject',
                'url': absolute_url(request, '/static/images/logo.jpeg'),
            },
        },
        'mainEntityOfPage': {
            '@type': 'WebPage',
            '@id': canonical_url,
        },
    }
    context = {
        'news': news,
        'absolute_image_url': absolute_image_url,
        'category': category,
        'canonical_url': canonical_url,
        'meta_description': clean_description(news.text),
        'article_schema': json.dumps(article_schema),
    }
    return render(request, 'detail.html', context)


def category_news(request, id):
    category_name = get_object_or_404(Category, id=id)
    all_news = News.objects.filter(category_id=id).select_related('category').order_by('-id')[:30]


    context = {
        'news': all_news,
        'category_name': category_name,
        'canonical_url': absolute_url(request, reverse('category_news', args=[category_name.id])),
        'meta_description': category_name.desc or f'Latest {category_name.name} news updates from Exclusive Bulletin.',
    }
    return render(request, 'category_news.html', context)


def robots_txt(request):
    sitemap_url = absolute_url(request, reverse('sitemap_xml'))
    news_sitemap_url = absolute_url(request, reverse('news_sitemap_xml'))
    content = f"""User-agent: *
Allow: /

Sitemap: {sitemap_url}
Sitemap: {news_sitemap_url}
"""
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    urls = [
        {
            'loc': absolute_url(request, reverse('homepage')),
            'lastmod': timezone.now(),
            'priority': '1.0',
        }
    ]

    for item in News.objects.all().order_by('-updated_at')[:1000]:
        urls.append({
            'loc': absolute_url(request, reverse('news_detail', args=[item.id])),
            'lastmod': item.updated_at or item.created_at,
            'priority': '0.9',
        })

    for item in Category.objects.all():
        urls.append({
            'loc': absolute_url(request, reverse('category_news', args=[item.id])),
            'lastmod': item.updated_at or item.created_at,
            'priority': '0.7',
        })

    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for item in urls:
        body.append('  <url>')
        body.append(f'    <loc>{escape(item["loc"])}</loc>')
        body.append(f'    <lastmod>{item["lastmod"].date().isoformat()}</lastmod>')
        body.append('    <changefreq>hourly</changefreq>')
        body.append(f'    <priority>{item["priority"]}</priority>')
        body.append('  </url>')
    body.append('</urlset>')
    return HttpResponse('\n'.join(body), content_type='application/xml')


def news_sitemap_xml(request):
    cutoff = timezone.now() - timedelta(days=2)
    articles = News.objects.filter(created_at__gte=cutoff).order_by('-created_at')[:1000]
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]
    for article in articles:
        body.append('  <url>')
        body.append(f'    <loc>{escape(absolute_url(request, reverse("news_detail", args=[article.id])))}</loc>')
        body.append('    <news:news>')
        body.append('      <news:publication>')
        body.append(f'        <news:name>{escape(PUBLICATION_NAME)}</news:name>')
        body.append('        <news:language>en</news:language>')
        body.append('      </news:publication>')
        body.append(f'      <news:publication_date>{article.created_at.isoformat()}</news:publication_date>')
        body.append(f'      <news:title>{escape(article.title or PUBLICATION_NAME)}</news:title>')
        body.append('    </news:news>')
        body.append('  </url>')
    body.append('</urlset>')
    return HttpResponse('\n'.join(body), content_type='application/xml')
