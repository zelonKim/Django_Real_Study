
import time
from django.db import connection, reset_queries
from django.db.models import Count, Avg, Q, Prefetch
from market.models import Product, Order, OrderItem


def understanding_db_blocking():
    """DB Blocking의 본질 이해"""
 
    print("""
    [성능 저하의 진실]

    많은 개발자들의 오해:
    ❌ "Python이 느려서 Django가 느리다"
    ❌ "코드를 최적화하면 빨라진다"
    ❌ "더 빠른 서버를 사면 해결된다"

    실제 원인:
    ✅ Django 성능 = DB 응답 속도
    ✅ Worker는 대부분 "DB 대기" 상태
    ✅ Python 실행 시간은 전체의 1~5%




##############################




# ============================================================================
# DB Blocking 최적화 방법
# ============================================================================

def db_blocking_checklist():

[1단계: 문제 파악]

✅ Django Debug Toolbar 설치
   pip install django-debug-toolbar
    → 각 페이지의 쿼리 수와 시간 확인

✅ 쿼리 로깅
   LOGGING = {
       'loggers': {
           'django.db.backends': {
               'level': 'DEBUG',
           }
       }
   }

✅ N+1 문제 감지
   - Similar queries 경고 확인
   - 반복문 안의 쿼리 찾기




##############################



[2단계: 쿼리 최적화]

✅ select_related 사용
    # ForeignKey, OneToOne
    Order.objects.select_related('user', 'address').all()

✅ prefetch_related 사용
    # ManyToMany, 역참조
    Order.objects.prefetch_related('items__product').all()

✅ only/defer 사용
    # 필요한 필드만 가져오기
    User.objects.only('id', 'username')

✅ annotate로 미리 계산
    # count, sum 등을 쿼리에서 계산
    Order.objects.annotate(item_count=Count('items'))

✅ exists() 사용
    # count() 대신, exists()
    if Order.objects.filter(user=user).exists():




##############################




[3단계: 인덱스 추가]

✅ 자주 조회하는 필드에 인덱스
   class Meta:
       indexes = [
           models.Index(fields=['status']),
           models.Index(fields=['created_at']),
       ]
       

✅ 복합 인덱스
   models.Index(fields=['user', 'status'])





##############################




[4단계: 캐싱 도입]

✅ 쿼리 결과 캐싱
   from django.core.cache import cache
   
   result = cache.get('key')
   if not result:
       result = expensive_query()
       cache.set('key', result, 300)


✅ 템플릿 프래그먼트 캐싱
   {% load cache %}
   {% cache 500 sidebar %}
       ... expensive queries ...
   {% endcache %}




##############################




[5단계: 비동기 처리]

✅ Celery로 백그라운드 작업
   @shared_task
   def generate_report():
       # 복잡한 집계 -> 오래 걸리는 작업은 비동기로


✅ 배치 처리
   # 실시간이 필요 없는 통계는 주기적으로
    """)
