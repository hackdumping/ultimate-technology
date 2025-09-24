import uuid

from cloudinary.models import CloudinaryField
from django.db import models
from django.utils import timezone
from django.db.models.fields import BooleanField
from django_resized import ResizedImageField

# Create your models here.

class Marque(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

class Pays(models.Model):
    nom = models.CharField(max_length=200, default="Cameroun")

    def __str__(self):
        return self.nom

class Ville(models.Model):
    nom = models.CharField(max_length=200, default="Douala")

    def __str__(self):
        return self.nom

class Forfait(models.Model):
    nom = models.CharField(max_length=200)
    prix = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.nom} - {self.prix} XAF / mois"

class Vendeur(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    pays = models.ForeignKey(Pays, on_delete=models.PROTECT, default=None, blank=True, null=True) #models.CharField(max_length=200, default="Cameroun")
    tel = models.CharField(max_length=20)
    email = models.EmailField(max_length=200, unique=True)
    mdp = models.CharField(max_length=255)
    ville = models.ForeignKey(Ville, on_delete=models.PROTECT, default=None, blank=True, null=True)  #models.CharField(max_length=255, default="Douala")
    frais = models.PositiveIntegerField()
    forfait = models.ForeignKey(Forfait, on_delete=models.PROTECT, default=None, null=True, blank=True)
    date_insertion = models.DateTimeField(auto_now_add=True)
    date_exp = models.DateField(verbose_name="Date expiration", null=True, blank=True)
    #logo = models.ImageField(upload_to='logos/', blank=True, null=True, default="images/no_logo.jpg")
    logo = CloudinaryField('logo', folder='produits/', blank=True, null=True, default="images/no_logo.jpg")
    jours = models.PositiveIntegerField(default=0) #, editable=False)

    class Meta:
        ordering = ['-date_insertion']

    def save(self, *args, **kwargs):
        # Calculer les jours restants avant sauvegarde
        if self.date_exp:
            aujourdhui = timezone.now().date()
            difference = self.date_exp - aujourdhui
            self.jours = difference.days if difference.days >= 0 else 0
        else:
            self.jours = 1

        super().save(*args, **kwargs)

    # Méthode pour accéder facilement
    def jours_restants(self):
        return self.jours

    def __str__(self):
        return f"{self.nom}[{self.tel} - forfait {self.forfait.nom} - {self.jours_restants()} jours restant"


class Produit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendeur = models.ForeignKey(Vendeur, on_delete=models.PROTECT, default=None, null=True, blank=True)
    marque = models.ForeignKey(Marque, on_delete=models.PROTECT, related_name='marque')
    model = models.CharField(max_length=255)
    cpu = models.CharField(max_length=255)
    ram = models.CharField(max_length=255)
    stockage = models.CharField(max_length=255)
    graphic = models.CharField(max_length=255, default="", blank=True)
    description = models.TextField()
    ancien_prix = models.PositiveIntegerField(blank=True, default=0)
    nouveau_prix = models.PositiveIntegerField()
    est_promo = models.BooleanField(default=False)
    prix_promo = models.PositiveIntegerField(blank=True, default=0)
    est_pc = models.BooleanField(default=True)
    est_vendue = models.BooleanField(default=False)
    """image = ResizedImageField(
        size=[500, 500],  # Carré 500x500
        crop=['middle', 'center'],  # Centrage
        quality=75,
        upload_to='produits/',
        blank=True,
        null=True
    )"""
    image = CloudinaryField('image', folder='produits/', blank=True, null=True)


    """image2 = ResizedImageField(
        size=[500, 500],  # Carré 500x500
        crop=['middle', 'center'],  # Centrage
        quality=75,
        upload_to='produits/',
        blank=True,
        null=True
    )"""
    image2 = CloudinaryField('image2', folder='produits/', blank=True, null=True )

    """image3 = ResizedImageField(
        size=[500, 500],  # Carré 500x500
        crop=['middle', 'center'],  # Centrage
        quality=75,
        upload_to='produits/',
        blank=True,
        null=True
    )"""
    #image = models.ImageField(upload_to='produits/', blank=True, null=True)
    #image2 = models.ImageField(upload_to='produits/', blank=True, null=True)
    #image3 = models.ImageField(upload_to='produits/', blank=True, null=True)
    image3 = CloudinaryField('image3', folder='produits/', blank=True, null=True)

    date_insertion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_insertion', '-marque']

    def __str__(self):
        return f"{self.marque.nom} {self.model} --- RAM {self.ram} - {self.stockage} en rupture : {self.est_vendue}"

    """
    # Propriété pour compatibilité
    @property
    def image_url(self):
        #Retourne l'URL Cloudinary de l'image
        if self.image:
            return self.image.url
        if self.image2:
            return self.image2.url
        if self.image3:
            return self.image3.url
        return None

    @property
    def thumbnail_url(self):
        #URL avec transformations pour thumbnail
        if self.image:
            return self.image.build_url(width=300, height=200, crop="fill")
        if self.image2:
            return self.image2.build_url(width=300, height=200, crop="fill")
        if self.image3:
            return self.image3.build_url(width=300, height=200, crop="fill")
        return None
    """

class Staff(models.Model):
    nom = models.CharField(max_length=255)
    alias = models.CharField(max_length=255, default="", blank=True)
    role = models.CharField(max_length=255)
    tel = models.CharField(max_length=100)
    #image = models.ImageField(upload_to='staff/', blank=True, null=True)
    image = CloudinaryField('image', folder='staff/', blank=True, null=True )
    date_insertion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-nom']

    def __str__(self):
        return f"{self.nom} -- {self.tel}"

class Client(models.Model):
    email = models.EmailField(max_length=255)
    date_insertion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_insertion']

    def __str__(self):
        return f"{self.email}"


