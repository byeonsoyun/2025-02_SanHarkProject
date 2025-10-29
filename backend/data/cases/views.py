from django.db.models import Q
from django.shortcuts import render
from .models import LawArticle, CaseLaw

def search_law(request):
    query = request.GET.get('q', '')
    law_results = []
    case_results = []

    if query:
        # 법령 검색
        law_results = LawArticle.objects.filter(
            Q(law_name__icontains=query) |
            Q(article_num__icontains=query) |
            Q(article_title__icontains=query) |
            Q(article_content__icontains=query)
        )[:50]

        # 판례 검색 (CaseLaw 필드명에 맞게 수정)
        case_results = CaseLaw.objects.filter(
            Q(case_title__icontains=query) |
            Q(content_summary__icontains=query) |
            Q(case_number__icontains=query) |
            Q(court_name__icontains=query)
        )[:50]

    return render(
        request,
        'cases/search.html',
        {
            'query': query,
            'law_results': law_results,
            'case_results': case_results
        }
    )
