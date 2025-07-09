import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")
# EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")

# def get_embedding(text):
#     try:
#         response = openai_client.embeddings.create(
#             model=EMBEDDING_DEPLOYMENT,
#             input=text
#         )
#         return response.data[0].embedding
#     except Exception as e:
#         raise RuntimeError(f"임베딩 생성 실패: {e}")

def get_tuning_suggestion(sql, duration_ms, lang, similar_queries=None, dbms_type="PostgreSQL"):
    base_prompt = ""
    if similar_queries:
        base_prompt = f"""
참고: 다음은 유사한 쿼리들과 과거 튜닝 제안들입니다:
{chr(10).join([f"- SQL: {q['sql_query'][:100]}..." + f"  제안: {q['suggestion'][:100]}..." for q in similar_queries[:3]])}

"""
    if lang == "한국어":
        system_msg = f"당신은 {dbms_type} 성능 최적화를 잘하는 전문가입니다. 과거 유사 사례를 참고하여 더 정확한 답변을 제공하세요."
        prompt = base_prompt + f"""
다음 {dbms_type} SQL 쿼리는 {duration_ms:.2f}ms 이상 걸렸거나 오류가 발생했습니다.
성능 향상 또는 오류 수정 방안을 **한국어로** 제안해 주세요.

SQL:
{sql}
"""
    elif lang == "Tiếng Việt":
        system_msg = f"Bạn là chuyên gia tối ưu hiệu suất truy vấn {dbms_type}. Hãy tham khảo các trường hợp tương tự để đưa ra lời khuyên chính xác hơn."
        prompt = base_prompt + f"""
Câu truy vấn {dbms_type} sau đây mất hơn {duration_ms:.2f}ms hoặc gặp lỗi khi thực thi.
Hãy đưa ra đề xuất cải thiện hiệu suất **bằng tiếng Việt**.

SQL:
{sql}
"""
    else:
        system_msg = f"You are an experienced {dbms_type} SQL performance expert. Use similar past cases to provide more accurate recommendations."
        prompt = base_prompt + f"""
The following {dbms_type} SQL query took over {duration_ms:.2f}ms or caused an error.
Please suggest performance improvements or error fixes in **English**.

SQL:
{sql}
"""

    try:
        response = openai_client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Azure OpenAI API 에러: {e}"
