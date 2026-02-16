from django.db import connection, reset_queries
from django.db.models import Q, F, Count, Avg, Max, Min, Sum


"""복잡한 쿼리 분석"""
def complex_query_analysis():
    from book.models import Book
    
    print("Q 객체 사용  ->  필터링 조건 추가")
    queryset = Book.objects.filter(
        Q(price__gte=10000) & (Q(title__icontains='Python') | Q(title__icontains='Django'))
    )
    print(queryset.query)
    # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date" 
    # FROM "books" 
    # WHERE ("books"."price" >= 10000 AND ("books"."title" LIKE %Python% ESCAPE '\' OR "books"."title" LIKE %Django% ESCAPE '\'))
    
    
    #########################
    
    
    print("objects.values() 사용  ->  GROUP BY 집계")
    # 작가별로 책 통계(책 개수, 평균 가격, 최고 가격)를 집계하기
    
    queryset = Book.objects.values('author__name').annotate(
                book_count = Count('id'),
                avg_price = Avg('price'),
                max_price = Max('price')
            ).order_by('-book_count')
    
    print(queryset.query)
    # SELECT "authors"."name" AS "author__name", 
    #       COUNT("books"."id") AS "book_count", 
    #       (CAST(AVG("books"."price") AS NUMERIC)) AS "avg_price", 
    #       (CAST(MAX("books"."price") AS NUMERIC)) AS "max_price" 
    # FROM "books" 
    # INNER JOIN "authors" ON ("books"."author_id" = "authors"."id") 
    # GROUP BY 1 
    # ORDER BY 2 DESC




###########################




"""서브쿼리 분석"""
def subquery_analysis():
    from book.models import Book, Author
    from django.db.models import Subquery, OuterRef
    

    print("OuterRef()사용 -> 바깥 쿼리의 해당 컬럼값을 참조")
     # 각 작가의 가장 비싼 책 가격을 가져오기
     
    max_price_subquery = Book.objects.filter(
        author = OuterRef('pk') 
    ).order_by('-price').values('price')[:1]
    
    queryset = Author.objects.annotate(
        max_book_price = Subquery(max_price_subquery)
    )
    
    print(queryset.query)
    # SELECT "authors"."id", "authors"."name", "authors"."email", "authors"."created_at", 
    #   (SELECT U0."price" AS "price"  
    #     FROM "books" U0   
    #     WHERE U0."author_id" = ("authors"."id")  
    #     ORDER BY 1 DESC  
    #     LIMIT 1
    #   )AS "max_book_price" 
    # FROM "authors"




##############################



"""JOIN 쿼리 상세 분석"""
def join_analysis():
    from book.models import Book
    
    print(".select_related()사용 -> INNER JOIN ")
    # 내부 조인을 통해 books와 authors 테이블 결합하기 (NULL인 경우 결과에서 제외)
    queryset = Book.objects.select_related('author')
    
    sql = str(queryset.query)
    print(sql)
    # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date", "authors"."id", "authors"."name", "authors"."email", "authors"."created_at" 
    # FROM "books" 
    # INNER JOIN "authors" 
    # ON ("books"."author_id" = "authors"."id")


    ##################

    
    print("Multiple JOIN")
    # 2개의 INNER JOIN으로 테이블 3개 결합하기
    queryset = Book.objects.select_related('author', 'publisher')
    
    sql = str(queryset.query)
    print(sql)
    # SELECT "books"."id", "books"."title", "books"."author_id", "books"."publisher_id", "books"."price", "books"."published_date", "authors"."id", "authors"."name", "authors"."email", "authors"."created_at", "publishers"."id", "publishers"."name", "publishers"."country" 
    # FROM "books" 
    # INNER JOIN "authors" ON ("books"."author_id" = "authors"."id") 
    # INNER JOIN "publishers" ON ("books"."publisher_id" = "publishers"."id")




##############################




if __name__ == "__main__":
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    complex_query_analysis()
    subquery_analysis()
    join_analysis()
