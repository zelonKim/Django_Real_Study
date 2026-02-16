"""
iterator()와 대용량 데이터 처리
"""
import sys
from django.db import connection, reset_queries


def normal_queryset_memory():
    """일반 QuerySet의 메모리 사용"""
    from book.models import Book
    
    reset_queries()
    
    books = Book.objects.all() # QuerySet을 전부 메모리에 캐싱함.
    
    # 반복 시작 -> 내부 캐시에 모든 결과가 저장됨.
    count = 0
    for book in books:
        count += 1
        print(f"{count}. {book.title}")
    
    print(f"\n처리된 책 수: {count}권") # 48
    print(f"총 쿼리 수: {len(connection.queries)}") # 1
 
 
    # 다시 반복해도 쿼리 실행 안됨. (캐시 사용)
    for book in books:
        print(f"캐시된 책들: {book}")
    
    print(f"총 쿼리 수: {len(connection.queries)}") # 1




#############################



def iterator_basic():
    """iterator()의 기본 사용법"""
    from book.models import Book
    
    reset_queries()
    
    # .iterator() 사용 -> QuerySet을 메모리에 캐싱하지 않음.
    books = Book.objects.all().iterator()
    
    count = 0
    for book in books:
        count += 1
        print(f"{count}. {book.title}")
    
    print(f"총 쿼리 수: {len(connection.queries)}") # 1
 
 
    #######################
    
 
    # 다시 반복하려면 새로운 .iterator() 호출 필요
    books = Book.objects.all().iterator()
    
    for book in books:
        print(f"캐시된 책들: {book}")
    
    print(f"총 쿼리 수: {len(connection.queries)}") # 2
    
    

#############################


def when_to_use_iterator():
    
    print("""
    ✅ iterator() 사용을 권장하는 경우:

    1. 대용량 데이터 한 번만 순회
        - 수만 ~ 수십만 행의 데이터 처리
        - 배치 작업, 데이터 마이그레이션
    for book in Book.objects.all().iterator():
        process(book) 


    2. 메모리 제약이 있는 환경
        - 제한된 메모리에서 실행
        - 큰 객체를 다루는 경우
    for large_file in File.objects.all().iterator():
        export(large_file)


    3. 실시간 스트리밍 처리
    - 로그 분석
    - 실시간 데이터 파이프라인
    for log in Log.objects.filter(date=today).iterator():
        analyze(log)


    4. 데이터 변환/내보내기
    - CSV 내보내기
    - 데이터베이스 마이그레이션
    with open('export.csv', 'w') as f:
        for item in Item.objects.all().iterator():
            f.write(format_csv(item))



❌ iterator() 사용을 피해야 하는 경우:

1. 데이터를 여러 번 순회
   - 캐시가 없으므로 매번 DB 조회
   books = Book.objects.all().iterator()
   list(books)  # 첫 번째 순회
   list(books)  # 오류! 이미 소진됨


2. 소량의 데이터
   - 수백 개 이하의 데이터
   - 캐싱의 이점이 더 큼
   # 10개만 가져오는데 iterator() 불필요
   books = Book.objects.all()[:10].iterator()


3. 연관 객체에 접근
   - select_related / prefetch_related 사용 불가
   - N+1 문제 발생 가능
   for book in Book.objects.iterator():
       print(book.author.name)  # 매번 쿼리!


4. 정렬/필터가 필요한 경우
   - 전체 데이터셋이 필요한 작업
   - len(), count(), 인덱싱 등
""")


#############################



if __name__ == "__main__":
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    normal_queryset_memory()
    iterator_basic()
    when_to_use_iterator()
   