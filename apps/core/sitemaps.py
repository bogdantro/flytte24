from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse


class StaticViewsSitemap(Sitemap):
    """The site's fixed, non-parameterized pages (spec §14: home=1.0,
    other static pages=0.8).

    Regression note: this class previously listed URL names from an
    unrelated car-dealership template ('sell', 'buy_car', 'verksted',
    'forsikring', 'finansiering', 'garanti', 'avtale', 'price', etc.) that
    have never existed in this project — every one of those reverse()
    calls raised NoReverseMatch, so GET /sitemap.xml 500'd unconditionally.
    """
    changefreq = 'daily'

    def items(self):
        return ['home', 'leads:wizard', 'for_business', 'blog_index', 'agency_list']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == 'home' else 0.8


class CitySitemap(Sitemap):
    """The 5 static city landing pages (spec §7/§14: priority 0.7)."""
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        from apps.leads.cities import CITIES
        return list(CITIES.keys())

    def location(self, slug):
        return reverse(f'city_{slug}')


class DistrictSitemap(Sitemap):
    """The 14 Oslo district pages (spec §8/§14: priority 0.6)."""
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        from apps.core.districts import OSLO_DISTRICTS
        return list(OSLO_DISTRICTS.keys())

    def location(self, slug):
        return reverse('district_detail', args=[slug])


class AgencySitemap(Sitemap):
    """Partner agency profile pages (spec §9/§14: priority 0.6)."""
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        from apps.core.models import Agency
        return Agency.objects.all()

    def location(self, agency):
        return reverse('agency_detail', args=[agency.slug])


class ArticleSitemap(Sitemap):
    """Blog articles (spec §10/§14: priority 0.5, real lastmod dates)."""
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        from apps.core.models import Article
        return Article.objects.all()

    def location(self, article):
        return reverse('blog_article', args=[article.slug])

    def lastmod(self, article):
        return article.date
