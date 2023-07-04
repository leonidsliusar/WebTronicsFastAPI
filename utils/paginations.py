from fastapi import Query


class Paginator:
    def __init__(self, page: int = Query(ge=0, default=0), limit: int = Query(ge=1, le=100, default=10)):
        self.page = page
        self.limit = limit
