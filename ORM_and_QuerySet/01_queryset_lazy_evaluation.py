"""
from book.models import Author, Publisher, Book

"더미 데이터"
a = Author.objects.create(name = "Kim", email = "kim@test.com")
p = Publisher.objects.create(name = "TestPub", country = "KR")

for i in range(10):
    Book.objects.create(
        title = f"Python Book {i}",
        author = a,
        publisher = p,
        price = 15000,
        published_date = "2024-01-01"
    )
"""




from django.db import connection

# 1. QuerySet의 본질
def queryset_essence():
    """ QuerySet은 실제 데이터가 아닌, SQL문을 담고 있는 객체임."""
    from book.models import Book
    
    # QuerySet 생성 -> 이 시점에는 DB 접근이 발생하지 않음.
    queryset = Book.objects.filter(price__gte=10000)
    print(f"QuerySet 객체의 타입: {type(queryset)}") # <class 'django.db.models.query.QuerySet'>
    print(f"QuerySet이 담고 있는 SQL문: {queryset.query}") # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date" FROM "books" WHERE "books"."price" >= 10000
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 0
   
    # order_by 정렬 -> 여전히 DB 접근 발생 X
    queryset = queryset.order_by('-published_date')
    print(f"QuerySet이 담고 있는 SQL문: {queryset.query}") # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date" FROM "books" WHERE "books"."price" >= 10000 ORDER BY "books"."published_date" DESC
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 0
    
    



####################################




# Lazy Evaluation (지연 실행)
def lazy_evaluation_demo():
    """실제 데이터가 필요한 순간에만 쿼리가 실행되어 DB에 접근함."""
    from book.models import Book
    from django.db.models import Sum
    
    # 1. 반복문 시작 -> DB 접근 발생 O
    books = Book.objects.filter(price__gte=10000)
    for book in books[:3]: 
        print(f"{book.title}")  # Python Book 0   Python Book 1   Python Book 2
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 1
    
    
    # 2. len() 호출 -> DB 접근 발생 O
    books2 = Book.objects.filter(price__lte=20000)
    book_count = len(books2)
    print(book_count) # 10
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 2
    
    
    # 3. bool() 호출 -> DB 접근 발생 O
    books3 = Book.objects.filter(price__gte=100000)
    exists = bool(books3)  
    print(exists) # False
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 3
    
    
    # 4. 리스트 변환 -> DB 접근 발생 O
    books4 = Book.objects.all()
    book_list = list(books4)
    print(book_list) # [<Book: Python Book 0>, <Book: Python Book 1>, <Book: Python Book 2>, <Book: Python Book 3>, <Book: Python Book 4>, <Book: Python Book 5>, <Book: Python Book 6>, <Book: Python Book 7>, <Book: Python Book 8>, <Book: Python Book 9>]
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 4
    
    
    # 5. 튜플 변환 -> DB 접근 발생 O
    books5 = Book.objects.all()
    book_tuple = tuple(books5)
    print(book_tuple) # (<Book: Python Book 0>, <Book: Python Book 1>, <Book: Python Book 2>, <Book: Python Book 3>, <Book: Python Book 4>, <Book: Python Book 5>, <Book: Python Book 6>, <Book: Python Book 7>, <Book: Python Book 8>, <Book: Python Book 9>)
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 5
    
    
    # 6. 인덱싱 -> DB 접근 발생 O
    books6 = Book.objects.order_by('title')
    first_book = books6[0]  
    print(first_book.title) # Python Book 0
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 6
    
    
    # 7. 슬라이싱 -> DB 접근 발생 O
    books7 = Book.objects.order_by('title')
    middle_books = books7[3:6]  
    print(middle_books)  # <QuerySet [<Book: Python Book 3>, <Book: Python Book 4>, <Book: Python Book 5>]>
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 7
    
    
    # 8. 값 추출 -> DB 접근 발생 O
    books8 = Book.objects.all()
    book_values = books8.values()  
    print(book_values[0]) # {'id': 1, 'title': 'Python Book 0', 'author_id': 1, 'publisher_id': 1, 'price': Decimal('15000.00'), 'published_date': datetime.date(2024, 1, 1)}
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 8
    
    
    # 9. 집계 함수 -> DB 접근 발생 O
    books9 = Book.objects.all()
    sum_book =  books9.aggregate(sum_price=Sum('price'))
    print(sum_book) # {'sum_price': Decimal('150000')}
    print(f"현재까지 실행된 쿼리 수: {len(connection.queries)}") # 9
    




#################################




if __name__ == "__main__":
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  
    django.setup()

    queryset_essence()
    lazy_evaluation_demo()
