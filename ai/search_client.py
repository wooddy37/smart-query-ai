import os
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes.models import (
        SearchIndex,
        SearchField,
        SearchFieldDataType,
        SimpleField,
        SearchableField,
        VectorSearch,
        VectorSearchProfile,
        HnswAlgorithmConfiguration,
    )
from ai.openai_client import openai_client 
from dotenv import load_dotenv

# .env 파일에서 환경 변수 불러오기 (API 키, 엔드포인트 등)
load_dotenv()

# OpenAI 모델 설정 (임베딩 모델명 등)
# deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
# embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# 인덱스 설정용 클라이언트 (인덱스 생성, 수정 등 구조 관리)
search_index_client = SearchIndexClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
)

# DBMS별 인덱스 네이밍
def get_index_name(dbms_type: str) -> str:
    base_name = os.getenv("AZURE_SEARCH_INDEX_NAME_BASE", "index-queries")
    return f"{base_name}-{dbms_type}"

# 검색용 클라이언트 (문서 업로드, 검색 등 데이터 조작)
# search_client = SearchClient(
#     endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
#     index_name=os.getenv("AZURE_SEARCH_INDEX_NAME", "dbms-queries"),
#     credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
# )

# DBMS별 SearchClient 생성(문서 업로드, 검색 등 데이터 조작)
def get_search_client(dbms_type: str) -> SearchClient:
    index_name = get_index_name(dbms_type)
    return SearchClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=index_name,
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
    )

# Azure Search 인덱스를 생성 (필드 정의 및 벡터 검색 설정 포함)    
def create_or_update_index(dbms_type: str) -> bool:
    """Azure AI Search 인덱스 생성"""
    index_name = get_index_name(dbms_type)
    
    # 인덱스 내 필드 정의 (일반 필드, 검색 필드, 벡터 필드 등)
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="user_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="sql_query", type=SearchFieldDataType.String, searchable=True),
        SearchableField(name="suggestion", type=SearchFieldDataType.String, searchable=True),
        SimpleField(name="query_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="duration_ms", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="language", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="dbms_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="project_code", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SearchField(
        name="sql_embedding",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="sql-profile"
        ),
    ]
    
    # 벡터 검색 설정 정의 (HNSW 알고리즘 사용, cosine 유사도)
    vector_search = VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="sql-profile",
                algorithm_configuration_name="sql-hnsw"
            )
        ],
        algorithms=[
            HnswAlgorithmConfiguration(
                name="sql-hnsw",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ]
    )
    
   # 인덱스 구성 객체 생성
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search
    )
    
    # 인덱스 생성 또는 업데이트 시도
    try:
        search_index_client.create_or_update_index(index)
        return True
    except Exception as e:
        raise RuntimeError(f"인덱스 생성/업데이트 실패: {e}")


# 키워드 기반 문서 검색 (벡터 검색이 아닌 일반 검색)
def search_documents(dbms_type: str, query_text: str, filters=None, top_k=10):
    # index_name = get_index_name(dbms_type=dbms_type)
    # get_or_create_search_index(index_name)

    create_or_update_index(dbms_type)
    client = get_search_client(dbms_type)
    try:
        # 임베딩 생성은 외부에서 수행하고 query_text와 벡터 둘다 전달하는 형태일 수 있음
        # 여기서는 간단히 query_text 텍스트검색 예시
        vector_query = None  # 필요시 확장 가능
        results = client.search(
            search_text=query_text,
            filter=filters,
            top=top_k,
            include_total_count=True
        )
        return list(results)
    except Exception as e:
        raise RuntimeError(f"검색 실패: {e}")

# # 인덱스 생성여부 체크
# def get_or_create_search_index(index_name: str):
#     # credential = AzureKeyCredential(AZURE_SEARCH_KEY)
#     # index_client = SearchIndexClient(endpoint=AZURE_SEARCH_ENDPOINT, credential=credential)

#     try:
#         search_index_client.get_index(index_name)
#     except Exception as e:
#         print(f"🔧 인덱스 '{index_name}' 가 없어 새로 생성합니다.")
#         fields = [
#             SimpleField(name="id", type=SearchFieldDataType.String, key=True),
#             SimpleField(name="user_id", type=SearchFieldDataType.String, filterable=True),
#             SearchableField(name="sql_query", type=SearchFieldDataType.String, searchable=True),
#             SearchableField(name="suggestion", type=SearchFieldDataType.String, searchable=True),
#             SimpleField(name="query_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
#             SimpleField(name="duration_ms", type=SearchFieldDataType.Double, filterable=True, sortable=True),
#             SimpleField(name="language", type=SearchFieldDataType.String, filterable=True, facetable=True),
#             SimpleField(name="dbms_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
#             SimpleField(name="project_code", type=SearchFieldDataType.String, filterable=True, facetable=True),
#             SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
#             SearchField(
#             name="sql_embedding",
#             type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
#             searchable=True,
#             vector_search_dimensions=1536,
#             vector_search_profile_name="sql-profile"
#             ),
#         ]
#         index = SearchIndex(name=index_name, fields=fields)
#         search_index_client.create_index(index)

# 의미 기반 검색 (벡터 임베딩을 이용한 semantic search)
def semantic_search_queries(dbms_type: str, query_text: str, filters=None, top_k=10):
    """의미 기반 검색 수행"""
    client = get_search_client(dbms_type)
    try:
         # 쿼리 텍스트를 벡터로 변환
        query_embedding = get_embedding(query_text)
        if not query_embedding:
            return []
        
        # 벡터 검색 쿼리 구성
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="sql_embedding"
        )
        
         # 검색 실행 (벡터 검색 + 키워드 검색 병행 가능)
        search_results = client.search(
            search_text=query_text,
            vector_queries=[vector_query],
            filter=filters,
            top=top_k,
            include_total_count=True
        )
        
        return list(search_results)
    except Exception as e:
        raise RuntimeError(f"검색 실패: {e}")
    

# 텍스트를 임베딩 벡터로 변환하는 함수 (OpenAI API 사용)
def get_embedding(text):
    """텍스트를 벡터 임베딩으로 변환"""
    try:
        response = openai_client.embeddings.create(
            input=text,
            model=embedding_deployment
        )
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"임베딩 생성 실패: {e}")

# 패싯(Facets) 필터링 정보 조회 (쿼리 타입, 언어, DBMS 분포)        
def get_facets(dbms_type: str):
    client = get_search_client(dbms_type)
    try:
        results = client.search(
            search_text="*",
            facets=["query_type", "language", "dbms_type"],
            top=0
        )
        return results.get_facets()
    except Exception as e:
        raise RuntimeError(f"패싯 조회 실패: {e}")


def index_query_to_search(doc: dict, dbms_type: str):

    # index_name = get_index_name(dbms_type)
    client = get_search_client(dbms_type)
    try:
        client.upload_documents([doc])
    except Exception as e:
        raise RuntimeError(f"[{get_index_name(dbms_type)}] 인덱스 업로드 실패: {e}")
    


