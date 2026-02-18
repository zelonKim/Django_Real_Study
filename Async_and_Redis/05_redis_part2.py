import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


#################################


"""
4️⃣ Redis 고급 캐싱 패턴 실습
"""
import time
import hashlib
import random
import threading
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from market.models import Product, Order
from django.db import connection, reset_queries
from django.db.models import Sum, Avg, Count

# ============================================================================
# 실습 1: TTL 기반 캐싱 (시간 기반 무효화)
# ============================================================================

def practice_ttl_caching():
    """TTL 기반 캐싱 실습"""

    # 상품 데이터 캐싱 함수
    def get_product_with_ttl(product_id, ttl=300):
        """TTL을 사용한 상품 조회"""
        cache_key = f'product_ttl:{product_id}'
        
        # 캐시 확인
        product_data = cache.get(cache_key)
        
        if product_data:
            print(f"✅ 캐시 히트: product_id={product_id}")
            return product_data
        
        # 캐시 미스 - DB 조회
        print(f"❌ 캐시 미스: product_id={product_id} → DB 조회")
        try:
            product = Product.objects.get(id=product_id)
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'category': product.category,
            }
            
            # TTL과 함께 캐시 저장
            cache.set(cache_key, product_data, ttl)
            print(f"💾 캐시 저장 완료 (TTL: {ttl}초)")
            return product_data
        
        except Product.DoesNotExist:
            return None
    
    
    
    
    print("\n[테스트 1] 짧은 TTL (5초)")
    product1 = get_product_with_ttl(1, ttl=5)
    print(f"데이터: {product1}") 
    # ❌ 캐시 미스: product_id=1 → DB 조회
    # 💾 캐시 저장 완료 (TTL: 5초)
    # 데이터: {'id': 1, 'name': 'Product 0', 'price': 725.0, 'category': 'electronics'}
        
    
    print("\n[테스트 2] 즉시 다시 조회 (캐시 히트)")
    product1_cached = get_product_with_ttl(1, ttl=5)
    print(f"데이터: {product1_cached}")
    # ✅ 캐시 히트: product_id=1
    # 데이터: {'id': 1, 'name': 'Product 0', 'price': 725.0, 'category': 'electronics'}

    
    print("5초 대기 중...")
    time.sleep(5.1)
    
    
    print("\n[테스트 3] 5초 대기 후 조회 (캐시 만료)")
    product1_expired = get_product_with_ttl(1, ttl=5)
    print(f"데이터: {product1_expired}")
    # ❌ 캐시 미스: product_id=1 → DB 조회
    # 💾 캐시 저장 완료 (TTL: 5초)
    # 데이터: {'id': 1, 'name': 'Product 0', 'price': 725.0, 'category': 'electronics'}
        

    print("\n✅ TTL 실습 완료!")
    print("💡 배운 점: TTL은 데이터 특성에 맞게 설정해야 함")







# ============================================================================
# 실습 2: 이벤트 기반 캐시 무효화 (Django Signal)
# ============================================================================

"""상품이 저장되면 관련 캐시를 모두 삭제하는 시그널"""
@receiver(post_save, sender=Product) # 상품이 저장될때 해당 함수를 자동실행 하도록 함.
def invalidate_product_cache_on_save(sender, instance, **kwargs):

    cache_keys = [
        f'product:{instance.id}',
        f'product_ttl:{instance.id}',
        f'product_detail:{instance.id}',
    ]
    
    for key in cache_keys:
        cache.delete(key)  # 개별 상품 캐시 삭제
    
    # 카테고리 관련 캐시 삭제
    cache.delete(f'products_by_category:{instance.category}')
    
    print(f"🗑️ 캐시 무효화: Product {instance.id} 저장됨.")


###########################


"""상품이 삭제되면 관련 캐시를 모두 삭제하는 시그널"""
@receiver(post_delete, sender=Product) # 상품이 삭제될때 해당 함수를 자동실행 하도록 함.
def invalidate_product_cache_on_delete(sender, instance, **kwargs):
    
    cache_keys = [
        f'product:{instance.id}',
        f'product_ttl:{instance.id}',
        f'product_detail:{instance.id}',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    cache.delete(f'products_by_category:{instance.category}')
    
    print(f"🗑️ 캐시 무효화: Product {instance.id} 삭제됨")


########################


"""이벤트 기반 캐시 무효화 실습"""
def practice_event_based_invalidation():

    # 상품 조회 및 캐싱
    def get_product_cached(product_id):
        cache_key = f'product:{product_id}'
        
        product_data = cache.get(cache_key)
        if product_data:
            print(f"✅ 캐시 히트: {cache_key}")
            return product_data
        
        print(f"❌ 캐시 미스: {cache_key}")
        try:
            product = Product.objects.get(id=product_id)
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
            }
            cache.set(cache_key, product_data, 300)
            return product_data
        
        except Product.DoesNotExist:
            return None
    
    
    
    print("\n[테스트 1] 상품 조회 및 캐싱")
    product = get_product_cached(1)
    print(f"상품 데이터: {product}")
    # ❌ 캐시 미스: product:1
    # 상품 데이터: {'id': 1, 'name': 'Product 0', 'price': 725.0}
    
    
    print("\n[테스트 2] 다시 조회 (캐시 히트)")
    product = get_product_cached(1)
    print(f"상품 데이터: {product}")
    # ✅ 캐시 히트: product:1
    # 상품 데이터: {'id': 1, 'name': 'Product 0', 'price': 725.0}
    
    
    
    
    print("\n[테스트 3] 상품 정보 수정")
    try:
        product_obj = Product.objects.get(id=2)
        old_price = product_obj.price
        product_obj.price = float(product_obj.price) + 100
        product_obj.save()  # 시그널 발동 → invalidate_product_cache_on_save() 호출 
        # 🗑️ 캐시 무효화: Product 1 저장됨.
        
        print("\n[테스트 4] 수정 후 다시 조회 (캐시 미스)")
        product = get_product_cached(2)
        # ❌ 캐시 미스: product:1
        
        
        product_obj.delete() # 시그널 발동 -> invalidate_product_cache_on_delete() 호출
         # 🗑️ 캐시 무효화: Product 1 삭제됨
         
        product = get_product_cached(1)
        # ❌ 캐시 미스: product:1

        
    except Product.DoesNotExist:
        print("상품이 존재하지 않습니다.")
    
    print("\n✅ 이벤트 기반 캐시 무효화 실습 완료!")
    print("💡 배운 점: 데이터 변경 시 자동으로 캐시가 갱신됨")






# ============================================================================
# 실습 3: 태그 기반 캐시 무효화
# ============================================================================

class TagBasedCache:
    """태그 기반 캐시 관리"""
    
    @staticmethod
    def get_tag_version(tag):
        """태그의 현재 버전 가져오기"""
        key = f'tag_version:{tag}'
        version = cache.get(key)
        if version is None:
            version = 1
            cache.set(key, version, None)  # 영구 저장
        return version
    
    
    @staticmethod
    def invalidate_tag(tag):
        """태그 버전 증가 → 관련 캐시 모두 무효화"""
        key = f'tag_version:{tag}'
        version = cache.get(key, 0)
        cache.set(key, version + 1, None)
        print(f"🔄 태그 무효화: {tag} (v{version} → v{version+1})")
    
    
    @staticmethod
    def get_cached_data(cache_key, tag, fetch_func, ttl=300):
        """태그를 포함한 캐시 키로 데이터 가져오기"""
        # 태그 버전 포함한 실제 캐시 키
        tag_version = TagBasedCache.get_tag_version(tag)
        versioned_key = f'{cache_key}:v{tag_version}'
        
        # 캐시 확인
        data = cache.get(versioned_key)
        if data:
            print(f"✅ 캐시 히트: {versioned_key}")
            return data
        
        # 캐시 미스 - 데이터 가져오기
        print(f"❌ 캐시 미스: {versioned_key}")
        data = fetch_func()
        cache.set(versioned_key, data, ttl)
        
        return data


###########################


"""태그 기반 캐시 무효화 실습"""
def practice_tag_based_invalidation():
    
    # 카테고리별 상품 목록 조회
    def get_products_by_category(category):
        """카테고리별 상품 목록"""
        def fetch():
            products = Product.objects.filter(category=category)[:5]
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': float(p.price)
                }
                for p in products
            ]
        
        cache_key = f'products_by_category:{category}'
        
        return TagBasedCache.get_cached_data(
            cache_key, 
            tag='products',  # 모든 상품 관련 캐시에 'products' 태그
            fetch_func=fetch
        )
    
    
    
    print("\n[테스트 1] 여러 카테고리 상품 조회")
    electronics = get_products_by_category('Electronics')
    print(f"Electronics 상품 수: {len(electronics)}")
    # ❌ 캐시 미스: products_by_category:Electronics:v1
    # Electronics 상품 수: 0
    
    books = get_products_by_category('Books')
    print(f"Books 상품 수: {len(books)}")
    # ❌ 캐시 미스: products_by_category:Books:v1
    # Books 상품 수: 0
    
    print("\n[테스트 2] 다시 조회 (캐시 히트)")
    electronics = get_products_by_category('Electronics')
    books = get_products_by_category('Books')
    # ❌ 캐시 미스: products_by_category:Electronics:v1
    # ❌ 캐시 미스: products_by_category:Books:v1
    
    
    print("\n[테스트 3] 'products' 태그 무효화")
    print("→ 모든 상품 관련 캐시가 한 번에 무효화됨")
    TagBasedCache.invalidate_tag('products')
    # 🔄 태그 무효화: products (v1 → v2)
    
    
    print("\n[테스트 4] 무효화 후 다시 조회 (캐시 미스)")
    electronics = get_products_by_category('Electronics')
    books = get_products_by_category('Books')
    # ❌ 캐시 미스: products_by_category:Electronics:v2
    # ❌ 캐시 미스: products_by_category:Books:v2
    
    
    print("\n✅ 태그 기반 캐시 무효화 실습 완료!")
    print("💡 배운 점: 관련된 캐시를 그룹으로 한 번에 무효화 가능")






# ============================================================================
# 실습 4: 캐시 스탬피드 방지 (락 사용)
# ============================================================================

class CacheWithLock:
    """락을 사용한 캐시 스탬피드 방지"""
    
    _locks = {}
    
    @classmethod
    def get_or_set(cls, cache_key, fetch_func, ttl=300):
        """락을 사용하여 안전하게 캐시 가져오기"""
        # 1차 캐시 확인
        data = cache.get(cache_key)
        if data:
            return data
        
        # 락 생성 (없으면)
        if cache_key not in cls._locks:
            cls._locks[cache_key] = threading.Lock()
        
        # 락 획득
        with cls._locks[cache_key]:
            # 2차 캐시 확인 (다른 스레드가 채웠을 수 있음)
            data = cache.get(cache_key)
            if data:
                print(f"락 내에서 캐시 발견: {cache_key}")
                return data
            
            # DB 조회 (한 스레드만 실행)
            print(f"락 획득 후 DB 조회: {cache_key}")
            data = fetch_func()
            cache.set(cache_key, data, ttl)
            
            return data


##########################


"""캐시 스탬피드 방지 실습"""
def practice_cache_stampede_prevention():

    # 복잡한 통계 계산 시뮬레이션
    def calculate_statistics():
        """시간이 오래 걸리는 통계 계산"""
        time.sleep(1)  # 계산 시뮬레이션
        
        stats = Order.objects.aggregate(
            total_orders = Count('id'),
            total_revenue = Sum('total_amount'),
            avg_order = Avg('total_amount')
        )
        
        return {
            'total_orders': stats['total_orders'] or 0,
            'total_revenue': float(stats['total_revenue'] or 0),
            'avg_order': float(stats['avg_order'] or 0),
            'calculated_at': time.time()
        }
    
    # 캐시 클리어
    cache.delete('statistics')
    
    print("\n[시뮬레이션] 5개의 동시 요청")
    print("→ 락이 없으면 5번 모두 DB 조회")
    print("→ 락이 있으면 1번만 DB 조회, 나머지는 대기 후 캐시 사용")
    
    

    import concurrent.futures
    
    def request_stats(request_id):
        """통계 요청 시뮬레이션"""
        print(f"[요청 {request_id}] 시작")
        
        start = time.time()
        
        stats = CacheWithLock.get_or_set(
            'statistics',
            calculate_statistics,
            ttl=60
        )
        
        elapsed = time.time() - start
        
        print(f"[요청 {request_id}] 완료 ({elapsed:.2f}초)")
        print(stats)
        
        return stats
    
    
    
    # 5개 동시 요청
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(request_stats, i+1) 
            for i in range(5)
        ]
        results = [f.result() for f in futures]
    
        # [시뮬레이션] 5개의 동시 요청
        # → 락이 없으면 5번 모두 DB 조회
        # → 락이 있으면 1번만 DB 조회, 나머지는 대기 후 캐시 사용
        
        # [요청 1] 시작
        # [요청 2] 시작
        # [요청 3] 시작
        # [요청 4] 시작
        # [요청 5] 시작
        
        # 락 획득 후 DB 조회: statistics
        # [요청 1] 완료 (1.05초)
        # {'total_orders': 10000, 'total_revenue': 2751635.0, 'avg_order': 275.1635, 'calculated_at': 1771404546.710975}
        
        # 락 내에서 캐시 발견: statistics
        # [요청 4] 완료 (1.05초)
        # {'total_orders': 10000, 'total_revenue': 2751635.0, 'avg_order': 275.1635, 'calculated_at': 1771404546.710975}
        
        # 락 내에서 캐시 발견: statistics
        # [요청 2] 완료 (1.05초)
        # {'total_orders': 10000, 'total_revenue': 2751635.0, 'avg_order': 275.1635, 'calculated_at': 1771404546.710975}
        
        # 락 내에서 캐시 발견: statistics
        # [요청 3] 완료 (1.05초)
        # {'total_orders': 10000, 'total_revenue': 2751635.0, 'avg_order': 275.1635, 'calculated_at': 1771404546.710975}
       
        # 락 내에서 캐시 발견: statistics
        # [요청 5] 완료 (1.05초)
        # {'total_orders': 10000, 'total_revenue': 2751635.0, 'avg_order': 275.1635, 'calculated_at': 1771404546.710975}

    
    print("\n✅ 캐시 스탬피드 방지 실습 완료!")
    print("💡 배운 점: 락을 사용하면 ㄷ시 요청 시 1번만 DB 조회")








# ============================================================================
# 실습 5: 확률적 조기 갱신
# ============================================================================

class ProbabilisticCache:
    """확률적 조기 갱신"""
    
    @staticmethod
    def get_or_refresh(cache_key, fetch_func, ttl=60, early_refresh_ratio=0.2):
        from django_redis import get_redis_connection
        """
        확률적 조기 갱신
        
        ttl의 80% 지나면 일부 요청이 미리 갱신
        """
        # 캐시와 남은 시간 확인
        data = cache.get(cache_key, version=1)
        
        if data is not None:
            # Redis에서 TTL 확인 (django-redis 사용 시)
            try:
                redis_conn = get_redis_connection("default") # Redis에 직접 연결하기 위함.
                remaining = redis_conn.ttl(cache.make_key(cache_key, version=1)) # TTL을 조회함. # 실제 Redis에 저장하기 위한 키를 만듦.
                
                if remaining > 0:
                    # 남은 시간이 적으면 확률적으로 갱신
                    if remaining < ttl * early_refresh_ratio:
                        refresh_probability = 0.1 # 10% 확률
                        
                        if random.random() < refresh_probability:
                            print(f"🎲 확률적 조기 갱신: {cache_key} (남은시간: {remaining}초)")
                            # 확률적 조기 갱신: hot_products (남은시간: 1초)
                            
                            data = fetch_func()
                            cache.set(cache_key, data, ttl, version=1)
                    
                    return data
            except:
                # Redis 아닌 경우 또는 오류 시 그냥 반환
                return data
        
        # 캐시 미스
        print(f"❌ 캐시 미스: {cache_key}")
        data = fetch_func()
        cache.set(cache_key, data, ttl, version=1)
        return data






def practice_probabilistic_refresh():
    """확률적 조기 갱신 실습"""

    def get_hot_products():
        """인기 상품 조회"""
        print("  📊 인기 상품 계산 중...")
        
        products = Product.objects.all()[:5]
        
        return [
            {'id': p.id, 'name': p.name, 'price': float(p.price)}
            for p in products
        ]
    
    # TTL을 짧게 설정 (10초)
    ttl = 10
    cache_key = 'hot_products'
    
    # 캐시 클리어
    cache.delete(cache_key, version=1)
    
    print(f"\n[테스트] TTL={ttl}초, 조기 갱신 기준={ttl * 0.2}초") 
    # [테스트] TTL=10초, 조기 갱신 기준=2.0초
    print("→ 남은 시간이 2초 이하면 10% 확률로 미리 갱신\n")
    
    
    # 첫 조회
    print("[1] 첫 조회")
    products = ProbabilisticCache.get_or_refresh(cache_key, get_hot_products, ttl)
    print(products)
    
    # 여러 번 조회 시뮬레이션
    for i in range(2, 15):
        time.sleep(1)
        print(f"\n[{i}] {i}초 후 조회")
        products = ProbabilisticCache.get_or_refresh(cache_key, get_hot_products, ttl)
        print(products)
        
        if i >= ttl:
            print(" → TTL 만료!")
            break
    
    
    print("\n✅ 확률적 조기 갱신 실습 완료!")
    print("💡 배운 점: 캐시 만료 직전에 일부 요청이 미리 갱신하여")
    print("   스탬피드 방지")





# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    # 각 실습을 순서대로 실행
    try:
       # 1. TTL 기반 캐싱
        practice_ttl_caching()
        
      
        # 2. 이벤트 기반 무효화
        practice_event_based_invalidation()
       
       
        # 3. 태그 기반 무효화
        practice_tag_based_invalidation()
        

        # 4. 캐시 스탬피드 방지
        practice_cache_stampede_prevention()
        
        
        # 5. 확률적 조기 갱신
        practice_probabilistic_refresh()
        
        
        """
        📚 학습 정리:
            1. TTL 캐싱: 데이터 특성에 맞는 만료 시간 설정
            2. 이벤트 기반: 데이터 변경 시 자동 캐시 무효화
            3. 태그 기반: 관련 캐시를 그룹으로 관리
            4. 스탬피드 방지: 락으로 동시 요청 제어
            5. 조기 갱신: 만료 직전 확률적 갱신
            
            💡 핵심:
            - 캐시는 DB 부하를 줄이는 도구
            - 적절한 TTL과 무효화 전략이 중요
            - 항상 측정하고 효과 검증
        """
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
       