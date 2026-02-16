"""
Raw SQL 실행 방법 및 활용
"""
from django.db import connection


def raw_sql_with_cursor():
    
    print("[방법1] connection.cursor() 사용")
    
    with connection.cursor() as cursor: # with as로 커서 관리 -> 자동으로 커서 닫힘.
        # 반드시 파라미터를 %s로 바인딩 -> SQL 인젝션 방지
        cursor.execute("SELECT id, title, price FROM books WHERE price > %s", [10000])
        
        rows = cursor.fetchall() # 결과 가져오기
        
        for row in rows:
            print(f"  id: {row[0]}, 제목: {row[1]}, 가격: {row[2]}")
    


########################



def raw_manager():
    from book.models import Book
    
    print("[방법2] objects.raw() 사용")
    
    books = Book.objects.raw("""
        SELECT b.*
        FROM books b
        INNER JOIN authors a ON b.author_id = a.id
        WHERE b.price > %s
        ORDER BY b.published_date DESC
    """, [10000])
    
    for book in books[:5]:
        print(f"  {book.title} - {book.price}원")
        print(f"   작가: {book.author.name}")  # 연관 객체 접근 가능




########################



"""복잡한 집계 쿼리"""
def complex_aggregation():
    
    with connection.cursor() as cursor:
        
        cursor.execute("""
            SELECT 
                a.name as author_name,
                COUNT(b.id) as book_count,
                AVG(b.price) as avg_price,
                MAX(b.price) as max_price,
                MIN(b.price) as min_price,
                SUM(b.price) as total_price
            FROM authors a
            LEFT JOIN books b 
            ON a.id = b.author_id
            GROUP BY a.id, a.name
            HAVING COUNT(b.id) > 0
            ORDER BY book_count DESC, avg_price DESC
            LIMIT 10
        """)
        
        columns = [col[0] for col in cursor.description]
        results = cursor.fetchall()
        
        for row in results:
            print(f"{row[0]:<20} {row[1]:>8} {row[2]:>12,.0f} {row[3]:>12,.0f} {row[4]:>12,.0f}")



########################



"""윈도우 함수 - ROW_NUMBER()"""
def window_functions():

    print("[예시 1] ORDER BY를 통해 순위 매기기")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                title,
                price,
                ROW_NUMBER() OVER (ORDER BY price DESC) as price_rank
            FROM books
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        print("비싼 책 순위:")
        
        for title, price, rank in results:
            print(f"  {rank}위. {title} - {price:,.0f}원")
            #   1위. Book 3 - 20,000원
            #   2위. Book 3 - 20,000원
            #   3위. Book 3 - 20,000원
            #   4위. Book 3 - 20,000원
            #   5위. Python Book 0 - 15,000원
            #   6위. Python Book 1 - 15,000원
            #   7위. Python Book 2 - 15,000원
            #   8위. Python Book 3 - 15,000원
            #   9위. Python Book 4 - 15,000원
            #   10위. Python Book 5 - 15,000원
                
                
                
    #####################
    
    
    print("[예시 2] PARTITION BY를 통해 카테고리별로 순위 매기기")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.name as author_name,
                b.title,
                b.price,
                ROW_NUMBER() OVER (
                    PARTITION BY b.author_id 
                    ORDER BY b.price DESC
                ) as rank_in_author
            FROM books b
            INNER JOIN authors a ON b.author_id = a.id
        """)
        
        results = cursor.fetchall()
        
        print("\n 작가별 가장 비싼 책 순위:")
        current_author = None
        
        for author, title, price, rank in results:
            if rank <= 2:  # 상위 2개만
                if author != current_author:
                    print(f"\n{author}:")
                    current_author = author
                    
                print(f"  {rank}위. {title} - {price:,.0f}원")
                # Kim:
                #   1위. Python Book 0 - 15,000원
                #   2위. Python Book 1 - 15,000원

                # Lee:
                #   1위. Book 3 - 20,000원
                #   2위. Book 3 - 20,000원

                # Park:
                #   1위. CSS Book 0 - 5,000원
                #   2위. CSS Book 1 - 5,000원



########################




"""CTE (Common Table Expression)"""
def cte_query():

    print("CTE (WITH 절) -> 복잡한 서브쿼리를 미리 구조화 해줌.")

    with connection.cursor() as cursor:
        cursor.execute("""
            WITH expensive_books AS (
                SELECT 
                    author_id,
                    COUNT(*) as expensive_count,
                    AVG(price) as avg_expensive_price
                FROM books
                WHERE price >= 20000
                GROUP BY author_id
            ),
            
            all_books AS (
                SELECT 
                    author_id,
                    COUNT(*) as total_count,
                    AVG(price) as avg_total_price
                FROM books
                GROUP BY author_id
            )
            
            SELECT 
                a.name,
                COALESCE(eb.expensive_count, 0) as expensive_books,
                ab.total_count as total_books,
                COALESCE(eb.avg_expensive_price, 0) as avg_expensive_price,
                ab.avg_total_price
                
            FROM authors a
            INNER JOIN all_books ab 
            ON a.id = ab.author_id
            LEFT JOIN expensive_books eb 
            ON a.id = eb.author_id
            
            ORDER BY expensive_books DESC
            
            LIMIT 10
        """)
        
        
        # COALESCE(컬럼명, 0): 해당 컬럼값이 NULL일 경우, 0으로 치환해줌.
        print(f"{'작가':<20} {'고가책':>8} {'전체':>8} {'고가평균':>15} {'전체평균':>15}")
        
        for row in cursor.fetchall():
            print(f"{row[0]:<20} {row[1]:>8} {row[2]:>8} {row[3]:>15,.0f} {row[4]:>15,.0f}")
            # Lee                         5       10          20,000          15,000
            # Kim                         0       20               0          13,750
            # Park                        0        3               0           5,000







########################




"""
더미 데이터
    
root = Book.objects.create(title = "Python Master", author = lee, publisher = lee_pub, price = 30000, published_date = "2025-01-01")
    
v2 = Book.objects.create(title = "Python Master 2nd", author = lee, publisher = lee_pub, price = 20000, published_date = "2025-02-01", parent = root)
    
v3 = Book.objects.create(title = "Python Master 3rd",  author = lee, publisher = lee_pub, price = 10000,  published_date = "2025-03-01", parent = v2)
        
"""



def recursive_cte():
    """재귀 CTE - 계층 구조 처리"""
    
    with connection.cursor() as cursor:
        cursor.execute("""
        WITH RECURSIVE book_tree AS (

            -- 1️⃣ 최상위 루트 책 (parent가 없는 책)
            SELECT
                id,
                title,
                parent_id,
                1 AS level,
                title AS path
            FROM books
            WHERE parent_id IS NULL

            UNION ALL

            -- 2️⃣ 자식 책 (parent가 있는 책)
            SELECT
                b.id,
                b.title,
                b.parent_id,
                bt.level + 1,
                bt.path || ' → ' || b.title
            FROM books b
            
            INNER JOIN book_tree bt
            ON b.parent_id = bt.id
        )

        SELECT *
        FROM book_tree
        ORDER BY path;
        """)
    
        rows = cursor.fetchall()

        print("\n📚 Book Series Tree\n")
        
        for _id, title, parent_id, level, path in rows:
            indent = "  " * (level - 1)
            print(f"{indent} - {title}")
            # - Python Master
            #     - Python Master 2nd
            #         - Python Master 3rd
    
    



########################


def bulk_operations():
    
    print("대량 INSERT")
    with connection.cursor() as cursor:
        # 한 번에 여러 행 삽입
        cursor.execute("""
            INSERT INTO books (title, author_id, publisher_id, price, published_date)
            VALUES 
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s)
            RETURNING id
        """, 
            [
                'Book 1', 1, 1, 10000, '2024-01-01',
                'Book 2', 1, 1, 15000, '2024-01-02',
                'Book 3', 2, 1, 20000, '2024-01-03',
            ]
        )
        inserted_ids = cursor.fetchall() # INSERT후, RETURNING id를 반환함.
        print(f"삽입된 ID들: {inserted_ids}") # [(43,), (44,), (45,)]
    
    
    ###################
    
    
    print("대량 UPDATE")
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE books
            SET price = price * 1.1
            WHERE published_date < %s
        """, ['2025-01-01'])
        
        print(f"업데이트된 행 수: {cursor.rowcount}") # 37
    
    




########################





"""Raw SQL을 사용해야 하는 경우"""
def when_to_use_raw_sql():
    
    print("""
        ✅ Raw SQL이 필요한 경우:

        1. 복잡한 JOIN과 서브쿼리
            - 3개 이상의 테이블 JOIN
            - 복잡한 중첩 서브쿼리

        2. 윈도우 함수 (Window Functions)
            - ROW_NUMBER(), RANK(), LAG(), LEAD()
            - PARTITION BY 절 사용

        3. CTE (Common Table Expression)
            - WITH 절을 사용한 복잡한 쿼리
            - 재귀 CTE

        4. 데이터베이스 특화 기능
            - PostgreSQL의 ARRAY, JSONB 연산
            - MySQL의 FULLTEXT 검색

        5. 성능 최적화
            - 대량 데이터 처리
            - 복잡한 집계 연산
            - 인덱스 힌트 사용

        6. 레거시 쿼리 마이그레이션
            - 기존 SQL 쿼리를 그대로 사용
            - 검증된 쿼리 유지


    ❌ ORM을 사용해야 하는 경우:
        1. 단순 CRUD 작업
        2. 기본적인 필터링, 정렬
        3. 연관 객체 조회
        4. 포터블한 코드가 필요한 경우
        5. 프로젝트 초기 단계


    ⚖️ 균형잡힌 접근:
        - 기본은 ORM, 필요시 Raw SQL
        - 성능 측정 후 최적화
        - 복잡도와 유지보수성 고려

""")





########################




if __name__ == "__main__":
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    raw_sql_with_cursor()
    raw_manager()
    complex_aggregation()
    window_functions()
    cte_query()
    recursive_cte()
    bulk_operations()
    when_to_use_raw_sql()
 