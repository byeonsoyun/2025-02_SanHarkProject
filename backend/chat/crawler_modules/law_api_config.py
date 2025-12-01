# backend/chat/crawler_modules/law_api_config.py 수정

from .crawler_term import collect_and_normalize_terms
from .crawler_daily_term import collect_and_normalize_daily_terms
from .crawler_term_daily_rlt import collect_and_normalize_term_daily_rlt
from .crawler_daily_term_rlt import collect_and_normalize_daily_term_rlt
from .crawler_term_article_rlt import collect_and_normalize_term_article_rlt
from .crawler_article_term_rlt import collect_and_normalize_article_term_rlt
from .crawler_law_rlt import collect_and_normalize_law_rlt

from .crawler_precedent import collect_and_normalize_precedents # 🚨 판례 크롤러 임포트 추가 🚨



API_CONFIG = [
    {
        "name": "법령용어",
        "target": "lstrmAI",
        "doc_type": "법령용어",
        "collector_function": collect_and_normalize_terms,
    },
    {
        "name": "일상용어",
        "target": "dlytrm",
        "doc_type": "일상용어",
        "collector_function": collect_and_normalize_daily_terms,
    },

    {
        "name": "용어_일상용어_연계",
        "target": "lstrmRlt",
        "doc_type": "용어관계_법령_일상",
        "collector_function": collect_and_normalize_term_daily_rlt,
    },
    {
        "name": "일상용어_법령용어_연계",
        "target": "dlytrmRlt",
        "doc_type": "일상용어_법령용어_연계", # 새로운 doc_type 정의
        "collector_function": collect_and_normalize_daily_term_rlt,
    },

    {
        "name": "법령용어_조문_연계",
        "target": "lstrmRltJo",
        "doc_type": "법령용어_조문_연계", # 새로운 doc_type 정의
        "collector_function": collect_and_normalize_term_article_rlt,
    },

    {
        "name": "조문_법령용어_연계",
        "target": "joRltLstrm",
        "doc_type": "조문_법령용어_연계", # doc_type 정의
        "collector_function": collect_and_normalize_article_term_rlt,
    },

    {
        "name": "법령_법령_연계",
        "target": "lsRlt",
        "doc_type": "법령_법령_연계", # 새로운 doc_type 정의
        "collector_function": collect_and_normalize_law_rlt,
    },
]


    # # 🚨 판례 API 설정 추가 🚨
    # {
    #     "name": "판례",
    #     "target": "precSearch",
    #     "doc_type": "판례",
    #     "collector_function": collect_and_normalize_precedents,
    # },