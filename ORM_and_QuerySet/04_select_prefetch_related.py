"""
더미 데이터
from book.models import Book, Review
import random

books = Book.objects.all()
books.count()

for book in books:
    for i in range(random.randint(2, 5)):  # 책당 2~5개 리뷰
        Review.objects.create(
            book=book,
            reviewer_name=f"Reviewer_{i}",
            rating=random.randint(1, 5),
            comment=f"{book.title}에 대한 리뷰 {i}"
        )
"""


"""
select_related / prefetch_related 차이와 사용법
"""
from django.db import connection, reset_queries
from django.db.models import Prefetch, Count



def select_related_basics():
    """select_related - JOIN 기반 최적화"""
    from book.models import Book
 
    reset_queries()
    
    print("\n[사용 전]")
    books = Book.objects.all()
    
    for book in books:
        print(f"{book.title} - {book.author.name}")
    
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}")  # 19
    
    
    
    
    print("\n[사용 후]")
    
    reset_queries()
    
    # OneToOneField 혹은 Forward FK(정참조)에 사용함.
    books = Book.objects.select_related('author').all()
    
    for book in books:
        print(f"{book.title} - {book.author.name}")
    
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}")  # 1 
    
    
    # SQL JOIN을 사용하여 한 번의 쿼리로 연관 데이터를 가져옴.
    print("\n생성된 SQL:")
    print(connection.queries[0]['sql'])
    # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date", "authors"."id", "authors"."name", "authors"."email", "authors"."created_at" 
    # FROM "books" 
    # INNER JOIN "authors" ON ("books"."author_id" = "authors"."id") 



############################


"""여러 관계를 동시에 로드"""
def select_related_multiple():

    from book.models import Book
    
    reset_queries()
    
    # author와 publisher를 동시에 로드
    books = Book.objects.select_related('author', 'publisher').all()
    
    for book in books:
        print(f"{book.title}")
        print(f"  작가: {book.author.name}")
        print(f"  출판사: {book.publisher.name}")
    
    print(f"\n 현재까지 실행된 쿼리 수: {len(connection.queries)}")  # 1
    
    
    # 다중 조인
    print("\n생성된 SQL:")
    sql = connection.queries[0]['sql'] 
    print(sql[:500] + "..." if len(sql) > 500 else sql)
    # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date", "authors"."id", "authors"."name", "authors"."email", "authors"."created_at", "publishers"."id", "publishers"."name", "publishers"."country" 
    # FROM "books" 
    # INNER JOIN "authors" ON ("books"."author_id" = "authors"."id") 
    # INNER JOIN "publishers" ON ("books"."publisher_id" = "publishers"."id")



############################




"""체이닝 관계 로드"""
def select_related_chaining():
    from book.models import Review
    
    reset_queries()
    
    # 리뷰를 조회하면서 책과 작가까지 한 번에 로드함.
    reviews = Review.objects.select_related(
        'book',           # Review → Book
        'book__author',   # Book → Author (이중 언더스코어 사용)
        'book__publisher' # Book → Publisher
    ).all()[:5]
    
    for review in reviews:
        print(f"리뷰: {review.rating}점")
        print(f"  책: {review.book.title}")
        print(f"  작가: {review.book.author.name}")
        print(f"  출판사: {review.book.publisher.name}")
        print()
    
    print(f"쿼리 수: {len(connection.queries)}")  # 1





############################





"""prefetch_related - 별도 쿼리 방식"""
def prefetch_related_basics():
  
    from book.models import Author
    
    reset_queries()
    
    print("\n[사용 전]")
    authors = Author.objects.all()
    
    for author in authors:
        books = author.books.all() 
        print(f"{author.name}: {books.count()}권")
    
    print(f"현재까지의 쿼리 수: {len(connection.queries)}") # 4
    
    
    
    print("\n[사용 후]")
    reset_queries()
    
    # ManyToManyField 혹은 reverse FK(역참조)에 사용함.
    authors = Author.objects.prefetch_related('books').all()
    
    for author in authors:
        books = author.books.all()
        print(f"{author.name}: {books.count()}권")
   
    print(f"현재까지의 쿼리 수: {len(connection.queries)}") # 2



############################










def how_prefetch_works():
    """prefetch_related의 동작 원리"""
     # 별도의 쿼리로 데이터를 가져온 후, Python에서 조합함.
    from book.models import Author
    
    reset_queries()
    
    authors = Author.objects.prefetch_related('books').all()
    
    # 첫 번째 쿼리가 실행됨. -> authors 조회
    author_list = list(authors)
    print(f"1단계 - authors 조회 후 쿼리 수: {len(connection.queries)}") # 2
    print(f"   SQL: {connection.queries[0]['sql']}") 
    # SELECT "authors"."id", "authors"."name", "authors"."email", "authors"."created_at" 
    # FROM "authors"
    
    
    # 두 번째 쿼리가 자동으로 실행됨. -> 모든 books 조회
    print(f"\n2단계 - prefetch 후 쿼리 수: {len(connection.queries)}") # 2
    print(f"   SQL: {connection.queries[1]['sql']}") 
    # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date" 
    # FROM "books" 
    # WHERE "books"."author_id" IN (1, 2, 3)
    
    print("\n => JOIN 대신 IN 절 사용 + Python에서 조합")
 
   
   

############################




def select_vs_prefetch():
    """select_related vs prefetch_related 비교"""
    
comparison = """
┌─────────────────────┬────────────────────┬──────────────────────┐
│      구분            │  select_related    │  prefetch_related    │
├─────────────────────┼────────────────────┼──────────────────────┤
│ 사용 대상             │ OneToOne           │ ManyToMany           │
│                     │ 정참조 (Forward FK)  │ 역참조 (Reverse FK)   │
├─────────────────────┼────────────────────┼──────────────────────┤
│ 쿼리 방식             │ SQL JOIN           │ 별도 쿼리 + Python     │
├─────────────────────┼────────────────────┼──────────────────────┤
│ 쿼리 수               │ 1개 (JOIN 사용)     │ 2개 이상              │
├─────────────────────┼────────────────────┼──────────────────────┤
│ 참조 방향             │ 정방향 (→)           │ 역방향 (←)             │
├─────────────────────┼────────────────────┼──────────────────────┤
│ 예시                 │ book.author        │ author.books         │
│                     │ book.publisher     │ book.reviews         │
├─────────────────────┼────────────────────┼──────────────────────┤
│ 장점                 │ 쿼리 1개로 해결        │ 유연한 필터링 가능       │
│                     │ DB 부하 최소화        │ 대용량 데이터 처리        │
├─────────────────────┼────────────────────┼──────────────────────┤
│ 단점                 │ JOIN 테이블 증가 시,   │ 메모리 사용량 증가,      │ 
│                     │ 성능 저하 가능         │ Python 처리 필요       │
└─────────────────────┴────────────────────┴──────────────────────┘

* 둘 다 사용 가능한 경우 → select_related 우선 (쿼리 수가 더 적음)
"""

print(comparison)


############################


def combining_both():
    """refetch_related와 select_related를 함께 사용"""
    from book.models import Author, Book
    
    reset_queries()
    
    authors = Author.objects.prefetch_related( # 역참조
        Prefetch(
            'books',
            queryset = Book.objects.select_related('publisher') # 정참조
        )
    ).all()
    
    for author in authors:
        print(f"\n작가: {author.name}")
        for book in author.books.all():
            print(f"  - {book.title} ({book.publisher.name})")
    
    # 작가: Kim
    # - Python Book 0 (TestPub)
    # - Python Book 1 (TestPub)
    # - Python Book 2 (TestPub)
    # - Python Book 3 (TestPub)
    # - Python Book 4 (TestPub)
    # - Python Book 5 (TestPub)
    # - Python Book 6 (TestPub)
    # - Python Book 7 (TestPub)
    # - Python Book 8 (TestPub)
    # - Python Book 9 (TestPub)

    # 작가: Lee
    # - HTML Book 0 (LeePub)
    # - HTML Book 1 (LeePub)
    # - HTML Book 2 (LeePub)
    # - HTML Book 3 (LeePub)
    # - HTML Book 4 (LeePub)

    # 작가: Park
    # - CSS Book 0 (ParkPub)
    # - CSS Book 1 (ParkPub)
    # - CSS Book 2 (ParkPub)
    
    print(f"\n\n총 쿼리 수: {len(connection.queries)}") # 2
    print("=> 1(authors) + 1(books with publisher JOIN) = 2 쿼리")


############################


def conditional_prefetch():
    """prefetch_related 조건 사용법"""
    from book.models import Book, Author
    
    reset_queries()
    
    # 특정 조건을 만족하는 책만 prefetch
    authors = Author.objects.prefetch_related(
        Prefetch(
            'books',
            queryset = Book.objects.filter(price__gte=15000).order_by('-published_date'),
            to_attr='expensive_books' # 커스텀 속성명
        )
    ).all()
    
    for author in authors:
        print(f"\n작가: {author.name}")
        for book in author.expensive_books: # 커스텀 속성명을 사용함.
            print(f"  - {book.title} ({book.price}원)")
            
            # 작가: Kim
            # - Python Book 0 (15000.00원)
            # - Python Book 1 (15000.00원)
            # - Python Book 2 (15000.00원)
            # - Python Book 3 (15000.00원)
            # - Python Book 4 (15000.00원)
            # - Python Book 5 (15000.00원)
            # - Python Book 6 (15000.00원)
            # - Python Book 7 (15000.00원)
            # - Python Book 8 (15000.00원)
            # - Python Book 9 (15000.00원)

            # 작가: Lee

            # 작가: Park
    
    print(f"\n총 쿼리 수: {len(connection.queries)}") # 2
    
    


############################




if __name__ == "__main__":
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    select_related_basics()
    select_related_multiple()
    select_related_chaining()
    prefetch_related_basics()
    how_prefetch_works()
    select_vs_prefetch()
    combining_both()
    conditional_prefetch()