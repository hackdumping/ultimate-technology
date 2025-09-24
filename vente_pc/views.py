import datetime
import uuid

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.utils import timezone
from django.core.management import call_command
from .models import Produit, Staff, Client, Vendeur, Forfait, Ville, Pays, Marque
from django.conf import settings
import urllib.parse
import json
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.core.mail import send_mail, send_mass_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import re
import os
# Create your views here.


def generate_whatsapp_link(number, message):
    """Génère un lien HTML pour WhatsApp"""
    clean_number = ''.join(filter(str.isdigit, number))
    encoded_message = urllib.parse.quote(message)
    link = f"https://wa.me/{clean_number}?text={encoded_message}"
    return link


def regrouper_par_vendeur(produits):
    """
    Regroupe une liste de produits par vendeur_id

    Args:
        produits (list): Liste de dictionnaires représentant des produits

    Returns:
        dict: Dictionnaire où les clés sont les vendeur_id et les valeurs
              sont les listes de produits correspondants
    """
    produits_par_vendeur = {}

    for produit in produits:
        vendeur_id = produit.get('vendeur_id')

        # Si le vendeur n'existe pas encore dans le dictionnaire, créer une nouvelle liste
        if vendeur_id not in produits_par_vendeur:
            produits_par_vendeur[vendeur_id] = []

        # Ajouter le produit à la liste du vendeur correspondant
        produits_par_vendeur[vendeur_id].append(produit)

    return produits_par_vendeur


def statut_produit(est_vendue):
    if est_vendue == 'True':
        return "EN RUPTURE"
    else:
        return "EN STOCK"


@csrf_exempt
def index(request):
    context = {}

    context['est_soumis'] = False
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

    produits = Produit.objects.all()

    list_produits = []

    for produit in produits:
        message = f"""
            Salut !
    j'aimerais acheté ce produit : 
    {root}/{str(produit.id)}

    #ultimate-technology
            """
        url = generate_whatsapp_link(produit.vendeur.tel, message)
        tmp = {
            'id': str(produit.id),
            'marque': produit.marque.nom,
            'model': produit.model,
            'cpu': produit.cpu,
            'ram': produit.ram,
            'stockage': produit.stockage,
            'graphic': produit.graphic,
            'description': produit.description,
            'ancien_prix': produit.ancien_prix,
            'nouveau_prix': produit.nouveau_prix,
            'est_promo': str(produit.est_promo),
            'prix_promo': produit.prix_promo,
            'est_pc': str(produit.est_pc),
            'est_vendue': str(produit.est_vendue),
            'image': produit.image.url,
            'date_insertion': str(produit.date_insertion).split('.')[0],
            'url': url,
            'ville' : produit.vendeur.ville.nom,
            'pays' : produit.vendeur.pays.nom,
            'frais' : produit.vendeur.frais,
        }
        list_produits.append(tmp)
    context['produits'] = list_produits

    if request.method == 'POST':
        if request.POST.get('name'):
            data_json = request.POST.get('data')
            data = json.loads(data_json)
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')

            mess = f"""

            Nom du client : {name}
            Email : {email}
            Téléphone / WhatsApp : {phone}
            Adresse de Livraison : {address}
            

                        """

            produits = []
            for el in data:
                produit = Produit.objects.filter(id=data[el].get('id')).first()

                tmp2 = {
                    'id': str(produit.id),
                    'marque': produit.marque.nom,
                    'model': produit.model,
                    'ancien_prix': produit.ancien_prix,
                    'nouveau_prix': produit.nouveau_prix,
                    'est_promo': produit.est_promo,
                    'prix_promo': produit.prix_promo,
                    'est_pc': str(produit.est_pc),
                    'est_vendue': str(produit.est_vendue),
                    'qte' : data[el].get('qty'),
                    'solde_promo' : int(data[el].get('qty')) * produit.prix_promo,
                    'solde_reel' : int(data[el].get('qty')) * produit.nouveau_prix,
                    'vendeur_id' : str(produit.vendeur.id)
                }
                produits.append(tmp2)
            liste = regrouper_par_vendeur(produits)
            total = 0
            f = 0
            for vendeur_id, produits_vendeur in liste.items():
                vendeur = Vendeur.objects.get(id=vendeur_id)
                messages = ""
                i = 0
                t_promo = 0
                t_reel = 0
                for produit in produits_vendeur:
                    if int(produit['prix_promo']) != 0:
                        t_promo = t_promo + int(produit['qte']) * int(produit['prix_promo'])
                    else :
                        t_reel = t_reel + int(produit['qte'])  * int(produit['nouveau_prix'])
                    tmp = f"""
                ----------------------------
                Produit {i + 1} : {root}/{produit['id']}
                    -> Nom : {produit['marque']} {produit['model']}
                    -> Nouveau Prix : {produit['nouveau_prix']} FCFA
                    -> Prix Promo : {produit['prix_promo']} FCFA
                    -> Quantité : {produit['qte']}
                    -> Statut : {statut_produit(produit['est_vendue'])}
                    
                                """
                    messages = messages + "\n" + tmp
                    i+=1

                total += t_promo + t_reel
                f += vendeur.frais
                messages += f"""
                
                Frais de livraision: {vendeur.frais}
            
                =======================
                
                TOTAL : {t_promo + t_reel + vendeur.frais} FCFA
            
            
            
                by Ultimate-Technology
                """
                messages = mess + "\n" + messages
                send_mail(
                    'NOUVELLE COMMANDE SUR ULTIMATE-TECHNOLOGY',
                    messages,
                    settings.EMAIL_HOST_USER,
                    [vendeur.email],
                    fail_silently=False,
                )

            # Email HTML client pour confirmation de la commande
            sujet = "Information sur la commande"
            html_message = render_to_string('./emails/commande.html', {
                'name' : name,
                'email' : email,
                'phone' : phone,
                'root' : root,
                'address' : address,
                'total' : total+f,
                'produits': produits,
                'frais' : f,
            })
            message_texte = strip_tags(html_message)

            send_mail(
                sujet,
                message_texte,
                settings.EMAIL_HOST_USER,
                [email],
                html_message=html_message
            )
            return HttpResponseRedirect('/#home')

        if request.POST.get('email_client'):
            email = request.POST.get('email_client')
            nombre = Client.objects.filter(email=email).count()
            if (nombre == 0):
                client = Client(email=email)
                client.save()
                # Email HTML
                sujet = "Bienvenue sur notre site"
                html_message = render_to_string('./emails/bienvenue.html', {
                    'root': root,
                })
                message_texte = strip_tags(html_message)

                send_mail(
                    sujet,
                    message_texte,
                    settings.EMAIL_HOST_USER,
                    [email],
                    html_message=html_message
                )
            return  HttpResponseRedirect('/#home')

    return render(request, 'index.html', context=context)

def details(request, id):
    produit = Produit.objects.filter(id=id).first()
    context = {}
    context['produit'] = produit
    message = f"""
    Salut ! 
j'aimerais acheté ce produit : 
{request.build_absolute_uri()}
    
#ultimate-technology
    """
    context['lien'] = generate_whatsapp_link(produit.vendeur.tel, message)
    context['test_utl_detail'] = f"{produit.id}" in str(request.build_absolute_uri())
    context['model'] = produit.model
    context['marque'] = produit.marque
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

    context['url_image'] = f"{root}{produit.image.url}"
    #if not ('vendeur' in request.session):
    #    return redirect('login_vendeur')
    return render(request, 'details.html', context=context)


def details_vendeur(request, id):
    if not request.session['vendeur']:
        return redirect('login_vendeur')
    produit = Produit.objects.filter(id=id).first()
    context = {}
    context['produit'] = produit
    message = f"""
    Salut ! 
j'aimerais acheté ce produit : 
{request.build_absolute_uri()}

#ultimate-technology
    """
    context['lien'] = generate_whatsapp_link(produit.vendeur.tel, message)
    context['test_utl_detail'] = f"{produit.id}" in str(request.build_absolute_uri())
    context['model'] = produit.model
    context['marque'] = produit.marque
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

    context['url_image'] = f"{root}{produit.image.url}"

    return render(request, 'details_vendeur.html', context=context)


def promotions(request):
    produits = Produit.objects.filter(est_promo=True).all()
    context = {}
    list_produits = []
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

    for produit in produits:
        message = f"""
            Salut !
j'aimerais acheté ce produit : 
{root}/{str(produit.id)}
            
#ultimate-technology
            """
        url = generate_whatsapp_link('+237658630407', message)
        tmp = {
            'id': str(produit.id),
            'marque': produit.marque.nom,
            'model': produit.model,
            'cpu': produit.cpu,
            'ram': produit.ram,
            'stockage': produit.stockage,
            'graphic': produit.graphic,
            'description': produit.description,
            'ancien_prix': produit.ancien_prix,
            'nouveau_prix': produit.nouveau_prix,
            'est_promo': str(produit.est_promo),
            'prix_promo': produit.prix_promo,
            'est_pc': str(produit.est_pc),
            'est_vendue': str(produit.est_vendue),
            'image': produit.image.url,
            'date_insertion': str(produit.date_insertion).split('.')[0],
            'url': url,
            'ville': produit.vendeur.ville.nom,
            'pays': produit.vendeur.pays.nom,
        }
        list_produits.append(tmp)
    context['produits'] = list_produits
    context[ 'url_test'] = "promotions" in str(request.build_absolute_uri())

    return render(request, 'promotions.html', context=context)

def a_propos(request):
    staffs = Staff.objects.all()
    context = {}
    context['staffs'] = staffs
    return render(request, 'a-propos.html', context=context)

@csrf_exempt
def contact(request):
    if request.method == 'POST':
        nom = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Email HTML
        sujet = "Nouveau Message"
        html_message = render_to_string('emails/message.html', {
            'date' : str(datetime.datetime.now()).split('.')[0],
            'nom' : nom,
            'email' : email,
            'message' : message,
        })
        message_texte = strip_tags(html_message)

        send_mail(
            sujet,
            message_texte,
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER],
            html_message=html_message
        )
        return redirect('contact')

    return render(request, 'contact.html')

def login(request):
    if ('vendeur' in request.session):
        return redirect('vendeur')
    context = {}
    context['numero'] = settings.NUMERO
    context['msg'] = ""
    context['msg2'] = ""
    if request.method == 'POST':
        code = request.POST['code']
        mdp = request.POST['password']
        donnees = {
            'code' : code,
            'mdp': mdp,
        }
        context['donnees'] = donnees
        parsed = urllib.parse.urlparse(request.build_absolute_uri())
        root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
        try:
            # Convertir en UUID
            uuid_obj = uuid.UUID(code)
            #vdr = get_object_or_404(Vendeur, id=uuid_obj)
            if Vendeur.objects.filter(id=uuid_obj).exists():
                vdr = get_object_or_404(Vendeur, id=uuid_obj)
                if mdp != vdr.mdp:
                    context['msg'] = "Mot de passe incorrect !"
                elif vdr.jours_restants() == 0:
                    context['msg'] = f"Votre forfait {vdr.forfait.nom} a expiré ! contacter l'admin pour un renouvellement !"
                else:
                    request.session['vendeur'] = {
                        'code' : str(vdr.id),
                        'nom' : vdr.nom,
                        'tel' : vdr.tel,
                        'email' : vdr.email,
                        'mdp' : vdr.mdp,
                        'pays' : vdr.pays.nom,
                        'ville' : vdr.ville.nom,
                        'frais' : vdr.frais,
                        'forfait_nom' : vdr.forfait.nom,
                        'forfait_prix' : vdr.forfait.prix,
                        'date_insertion' : str(vdr.date_insertion),
                        'date_exp' : str(vdr.date_exp),
                        'logo' : vdr.logo.url,
                        'jours' : vdr.jours,
                    }
                    return redirect("vendeur")
            else:
                context['msg'] = "Aucun compte trouvé !"
        except (ValueError, ValidationError, Vendeur.DoesNotExist):
            # Gestion d'erreur
            context['msg'] = "Aucun compte trouvé !"
        return render(request, 'login_vendeur.html', context=context)

    return render(request, 'login_vendeur.html', context=context)

def register(request):
    context = {}
    context['msg'] = ""
    context['msg2'] = ""
    forfaits = Forfait.objects.all()
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    context['forfaits'] = forfaits
    if request.method == 'POST':
        nom = request.POST['company']
        telephone = request.POST['whatsapp']
        email = request.POST['email']
        plan = request.POST['plan']
        ville = request.POST['ville'].capitalize().replace('é','e')
        pays = request.POST['pays'].capitalize().replace('é','e')
        donnees = {
            'nom' : nom,
            'tel' : telephone,
            'email' : email,
            'plan' : plan,
            'mdp' : request.POST['password'],
            'mdp2' : request.POST['confirm'],
            'frais' : request.POST['frais'],
            'ville' : ville,
            'pays' : pays,
        }
        context['donnees'] = donnees

        vdr = Vendeur.objects.filter(email=email).first()
        if vdr:
            context['msg2'] = "Cet e-mail existe déjà !"
            return render(request, 'register_vendeur.html', context=context)

        mdp = request.POST['password']
        mdp2 = request.POST['confirm']
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
        if(mdp != mdp2):
            context['msg'] = "Le mot de passe ne correspond pas !"
        elif not re.match(pattern, mdp):
            context['msg'] = "Le mot de passe doit avoir au moins 8 caractère, chiffre, majuscule, miniscule et caractère spéciaux (!@#$%^&*(),.?\"...)"
        else:
            mVille = Ville.objects.get(nom=ville)
            if not mVille :
                mVille = Ville(nom=ville)
                mVille.save()
            mPays = Pays.objects.get(nom=pays)
            if not mPays:
                mPays = Pays.objects.get(nom=pays)
                mPays.save()

            frais = request.POST['frais']
            forfait = Forfait.objects.get(nom=request.POST['plan'])

            if 'logo' in request.FILES:
                save_vendeur = Vendeur(nom=nom, tel=telephone, email=email, mdp=mdp, frais=frais, forfait=forfait, pays=mPays, ville=mVille, logo=request.FILES.get('logo'))
            else:
                save_vendeur = Vendeur(nom=nom, tel=telephone, email=email, mdp=mdp, frais=frais, forfait=forfait, pays=mPays, ville=mVille)
            save_vendeur.save()

            # Email HTML pour l'admin
            sujet = f"Inscription chez Ultimate-Technology"
            html_message = render_to_string('emails/nouveau_vendeur.html', {
                'vendeur' : Vendeur.objects.get(email=email),
                'insertion' : str(Vendeur.objects.get(email=email).date_insertion),
                'expiration' : str(Vendeur.objects.get(email=email).date_exp)
            })
            message_texte = strip_tags(html_message)

            send_mail(
                sujet,
                message_texte,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                html_message=html_message
            )

            # Email HTML pour Vendeur
            sujet = f"Inscription du vendeur {nom}"
            html_message = render_to_string('emails/bienvenue_vendeur.html', {
                'vendeur': Vendeur.objects.get(email=email),
                'insertion': str(Vendeur.objects.get(email=email).date_insertion),
                'expiration': str(Vendeur.objects.get(email=email).date_exp),
                'numero' : settings.NUMERO,
                'root' : root
            })
            message_texte = strip_tags(html_message)

            send_mail(
                sujet,
                message_texte,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                html_message=html_message
            )

            return redirect('login_vendeur')

    return render(request, 'register_vendeur.html', context=context)

def recover(request):
    context = {}
    context['msg'] = ""
    context['msg2'] = ""
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    if request.method == 'POST':
        email = request.POST['email']
        donnees = {
            'email': email,
        }
        context['donnees'] = donnees
        vdr = Vendeur.objects.get(email=email)
        if vdr:
            context['msg'] = "Un email vous sera envoyer !"

            # Email HTML pour recuperation
            sujet = f"Récupération de compte"
            html_message = render_to_string('emails/recuperation.html', {
                'vendeur': Vendeur.objects.get(email=email),
                'numero': settings.NUMERO,
                'root' : root,
            })
            message_texte = strip_tags(html_message)

            send_mail(
                sujet,
                message_texte,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                html_message=html_message
            )
        else:
            context['msg2'] = "Aucun compte trouvé !"

    return render(request, 'recover_vendeur.html')

#@ensure_csrf_cookie
#@login_required(login_url="login_vendeur")
def index_vendeur(request):
    context = {}
    # Vérifier la session
    if 'vendeur' not in request.session:
        return redirect('login_vendeur')

    try:
        # Récupérer le vendeur
        vdr = Vendeur.objects.get(id=request.session['vendeur']['code'])  # Ou selon votre structure

        # Gestion de l'expiration
        if vdr.date_exp:
            aujourdhui = timezone.now().date()
            difference = vdr.date_exp - aujourdhui
            jours_restants = difference.days if difference.days >= 0 else 0

            # Mettre à jour si nécessaire
            if hasattr(vdr, 'jours') and vdr.jours != jours_restants:
                vdr.jours = jours_restants
                vdr.save()

            # Rediriger si expiration
            if jours_restants <= 0:
                del request.session['vendeur']
                return redirect('login_vendeur')

        # Récupérer les produits
        produits = Produit.objects.filter(vendeur=vdr)
        context['produits'] = produits
        context['vendeur'] = vdr

    except Vendeur.DoesNotExist:
        # Nettoyer la session si le vendeur n'existe plus
        del request.session['vendeur']
        return redirect('login_vendeur')
    context['est_soumis'] = False
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

    #produits = Produit.objects.filter(vendeur=vdr)


    list_produits = []

    for produit in produits:
        message = f"""
                Salut !
        j'aimerais acheté ce produit : 
        {root}/{str(produit.id)}

        #ultimate-technology
                """
        url = generate_whatsapp_link(produit.vendeur.tel, message)
        tmp = {
            'id': str(produit.id),
            'marque': produit.marque.nom,
            'model': produit.model,
            'cpu': produit.cpu,
            'ram': produit.ram,
            'stockage': produit.stockage,
            'graphic': produit.graphic,
            'description': produit.description,
            'ancien_prix': produit.ancien_prix,
            'nouveau_prix': produit.nouveau_prix,
            'est_promo': str(produit.est_promo),
            'prix_promo': produit.prix_promo,
            'est_pc': str(produit.est_pc),
            'est_vendue': str(produit.est_vendue),
            'image': produit.image.url,
            'date_insertion': str(produit.date_insertion).split('.')[0],
            'url': url,
            'pays' : produit.vendeur.pays.nom,
            'ville' : produit.vendeur.ville.nom,
        }
        list_produits.append(tmp)
    context['produits'] = list_produits
    context['url'] = f"{root}/vendeur/mystore/{str(vdr.id)}"

    if request.method == 'POST':
        if 'vendeur' in request.session:
            del request.session['vendeur']
        request.session.flush()
        return redirect("index")


    return render(request, 'index_vendeur.html', context=context)


def profil(request):
    if 'vendeur' not in request.session:
        return redirect('login_vendeur')
    context = {}
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    vdr = Vendeur.objects.filter(id=request.session['vendeur']['code']).first()
    if vdr.date_exp:
        aujourdhui = timezone.now().date()
        difference = vdr.date_exp - aujourdhui
        vdr.jours = difference.days if difference.days >= 0 else 0
        vdr.save()
    if vdr.jours == 0:
        del request.session['vendeur']
        return redirect('login_vendeur')
    context['vendeur'] = vdr
    context['root'] = root
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        tel = request.POST.get('tel')
        frais = request.POST.get('frais')
        mdp = request.POST.get('mdp')
        pays = request.POST.get('pays')
        ville = request.POST.get('ville')
        id = request.POST.get('id')

        vendeur = Vendeur.objects.get(id=id)

        if not Pays.objects.get(nom=pays):
            Pays(nom=pays).save()
        if not Ville.objects.get(nom=ville):
            Ville(nom=ville).save()
        p = Pays.objects.get(nom=pays)
        v = Ville.objects.get(nom=ville)

        vendeur.nom = nom
        vendeur.email = email
        vendeur.tel = tel
        vendeur.frais
        vendeur.mdp
        vendeur.ville = v
        vendeur.pays = p
        if 'logo' in request.FILES :
            logo = request.FILES['logo']
            vendeur.logo = logo
            vendeur.save()
        else :
            vendeur.save()
        context['msg'] = "Modfication effectué avec succès !"
        context['vendeur'] = vendeur

    return render(request, 'profil_vendeur.html', context)


def editer_produit(request, id):

    if 'vendeur' not in request.session:
        return redirect('login_vendeur')

    produit = Produit.objects.get(id=id)
    context = {}
    context['produit'] = produit
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    context['root'] = root;
    if request.method == 'POST':
        marque = request.POST['marque'].capitalize()
        model = request.POST['model']
        cpu = request.POST['cpu']
        ram = request.POST['ram']
        stockage = request.POST['stockage']
        graphic = request.POST['graphic']
        description = request.POST['description']
        ancien_prix = request.POST.get('ancien_prix', 0)
        nouveau_prix = request.POST['nouveau_prix']
        est_promo = request.POST.get('est_promo') == 'on'
        prix_promo = request.POST.get('prix_promo', 0)
        est_pc = request.POST['est_pc']
        est_vendue = request.POST.get('est_vendue') == 'on'


        produit = Produit.objects.get(id=id)
        produit.marque.nom = marque
        produit.model = model
        produit.cpu = cpu
        produit.ram = ram
        produit.stockage = stockage
        produit.graphic = graphic
        produit.description = description
        produit.nouveau_prix = nouveau_prix
        produit.est_promo = est_promo
        produit.ancien_prix = int(ancien_prix) if ancien_prix else 0
        produit.prix_promo = int(prix_promo) if prix_promo else 0
        produit.est_vendue = est_vendue
        image = request.FILES.get('image', None)
        image2 = request.FILES.get('image2', None)
        image3 = request.FILES.get('image3', None)
        if image:
            produit.image = image
        if image2:
            produit.image2 = image2
        if image3:
            produit.image3 = image3
        if 'action' in request.POST :
            if request.POST['action'] == "Enregistrer":
                produit.save()
            else:
                produit = Produit.objects.get(id=id)
                produit.delete()
            return redirect('vendeur')

    return render(request, 'editer_produit.html', context)

def ajouter_produit(request):

    if 'vendeur' not in request.session:
        return redirect('login_vendeur')
    context = {}
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    context['root'] = root
    if request.method == 'POST':
        marque = request.POST['marque'].capitalize()
        model = request.POST['model'].capitalize()
        cpu = request.POST['cpu']
        ram = request.POST['ram']
        stockage = request.POST['stockage']
        graphic = request.POST['graphic']
        description = request.POST['description']

        ancien_prix = request.POST.get('ancien_prix', 0)
        ancien_prix = int(ancien_prix) if ancien_prix else 0

        nouveau_prix = request.POST['nouveau_prix']
        est_promo = request.POST.get('est_promo') == 'on'

        prix_promo = request.POST.get('prix_promo', 0)
        prix_promo = int(prix_promo) if prix_promo else 0

        est_pc = request.POST['est_pc']
        est_vendue = request.POST.get('est_vendue') == 'on'
        image = request.FILES.get('image', None)
        image2 = request.FILES.get('image2', None)
        image3 = request.FILES.get('image3', None)

        if not Marque.objects.get(nom=marque):
            Marque(nom=marque).save()
        vdr = Vendeur.objects.get(id=request.session['vendeur']['code'])
        produit = Produit(vendeur=vdr, marque=Marque.objects.get(nom=marque), model=model, cpu=cpu, ram=ram,stockage=stockage,graphic=graphic, description=description, ancien_prix=ancien_prix, nouveau_prix=nouveau_prix, est_promo=est_promo, est_pc=est_pc, prix_promo=prix_promo, est_vendue=est_vendue, image=image, image2=image2, image3=image3)
        produit.save()
        context['msg'] = 'Produit ajouté avec succès !'

    return render(request, 'ajouter_produit.html', context=context)

def mystore_index(request, id):

    vendeur = Vendeur.objects.get(id=id)
    if vendeur.forfait.nom == "Standard":
        return redirect("index")
    if vendeur.jours == 0:
        return redirect("error_404")
    context = {}
    context['vendeur'] = vendeur
    context['est_soumis'] = False
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    context['root'] = root
    produits = Produit.objects.filter(vendeur_id=id)

    list_produits = []

    for produit in produits:
        message = f"""
                Salut !
        j'aimerais acheté ce produit : 
        {root}/{str(produit.id)}

        #ultimate-technology
                """
        url = generate_whatsapp_link(vendeur.tel, message)
        tmp = {
            'id': str(produit.id),
            'marque': produit.marque.nom,
            'model': produit.model,
            'cpu': produit.cpu,
            'ram': produit.ram,
            'stockage': produit.stockage,
            'graphic': produit.graphic,
            'description': produit.description,
            'ancien_prix': produit.ancien_prix,
            'nouveau_prix': produit.nouveau_prix,
            'est_promo': str(produit.est_promo),
            'prix_promo': produit.prix_promo,
            'est_pc': str(produit.est_pc),
            'est_vendue': str(produit.est_vendue),
            'image': produit.image.url,
            'date_insertion': str(produit.date_insertion).split('.')[0],
            'url': url,
            'ville' : produit.vendeur.ville.nom,
            'pays' : produit.vendeur.pays.nom,
            'vendeur_id' : str(produit.vendeur.id),
        }
        list_produits.append(tmp)
    context['produits'] = list_produits

    if request.method == 'POST':
        if request.POST.get('name'):
            data_json = request.POST.get('data')
            data = json.loads(data_json)
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            total = request.POST.get('total')

            mess = f"""

                Nom du client : {name}
                Email : {email}
                Téléphone / WhatsApp : {phone}
                Adresse de Livraison : {address}

                            """
            i = 0
            t_promo = 0
            t_reel = 0
            produits = []
            for el in data:
                produit = Produit.objects.filter(id=data[el].get('id')).first()

                tmp2 = {
                    'id': str(produit.id),
                    'marque': produit.marque.nom,
                    'model': produit.model,
                    'ancien_prix': produit.ancien_prix,
                    'nouveau_prix': produit.nouveau_prix,
                    'est_promo': produit.est_promo,
                    'prix_promo': produit.prix_promo,
                    'est_pc': str(produit.est_pc),
                    'est_vendue': str(produit.est_vendue),
                    'qte' : data[el].get('qty'),
                    'solde_promo' : int(data[el].get('qty')) * produit.prix_promo,
                    'solde_reel' : int(data[el].get('qty')) * produit.nouveau_prix,
                }
                produits.append(tmp2)
                if produit.prix_promo != 0:
                    t_promo = t_promo + int(data[el].get('qty')) * produit.prix_promo
                else:
                    t_reel = t_reel + int(data[el].get('qty')) * produit.nouveau_prix

                tmp = f"""
                ----------------------------
                Produit {i + 1} : {root}/{produit.id}
                    -> Nom : {produit.marque} {produit.model}
                    -> Nouveau Prix : {produit.nouveau_prix} FCFA
                    -> Prix Promo : {produit.prix_promo} FCFA
                    -> Quantité : {data[el].get('qty')}

                                """
                mess = mess + "\n" + tmp
                i+=1
            mess += f"""
            
                Frais de livraision si Douala : {vendeur.frais} FCFA


                =======================
                TOTAL : {t_promo + t_reel + vendeur.frais} FCFA



                by Ultimate-Technology
                """
            send_mail(
                'NOUVELLE COMMANDE',
                mess,
                settings.EMAIL_HOST_USER,
                [vendeur.email],
                fail_silently=False,
            )
            # Email HTML pour les clients
            sujet = "Information sur la commande"
            html_message = render_to_string('./emails/mystore_commande.html', {
                'name' : name,
                'email' : email,
                'phone' : phone,
                'root' : root,
                'address' : address,
                'total' : t_promo + t_reel + vendeur.frais,
                'produits': produits,
                'vendeur_num' : vendeur.tel,
                'frais' : vendeur.frais
            })
            message_texte = strip_tags(html_message)

            send_mail(
                sujet,
                message_texte,
                settings.EMAIL_HOST_USER,
                [email],
                html_message=html_message
            )
            return redirect('mystore_index', id=id)

        if request.POST.get('email_client'):
            email = request.POST.get('email_client')
            nombre = Client.objects.filter(email=email).count()
            if (nombre == 0):
                client = Client(email=email)
                client.save()
                # Email HTML
                sujet = "Bienvenue sur notre site"
                html_message = render_to_string('./emails/bienvenue.html', {
                    'root': root,
                })
                message_texte = strip_tags(html_message)

                send_mail(
                    sujet,
                    message_texte,
                    settings.EMAIL_HOST_USER,
                    [email],
                    html_message=html_message
                )
            return  redirect('mystore_index', id=id)

    return render(request, 'mystore_index.html', context=context)

def mystore_promotion(request, id):
    vendeur = Vendeur.objects.get(id=id)
    if vendeur.forfait.nom == "Standard":
        return redirect("index")
    if vendeur.jours == 0:
        return redirect("error_404")
    produits = Produit.objects.filter(vendeur_id=id, est_promo=True).all()
    context = {}
    list_produits = []
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

    for produit in produits:
        message = f"""
                Salut !
    j'aimerais acheté ce produit : 
    {root}/{str(produit.id)}

    #ultimate-technology
                """
        url = generate_whatsapp_link(vendeur.tel, message)
        tmp = {
            'id': str(produit.id),
            'marque': produit.marque.nom,
            'model': produit.model,
            'cpu': produit.cpu,
            'ram': produit.ram,
            'stockage': produit.stockage,
            'graphic': produit.graphic,
            'description': produit.description,
            'ancien_prix': produit.ancien_prix,
            'nouveau_prix': produit.nouveau_prix,
            'est_promo': str(produit.est_promo),
            'prix_promo': produit.prix_promo,
            'est_pc': str(produit.est_pc),
            'est_vendue': str(produit.est_vendue),
            'image': produit.image.url,
            'ville': produit.vendeur.ville.nom,
            'pays': produit.vendeur.pays.nom,
            'date_insertion': str(produit.date_insertion).split('.')[0],
            'url': url,
            'vendeur_id': str(vendeur.id)
        }
        list_produits.append(tmp)
    context['produits'] = list_produits
    context['url_test'] = "promotions" in str(request.build_absolute_uri())
    context['root'] = root
    context['vendeur'] = vendeur

    return render(request, 'mystore_promotion.html', context)


def mystore_details(request, id, id2):
    vendeur = Vendeur.objects.get(id=id)
    if vendeur.forfait.nom == "Standard":
        return redirect("index")
    if vendeur.jours == 0:
        return redirect("error_404")
    produit = Produit.objects.get(id=id2)
    context = {}
    context['produit'] = produit
    message = f"""
        Salut ! 
    j'aimerais acheté ce produit : 
    {request.build_absolute_uri()}

    #ultimate-technology
        """
    context['lien'] = generate_whatsapp_link(produit.vendeur.tel, message)
    context['test_utl_detail'] = f"{produit.id}" in str(request.build_absolute_uri())
    context['model'] = produit.model
    context['marque'] = produit.marque
    parsed = urllib.parse.urlparse(request.build_absolute_uri())
    root = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    context['vendeur'] = vendeur
    context['url_image'] = f"{root}{produit.image.url}"

    return render(request, 'mystore_details.html', context=context)


from typing import Optional
def error_404(request, exception: Optional[Exception] = None):

    return render(request, 'errors/404.html', status=404)

def error_500(request):

    return render(request, 'errors/500.html', status=500)

"""
def envoyer_email_django(request):
    # Email simple
    send_mail(
        'Sujet de l\'email',
        'Message en texte brut.',
        'hackdumping@gmail.com',
        ['erictchoupe5@gmail.com'],
        fail_silently=False,
    )
    
    # Email HTML
    sujet = "Bienvenue sur notre site"
    html_message = render_to_string('emails/bienvenue.html', {
        'user': request.user,
        'site_url': 'https://example.com'
    })
    message_texte = strip_tags(html_message)

    send_mail(
        sujet,
        message_texte,
        'noreply@example.com',
        ['user@example.com'],
        html_message=html_message
    )

    # Email avec pièce jointe
    email = EmailMessage(
        'Votre facture',
        'Veuillez trouver votre facture ci-jointe.',
        'billing@example.com',
        ['client@example.com']
    )
    email.attach_file('factures/facture_123.pdf')
    email.send()
    
    return HttpResponse("Emails envoyés!")
"""