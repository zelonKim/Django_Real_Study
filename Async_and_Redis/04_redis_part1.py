import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


################################


"""
4️⃣ Redis를 통한 DB 부하 감소와 아키텍처 개선
"""

import time
import json
from django.views.decorators.cache import cache_page
from django.db import connection, reset_queries
from market.models import Product, Order
from django.core.cache import cache


"""Redis의 아키텍처적 역할 이해 - DB 보호를 위한 아키텍처 레이어"""
def understanding_redis_architecture():

    print("""
    [Redis에 대한 오해]

    ❌ 잘못된 이해:
        "Redis는 빠른 캐시다"
        "Redis를 쓰면 자동으로 빨라진다"
        "Redis = 성능 최적화 도구"

    ✅ 올바른 이해:
        "Redis는 DB 부하를 줄이는 아키텍처 레이어다"
        "Redis는 DB를 보호하기 위한 방어막이다"
        "Redis는 Worker 점유 시간을 줄인다"




    [Redis가 해결하는 진짜 문제]

    문제 상황:
    ┌─────────────────────────────────────────────────────────┐
    │  100개 요청 → 모두 같은 상품 조회                             │
    │                                                         │
    │  각 요청: DB 쿼리 100ms 소요                               │
    │  총 DB 부하: 100번 × 100ms = 10초                         │
    │                                                         │
    │  문제:                                                   │
    │  - DB에 동일한 쿼리 100번 실행                               │
    │  - Worker 100번 점유 (총 10초)                            │
    │  - DB 리소스 낭비                                         │
    └─────────────────────────────────────────────────────────┘

    Redis 도입 후:
    ┌─────────────────────────────────────────────────────────┐
    │  1번째 요청: DB 쿼리 (100ms) → Redis 저장                   │
    │  2-100번째 요청: Redis 조회 (1ms)                          │
    │                                                         │
    │  총 시간: 100ms + 99ms = 199ms                           │
    │  개선: 10초 → 0.2초 (50배 빠름!)                           │
    │                                                         │
    │  효과:                                                   │
    │  - DB 쿼리 100번 → 1번                                   │
    │  - Worker 점유 10초 → 0.2초                              │
    │  - DB 보호 ✅                                            │
    └─────────────────────────────────────────────────────────┘




    [Redis의 실제 역할]

    1. DB 방어막 (Shield)
    ┌─────────┐
    │ Request │
    └────┬────┘
         │
    ┌────▼────┐
    │  Redis  │ ← 대부분의 요청이 여기서 처리
    └────┬────┘
         │ (캐시 미스)
    ┌────▼────┐
    │   DB    │ ← 필요할 때만 접근
    └─────────┘


    2. Worker 점유 시간 감소
    - DB 조회: 100ms
    - Redis 조회: 1ms
    → Worker가 99ms 빨리 해제됨
    → 더 많은 요청 처리 가능


    3. DB 리소스 절약
    - 동일한 쿼리 반복 방지
    - DB 커넥션 절약
    - DB CPU/메모리 절약



    [성능 개선의 본질]
    ❌ "Redis가 빨라서" (X)
    ✅ "DB 접근을 줄여서" (O)

    Redis는 도구일 뿐, 핵심은:
        → 불필요한 DB 접근 제거
        → Worker 점유 시간 최소화
        → 시스템 안정성 확보
     """)






# ============================================================================
# 예제 1: Redis 없이 vs Redis 사용 비교
# ============================================================================

def without_redis_example():
    """Redis 없이 동일한 데이터를 여러 번 조회"""
    from market.models import Product
    
    # 시나리오: 같은 상품 정보를 1000번 조회
    product_id = 1
    iterations = 1000
    
    reset_queries()
    
    start = time.time()
    
    for i in range(iterations):
        # 매번 DB 조회!
        product = Product.objects.get(id=product_id)
        _ = product.name
    
    elapsed = time.time() - start
    
    queries = len(connection.queries) 
    
    
    
    
    print(f"\n[Redis 없음]")
    print(f"조회 횟수: {iterations}번") # 1000번
    print(f"실행 시간: {elapsed * 1000:.2f}ms") # 118.42ms
    print(f"쿼리 수: {queries}개") # 1000개
    print(f"평균 시간: {(elapsed / iterations) * 1000:.2f}ms per request") # 0.12ms per request

    
    print(f"\n문제점:")
    print(f"→ 동일한 쿼리를 {queries}번 실행") # 1000번 실행
    print(f"→ DB 커넥션 {queries}번 사용") #  1000번 사용
    print(f"→ Worker가 {elapsed:.2f}초 동안 점유") #  0.12초 동안 점유
    print(f"→ DB 리소스 낭비")
    
    return elapsed, queries


    ################################
    

# Django에서 Redis를 사용할 때는 django.core.cache를 통해 키–밸류 쌍 형태로 읽기, 쓰기, 삭제를 수행함.

def with_redis_example():
    """Redis로 캐싱하여 DB 접근 최소화"""
    from market.models import Product
    from django.core.cache import cache
    
    product_id = 1
    iterations = 1000
    cache_key = f'product:{product_id}'
    
    cache.delete(cache_key)  # Redis 캐시 삭제
    
    reset_queries()
    start = time.time()
    
    for i in range(iterations):
        product_data = cache.get(cache_key) # Redis 캐시 읽기
        
        if product_data is None: # 캐시 Miss
            product = Product.objects.get(id=product_id) # DB 조회
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': float(product.price)
            }
            
            cache.set(cache_key, product_data, 300)  # Redis 캐시 쓰기 (300초)
            print(f"[{i + 1}] DB 조회 → Redis 저장")
            
        else:  # 캐시 Hit
            if i == 1:
                print(f"[{i + 1}] Redis에서 조회 (이후 생략...)")
    
    elapsed = time.time() - start
    queries = len(connection.queries)
    
    
    
    print(f"\n[Redis 사용]")
    print(f"조회 횟수: {iterations}번") # 1000번
    print(f"실행 시간: {elapsed * 1000:.2f}ms") # 55.38ms
    print(f"쿼리 수: {queries}개") # 1개
    print(f"평균 시간: {(elapsed / iterations) * 1000:.2f}ms per request") # 0.06ms per request
    
    print(f"\n개선 효과:")
    print(f"→ DB 쿼리 1번만 실행")
    print(f"→ 나머지 999번은 Redis에서 조회")
    print(f"→ Worker 점유 시간 대폭 감소")
    print(f"→ DB 부하 99% 감소")
    
    return elapsed, queries




    ########################
    
    
    
    
"""Redis 도입 전후 비교"""
def compare_redis_impact():
    
    # 측정
    no_redis_time, no_redis_queries = without_redis_example()
    redis_time, redis_queries = with_redis_example()
    
    # 비교
    time_improvement = ((no_redis_time - redis_time) / no_redis_time) * 100
    query_reduction = ((no_redis_queries - redis_queries) / no_redis_queries) * 100
    
    print(f"\n시간:")
    print(f"  Redis 없음: {no_redis_time*1000:.2f}ms") #  118.42ms
    print(f"  Redis 사용: {redis_time*1000:.2f}ms") #  55.38ms
    print(f"  개선율: {time_improvement:.1f}% 빠름") # 53.2% 빠름
    
    print(f"\nDB 쿼리:")
    print(f"  Redis 없음: {no_redis_queries}개") # 1000개
    print(f"  Redis 사용: {redis_queries}개") # 1개
    print(f"  감소율: {query_reduction:.1f}% 감소") # 99.9% 감소
    
    print(f"\n핵심 인사이트:")
    print(f"→ Redis의 목적은 '속도'가 아니라, 'DB 보호'임.")
    print(f"→ 부수 효과로 응답 시간도 빨라짐")





# ============================================================================
# 예제 2: Cache-Aside 패턴 구현
# ============================================================================

"""Cache-Aside 패턴의 정확한 구현"""
class CacheAsidePattern:

    @staticmethod
    def get_product(product_id):
        from django.core.cache import cache
        
        """
        [Cache-Aside 패턴]
        
        흐름:
            1. 캐시 확인
            2. 있으면 반환 (캐시 Hit)
            3. 없으면 DB 조회 (캐시 Miss)
            4. DB 결과를 캐시에 저장
            5. 반환
        """
        
        
        cache_key = f'product:{product_id}'
        
        # 1. 캐시 확인
        cached = cache.get(cache_key)
        
        if cached:
            # 2. 있으면 반환
            print(f"✅ 캐시 히트: product:{product_id}")
            return cached
        
        # 3. 없으면 DB 조회
        print(f"❌ 캐시 미스: product:{product_id} → DB 조회")
        product = Product.objects.get(id=product_id)
        
        
        # 4. DB 결과를 캐시에 저장
        product_data = {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'category': product.category
        }
        cache.set(cache_key, product_data, 300) 
        
        
        # 5. 반환
        return product_data

    
    
    
    ###########################
    
    
    

    @staticmethod
    def get_order_with_items(order_id):
        from django.core.cache import cache
        
        """
        복잡한 데이터의 Cache-Aside 패턴
        """
        
        cache_key = f'order_full:{order_id}'
        
        # 1. 캐시 확인
        cached = cache.get(cache_key)
        
        if cached:
            # 2. 있으면 반환
            print(f"✅ 캐시 Hit: order:{order_id}")
            return cached
        
        # 3. 없으면 DB 조회 
        print(f"❌ 캐시 미스: order:{order_id} → DB 조회")

        order = Order.objects.select_related('user').prefetch_related(
            'items__product'
        ).get(id=order_id)
        
        
        # 4. DB 결과를 캐시에 저장
        order_data = {  # 데이터 직렬화
            'id': order.id,
            'user': {
                'id': order.user.id,
                'username': order.user.username
            },
            'total_amount': float(order.total_amount),
            'items': [
                {
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price)
                }
                for item in order.items.all()
            ]
        }
        
        cache.set(cache_key, order_data, 300)
        
        # 5. 반환
        return order_data
    
    
    
    
    
    ##########################
    
    
    
    
    @staticmethod
    def update_product(product_id, **updates):
        """
        중요!! 데이터가 변경되면 캐시를 삭제해줘야 함.
        """
        # 1. DB 업데이트
        Product.objects.filter(id=product_id).update(**updates)
        
        # 2. 캐시 무효화 (삭제)
        cache_key = f'product:{product_id}'
        cache.delete(cache_key)
        
        print(f"✅ 상품 업데이트 완료")
        print(f"✅ 캐시 무효화: {cache_key}")
        print(f"   다음 조회 시 DB에서 새로 가져옴")









# ============================================================================
# 예제 3: 실전 사용 예제 - 상품 목록
# ============================================================================

"""캐시 없는 상품 목록 - 매번 DB 조회"""
def product_list_without_cache():
    from market.models import Product
    
    # 100번 요청 시뮬레이션
    iterations = 100
    
    reset_queries()
    start = time.time()
    
    for i in range(iterations):
        # 매번 DB 조회
        products = Product.objects.filter(
            category='Electronics'
        ).order_by('-created_at')[:100]
        
        product_list = list(products)
        
        if i == 0:
            print(f"  [{i+1}] DB 조회: {len(product_list)}개 상품") # [1] DB 조회: 0개 상품
    
    elapsed = time.time() - start
    queries = len(connection.queries)
    
    print(f"\n결과:")
    print(f"  요청 수: {iterations}번") # 100번
    print(f"  총 시간: {elapsed*1000:.2f}ms") # 31.38ms
    print(f"  쿼리 수: {queries}개") # 100개
    print(f"  평균 응답: {(elapsed/iterations)*1000:.2f}ms") # 0.31ms
    
    return elapsed, queries


    #############################
    

"""캐시 사용 상품 목록 - 한 번만 DB 조회"""
def product_list_with_cache():
    from market.models import Product
    
    cache_key = 'product_list:electronics:100'
    
    # 캐시 클리어
    cache.delete(cache_key)
    
    iterations = 100
    
    reset_queries()
    
    start = time.time()
    
    for i in range(iterations):
        # 캐시 확인
        product_data = cache.get(cache_key)
        
        if product_data is None: # 캐시 Miss -> DB 조회
            products = Product.objects.filter(
                category='Electronics'
            ).order_by('-created_at')[:100]
            
            product_data = [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': float(p.price)
                }
                for p in products
            ]
            
            cache.set(cache_key, product_data, 300)
            print(f"  [{i+1}] DB 조회 → 캐시 저장") # [1] DB 조회 → 캐시 저장
            
        else: # 캐시 Hit
            if i == 1:
                print(f"  [{i+1}] 캐시 조회 (이후 생략...)") # [2] 캐시 조회 (이후 생략...)
    
    elapsed = time.time() - start
    queries = len(connection.queries)
    
    print(f"\n결과:")
    print(f"  요청 수: {iterations}번") # 100번
    print(f"  총 시간: {elapsed*1000:.2f}ms") # 11.96ms
    print(f"  쿼리 수: {queries}개") # 1개
    print(f"  평균 응답: {(elapsed/iterations)*1000:.2f}ms") # 0.12ms
    
    return elapsed, queries




# ============================================================================
# 예제 4: 뷰 레벨 캐싱
# ============================================================================

""" View-Level Cache 예제"""
def simulate_view_cache():
    import time
    from django.test import RequestFactory
    from django.views.decorators.cache import cache_page
    from django.http import JsonResponse
    from django.core.cache import cache
    from django.db import connection, reset_queries
    from market.models import Product

    rf = RequestFactory()

    # 캐시 초기화
    cache.clear()

    @cache_page(60 * 1) # View 응답 결과를 일정 시간 동안 캐시에 저장하여 그대로 재사용하도록 해줌.
    def product_list_view(request):
        """
        실제 View라고 가정하는 함수
        """
        products = list(Product.objects.all()[:100])

        # DB 비용을 일부러 크게 만들어 체감되게 함
        time.sleep(0.01)

        return JsonResponse({
            "count": len(products)
        })



    print("\n=== View Cache 실험 시작 ===")

    for i in range(5):
        reset_queries()

        request = rf.get("/products/")  # 같은 URL 요청 흉내

        start = time.time()
        response = product_list_view(request)
        print(response)
        elapsed = time.time() - start

        print(f"{i+1}번째 요청")
        print(f"  응답시간: {elapsed * 1000:.2f} ms")
        print(f"  DB 쿼리수: {len(connection.queries)} 개")

        
        # 1번째 요청
        #   응답시간: 20.83 ms
        #   DB 쿼리수: 1 개
        
        # 2번째 요청
        #   응답시간: 0.55 ms
        #   DB 쿼리수: 0 개
        
        # 3번째 요청
        #   응답시간: 0.38 ms
        #   DB 쿼리수: 0 개
        
        # 4번째 요청
        #   응답시간: 0.35 ms
        #   DB 쿼리수: 0 개
        
        # 5번째 요청
        #   응답시간: 0.30 ms
        #   DB 쿼리수: 0 개



"""
    [장점]
        ✅ 간단한 구현
        ✅ 전체 응답을 캐싱
        ✅ Worker 점유 시간 최소화


    [단점]
        ❌ 세밀한 제어 어려움
        ❌ 사용자별 캐시 불가
        ❌ 동적 컨텐츠 처리 어려움


    [추천 사용 사례]
        - 공개 API 엔드포인트
        - 정적인 목록 페이지
        - 자주 변경되지 않는 데이터
"""




################################




if __name__ == "__main__":
    compare_redis_impact()
    

    # Cache-Aside 패턴
    cache_aside = CacheAsidePattern()
    
    # 첫 조회 - 캐시 Miss
    product1 = cache_aside.get_product(1)
    
    # 두 번째 조회 - 캐시 Hit
    product2 = cache_aside.get_product(1)
    
    
    
    # 상품 목록 비교
    no_cache_time, no_cache_queries = product_list_without_cache()
    cache_time, cache_queries = product_list_with_cache()
    
    improvement = ((no_cache_time - cache_time) / no_cache_time) * 100
    print(f"\n상품 목록 개선율: {improvement:.1f}%") # 61.9%


    
    simulate_view_cache()
