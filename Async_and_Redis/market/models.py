from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    """상품 모델"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return self.name




class Order(models.Model):
    """주문 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '대기중'),
            ('processing', '처리중'),
            ('completed', '완료'),
            ('cancelled', '취소'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"




class OrderItem(models.Model):
    """주문 항목 모델"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='items')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'order_items'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"




class APILog(models.Model):
    """외부 API 호출 로그"""
    endpoint = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time = models.FloatField()  # 초 단위
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_logs'
        indexes = [
            models.Index(fields=['created_at']),
        ]