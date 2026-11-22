"""Small presentation helpers; business values still come from store records."""
from django import template

register = template.Library()


@register.filter
def initials(value):
    words = str(value or '').split()
    return ''.join(word[0] for word in words[:2]).upper() or '—'


def artwork_for_unit(unit):
    """Match the supplied container illustrations to the product's saved unit."""
    unit = str(unit or '').strip().casefold()
    if unit in ('pack', 'packs', 'packet', 'packets', 'bag', 'bags'):
        return 'imgProductIllustrationPacket'
    if unit in ('can', 'cans', 'tin', 'tins'):
        return 'imgProductIllustrationCan'
    if unit in ('sachet', 'sachets', 'pouch', 'pouches'):
        return 'imgProductIllustrationSachet'
    return 'imgIconPackage'


register.filter('product_artwork', artwork_for_unit)
