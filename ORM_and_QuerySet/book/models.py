# Django ORM 학습을 위한 예제 모델
from django.db import models



class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'authors'
    
    def __str__(self):
        return self.name




class Publisher(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'publishers'
    
    def __str__(self):
        return self.name







class Book(models.Model):
    title = models.CharField(max_length=200)
    
    author = models.ForeignKey(
        Author, 
        on_delete = models.CASCADE,
        related_name = 'books'  # 역참조 이름
    )
    
    publisher = models.ForeignKey(
        Publisher,
        on_delete = models.CASCADE,
        related_name = 'books'
    )
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    published_date = models.DateField()
    
    
    # 개정판 시리즈
    parent = models.ForeignKey(
        'self', #  자기(Book) 참조
        null = True,
        blank = True,
        related_name = 'children',
        on_delete = models.CASCADE
    )
    
    class Meta:
        db_table = 'books'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['published_date']),
        ]
    
    def __str__(self):
        return self.title









class Review(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete = models.CASCADE,
        related_name = 'reviews'
    )
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField()  # 1-5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews'
        indexes = [
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.book.title} - {self.rating}점"