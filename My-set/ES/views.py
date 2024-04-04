from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.paginator import EmptyPage
from django.shortcuts import render
from elasticsearch_dsl import A


@login_required
@ensure_csrf_cookie
def project_list(request):
    items_per_page = int(request.GET.get('page_size', 10))
    search = request.GET.get('search', '')
    page_size = request.GET.get('page_size', 10)
    industries_filter = request.GET.getlist('industries')
    technologies_filter = request.GET.getlist('technologies')
    is_public = request.GET.get('is_public', False)
    set_id = request.GET.get('set_id')

    result_set = ProjectDocument.search().filter('term', user__id=request.user.id)
    if is_public:
        result_set = result_set.filter('term', is_public=True)

    technology_agg = A('terms', field='technologies.name.keyword')
    result_set.aggs.bucket('technologies', technology_agg)

    industry_agg = A('terms', field='industries.name.keyword')
    result_set.aggs.bucket('industries', industry_agg)

    initial_technologies, initial_industries = ProjectListService.get_aggregation_results(result_set)

    if search:
        result_set = result_set.filter('multi_match', query=search, fields=['title', 'description'])
        technologies, industries = ProjectListService.get_aggregation_results(result_set)
        initial_technologies = ProjectListService.get_active_dict_items(initial_technologies, technologies)
        initial_industries = ProjectListService.get_active_dict_items(initial_industries, industries)

    if industries_filter:
        result_set = result_set.filter('terms', industries__name__keyword=industries_filter)
        technologies, _ = ProjectListService.get_aggregation_results(result_set)
        initial_technologies = ProjectListService.get_active_dict_items(initial_technologies, technologies)

    if technologies_filter:
        result_set = result_set.filter('terms', technologies__name__keyword=technologies_filter)
        _, industries = ProjectListService.get_aggregation_results(result_set)
        initial_industries = ProjectListService.get_active_dict_items(initial_industries, industries)

    filtered_technologies, filtered_industries = ProjectListService.get_aggregation_results(result_set)

    technologies = ProjectListService.confirm_dicts_with_items(initial_technologies, filtered_technologies)
    industries = ProjectListService.confirm_dicts_with_items(initial_industries, filtered_industries)

    elasticsearch_paginator = ElasticsearchQuerysetPaginator(result_set, items_per_page)
    page = int(request.GET.get('page', 1))

    try:
        projects = elasticsearch_paginator.page(page)
    except EmptyPage:
        projects = elasticsearch_paginator.page(elasticsearch_paginator.num_pages)

    data = {
        "projects": projects,
        "industries": industries,
        "technologies": technologies,
        "search": search,
        "sidebar_filter_params": {'industries': industries_filter,
                                  'technologies': technologies_filter},
        'page_size': page_size,
        'is_public': is_public,
    }
    if set_id:
        data.update({"set_id": set_id})
    return render(request, 'project_list.html', data)
