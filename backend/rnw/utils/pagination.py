def paginate_query(query, page: int = 1, per_page: int = 12):
    page = max(int(page or 1), 1)
    per_page = min(max(int(per_page or 12), 1), 100)
    return query.paginate(page=page, per_page=per_page, error_out=False)
