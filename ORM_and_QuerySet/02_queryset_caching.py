from django.db import connection, reset_queries


def queryset_caching_basic():
    """QuerySet의 기본 캐싱"""
    from book.models import Book
    
    reset_queries() # 쿼리 수 초기화

    print("\n[상황 1] 같은 QuerySet 객체를 두 번 사용")
    books = Book.objects.all()
    
    # DB 접근 발생 O
    book_list = list(books) 
    print(book_list[0]) # Python Book 0
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 1
    
    # 같은 QuerySet 객체로서, 캐시된 결과를 사용함. -> DB 접근 발생 X
    for book in books[:3]: 
        print(book.title) # Python Book 0  Python Book 1  Python Book 2
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}")  # 1
    



############################



def queryset_caching_pitfall():
    """캐싱이 작동하지 않는 경우"""
    from book.models import Book

    reset_queries() # 쿼리 수 초기화
    
    print("\n [상황 2] 매번 새로운 QuerySet객체 생성 ")
    # DB 접근 발생 O
    for book in Book.objects.all()[:3]:
        print(book.title)  #  Python Book 0  Python Book 1  Python Book 2
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 1
    
    
    # 새로운 QuerySet 객체로서, 캐시된 결과를 사용하지 않음. -> DB 접근 발생 O
    for book in Book.objects.all()[:3]:  
        print(book.title)  #  Python Book 0  Python Book 1  Python Book 2
    print(f"현재까지 실행된 쿼리 수:  {len(connection.queries)}")  # 2
    
    print("\n 매번 새로운 QuerySet을 생성하면 캐시를 활용할 수 없음")





############################




"""슬라이싱 - 부분 캐싱"""
def partial_caching():
    from book.models import Book
    
    print("\n 기본적으로 슬라이싱은 캐시를 사용하지 않음.")
    reset_queries() # 쿼리 수 초기화
    
    books = Book.objects.all()
    
    # DB 접근 발생 O
    first_five = books[:5] 
    print(first_five) # <QuerySet [<Book: Python Book 0>, <Book: Python Book 1>, <Book: Python Book 2>, <Book: Python Book 3>, <Book: Python Book 4>]>
    print(f"현재까지 실행된 쿼리 수:  {len(connection.queries)}") # 1
    
    # 슬라이싱은 캐시된 결과를 사용하지 않음. -> DB 접근 발생 O
    next_five = books[5:10]  
    print(next_five) # <QuerySet [<Book: Python Book 5>, <Book: Python Book 6>, <Book: Python Book 7>, <Book: Python Book 8>, <Book: Python Book 9>]>
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 2
    
    
    #######################

    
    print("\n 리스트 변환 이후에는 슬라이싱도 캐시를 사용하게 됨.")
    reset_queries()
    
    books2 = Book.objects.all()
    
    # DB 접근 발생 O
    list(books2) 
    print(f"전체 조회 후 쿼리 수: {len(connection.queries)}") # 1
    
    first_five = books2[:5]  # 캐시된 결과를 사용함.  ->  DB 접근 발생 X
    next_five = books2[5:10]  # 캐시된 결과를 사용함.  ->  DB 접근 발생 X
    print(f"슬라이싱 후 쿼리 수: {len(connection.queries)}")  # 1
    
    




###########################





def caching_with_related_objects():
    """연관 객체 접근 시 캐싱 문제"""
    from book.models import Book
    
    reset_queries()
    
    print("\n [문제 상황] 반복문 내에서 연관 객체 접근")
    books = Book.objects.all()[:5]
    print(f"QuerySet이 담고 있는 SQL문: {books.query}") 
    # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date" 
    # FROM "books" 
    # LIMIT 5
    
    for book in books:
        print(f"{book.title} - 작가: {book.author.name}")
        # 각 book의 author에 접근할 때마다 쿼리가 실행됨. (N+1 문제 발생)
    
    print(f"총 쿼리 수: {len(connection.queries)}") # 6
    print("=> 처음 books 조회 1번 + 각 author 조회 5번 = 6번 쿼리 발생")
    
    
    ####################
    
    
    print("\n[해결 방법] .select_related() 사용")
    reset_queries()
    
    books = Book.objects.select_related('author').all()[:5]
    print(f"QuerySet이 담고 있는 SQL문: {books.query}") 
    # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date", "authors"."id", "authors"."name", "authors"."email", "authors"."created_at" 
    # FROM "books" 
    # INNER JOIN "authors" ON ("books"."author_id" = "authors"."id") 
    # LIMIT 5
    
    for book in books:
        print(f"{book.title} - 작가: {book.author.name}")
        # 각 book의 author에 접근할 경우, 캐시된 결과를 사용함.
    
    print(f"총 쿼리 수: {len(connection.queries)}") # 1
    




###########################





def cache_invalidation():
    """캐시 무효화 - 언제 캐시가 사라지는가"""
    from book.models import Book
    
    reset_queries()
    
    books = Book.objects.all()
    
    # 첫 번째 반복 -> 캐시 생성
    for book in books:
        print(book.title)
    print(f"쿼리 수: {len(connection.queries)}") # 1
    
    # 두 번째 반복 -> 캐시 사용
    for book in books:
        print(book.title)
    print(f"쿼리 수: {len(connection.queries)}") # 1
    
    
    # QuerySet 수정 -> 캐시 무효화
    books = books.filter(price__gte=10000)  
    for book in books:
        print(book.title)
    print(f"쿼리 수: {len(connection.queries)}") # 2
    
    print("\n QuerySet을 수정하면 새로운 객체가 생성되어 캐시가 무효화됨")




################################





"""캐싱 최적화 모범 사례"""
def best_practices():
    from book.models import Book

    # 1. QuerySet을 변수에 저장하고 재사용
    books = Book.objects.filter(price__gte=10000)
    
    for book in books:
        print(book)
    
    count = len(books) 
    
    ##################
    
    # 2. 전체 데이터가 필요하면 list()로 미리 평가
    books = list(Book.objects.all())
    first_ten = books[:10]  # 메모리에서 슬라이싱
    last_ten = books[-10:]  # 메모리에서 슬라이싱
    
    ##################
    
    # 3. 연관 객체 접근 시, select_related() 사용
    books = Book.objects.select_related('author', 'publisher').all()

    


#################################




if __name__ == "__main__":
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    queryset_caching_basic()
    queryset_caching_pitfall()
    partial_caching()
    caching_with_related_objects()
    cache_invalidation()
    best_practices()