from django.urls import path, include
from .views import *
from django.conf.urls import handler404, handler500
import uuid

urlpatterns = [
    path('', index, name="index"),
    path('<uuid:id>/', details, name="details"),
    path('vendeur/details/<uuid:id>/', details_vendeur, name="detail_vendeur"),
    path('promotions/', promotions, name="promotion"),
    path('a-propos/', a_propos, name="a-propos"),
    path('contact/', contact, name="contact"),
    path('vendeur/', index_vendeur, name="vendeur"),
    path('vendeur/login/', login, name="login_vendeur"),
    path('vendeur/register/', register, name="register_vendeur"),
    path('vendeur/recover/', recover, name="recover_vendeur"),
    path('vendeur/profil/',profil, name="profil"),
    path('vendeur/editer/<uuid:id>/', editer_produit, name="editer_produit"),
    path('vendeur/ajouter', ajouter_produit, name="ajouter_produit"),
    path('vendeur/mystore/<uuid:id>/',mystore_index, name="mystore_index"),
    path('vendeur/mystore/<uuid:id>/promotions', mystore_promotion, name="mystore_promotion"),
    path('vendeur/mystore/<uuid:id>/<uuid:id2>/', mystore_details, name="mystore_details"),
    path('import-data/', import_database, name='import_data'),
]

# Configuration des handlers d'erreur

handler404 = error_404
handler500 = error_500
if settings.DEBUG:
    urlpatterns += [
        path('404/', error_404, {'exception': None}, name="error_404"),
        path('500/', error_500, name="error_500"),
    ]
