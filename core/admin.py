from django.contrib import admin

from .models import Collect, Payment, PaymentLike, PaymentComment

admin.site.register(Collect)
admin.site.register(Payment)
admin.site.register(PaymentLike)
admin.site.register(PaymentComment)
