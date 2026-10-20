"""Check local href/src targets and HTML fragments in the rendered Quarto site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1] / '_site'
PREFIX = '/pcb-for-beginners/'


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('name'):
            self.ids.add(attrs['name'])
        for key in ('href', 'src', 'poster'):
            if attrs.get(key):
                self.links.append(attrs[key])


def main():
    if not (ROOT / 'index.html').is_file():
        print('Missing _site/index.html. Run quarto render first.')
        return 1
    pages = {p.resolve(): Page(p) for p in ROOT.rglob('*.html')}
    errors = []
    checked = 0
    for path, page in pages.items():
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            route = unquote(url.path)
            if route.startswith(PREFIX):
                route = route[len(PREFIX):]
                target = ROOT / route
            elif route.startswith('/'):
                target = ROOT / route.lstrip('/')
            else:
                target = path.parent / route if route else path
            target = target.resolve()
            if target.is_dir():
                target = target / 'index.html'
            checked += 1
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                errors.append(f'{path.relative_to(ROOT)}: missing {link}')
            elif url.fragment and target.suffix == '.html':
                fragment = unquote(url.fragment)
                if target in pages and fragment not in pages[target].ids:
                    errors.append(f'{path.relative_to(ROOT)}: missing fragment {link}')
    for error in errors:
        print(error)
    print(f'Checked {len(pages)} HTML pages, {checked} local references: {len(errors)} errors')
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
