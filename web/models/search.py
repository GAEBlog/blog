
from google.appengine.api import search

_INDEX_NAME = 'articles'

class BlogSearch():
    
    def get(self, query):
        """Handles a get request with a query."""
        
        # sort results by author descending
        expr_list = [search.SortExpression(
            expression='_score * _rank',
            direction=search.SortExpression.DESCENDING)]
        # construct the sort options
        sort_opts = search.SortOptions(
             expressions=expr_list)

        query_options = search.QueryOptions(
            limit=20,
            sort_options=sort_opts,
            returned_fields=['group', 'title', 'author', 'date'],
            snippeted_fields=['content'])
        
        query_obj = search.Query(query_string=query, options=query_options)
        
        return  search.Index(name=_INDEX_NAME).search(query=query_obj)
        

    def create_document(self, docid, date, author, content, title, group):
        """Creates a search.Document from content written by the author."""
        
        # Let the search service supply the document id.
        return search.Document(
            doc_id = docid,
            fields=[
                search.TextField(name='group',   value=group),
                search.TextField(name='title',   value=title),
                search.TextField(name='author',  value=author),
                search.HtmlField(name='content', value=content),
                search.DateField(name='date',    value=date)
            ]
        )


    def insert_document(self, document):
        search.Index(name=_INDEX_NAME).put(document)

    