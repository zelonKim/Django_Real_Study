"""
더미 데이터
from book.models import Author, Publisher, Book


lee = Author.objects.create(name = "Lee", email = "lee@test.com")
lee_pub = Publisher.objects.create(name = "LeePub", country = "KR")

park = Author.objects.create(name = "Park", email = "park@test.com")
park_pub = Publisher.objects.create(name = "ParkPub", country = "KR")



for i in range(5):
    Book.objects.create(
        title = f"HTML Book {i}",
        author = lee,
        publisher = lee_pub,
        price = 10000,
        published_date = "2025-01-01"
    )
    
for i in range(3):
    Book.objects.create(
        title = f"CSS Book {i}",
        author = park,
        publisher = park_pub,
        price = 5000,
        published_date = "2026-01-01"
    )
"""





"""
N+1 문제의 발생 원리와 해결 방법
"""
from django.db import connection, reset_queries
from django.db.models import Prefetch


def n_plus_1_problem_demo():
    """ N+1 문제 발생 예시 """
    from book.models import Book
    
    reset_queries()
    
    print("\n[문제 상황] 책 목록과 각 책의 작가 조회")
    
    # 책 목록 조회 (1개 쿼리)
    books = Book.objects.all()[:10]
    
    # 각 책의 작가를 조회 (N개 쿼리)
    for i, book in enumerate(books, 1):
        author_name = book.author.name  # 추가 쿼리 발생!
        print(f"{i}. {book.title} - {author_name}")
    
    print(f"\n 총 실행된 쿼리 수: {len(connection.queries)}") # 11
    print("=> 1(books 조회) + N(각 author 조회) = N+1 쿼리")
    


################################



def n_plus_1_with_reverse_relation():
    """ 역참조에서의 N+1 문제 """
    from book.models import Book
    from book.models import Author
    
    reset_queries()
    
    print("\n[문제 상황] 작가 목록과 각 작가의 책 개수 조회")
    
    authors = Author.objects.all()[:5]
    
    for author in authors:
        book_count = author.books.count()   # 역참조 -> 매번 쿼리 발생
        print(f"{author.name}: {book_count}권") # Kim: 10권   # Lee: 5권   # Park: 3권
    
    print(f"\n총 쿼리 수: {len(connection.queries)}") # 4
    print("=> 1(authors 조회) + 3(각 author의 books.count()) = 4 쿼리")



################################



def n_plus_1_nested():
    """중첩된 N+1 문제 - 더 심각한 경우"""
    from book.models import Book
    
    reset_queries()
    
    print("\n[최악의 상황] 책 → 작가 → 리뷰까지 접근")
    
    books = Book.objects.all()[:5]
    
    for book in books:
        print(f"\n 책: {book.title}") # 각 책의 제목 조회
        
        print(f"  작가: {book.author.name}") # 각 책의 작가들 조회
        
        reviews = book.reviews.all()[:5]  
        for review in reviews:
            print(f"  리뷰: {review.comment[:50]}...")  # 각 책의 리뷰들 조회
    
    print(f"\n\n총 쿼리 수: {len(connection.queries)}") # 11
    print("=> title을 1번 조회 + author를 5번 조회 + review를 5번 조회 = 최소 11개 쿼리")



#################################


"""N+1 문제 원인 및 해결방안"""
def why_n_plus_1_happens():

    print("""
        1. 각 객체의 연관 데이터는 지연 로딩됨.(Lazy Loading)
        for book in books:
            book.author.name  # ← 이 시점에 추가 쿼리 실행!
        
        
        2. ORM은 필요한 순간에만 데이터를 가져옴.
        - 모든 연관 데이터를 미리 가져오면 불필요한 데이터도 포함
        - 메모리 효율을 위해 필요할 때만 조회
        
        
        3. 해결방안: 미리 필요한 연관 데이터를 알려주기
        - select_related(): JOIN으로 한 번에 가져오기
        - prefetch_related(): 별도 쿼리로 미리 가져오기
    """)




################################





"""N+1 문제 감지 방법"""
def detecting_n_plus_1():
    from book.models import Book
    
    print("\n방법 1: django.db.connection.queries 확인")
    
    reset_queries()
    
    books = Book.objects.all()[:5]
    
    for book in books:
        _ = book.author.name
    
    print(f"실행된 쿼리 수: {len(connection.queries)}") # 6
    
    if len(connection.queries) > 2:
        print("⚠️  N+1 문제 의심!")
    
    #################
    
    print("\n방법 2: Django Debug Toolbar 사용")
    print("""
        # settings.py
            INSTALLED_APPS += ['debug_toolbar']
            MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        
        # 브라우저에서 SQL 패널 확인
        # Similar queries가 많으면 N+1 문제!
    """)
    
    ################# 
    
    print("\n방법 3: django-silk 사용")
    print("""
        # 프로파일링 도구로 쿼리 분석
        pip install django-silk
        
        # URL 패턴별 쿼리 통계 확인
    """)
    
    #################
    
    print("\n방법 4: nplusone 패키지 사용")
    print("""
    pip install nplusone
    
    # settings.py
    MIDDLEWARE += ['nplusone.ext.django.NPlusOneMiddleware']
    
    # N+1 발생 시 자동으로 경고!
    """)





################################


def n_plus_1_real_world_impact():
    """실제 성능 영향 측정"""
    from book.models import Book
    import time

    # N+1 문제가 있는 경우 -> 최적화 X
    print("\n [N+1 문제 O] 최적화 없음")
    reset_queries()
    
    start = time.time()
    
    books = Book.objects.all()[:20]
    results = []
    
    for book in books:
        results.append({
            'title': book.title,
            'author': book.author.name,
            'publisher': book.publisher.name
        })
    
    time_with_n_plus_1 = time.time() - start
    queries_with_n_plus_1 = len(connection.queries)
    
    print(f"실행 시간: {time_with_n_plus_1:.4f}초") # 0.0085초
    print(f"쿼리 수: {queries_with_n_plus_1}개") # 37개
    
    
    #####################
    
    
    # N+1 문제가 없는 경우 -> 최적화 O
    print("\n select_related 사용")
    reset_queries()
    start = time.time()
    
    books = Book.objects.select_related('author', 'publisher').all()[:20]
    results = []
    
    for book in books:
        results.append({
            'title': book.title,
            'author': book.author.name,
            'publisher': book.publisher.name
        })
    
    time_optimized = time.time() - start
    queries_optimized = len(connection.queries)
    
    print(f"실행 시간: {time_optimized:.4f}초")  # 실행 시간: 0.0009초
    print(f"쿼리 수: {queries_optimized}개") # 1개
    
    # 비교
    print("\n[성능 개선 효과]")
    print(f"쿼리 수 감소: {queries_with_n_plus_1} → {queries_optimized}") # 37 → 1
    print(f"개선율: {(1 - queries_optimized/queries_with_n_plus_1) * 100:.1f}%") # 97.3%
    
    if time_with_n_plus_1 > 0:
        speedup = time_with_n_plus_1 / time_optimized
        print(f"속도 향상: {speedup:.2f}배") # 9.54배





################################



if __name__ == "__main__":
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    n_plus_1_problem_demo()
    n_plus_1_with_reverse_relation()
    n_plus_1_nested()
    why_n_plus_1_happens()
    detecting_n_plus_1()
    n_plus_1_real_world_impact()