from django.core.paginator import Paginator


class ElasticsearchQuerysetPaginator(Paginator):
    """
    Paginator class for ES.
    """
    def page(self, number: int):
        """
        Return a Page object for the given 1-based page number.

        Args:
            number (int): The 1-based page number to retrieve.

        Returns:
            Page: A Page object representing the requested page.

        """
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(self.object_list[bottom:top].to_queryset(), number, self)