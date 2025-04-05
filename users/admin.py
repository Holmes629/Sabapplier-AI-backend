from django.contrib import admin

from .models import user, Token

class usersAdmin(admin.ModelAdmin):
    list_display=('username','email','phone_number','address','city','state','country','pincode')
    search_fields=('username','email','phone_number','address','city','state','country','pincode')
    list_filter=('username','email','phone_number','address','city','state','country','pincode')
    list_per_page=10

admin.site.register(user,usersAdmin)
admin.site.register(Token)


