import json
from datetime import timedelta
from xml.sax.saxutils import escape

from django.db.models import F, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from news.models import News

from category.models import Category


# Create your views here.
PUBLICATION_NAME = 'Exclusive Bulletin'
PUBLICATION_LANGUAGE = 'en'


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


def article_url(request, article):
    return absolute_url(request, reverse('news_detail', args=[article.id]))


def article_keywords(article):
    keywords = ['breaking news', 'latest news', PUBLICATION_NAME]
    if article.category:
        keywords.insert(0, str(article.category))
    if article.city:
        keywords.insert(0, article.city)
    return ', '.join(keywords)


def organization_schema(request):
    return {
        '@context': 'https://schema.org',
        '@type': 'NewsMediaOrganization',
        'name': PUBLICATION_NAME,
        'url': absolute_url(request, reverse('homepage')),
        'logo': absolute_url(request, '/static/images/logo.jpeg'),
        'sameAs': [
            'https://www.facebook.com/share/1FPycMSh4s/',
            'https://x.com/vbnvikass',
            'https://youtube.com/@exclusivebulletin387',
        ],
    }


def homepage(request):
    news_qs = News.objects.select_related('category').only(
        'id',
        'category__name',
        'title',
        'text',
        'featured_image',
        'count',
        'created_at',
    )
    news = list(news_qs.order_by('-id')[:12])
    categories = Category.objects.filter(news__isnull=False).only('id', 'name').distinct().prefetch_related(
        Prefetch(
            'news_set',
            queryset=news_qs.order_by('-id')[:5],
            to_attr='homepage_news',
        )
    )
    featured_news = news[0] if news else None
    homepage_url = absolute_url(request, reverse('homepage'))
    home_schema = [
        organization_schema(request),
        {
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            'name': PUBLICATION_NAME,
            'url': homepage_url,
            'publisher': {
                '@type': 'NewsMediaOrganization',
                'name': PUBLICATION_NAME,
            },
        },
    ]
    context = {
        'news': news,
        'categories': categories,
        'featured_news': featured_news,
        'canonical_url': homepage_url,
        'home_schema': json.dumps(home_schema),
    }

    return render(request, 'index.html', context)


def news_detail(request, id):
    news = get_object_or_404(
        News.objects.select_related('category').only(
            'id',
            'category__name',
            'title',
            'city',
            'text',
            'featured_image',
            'count',
            'reporter',
            'created_at',
            'updated_at',
        ),
        id=id,
    )
    News.objects.filter(id=news.id).update(count=F('count') + 1)
    news.count += 1
    absolute_image_url = image_url(request, news)
    category = Category.objects.only('id', 'name').order_by('-id')
    canonical_url = absolute_url(request, reverse('news_detail', args=[news.id]))
    article_schema = {
        '@context': 'https://schema.org',
        '@type': 'NewsArticle',
        'headline': news.title,
        'description': clean_description(news.text),
        'image': [absolute_image_url],
        'datePublished': news.created_at.isoformat(),
        'dateModified': news.updated_at.isoformat() if news.updated_at else news.created_at.isoformat(),
        'keywords': article_keywords(news),
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
        'article_keywords': article_keywords(news),
        'article_schema': json.dumps(article_schema),
    }
    return render(request, 'detail.html', context)


def category_news(request, id):
    category_name = get_object_or_404(Category, id=id)
    all_news = News.objects.filter(category_id=id).select_related('category').only(
        'id',
        'category__name',
        'title',
        'text',
        'featured_image',
        'count',
        'created_at',
    ).order_by('-id')[:30]
    canonical_url = absolute_url(request, reverse('category_news', args=[category_name.id]))
    category_schema = {
        '@context': 'https://schema.org',
        '@type': 'CollectionPage',
        'name': f'{category_name.name} News',
        'description': category_name.desc or f'Latest {category_name.name} news updates from Exclusive Bulletin.',
        'url': canonical_url,
        'publisher': {
            '@type': 'NewsMediaOrganization',
            'name': PUBLICATION_NAME,
        },
    }

    context = {
        'news': all_news,
        'category_name': category_name,
        'canonical_url': canonical_url,
        'meta_description': category_name.desc or f'Latest {category_name.name} news updates from Exclusive Bulletin.',
        'category_schema': json.dumps(category_schema),
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
            'image': absolute_url(request, '/static/images/logo.jpeg'),
            'image_title': PUBLICATION_NAME,
        }
    ]

    for item in News.objects.all().order_by('-updated_at')[:1000]:
        urls.append({
            'loc': article_url(request, item),
            'lastmod': item.updated_at or item.created_at,
            'priority': '0.9',
            'image': image_url(request, item),
            'image_title': item.title or PUBLICATION_NAME,
        })

    for item in Category.objects.all():
        urls.append({
            'loc': absolute_url(request, reverse('category_news', args=[item.id])),
            'lastmod': item.updated_at or item.created_at,
            'priority': '0.7',
        })

    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for item in urls:
        body.append('  <url>')
        body.append(f'    <loc>{escape(item["loc"])}</loc>')
        body.append(f'    <lastmod>{item["lastmod"].isoformat()}</lastmod>')
        body.append('    <changefreq>hourly</changefreq>')
        body.append(f'    <priority>{item["priority"]}</priority>')
        if item.get('image'):
            body.append('    <image:image>')
            body.append(f'      <image:loc>{escape(item["image"])}</image:loc>')
            body.append(f'      <image:title>{escape(item["image_title"] or PUBLICATION_NAME)}</image:title>')
            body.append('    </image:image>')
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
        body.append(f'        <news:language>{PUBLICATION_LANGUAGE}</news:language>')
        body.append('      </news:publication>')
        body.append(f'      <news:publication_date>{article.created_at.isoformat()}</news:publication_date>')
        body.append(f'      <news:title>{escape(article.title or PUBLICATION_NAME)}</news:title>')
        body.append(f'      <news:keywords>{escape(article_keywords(article))}</news:keywords>')
        body.append('    </news:news>')
        if article.featured_image:
            body.append('    <image:image xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">')
            body.append(f'      <image:loc>{escape(image_url(request, article))}</image:loc>')
            body.append(f'      <image:title>{escape(article.title or PUBLICATION_NAME)}</image:title>')
            body.append('    </image:image>')
        body.append('  </url>')
    body.append('</urlset>')
    return HttpResponse('\n'.join(body), content_type='application/xml')


def rss_feed(request):
    articles = News.objects.select_related('category').all().order_by('-created_at')[:50]
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        f'    <title>{escape(PUBLICATION_NAME)}</title>',
        f'    <link>{escape(absolute_url(request, reverse("homepage")))}</link>',
        f'    <atom:link href="{escape(absolute_url(request, reverse("rss_feed")))}" rel="self" type="application/rss+xml" />',
        '    <description>Latest news updates from Exclusive Bulletin.</description>',
        f'    <language>{PUBLICATION_LANGUAGE}</language>',
        f'    <lastBuildDate>{timezone.now().strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>',
    ]
    for article in articles:
        url = article_url(request, article)
        body.extend([
            '    <item>',
            f'      <title>{escape(article.title or PUBLICATION_NAME)}</title>',
            f'      <link>{escape(url)}</link>',
            f'      <guid isPermaLink="true">{escape(url)}</guid>',
            f'      <description>{escape(clean_description(article.text, 45))}</description>',
            f'      <pubDate>{article.created_at.strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>',
        ])
        if article.category:
            body.append(f'      <category>{escape(str(article.category))}</category>')
        body.append('    </item>')
    body.extend(['  </channel>', '</rss>'])
    return HttpResponse('\n'.join(body), content_type='application/rss+xml')
