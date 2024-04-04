from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from import_export import resources, fields
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget
from .models import Project, Technology, Industry


class ProjectResource(resources.ModelResource):

    def __init__(self, **kwargs):
        super().__init__()
        self.project_user = kwargs.get("project_user")

    technologies = fields.Field(
        column_name='technologies',
        attribute='technologies',
        widget=ManyToManyWidget(Technology, field='name', separator=',')
    )
    industries = fields.Field(
        column_name='industries',
        attribute='industries',
        widget=ManyToManyWidget(Industry, field='name', separator=',')
    )
    project_user = fields.Field(column_name='user', attribute='user', widget=ForeignKeyWidget(get_user_model(), 'name'))

    class Meta:
        model = Project
        fields = ('id', 'title', 'url', 'description', 'technologies', 'industries', 'notes')
        export_order = fields
        skip_unchanged = True
        report_skipped = False

    def after_import_instance(self, instance, new: bool, row_number: int = None, **kwargs) -> None:
        """
        Set the user attribute of the imported instance.

        Args:
            instance (Project): The imported Project instance.
            new (bool): Indicates whether the instance is new or updated.
            row_number (int): The row number in the import file (optional).
            **kwargs: Additional keyword arguments.

        Returns:
            None

        """
        instance.user = kwargs.get("project_user")

    def filter_export(self, queryset: QuerySet, *args, **kwargs) -> QuerySet:
        """
        Filter the queryset based on the project user.

        Args:
            queryset (QuerySet): The original queryset to filter.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            QuerySet: The filtered queryset.
        """
        if self.project_user:
            return queryset.filter(user=self.project_user)
        return queryset
