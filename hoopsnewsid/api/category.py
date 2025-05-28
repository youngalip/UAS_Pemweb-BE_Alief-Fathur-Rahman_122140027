# hoopsnewsid/api/categories.py
from pyramid.view import view_config
from ..models.category import Category

@view_config(route_name='categories', renderer='json', request_method='GET')
def get_categories(request):
    try:
        categories = request.db.query(Category).all()  # gunakan request.db
        return [{'id': c.id, 'name': c.name} for c in categories]
    except AttributeError:
        request.response.status = 500
        return {'message': 'Database session not available in request'}
    except Exception as e:
        request.response.status = 500
        return {'message': str(e)}
