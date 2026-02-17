import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


####################################


"""
1️⃣ Sync (동기 처리) 학습
Django의 기본 실행 구조와 Worker 점유 방식
"""

import time
import threading
from django.http import JsonResponse
from django.views import View
from market.models import Product, Order, OrderItem, User


def understanding_sync_architecture():
    """Django의 동기(sync) 처리 구조"""
    
    print("""
[Django의 기본 실행 구조]

┌─────────────────────────────────────────────────────────────────┐
│                        클라이언트 요청                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    웹 서버 (Nginx, Apache)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WSGI 서버 (Gunicorn, uWSGI)                   │
│                                                                  │
│    Worker 1    Worker 2    Worker 3    Worker 4                 │
│      [요청]      [대기]      [대기]      [요청]                 │
│                                                                  │
│    ⚠️  한 번에 하나의 요청만 처리                               │
│    ⚠️  처리 중에는 다른 요청 받을 수 없음                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Django 애플리케이션                         │
│                                                                  │
│    View → ORM → DB Query → 응답 대기 (Blocking!) → 응답         │
│                                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        데이터베이스                              │
└─────────────────────────────────────────────────────────────────┘


[핵심 개념]

1. **Worker = 동시 처리 단위**
   - Gunicorn 설정: workers = 4
   - 4개 요청만 동시 처리 가능
   - 5번째 요청은 대기

2. **Worker 점유 시간 = 요청 처리 시간**
   - 요청 받음 → Worker 점유 시작
   - DB 응답 대기 중에도 Worker 점유
   - 응답 완료 → Worker 해제

3. **Blocking의 의미**
   - DB 쿼리 실행 중 Worker는 "아무것도 안 함"
   - 다른 요청을 받을 수 없음
   - CPU는 놀고 있지만, Worker는 점유 상태

    """)



######################################



#  가장 기본적인 동기 뷰
def sync_simple_view():
    """
    동작:
    1. 요청이 들어오면 Worker 점유 시작
    2. DB 쿼리 실행 (Blocking)
    3. 응답 반환 (Worker 해제)
    """
    
    print("[예제 1] 동기 방식의 기본 동작")
    
    print(f"[{threading.current_thread().name}] 요청 처리 시작")
    # [MainThread] 요청 처리 시작
    
    start = time.time()
    products = list(Product.objects.all())  # DB 조회 - 이 시간 동안 Worker가 대기 상태
    db_time = time.time() - start
    
    print(f"[{threading.current_thread().name}] DB 조회 완료: {db_time:.3f}초")
    # [MainThread] DB 조회 완료: 0.027초
    




#####################################



# 느린 DB 쿼리 시뮬레이션
def sync_slow_query_view():
    """
    문제점:
    - DB가 느리면 Worker가 오래 점유됨.
    - 다른 요청들은 대기해야 함.
    """
    
    print("[예제 2] Blocking 시간 시뮬레이션")
    from django.db.models import Count, Avg
        
    worker_name = threading.current_thread().name
    print(f"\n[{worker_name}] 요청 시작") # [MainThread] 요청 시작

    start = time.time()
    
    orders = Order.objects.select_related('user').prefetch_related('items').annotate(
        item_count = Count('items') # 복잡한 집계 쿼리
    )[:50]
    
    order_list = list(orders) # # DB 응답 대기 중 - Worker는 이 시간 동안 점유 상태
    
    elapsed = time.time() - start
    
    print(f"[{worker_name}] DB 처리 완료: {elapsed:.3f}초") # [MainThread] DB 처리 완료: 0.048초
     # [MainThread]는 이 시간 동안 다른 요청 처리 불가!!
    



################################





print("[예제 3] Worker 점유시간 비교 - N+1문제")

def optimized_view():
    print("최적화된 쿼리 -> Worker 점유 시간 짧음.")
    
    worker = threading.current_thread().name
    
    start = time.time()

    # 연관 객체는 select_related 사용 -> 최적화된 쿼리
    orderItems = OrderItem.objects.select_related('product').all()
    
    result = []
    for orderItem in orderItems:
        result.append({
            'product_name': orderItem.product.name, # 추가 쿼리
            'quantity': orderItem.quantity,
        })
    
    elapsed = time.time() - start
    
    print(f"✅ [{worker}] 최적화 쿼리: {elapsed:.3f}초 점유")
    # ✅ [MainThread] 최적화 쿼리: 0.519초 점유
    
   
    ######################
   
   
def unoptimized_view():
    print("최적화 안 된 쿼리 -> Worker 점유 시간 김")
    
    worker = threading.current_thread().name
    start = time.time()
    
    # N+1 문제가 있는 쿼리
    orderItems = OrderItem.objects.all()
    
    result = []
    for orderItem in orderItems:
        result.append({
            'product_name': orderItem.product.name,
            'quantity': orderItem.quantity,
        })
    
    elapsed = time.time() - start
    
    print(f"❌ [{worker}] 비최적화 쿼리: {elapsed:.3f}초 점유")
    #  [MainThread] 비최적화 쿼리: 6.893초 점유
    print(f" → 이 시간의 대부분은 DB 응답 대기!")
    


################################



print("[예제 4] 동시 요청 처리 한계 시뮬레이션")

def simulate_concurrent_requests():
    """
    여러 요청이 동시에 들어올 때 Worker 부족 현상 시뮬레이션
    """

    print("""
    [시나리오]
    - Worker 4개로 운영 중
    - 각 요청은 DB 쿼리로 500ms 소요
    - 10개 요청이 동시에 들어옴.

    [처리 과정]

    시간(ms)    Worker 1   Worker 2   Worker 3   Worker 4   대기열
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    0           요청1      요청2      요청3      요청4      요청5-10 대기
                ↓          ↓          ↓          ↓
                DB 대기... DB 대기... DB 대기... DB 대기...

    500         완료✅     완료✅     완료✅     완료✅     
                요청5      요청6      요청7      요청8      요청9-10 대기
                ↓          ↓          ↓          ↓
                DB 대기... DB 대기... DB 대기... DB 대기...

    1000        완료✅     완료✅     완료✅     완료✅
                요청9      요청10     [대기]     [대기]
                ↓          ↓
                DB 대기... DB 대기...

    1500        완료✅     완료✅     


    [결과 분석]

    - 10개 요청 처리 시간: 1.5초
    - Worker가 8개였다면: 1초 (33% 개선)
    - 각 요청이 250ms였다면: 0.75초 (50% 개선)

    ⚠️  **핵심 교훈**
    1. Worker 수를 늘려도 한계가 있음.
    2. DB 쿼리 속도가 전체 처리량을 결정함.
    3. Worker는 대부분 "DB 응답 대기" 상태임.
    
        → 따라서 Worker 추가보다 쿼리 최적화가 우선!!
    """)



#############################



print("예제 5: 실제 성능 측정")

def measure_worker_efficiency():

    start = time.time()
    
    print("비효율적인 코드")
    # → 1 + N + (N×M) 쿼리 = 대부분 DB 대기 시간 소요
    for user in User.objects.all():  # 1번 쿼리
        orders = user.orders.all()   # N번 쿼리
        for order in orders:         # M번 쿼리
            items = order.items.all()

    elapsed = time.time() - start
    
    print(f" {elapsed:.3f}초 점유\n") #  0.373초 점유


    #############################
    
    
    start = time.time()

    print("효율적인 코드")
    # → 3번 쿼리로 해결 = DB 대기 시간 최소화
    
    users = User.objects.prefetch_related(
        'orders__items'
    ).all()
    
    elapsed = time.time() - start

    print(f" {elapsed:.3f}초 점유\n") #  0.001초 점유



#############################


print("예제 6: 실전 권장사항")

def sync_best_practices():

    print("""
    [1] Worker 수 설정

        # Gunicorn 설정 예시
        workers = (2 × CPU코어 수) + 1

        예: 4코어 서버
        workers = (2 × 4) + 1 = 9

        ⚠️  주의:
        - Worker를 너무 많이 만들면 메모리 부족
        - Worker를 너무 적게 만들면 대기 시간 증가
        - 최적값은 부하 테스트로 찾기


##############################


    [2] DB 쿼리 최적화 (가장 중요!)

    ✅ select_related 사용
        Product.objects.select_related('category').all()

    ✅ prefetch_related 사용
        Order.objects.prefetch_related('items').all()

    ✅ only/defer 사용
        User.objects.only('id', 'username')

    ✅ 집계 쿼리 최적화
        Product.objects.annotate(order_count=Count('orders'))

    ❌ 절대 금지
    - 반복문 안에서 쿼리
    - N+1 문제 방치
    - 불필요한 데이터 조회


#############################


[3] 인덱스 활용

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    
    class Meta:
        indexes = [
            models.Index(fields=['category']),  # 자주 검색하는 필드
            models.Index(fields=['name']),
        ]


#############################


[4] 커넥션 풀 설정

# settings.py
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # 10분간 연결 유지
    }
}



##########################

[결론]

Django Sync 모델에서 성능 개선 우선순위:

    1️⃣  DB 쿼리 최적화 (90% 효과)
    2️⃣  인덱스 추가 (5% 효과)
    3️⃣  Worker 수 조정 (3% 효과)
    4️⃣  Python 코드 최적화 (2% 효과)

    → DB 접근을 줄이는 것이 핵심!
        """)



###############################



if __name__ == "__main__":
    understanding_sync_architecture()
    sync_simple_view()
    sync_slow_query_view()
    optimized_view()
    unoptimized_view()
    simulate_concurrent_requests()
    measure_worker_efficiency()
    sync_best_practices()