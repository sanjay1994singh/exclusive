from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('news-detail/<int:id>/', views.news_detail, name='news_detail'),
    path('category_news/<int:id>/', views.category_news, name='category_news'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('news-sitemap.xml', views.news_sitemap_xml, name='news_sitemap_xml'),
]
