from pyquery import PyQuery as pq

from schomeless.schema import Book, Chapter

__all__ = [
    'Ao3Api'
]


class Ao3Api:
    @staticmethod
    def parse_book(html_path):
        with open(html_path, 'r') as f:
            query = pq(f.read()).remove_namespaces()
        title = query('.meta h1').text()
        author = query('a[rel=author]').text()
        summary = ''
        summary_title = query('.meta p:contains("Summary")')
        if len(summary_title) > 0:
            summary = summary_title.next('blockquote').text()
        chapters = []
        chapters_node = query('div.userstuff')
        n_chapters = len(chapters_node)
        for i in range(n_chapters):
            node = chapters_node.eq(i)
            if node.attr('id') == 'chapters': continue
            # TODO: get chapter title
            paragraphs_node = node('p')
            n_paragraphs = len(paragraphs_node)
            paragraphs = paragraphs = [paragraphs_node.eq(i).text() for i in range(n_paragraphs)]
            chapters.append(Chapter(content="\n".join(paragraphs), title=''))
        book = Book(chapters, summary, title, author)
        return book
