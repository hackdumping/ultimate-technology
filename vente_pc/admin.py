from django.contrib import admin
from .models import Produit, Marque, Staff, Client, Vendeur, Forfait, Pays, Ville


# Register your models here.

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['marque', 'model','est_promo','est_vendue']
    list_filter = ['marque', 'model']
    search_fields = ['model']

admin.site.register(Marque)
admin.site.register(Staff)
admin.site.register(Client)
admin.site.register(Forfait)
admin.site.register(Pays)
admin.site.register(Ville)

@admin.register(Vendeur)
class VendeurAdmin(admin.ModelAdmin):
    list_display = ['id', 'nom',  'jours', 'tel']
    list_filter = ['date_exp', 'nom', 'tel']
    search_fields = ['nom', 'tel', 'jours']
