from bs4 import BeautifulSoup


def html_to_safe_text(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup(['script', 'style', 'iframe', 'object', 'embed']):
        tag.decompose()

    for tag in soup.find_all():
        attrs_to_remove = [attr for attr in tag.attrs if attr.startswith('on')]
        for attr in attrs_to_remove:
            del tag.attrs[attr]

        if 'href' in tag.attrs:
            href = tag.attrs['href']
            if isinstance(href, list):
                href = href[0] if href else ''
            if href.startswith('javascript:'):
                del tag.attrs['href']

    return soup.get_text(separator=' ', strip=True)
