from django.contrib import admin

from core.models import User, Product, FavoriteProducts


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_staff', 'role')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'price')


@admin.register(FavoriteProducts)
class FavoriteProductsAdmin(admin.ModelAdmin):
    list_display = ("product", "user")
