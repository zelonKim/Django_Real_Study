import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


##############################


"""
Django Async(비동기)의 실제 동작과 한계
"""
import asyncio
import time
from django.http import JsonResponse
import aiohttp
from asgiref.sync import sync_to_async
from market.models import Product, Order


def understanding_async_in_django():
    
    print("""
[Django Async의 진실]


많은 개발자들의 오해:
❌ "Async를 사용하면 Django가 빨라진다"
❌ "Async = 자동으로 성능 개선"
❌ "DB 쿼리도 비동기로 처리된다"


실제 현실:
✅ Async는 I/O 대기 시간을 활용하는 기술
✅ Django ORM은 여전히 동기 방식
✅ DB 쿼리는 여전히 Blocking


################################


✅ [Async가 도움이 되는 경우]
┌──────────────────────────────────────────────────────────┐
│  1. 외부 API 호출 (HTTP 요청)                                │
│  2. 파일 I/O (대용량 파일 읽기/쓰기)                            │
│  3. 메시지 큐 (RabbitMQ, Kafka 등)                          │
│  4. 외부 서비스 통신 (Redis, Elasticsearch 등)                │
└──────────────────────────────────────────────────────────┘
           ↓
    Async를 통해 대기시간 동안 다른 작업이 가능함.



❌ [Async가 도움이 안 되는 경우]
┌──────────────────────────────────────────────────────────┐
│  1. 데이터베이스 쿼리 (Django ORM)                           │
│  2. 이미지 처리 및 암호화 (CPU 집약적 연산)                     │
│  3. 동기 라이브러리 호출                                      │
└──────────────────────────────────────────────────────────┘
           ↓
     Async를 써도 Blocking 발생!! (ORM은 동기 방식으로만 동작하기 때문)




################################



[구조 비교]


* 동기 Sync (WSGI): 요청 → Worker → ORM (Blocking) → 응답
    => Worker는 대기 중에 다른 일을 못 함.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

* 비동기 Async (ASGI) - 외부 API 호출:
    요청 → Event Loop → HTTP 요청 (Non-blocking) → 응답
                ↓
          다른 요청 처리 가능 ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

* 비동기 Async (ASGI) - ORM 사용:
    요청 → Event Loop → ORM (여전히 Blocking) → 응답
                ↓
         다른 요청 처리 못 함 ❌

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

""")




##############################




print("[예제 1] 동기 vs 비동기 - 외부 API 호출 비교")

# 동기 방식 - 외부 API 호출
def sync_external_api_call():
    """
        문제점:
        - 각 API 호출이 순차적으로 실행
        - 응답을 기다리는 동안 Worker 점유
    """
    import requests
    
    
    start = time.time()
    
    # 3개 외부 API 호출 -> 이전 요청이 완료될 때까지 대기함.
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]
    
    results = []
    
    for url in urls:
        try:
            # requests - 동기 라이브러리 
            response = requests.get(url, timeout=5)
            results.append(response.json())
        except:
            results.append({'error': 'timeout'})
            
    print(f"호출 결과:{results}")
    
    elapsed = time.time() - start
    
    print(f"동기 방식: {elapsed:.2f}초") # 6.92초


#############################


# 비동기 방식 - 외부 API 호출
async def async_external_api_call():
    """
    개선점:
    - 3개 API를 동시에 호출
    - 대기 시간 동안 다른 요청 처리가 가능함.
    """
    
    start = time.time()
    
    #  3개 외부 API 호출 -> 비동기로 동시에 요청함. (대기시간 x)
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]
    
    
    async def fetch(session, url):
        try:
            async with session.get(url, timeout=5) as response:
                return await response.json()
        except:
            return {'error': 'timeout'}
    
    
    # aiohttp -> 비동기 라이브러리
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        print(f"호출 결과:{results}")
    
    elapsed = time.time() - start
    
    print(f"비동기 방식: {elapsed:.2f}초") # 1.95초
    
    
   






#################################








print("[예제 2] 동기 vs 비동기 - ORM 사용 비교")

# 동기 방식 - ORM 사용
def sync_with_orm_blocking():

    start = time.time()
    
    print("[sync 뷰] ORM 쿼리 시작...")
    
    def get_products():
        return list(Product.objects.all())
    
    products = get_products()
    #print(products)
    
    elapsed = time.time() - start
    
    print(f"[sync 뷰] ORM 쿼리 완료: {elapsed:.3f}초") # 0.018초
    
    print("⚠️  이 시간 동안 이벤트 루프가 Blocking됨!")
    print("⚠️  다른 요청을 처리할 수 없음!")
    


#################################


# 비동기 방식 - ORM 사용
async def async_with_orm_blocking():
    """
    async def로 정의했지만, ORM은 동기 방식이므로 여전히 Blocking 발생!!
      -> 다른 요청을 동시에 처리할 수 없음.
    """
    start = time.time()
    
    print("[Async 뷰] ORM 쿼리 시작...")
    
    # ❌ 이렇게 하면 에러 발생!
    #   products = Product.objects.all() 
    #       → "SynchronousOnlyOperation" 에러 발생
    
    # ⚠️ 비동기 방식이므로, @sync_to_async로 감싸줘야 함
    @sync_to_async
    def get_products():
        return list(Product.objects.all())
    
    products = await get_products() # ORM 호출 - 여전히 Blocking!
    # print(products)
    
    elapsed = time.time() - start
    
    print(f"[Async 뷰] ORM 쿼리 완료: {elapsed:.3f}초") # 0.017초
    
    print("⚠️  이 시간 동안 이벤트 루프가 Blocking됨!")
    print("⚠️  다른 요청을 처리할 수 없음!")
    




########################################








print("Async 사용 시 주의사항")

def async_pitfalls():

    print("""
    [실수 1] ORM을 그냥 사용
    async def my_view():
        products = Product.objects.all()  # ❌ 에러 발생!
        # -> SynchronousOnlyOperation: You cannot call this from an async context


    ✅ 정상 실행:
        @sync_to_async
        def get_products():
            return list(Product.objects.all())
        
        products = await get_products()




##############################




[실수 2] Async를 모든 곳에 사용

# ❌ ORM 위주 작업에 async 사용 -> 효과 X
async def list_orders(request):
    orders = await sync_to_async(Order.objects.all)()
    return JsonResponse(...)


# ✅ 외부 API가 있을 때만 async 사용 -> 효과 O
async def check_payment(request):
    result = await call_payment_api()  # 외부 결제 API 호출
    return JsonResponse(...)





###############################



[실수 3] @sync_to_async 남용

# ❌ 여러 번 처리
@sync_to_async
def get_product(id):
    return Product.objects.get(id=id)

@sync_to_async
def get_orders(user):
    return Order.objects.filter(user=user)

# 여러 번 사용 → 오히려 느려짐.
product = await get_product(1)
orders = await get_orders(user)



# ✅ 한 번에 처리
@sync_to_async
def get_all_data(user_id):
    product = Product.objects.get(id=1)
    orders = Order.objects.filter(user_id=user_id)
    return product, orders

product, orders = await get_all_data(user.id)



###############################



[실수 4] 동기 라이브러리 사용

# ❌ 동기 라이브러리를 async에서 사용
async def process_image(request):
    from PIL import Image
    img = Image.open('large_file.jpg')  # Image는 동기 라이브러리임!
    img.resize((800, 600)) 



# ✅ -> 별도 스레드나 프로세스로 처리해야함.
from concurrent.futures import ThreadPoolExecutor

async def process_image(request):
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, 
            heavy_image_processing
        )




###############################



[결론]
Async 사용 가이드라인:

✅ 사용해야 하는 경우:
   - 여러 외부 API 동시 호출
   - 외부 서비스와 통신 (Redis, ElasticSearch)
   - 파일 I/O가 많은 작업
   - WebSocket, Server-Sent Events


❌ 사용하지 말아야 하는 경우:
   - DB 쿼리만 있는 작업
   - CPU 집약적 작업
   - 동기 라이브러리 사용
   - 간단한 CRUD


⚠️  핵심:
   - Async는 "I/O 대기 시간"을 활용하는 기술임.
   - Django ORM은 I/O 대기를 해결하지 못함.
     → Async 사용 ≠ Django 성능 개선
""")





################################





print("실전 권장사항")


"""Django Async 실전 가이드"""
def async_best_practices():

    print("""
    [언제 Async를 도입해야 하는가?]

    1. 마이크로서비스 아키텍처
    ✅ 여러 서비스 API를 동시에 호출해야 할 때

    2. 실시간 기능
    ✅ WebSocket, SSE(Server-Sent Events)
    ✅ 실시간 알림, 채팅

    3. 외부 의존성이 많은 경우
    ✅ 결제, 배송, 알림 등 외부 API 통합
    ✅ 서드파티 서비스 연동

    4. 대용량 파일 처리
    ✅ 스트리밍 업로드/다운로드
    ✅ 비동기 파일 I/O


[Sync vs Async 선택 기준]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
작업 유형                    Sync    Async    비고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
일반 CRUD                    ✅      ❌      ORM 사용
복잡한 DB 쿼리                 ✅      ❌      여전히 blocking
외부 API 호출 (단일)           ✅       △       큰 차이 없음
외부 API 호출 (다중)           ❌       ✅      병렬 처리 가능
실시간 통신                    ❌      ✅      WebSocket 등
파일 업로드/다운로드             △       ✅      대용량 시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



[최종 권장사항]

1. 기본은 Sync (WSGI)
   - Django의 표준 방식
   - 대부분의 경우 충분
   - 안정적이고 검증됨


2. Async는 선택적 도입
   - 명확한 이득이 있을 때만
   - 외부 I/O가 많을 때
   - 실시간 기능이 필요할 때


3. 성능 개선의 우선순위
   1️⃣  DB 쿼리 최적화 (가장 효과적)
   2️⃣  캐싱 전략 (Redis)
   3️⃣  인덱스 추가
   4️⃣  Async 도입 (필요시)


⚠️  Async는 도구일 뿐, 만능 해결책이 아님!
    """)
    
    
    
##############################


if __name__ == "__main__": 
    sync_with_orm_blocking()
    asyncio.run(async_with_orm_blocking())
    