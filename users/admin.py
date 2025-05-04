from django.contrib import admin

from .models import user, Token

class usersAdmin(admin.ModelAdmin):
    list_display=('fullname','email','phone_number','address','city','state','country','pincode')
    search_fields=('fullname','email','phone_number','address','city','state','country','pincode')
    list_filter=('fullname','email','phone_number','address','city','state','country','pincode')
    list_per_page=10

admin.site.register(user,usersAdmin)
admin.site.register(Token)


