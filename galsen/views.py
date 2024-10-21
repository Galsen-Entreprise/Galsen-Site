from django.http import HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.db import models
from django.http import HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
import os
import time
from django.http import JsonResponse
from django.db.models import Q
from django.views import View
from galsen.utils import obtenir_marque_dispositif
from django.forms import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .decorators import role_required

''' =========== Les API ========= '''
from rest_framework import viewsets
from .serializers import CustomUserSerializer, PostSerializer, MediasPostSerializer, JobSerializer, BoutiqueSerializer, CommentaireSerializer, ReponseSerializer, ProductSerializer, MediasProductSerializer, ProfilSerializer, ExperienceSerializer, FormationSerializer, NotificationSerializer, CommandeSerializer

''' =========== Les Models ========= '''
from .models import CustomUser, Post, MediasPost, Job, Boutique, Commentaire, Reponse, Product, MediasProduct, Profil, Experience, Formation, Notification, Commande, Traffic

''' =========== Authentication ========= '''
from django.contrib.auth import authenticate, login, logout
from galsen.forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework import viewsets
from .serializers import CustomUserSerializer
from .forms import EmailChangeForm, NameChangeForm, RoleChangeForm, AccountDeleteForm, PasswordChangeForm

# Create your views here.

''' =========== Les API ========= '''
class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
class MediasPostViewSet(viewsets.ModelViewSet):
    queryset = MediasPost.objects.all()
    serializer_class = MediasPostSerializer

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

class BoutiqueViewSet(viewsets.ModelViewSet):
    queryset = Boutique.objects.all()
    serializer_class = BoutiqueSerializer

class CommentaireViewSet(viewsets.ModelViewSet):
    queryset = Commentaire.objects.all()
    serializer_class = CommentaireSerializer

class ReponseViewSet(viewsets.ModelViewSet):
    queryset = Reponse.objects.all()
    serializer_class = ReponseSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class MediasProductViewSet(viewsets.ModelViewSet):
    queryset = MediasProduct.objects.all()
    serializer_class = MediasProductSerializer

class ProfilViewSet(viewsets.ModelViewSet):
    queryset = Profil.objects.all()
    serializer_class = ProfilSerializer

class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

class FormationViewSet(viewsets.ModelViewSet):
    queryset = Formation.objects.all()
    serializer_class = FormationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

class CommandeViewSet(viewsets.ModelViewSet):
    queryset = Commande.objects.all()
    serializer_class = CommandeSerializer


def log_in(request):
    if request.method == 'POST':
        email = request.POST['email']  
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)
        if user is not None and user.is_authenticated:
            login(request, user)
            
            # Enregistrer le trafic
            today = timezone.now().date()
            traffic, created = Traffic.objects.get_or_create(date=today)
            traffic.visits += 1  # Incrémente le nombre de visites
            traffic.save()

            roles_valides = ['admin', 'personnel', 'ecole', 'entreprise']

            if user.rôle == 'admin':
                return redirect('SuperAdmin')
            else:
                return redirect('home')

    return render(request, 'auth/login.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        try:
            form.full_clean()  # Utilisez full_clean pour déclencher toutes les validations du formulaire
        except ValidationError as e:
            
            for field, messages in e.message_dict.items():
                form.add_error(field, messages)
        if form.is_valid():
            user = form.save()
            user.backend = 'galsen.backends.EmailBackend'
            login(request, user)
            
            user_role = request.user.rôle

            if user_role == 'admin':
                return render(request, '')
            elif user_role == 'personnel':
                return render(request, 'auth/personnel.html')
            elif user_role == 'ecole':
                return render(request, 'auth/ecole.html')
            elif user_role == 'entreprise':
                return render(request, 'auth/entreprise.html')
    else:
        form = CustomUserCreationForm()

    return render(request, 'auth/register.html', {'form': form})

def log_out(request):
    # pass
    logout(request)
    messages.success(request, 'Déconnecter👌🏾')
    return redirect('login')

def profile(request):
    if request.method == 'POST':
        user = request.user
        
        # Récupérer les données du formulaire POST
        pays = request.POST.get('pays')
        ville = request.POST.get('ville')
        quartier = request.POST.get('quartier')
        indicatif = request.POST.get('indicatif')
        phone = request.POST.get('phone')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        birthday = request.POST.get('birthday')

        # Mettre à jour les champs appropriés
        user.pays = pays
        user.ville = ville
        user.quartier = quartier
        user.indicatif_pays = indicatif
        user.number_phone = phone

        # Vérifier si les champs first_name et last_name sont fournis, sinon les définir sur None
        user.first_name = firstname if firstname else None
        user.last_name = lastname if lastname else None

        user.birthday = birthday

        user.save()

        messages.success(request, 'Profil mis à jour avec succès.')

        return redirect('login')

''' =========== Les Pages (home, personnel, entreprise, ecole, emplois, boutique) ========= '''
@role_required(['admin','personnel', 'ecole', 'entreprise'])
def home(request):
    # Récupérer tous les posts avec les médias associés, les utilisateurs, et la date de création
    posts = Post.objects.select_related('user').prefetch_related('mediaspost_set').order_by('-date_creation_post').all()
    user = request.user
    
    if request.method == "GET":
        contenu_post = request.GET.get('poste')
        if contenu_post is not None:
            posts = Post.objects.filter(contenu_post__icontains=contenu_post)
    
    if request.user.is_authenticated:
        marque_dispositif = obtenir_marque_dispositif(request)
        request.user.marque_dispositif = marque_dispositif
        request.user.save()

    context = {
        'posts': posts,
        'user': user
    }
    return render(request, 'pages/home.html', context)

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def personnel(request):
    CustomUsers = CustomUser.objects.filter(rôle='personnel')
    user = request.user
    query = request.GET.get('personnel')

    if query:
        # Séparer le query en mots individuels pour rechercher dans first_name, last_name et rôle
        query_words = query.split()

        # Construire une requête qui recherche dans first_name, last_name et rôle indépendamment de l'ordre
        filter_query = Q()
        for word in query_words:
            filter_query &= (
                Q(first_name__icontains=word) | 
                Q(last_name__icontains=word) |
                Q(metier__icontains=word)
            )

        CustomUsers = CustomUser.objects.filter(rôle='personnel').filter(filter_query)

    context = {
        'CustomUsers': CustomUsers,
        'user': user,
        'query': query,  # Ajouter la requête pour la réafficher dans le formulaire
        'result_count': CustomUsers.count()
    }
    return render(request, 'pages/personnel.html', context)

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def entreprise(request):
    CustomUsers = CustomUser.objects.filter(rôle='entreprise')
    user = request.user
    query = request.GET.get('entreprise')

    if query:
        # Séparer le query en mots individuels pour rechercher dans first_name, last_name et rôle
        query_words = query.split()

        # Construire une requête qui recherche dans first_name, last_name et rôle indépendamment de l'ordre
        filter_query = Q()
        for word in query_words:
            filter_query &= ( 
                Q(etablissement__icontains=word) |
                Q(metier__icontains=word)
            )

        CustomUsers = CustomUser.objects.filter(rôle='entreprise').filter(filter_query)

    context = {
        'CustomUsers': CustomUsers,
        'user': user,
        'query': query,  # Ajouter la requête pour la réafficher dans le formulaire
        'result_count': CustomUsers.count()
    }
    return render(request, 'pages/entreprise.html', context)

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def ecole(request):
    CustomUsers = CustomUser.objects.filter(rôle='ecole')
    user = request.user
    query = request.GET.get('ecole')

    if query:
        # Séparer le query en mots individuels pour rechercher dans first_name, last_name et rôle
        query_words = query.split()

        # Construire une requête qui recherche dans first_name, last_name et rôle indépendamment de l'ordre
        filter_query = Q()
        for word in query_words:
            filter_query &= ( 
                Q(etablissement__icontains=word) |
                Q(metier__icontains=word)
            )

        CustomUsers = CustomUser.objects.filter(rôle='ecole').filter(filter_query)

    context = {
        'CustomUsers': CustomUsers,
        'user': user,
        'query': query,  # Ajouter la requête pour la réafficher dans le formulaire
        'result_count': CustomUsers.count()
    }
    return render(request, 'pages/ecole.html', context)

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def emplois(request):
     # Récupérer l'utilisateur connecté
    user = request.user
    
    # Récupérer les offres d'emploi
    jobs = Job.objects.select_related('user').order_by('-date_creation_post').exclude(postule_job=user)
    
    if request.method == "GET":
        title = request.GET.get('job')
        if title is not None:
            jobs = jobs.filter(title__icontains=title)

    context = {
        'jobs': jobs,
        'user': user
    }
    return render(request, 'pages/emplois.html', context)

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def boutique(request):
    # Récupérer l'utilisateur connecté
    user = request.user

    # Récupérer les produits commandés par l'utilisateur connecté
    produits_commandes = Commande.objects.filter(user=user).values_list('product', flat=True)

    # Récupérer les 4 produits les plus récents, en excluant ceux commandés
    produits_recents = Product.objects.select_related('boutique').exclude(id__in=produits_commandes).order_by('-date_creation')[:4]
    
    # Récupérer 4 produits de la catégorie 'Electronic', en excluant ceux commandés
    electronic = Product.objects.select_related('boutique').filter(category='electronics').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Fashion', en excluant ceux commandés
    fashion = Product.objects.select_related('boutique').filter(category='fashion').exclude(id__in=produits_commandes)[:4]

    # Récupérer 4 produits de la catégorie 'Maison et Jardin', en excluant ceux commandés
    produits_maison_jardin = Product.objects.select_related('boutique').filter(category='home_garden').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Beauté et Santé', en excluant ceux commandés
    beauty_health = Product.objects.select_related('boutique').filter(category='beauty_health').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Alimentation et Boissons', en excluant ceux commandés
    food_drink = Product.objects.select_related('boutique').filter(category='food_drink').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Sport et Loisirs', en excluant ceux commandés
    sports_leisure = Product.objects.select_related('boutique').filter(category='sports_leisure').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Livres et Médias', en excluant ceux commandés
    books_media = Product.objects.select_related('boutique').filter(category='books_media').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Jouets et Enfants', en excluant ceux commandés
    toys_kids = Product.objects.select_related('boutique').filter(category='toys_kids').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Automobile et Outils', en excluant ceux commandés
    automotive_tools = Product.objects.select_related('boutique').filter(category='automotive_tools').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Animaux', en excluant ceux commandés
    pets = Product.objects.select_related('boutique').filter(category='pets').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Services et Abonnements', en excluant ceux commandés
    services = Product.objects.select_related('boutique').filter(category='services').exclude(id__in=produits_commandes)[:4]
    
    # Récupérer 4 produits de la catégorie 'Offres spéciales / Promotions', en excluant ceux commandés
    special_offers = Product.objects.select_related('boutique').filter(category='special_offers').exclude(id__in=produits_commandes)[:4]

    if request.method == "GET":
        nom_produit = request.GET.get('boutique')
        if nom_produit is not None:
            produits_recents = produits_recents.filter(nom_produit__icontains=nom_produit)
            electronic = electronic.filter(nom_produit__icontains=nom_produit)
            fashion = fashion.filter(nom_produit__icontains=nom_produit)
            produits_maison_jardin = produits_maison_jardin.filter(nom_produit__icontains=nom_produit)
            beauty_health = produits_maison_jardin.filter(nom_produit__icontains=nom_produit)
            food_drink = produits_maison_jardin.filter(nom_produit__icontains=nom_produit)
            sports_leisure = sports_leisure.filter(nom_produit__icontains=nom_produit)
            books_media = books_media.filter(nom_produit__icontanis=nom_produit)
            toys_kids = toys_kids.filter(nom_produit__icontains=nom_produit)
            pets = pets.filter(nom_produit__icontains=nom_produit)
            services = services.filter(nom_produit__icontains=nom_produit)
            special_offers = special_offers.filter(nom_produit__icontains=nom_produit)

    context = {
        'user': user,
        'produits_recents': produits_recents,
        'electronic': electronic,
        'fashion' : fashion,
        'produits_maison_jardin': produits_maison_jardin,
        'beauty_health' : beauty_health,
        'food_drink' : food_drink,
        'sports_leisure' : sports_leisure,
        'books_media' : books_media,
        'toys_kids' : toys_kids,
        'automotive_tools' : automotive_tools,
        'pets' : pets,
        'services' : services,
        'special_offers' : special_offers
        
    }
    return render(request, 'pages/boutique.html', context)


''' =========== Section Admin ========= '''
@role_required(['admin'])
def SuperAdmin(request):
    # Récupérer la date d'aujourd'hui en tenant compte du fuseau horaire
    today = timezone.now().date()
    
    # Récupérer le nombre de visites d'aujourd'hui
    traffic_count = Traffic.objects.filter(date=today).aggregate(total_visits=models.Sum('visits'))['total_visits'] or 0

    # Compter le nombre d'utilisateurs selon leur rôle
    admin_count = CustomUser.objects.filter(rôle='admin').count()
    personnel_count = CustomUser.objects.filter(rôle='personnel').count()
    ecole_count = CustomUser.objects.filter(rôle='ecole').count()
    entreprise_count = CustomUser.objects.filter(rôle='entreprise').count()
    
    # Compter le nombre total d'utilisateurs
    total_users_count = CustomUser.objects.count()
    
    # Compter le nombre de boutiques
    boutique_count = Boutique.objects.count()

    # Calculer le pourcentage pour chaque rôle
    def calculate_percentage(count):
        return (count / total_users_count * 100) if total_users_count > 0 else 0

    admin_percentage = calculate_percentage(admin_count)
    personnel_percentage = calculate_percentage(personnel_count)
    ecole_percentage = calculate_percentage(ecole_count)
    entreprise_percentage = calculate_percentage(entreprise_count)

    # Récupérer les données de trafic mensuel pour l'année actuelle et l'année précédente
    current_year = today.year
    previous_year = current_year - 1

    monthly_current_year = Traffic.objects.filter(date__year=current_year).values('date__month').annotate(total_visits=models.Sum('visits')).order_by('date__month')
    monthly_previous_year = Traffic.objects.filter(date__year=previous_year).values('date__month').annotate(total_visits=models.Sum('visits')).order_by('date__month')

    # Créer des tableaux pour stocker les visites mensuelles
    current_year_visits = [0] * 12
    previous_year_visits = [0] * 12

    for entry in monthly_current_year:
        month = entry['date__month'] - 1
        current_year_visits[month] = entry['total_visits']

    for entry in monthly_previous_year:
        month = entry['date__month'] - 1
        previous_year_visits[month] = entry['total_visits']

    context = {
        'traffic_count': traffic_count,
        'admin_count': admin_count,
        'admin_percentage': admin_percentage,
        'personnel_count': personnel_count,
        'personnel_percentage': personnel_percentage,
        'ecole_count': ecole_count,
        'ecole_percentage': ecole_percentage,
        'entreprise_count': entreprise_count,
        'entreprise_percentage': entreprise_percentage,
        'total_users_count': total_users_count,
        'boutique_count': boutique_count,
        'current_year_visits': current_year_visits,
        'previous_year_visits': previous_year_visits,
        'previous_year': previous_year,  # Passer l'année précédente au template
    }
    
    return render(request, 'admins/dashboard.html', context)


''' =========== Formulaires ========= '''
@role_required(['admin','personnel', 'ecole', 'entreprise'])
def create_post(request):
    if request.method == 'POST':
        contenu_post = request.POST.get('contenu_post')
        tag_post = request.POST.get('tag_post')
        video = request.FILES.get('video')
        
        # Obtenez les informations de session actuelles
        session_info = obtenir_marque_dispositif(request)

        # Créez un nouveau post avec les informations de session
        new_post = Post.objects.create(
            user=request.user,
            contenu_post=contenu_post,
            tag_post=tag_post,
            video=video,
            session_info=session_info
        )

        # Récupérer les fichiers images envoyés
        images = request.FILES.getlist('image')

        # Itérer sur chaque image et les enregistrer dans la base de données
        for image_file in images:
            MediasPost.objects.create(
                post=new_post,
                image=image_file
            )
    
        user_role = request.user.rôle
        messages.success(request, 'Poste créé avec succès!')

        if user_role == 'admin':
            return redirect('Ad_posts')
        else:
            return redirect('home')
    
    return render(request, 'formulaires/post.html')

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def create_job(request):
    if request.method == 'POST':
        contenu_job = request.POST.get('contenu_job')
        title = request.POST.get('title')
    
        newJob = Job.objects.create(
            user=request.user,
            contenu_job=contenu_job, 
            title=title
            )
    
    
        user_role = request.user.rôle
        
        if user_role == 'admin':
            return redirect('Ad_posts')
        else:
            return redirect('emplois')
        
    return render(request, 'formulaires/job.html')

class AddPostule(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        job = get_object_or_404(Job, pk=pk)

        # Vérifier si l'utilisateur a déjà aimé ou n'aime pas le poste
        is_dispostule = job.dispostule.filter(pk=request.user.pk).exists()
        is_postule = job.postule_job.filter(pk=request.user.pk).exists()

        # Si l'utilisateur n'aime pas le poste, le retirer de la liste des dislikes
        if is_dispostule:
            job.dispostule.remove(request.user)

        # Si l'utilisateur n'a pas déjà aimé le poste, l'ajouter aux likes
        if not is_postule:
            job.postule_job.add(request.user)
            postule_icon = '<i class="fa fa-thumbs-up primary"></i>'
        # Si l'utilisateur a déjà aimé le poste, le retirer des likes
        else:
            job.postule_job.remove(request.user)
            postule_icon = '<i class="fa fa-thumbs-up"></i>'

        # Renvoyer les informations mises à jour
        response_data = {
            'like_count': job.postule_job.count(),
            'postule_icon': postule_icon,
        }
        
        user_role = request.user.rôle
        if user_role == 'admin':
            return redirect('Ad_job')
        else:
            return redirect('emplois')

def create_boutique(request):
    if request.method == 'POST':
        # Récupère l'utilisateur connecté
        user = request.user
        
        # Récupère les données du formulaire
        nom_boutique = request.POST.get('nom_boutique')
        devise_boutique = request.POST.get('devise_boutique')
        
        # Crée un nouvel objet Boutique
        nouvelle_boutique = Boutique.objects.create(
            user=user,
            nom_boutique=nom_boutique,
            devise_boutique=devise_boutique
        )
        
        # Redirige vers la vue pour gérer la boutique
        return redirect('En_Gestion_Boutique')
        
    return render(request, 'auth/boutique.html')

def create_product(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        description = request.POST.get('description')
        nom_produit = request.POST.get('nom_produit')
        prix = request.POST.get('prix')
        video = request.FILES.get('video')
        category = request.POST.get('category')  # Récupérer la catégorie
        images = request.FILES.getlist('image')  # Récupérer les fichiers images envoyés

        # Récupérer l'utilisateur actuel
        utilisateur = request.user
        
        # Récupérer la boutique associée à l'utilisateur actuel
        boutique = Boutique.objects.get(user=utilisateur)
        
        # Créer un nouveau produit
        new_product = Product.objects.create(
            boutique=boutique,
            description=description,
            nom_produit=nom_produit,
            prix=prix,
            video=video,
            category=category  # Ajouter la catégorie
        )
        
        # Enregistrer chaque image comme un objet MediasProduct
        for image in images:
            MediasProduct.objects.create(
                produit=new_product,
                image=image
            )
        
        # Rediriger l'utilisateur après la création du produit
        return redirect('En_Gestion_Boutique')
        
    return render(request, 'formulaires/product.html')

''' =========== CV: Update profile, Create experience, Update experience, Create Formation, Update Formation ========= '''
@role_required(['admin','personnel', 'ecole', 'entreprise'])
def a_propos(request):
    # Récupérer l'utilisateur actuel
    user = request.user
    
    # Récupérer le profil de l'utilisateur s'il existe
    try:
        profil = Profil.objects.get(user=user)
    except Profil.DoesNotExist:
        profil = None
    
    # Récupérer l'expérience de l'utilisateur s'il existe
    try:
        experience = Experience.objects.get(user=user)
    except Experience.DoesNotExist:
        experience = None
    
    # Récupérer la formation de l'utilisateur si elle existe
    try:
        formation = Formation.objects.get(user=user)
    except Formation.DoesNotExist:
        formation = None
    
    # Charger le template de mise à jour correspondant au rôle de l'utilisateur
    user_role = user.rôle
    if user_role == 'admin':
        return render(request, 'profils/a_propos.html', {'user': user, 'profil': profil, 'experience': experience, 'formation': formation})
    else:
        return render(request, 'profils/a_propos.html', {'user': user, 'profil': profil, 'experience': experience, 'formation': formation})

def update_cv_profil(request):
    if request.method == 'POST':
        # Récupérez la description mise à jour depuis le formulaire
        description = request.POST.get('description')

        # Vérifiez si l'utilisateur a un profil existant
        if hasattr(request.user, 'profil'):
            # Mettez à jour la description du profil existant
            request.user.profil.description = description
            request.user.profil.save()
        else:
            # Créez un nouveau profil si l'utilisateur n'en a pas encore
            Profil.objects.create(user=request.user, description=description)

        # Rediriger l'utilisateur vers la page 'a_propos' après la mise à jour du profil
        return redirect('a_propos')
            
    else:    
        # Récupérer le profil de l'utilisateur
        profil = getattr(request.user, 'profil', None)
        context = {'profil': profil}
        return render(request, 'formulaires/update/cv/profil.html', context)
    
def create_cv_experience(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        title = request.POST.get('title')
        description = request.POST.get('description')

        # Créer une nouvelle instance de Experience
        new_experience = Experience.objects.create(user=request.user, title=title, description=description)

        # Rediriger l'utilisateur vers une page de confirmation ou une autre vue
        return redirect('a_propos')  # Remplacez 'nom_de_la_vue_de_confirmation' par le nom de la vue de confirmation appropriée

    return render(request, 'formulaires/update/cv/experience.html')


def update_cv_experience(request, experience_id):
    # Récupérer l'expérience à modifier
    experience = get_object_or_404(Experience, id=experience_id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        title = request.POST.get('title')
        description = request.POST.get('description')

        # Mettre à jour les données de l'expérience
        experience.title = title
        experience.description = description
        experience.save()

        # Rediriger l'utilisateur vers une page de confirmation ou une autre vue
        return redirect('a_propos')  # Remplacez 'nom_de_la_vue_de_confirmation' par le nom de la vue de confirmation appropriée

    # Charger les données de l'expérience dans le formulaire
    context = {'experience': experience}
    return render(request, 'formulaires/update/cv/update_experience.html', context)

def create_cv_formation(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        title = request.POST.get('title')
        description = request.POST.get('description')

        # Créer une nouvelle instance de Experience
        new_formation = Formation.objects.create(user=request.user, title=title, description=description)

        # Rediriger l'utilisateur vers une page de confirmation ou une autre vue
        return redirect('a_propos')  # Remplacez 'nom_de_la_vue_de_confirmation' par le nom de la vue de confirmation appropriée

    return render(request, 'formulaires/update/cv/formation.html')

def update_cv_formation(request, formation_id):
    # Récupérer l'formation à modifier
    formation = get_object_or_404(Formation, id=formation_id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        title = request.POST.get('title')
        description = request.POST.get('description')

        # Mettre à jour les données de l'expérience
        formation.title = title
        formation.description = description
        formation.save()

        # Rediriger l'utilisateur vers une page de confirmation ou une autre vue
        return redirect('a_propos')  # Remplacez 'nom_de_la_vue_de_confirmation' par le nom de la vue de confirmation appropriée

    # Charger les données de l'expérience dans le formulaire
    context = {'formation': formation}
    return render(request, 'formulaires/update/cv/update_formation.html', context)

''' =========== Les Updates ========= '''
@role_required(['admin','personnel', 'ecole', 'entreprise'])
def update(request):
    user_role = request.user.rôle

    if user_role == 'entreprise':
        # Charger le modèle de mise à jour pour l'entreprise
        if request.method == 'POST':
            # Récupérer les données du formulaire POST
            metier = request.POST.get('metier')
            pays = request.POST.get('pays')
            ville = request.POST.get('ville')
            quartier = request.POST.get('quartier')
            indicatif = request.POST.get('indicatif')
            phone = request.POST.get('phone')

            # Mettre à jour les champs appropriés
            user = request.user
            user.metier = metier
            user.pays = pays
            user.ville = ville
            user.quartier = quartier
            user.indicatif_pays = indicatif
            user.number_phone = phone  
            user.save()

            # Rediriger vers le profil de l'entreprise
            return redirect('detail_profile')

        # Charger le modèle de mise à jour pour l'entreprise
        return render(request, 'formulaires/update/admin_statut.html')
    
    elif user_role == 'personnel':
        # Charger le modèle de mise à jour pour le personnel
        if request.method == 'POST':
            # Récupérer les données du formulaire POST
            metier = request.POST.get('metier')
            pays = request.POST.get('pays')
            ville = request.POST.get('ville')
            quartier = request.POST.get('quartier')
            indicatif = request.POST.get('indicatif')
            phone = request.POST.get('phone')

            # Mettre à jour les champs appropriés
            user = request.user
            user.metier = metier
            user.pays = pays
            user.ville = ville
            user.quartier = quartier
            user.indicatif_pays = indicatif
            user.number_phone = phone  
            user.save()
            return redirect('detail_profile')
        
        return render(request, 'formulaires/update/personnel_statut.html')

    elif user_role == 'ecole':
        # Charger le modèle de mise à jour pour l'école
        if request.method == 'POST':
            # Récupérer les données du formulaire POST
            metier = request.POST.get('metier')
            pays = request.POST.get('pays')
            ville = request.POST.get('ville')
            quartier = request.POST.get('quartier')
            indicatif = request.POST.get('indicatif')
            phone = request.POST.get('phone')

            # Mettre à jour les champs appropriés
            user = request.user
            user.metier = metier
            user.pays = pays
            user.ville = ville
            user.quartier = quartier
            user.indicatif_pays = indicatif
            user.number_phone = phone  
            user.save()
            
            return redirect('detail_profile')
        
        return render(request, 'formulaires/update/ecole_statut.html')

    elif user_role == 'admin':
        # Charger le modèle de mise à jour pour l'admin
        if request.method == 'POST':
            # Récupérer les données du formulaire POST
            metier = request.POST.get('metier')
            pays = request.POST.get('pays')
            ville = request.POST.get('ville')
            quartier = request.POST.get('quartier')
            indicatif = request.POST.get('indicatif')
            phone = request.POST.get('phone')

            # Mettre à jour les champs appropriés
            user = request.user
            user.metier = metier
            user.pays = pays
            user.ville = ville
            user.quartier = quartier
            user.indicatif_pays = indicatif
            user.number_phone = phone  
            user.save()
            
            return redirect('Ad_profile')
        return render(request, 'formulaires/update/admin_statut.html')

    # Si aucun rôle correspondant n'est trouvé ou si la méthode de requête n'est pas POST
    return render(request, 'path_vers_votre_template_d_erreur.html')

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def update_profile(request):
    CustomUser = request.user
    if request.method == 'POST':
        user = request.user
        new_profile_image = request.FILES.get('image')

        # Supprimer l'ancienne image de la base de données et localement
        if user.profile_image:
            old_image_path = os.path.join(settings.MEDIA_ROOT, str(user.profile_image))
            os.remove(old_image_path)

        # Enregistrer la nouvelle image dans le répertoire de stockage local
        user.profile_image = new_profile_image
        user.save()

        user_role = request.user.rôle
        
        if user_role == 'admin':
            return redirect('Ad_profile')
        else:
            return redirect('detail_profile')
        # Rediriger vers la page de profil appropriée
    else:
        return render(request, 'formulaires/update/update_profile.html', {'CustomUser': CustomUser})

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def update_banner(request):
    CustomUser = request.user
    if request.method == 'POST':
        user = request.user
        new_profile_banner = request.FILES.get('banner')

        # Supprimer l'ancienne image de la base de données et localement
        if user.banner_image:
            old_image_path = os.path.join(settings.MEDIA_ROOT, str(user.banner_image))
            os.remove(old_image_path)

        # Enregistrer la nouvelle image dans le répertoire de stockage local
        user.banner_image = new_profile_banner
        user.save()

        user_role = request.user.rôle
        
        if user_role == 'admin':
            return redirect('Ad_profile')
        else:
            return redirect('detail_profile')
        # Rediriger vers la page de profil ou toute autre page appropriée
    else:
        return render(request, 'formulaires/update/update_banner.html', {'CustomUser': CustomUser})

def update_logo_boutique(request):
    if request.method == 'POST':
        # Récupérer l'utilisateur actuellement connecté
        user = request.user

        # Récupérer la boutique associée à cet utilisateur
        boutique = Boutique.objects.get(user=user)

        # Récupérer l'image du formulaire
        image = request.FILES.get('image')

        # Mettre à jour la photo de profil de la boutique
        if image:
            # Supprimer l'ancienne image de la base de données et localement
            if boutique.photo_profil:
                old_image_path = boutique.photo_profil.path
                boutique.photo_profil.delete(save=False)

            # Enregistrer la nouvelle image dans la base de données
            boutique.photo_profil = image
            boutique.save()

        # Rediriger vers une page de confirmation ou une autre vue
        return redirect('En_Gestion_Boutique')

    # Si la méthode de requête est GET, simplement renvoyer le formulaire HTML
    return render(request, 'formulaires/update/update_logo_boutique.html')
# break

# Update Banner Boutique
def update_banner_boutique(request):
    if request.method == 'POST':
        # Récupérer l'utilisateur actuellement connecté
        user = request.user

        # Récupérer la boutique associée à cet utilisateur
        boutique = Boutique.objects.get(user=user)

        # Récupérer l'image du formulaire
        image = request.FILES.get('image')

        # Mettre à jour la photo de profil de la boutique
        if image:
            # Supprimer l'ancienne image de la base de données et localement
            if boutique.banner_image:
                old_image_path = boutique.banner_image.path
                boutique.banner_image.delete(save=False)

            # Enregistrer la nouvelle image dans la base de données
            boutique.banner_image = image
            boutique.save()

        # Rediriger vers une page de confirmation ou une autre vue
        return redirect('En_Gestion_Boutique')

    # Si la méthode de requête est GET, simplement renvoyer le formulaire HTML
    return render(request, 'formulaires/update/update_banner_boutique.html')
# break

# Update Description Boutique
def update_description_boutique(request):
    if request.method == 'POST':
        # Récupérer l'utilisateur actuellement connecté
        user = request.user

        # Récupérer la boutique associée à cet utilisateur
        boutique = Boutique.objects.get(user=user)

        
        description = request.POST.get('description')

        

        boutique.description = description
        boutique.save()

        # Rediriger vers une page de confirmation ou une autre vue
        return redirect('En_Gestion_Boutique')

    # Si la méthode de requête est GET, simplement renvoyer le formulaire HTML
    return render(request, 'formulaires/update/update_description_boutique.html')
# break

''' =========== Les Likes ========= '''       
class AddLikes(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)

        # Vérifier si l'utilisateur a déjà aimé ou n'aime pas le poste
        is_dislike = post.dislike.filter(pk=request.user.pk).exists()
        is_like = post.like_post.filter(pk=request.user.pk).exists()

        # Si l'utilisateur n'aime pas le poste, le retirer de la liste des dislikes
        if is_dislike:
            post.dislike.remove(request.user)

        # Si l'utilisateur n'a pas déjà aimé le poste, l'ajouter aux likes
        if not is_like:
            post.like_post.add(request.user)
            like_icon = '<i class="fa fa-thumbs-up primary"></i>'
        # Si l'utilisateur a déjà aimé le poste, le retirer des likes
        else:
            post.like_post.remove(request.user)
            like_icon = '<i class="fa fa-thumbs-up"></i>'

        # Renvoyer les informations mises à jour
        response_data = {
            'like_count': post.like_post.count(),
            'like_icon': like_icon,
        }
        return JsonResponse(response_data)
    
def suivre_utilisateur(request, user_id):
    if request.method == 'POST':
        # Récupérer l'utilisateur cible
        user_to_follow = get_object_or_404(CustomUser, pk=user_id)
        
        # Vérifier si l'utilisateur actuel suit déjà l'utilisateur cible
        if user_to_follow.followers.filter(id=request.user.id).exists():
            # Si oui, le retirer des followers
            user_to_follow.followers.remove(request.user)
            following = False
        else:
            # Sinon, l'ajouter aux followers
            user_to_follow.followers.add(request.user)
            following = True
        
        # Préparer les données de réponse
        response_data = {
            'following': following,
            'user_id': user_id,
        }

        return JsonResponse(response_data)

''' =========== Les Details (Profils, Post, Emplois) ========= '''
def detail_profile(request):
    user = request.user
    total_likes_received = user.total_likes_received()

    # Récupérer tous les posts de l'utilisateur
    posts = Post.objects.filter(user=user)

    return render(request, 'profils/user.html', {
        'user': user, 
        'total_likes_received': total_likes_received,
        'posts': posts  # Passer les postes au template
    })

def user_detail(request, user_id):
    profile_user = get_object_or_404(CustomUser, pk=user_id)
    posts = Post.objects.filter(user=profile_user)  # Récupère tous les posts de cet utilisateur
    return render(request, 'profils/users_public.html', {'profile_user': profile_user, 'posts': posts})

def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    return render(request, 'details/job.html', {'job': job})

@role_required(['entreprise'])
def En_Gestion_Boutique(request):
    try:
        # Récupérer la boutique associée à l'utilisateur connecté
        user_boutique = Boutique.objects.get(user=request.user)
        
        # Récupérer les produits associés à cette boutique
        produits = Product.objects.filter(boutique=user_boutique)

        # Afficher les informations dans la page profil boutique
        return render(request, 'profils/boutique.html', {
            'user_boutique': user_boutique,
            'produits': produits
        })
    
    except Boutique.DoesNotExist:
        # Rediriger vers la page de création de boutique si elle n'existe pas
        return redirect('create_boutique')

def postulant(request):
    # Récupérer toutes les offres postées par l'utilisateur connecté
    user_jobs = Job.objects.filter(user=request.user)  # Assurez-vous que `user` est le champ qui stocke l'utilisateur qui a posté l'offre

    # Récupérer tous les postulants pour les offres de l'utilisateur connecté
    postulants = {}
    for job in user_jobs:
        postulants[job] = job.postule_job.all()

    context = {
        'postulants': postulants,
    }
    
    return render(request, 'details/postulant.html', context)

def vos_postule(request):
    # Récupérer les postulations de l'utilisateur connecté
    postulations = Job.objects.filter(postule_job=request.user)
    
    context = {
        'postulations': postulations,
    }
    
    return render(request, 'details/vos_postules.html', context)

def product_detail(request, product_id):
    # Récupérer le produit spécifique
    produit = Product.objects.select_related('boutique').get(id=product_id)

    # Récupérer d'autres produits de la même catégorie
    produits_meme_categorie = Product.objects.filter(category=produit.category).exclude(id=product_id)[:10]

    context = {
        'produit': produit,
        'produits_meme_categorie': produits_meme_categorie
    }
    return render(request, 'details/product.html', context)

def vos_commande(request):
    # Récupérer les commandes de l'utilisateur connecté
    commandes = Commande.objects.filter(user=request.user)
    
    context = {
        'commandes': commandes,
    }
    
    return render(request, 'Details/Vos_commandes.html', context)

def les_commandes(request):
    # Récupérer toutes les commandes de l'utilisateur connecté
    commandes = Commande.objects.filter(user=request.user)
    
    context = {
        'commandes': commandes,
    }
    
    return render(request, 'details/commandes.html', context)

def amis(request):
    # Récupérer l'utilisateur connecté
    current_user = request.user

    # Récupérer ceux que l'utilisateur suit et ceux qui le suivent
    following = current_user.get_following()
    followers = current_user.get_followers()

    # Trouver les amis mutuels (ceux que l'utilisateur suit et qui le suivent)
    mutual_friends = set(following).intersection(set(followers))

    # Récupérer la valeur du champ de recherche
    search_query = request.GET.get('search', '')

    if search_query:
        # Appliquer le filtre sur les utilisateurs suivis (following)
        following = following.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(etablissement__icontains=search_query)
        )

        # Appliquer le filtre sur les utilisateurs qui suivent l'utilisateur (followers)
        followers = followers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(etablissement__icontains=search_query)
        )

        # Filtrer les amis mutuels manuellement (car intersection() convertit en set)
        mutual_friends = [friend for friend in mutual_friends if
                          search_query.lower() in friend.first_name.lower() or
                          search_query.lower() in friend.last_name.lower() or
                          search_query.lower() in (friend.etablissement or '').lower()]

    context = {
        'following': following,
        'followers': followers,
        'mutual_friends': mutual_friends,
        'search_query': search_query,
    }

    return render(request, 'details/amis.html', context)

def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'details/post.html', {'post': post})

@role_required(['admin','personnel', 'ecole', 'entreprise'])
def post_comments(request, post_id):
    
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)  # Utilisation de id=post_id pour récupérer le post
        contenu_commentaire = request.POST.get('contenu_commentaire')
        image = request.FILES.get('image')
        
        # Créez un nouvel objet Commentaire avec les données soumises
        commentaire = Commentaire.objects.create(post=post, user=request.user, contenu_commentaire=contenu_commentaire, image=image)
        
        # Redirigez l'utilisateur vers la même page ou une autre page appropriée
        #return redirect('detail_post', post_id=post_id)
    
    post = get_object_or_404(Post, id=post_id)
    comments = Commentaire.objects.filter(post=post)
    return render(request, 'Commentaire/comment_post.html', {'post': post, 'comments': comments})

# ========== Les Réponses: Commentaires ===================
@role_required(['admin','personnel', 'ecole', 'entreprise'])
def comment_responses(request, comment_id):
    
    if request.method == 'POST':
        comment = get_object_or_404(Commentaire, id=comment_id)
        contenu_text = request.POST.get('contenu_text')
        image = request.FILES.get('image')
        
        reponse = Reponse.objects.create(commentaire=comment, user=request.user, contenu_text=contenu_text, image=image)
    
    comment = get_object_or_404(Commentaire, id=comment_id)
    responses = Reponse.objects.filter(commentaire_id=comment.id)
    return render(request, 'Commentaire/response.html', {'comment': comment, 'responses': responses})


def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
def a_propos_detail(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    context = {'user': user}
    
    if user.rôle == 'personnel':
        template_name = 'profils/a_propos_public.html'
        context['profil'] = get_or_none(Profil, user=user)
        context['experience'] = get_or_none(Experience, user=user)
        context['formation'] = get_or_none(Formation, user=user)
    elif user.rôle == 'entreprise':
        template_name = 'profils/a_propos_public.html'
        context['profil'] = get_or_none(Profil, user=user)
        context['experience'] = get_or_none(Experience, user=user)
        # Ajoutez les données spécifiques à l'entreprise au besoin
    elif user.rôle == 'ecole':
        template_name = 'profils/a_propos_public.html'
        context['profil'] = get_or_none(Profil, user=user)
        context['experience'] = get_or_none(Experience, user=user)
        context['formation'] = get_or_none(Formation, user=user)
        # Ajoutez les données spécifiques à l'école au besoin
    else:
        # Gérer le cas où le rôle n'est pas reconnu
        template_name = 'profils/a_propos_public.html'
    
    return render(request, template_name, context)

''' =========== Paramétres ========= '''
def Settings_profil(request):
    CustomUser = request.user
    return render(request, 'parameter/links.html', {'CustomUser': CustomUser})

def settingEmail(request):
    if request.method == 'POST':
        form = EmailChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            logout(request)
            return redirect('login')
    else:
        form = EmailChangeForm(instance=request.user)
    
    return render(request, 'parameter/updates/email.html', {'form': form})

def settingNames(request):
    if request.method == 'POST':
        form = NameChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            user_role = request.user.rôle
            if user_role == 'admin':
                return redirect('Ad_profile')
            elif user_role == 'personnel':
                return redirect('Per_profile')
            elif user_role == 'ecole':
                return redirect('Ec_profile')
            elif user_role == 'entreprise':
                return redirect('En_profile')
    else:
        form = NameChangeForm(instance=request.user)
    
    return render(request, 'parameter/updates/names.html', {'form': form, 'CustomUser': request.user})

def settingRole(request):
    if request.method == 'POST':
        form = RoleChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            update_session_auth_hash(request, user)
            return redirect('logout')  # Redirection vers la déconnexion après le changement de rôle
    else:
        form = RoleChangeForm(instance=request.user)
    
    return render(request, 'parameter/updates/role.html', {'form': form})

def settingPassWord(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Met à jour le hachage du mot de passe dans la session
            logout(request)  # Déconnecte l'utilisateur
            return redirect('login')  # Redirige vers la page de connexion après modification du mot de passe
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'parameter/updates/password.html', {'form': form})

def settingDelete(request):
    if request.method == 'POST':
        form = AccountDeleteForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            user = request.user
            if user.check_password(password):
                user.delete()
                return redirect('login')  # Rediriger vers la page de connexion après suppression du compte
            else:
                form.add_error('password', "Mot de passe incorrect.")
    else:
        form = AccountDeleteForm()
    
    return render(request, 'parameter/updates/delete.html', {'form': form})