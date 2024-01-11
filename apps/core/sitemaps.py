from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse

class StaticViewsSitemap(Sitemap):
    changefreq = 'daily'  # Overall change frequency

    def items(self):
        return ['home', 'sell', 'book_time', 'buy_car', 'contact', 'verdivurdering', 'services', 'verksted', 'transport', 'forsikring', 'finansiering', 'garanti', 'avtale', 'about', 'price']

    def location(self, item):
        return reverse(item)


