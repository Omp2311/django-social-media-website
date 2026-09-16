from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Post, LikePost, FollowersCount
from itertools import chain
import random


@login_required(login_url='signin')
def index(request):
    user_object = request.user

    user_profile, created = Profile.objects.get_or_create(
        user=user_object,
        defaults={
            'id_user': user_object.id
        }
    )

    user_following_list = []
    feed = []

    user_following = FollowersCount.objects.filter(
        follower=request.user.username
    )

    for users in user_following:
        user_following_list.append(users.user)

    for username in user_following_list:
        feed_lists = Post.objects.filter(user=username)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    # User suggestions
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        followed_user = User.objects.filter(
            username=user.user
        ).first()

        if followed_user:
            user_following_all.append(followed_user)

    new_suggestions_list = [
        user
        for user in all_users
        if user not in user_following_all
        and user != request.user
    ]

    random.shuffle(new_suggestions_list)

    suggestions_username_profile_list = []

    for suggested_user in new_suggestions_list:
        profile, created = Profile.objects.get_or_create(
            user=suggested_user,
            defaults={
                'id_user': suggested_user.id
            }
        )

        suggestions_username_profile_list.append(profile)

    context = {
        'user_profile': user_profile,
        'posts': feed_list,
        'suggestions_username_profile_list':
            suggestions_username_profile_list[:4]
    }

    return render(request, 'index.html', context)


@login_required(login_url='signin')
def upload(request):

    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST.get('caption', '')

        Post.objects.create(
            user=user,
            image=image,
            caption=caption
        )

    return redirect('/')


@login_required(login_url='signin')
def search(request):
    user_object = request.user

    user_profile, created = Profile.objects.get_or_create(
        user=user_object,
        defaults={
            'id_user': user_object.id
        }
    )

    username_profile_list = []

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        username_object = User.objects.filter(
            username__icontains=username
        )

        for user in username_object:
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'id_user': user.id
                }
            )

            username_profile_list.append(profile)

    context = {
        'user_profile': user_profile,
        'username_profile_list': username_profile_list
    }

    return render(request, 'search.html', context)


@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    if not post_id:
        return redirect('/')

    post = Post.objects.filter(id=post_id).first()

    if not post:
        return redirect('/')

    like_filter = LikePost.objects.filter(
        post_id=post_id,
        username=username
    ).first()

    if like_filter is None:
        LikePost.objects.create(
            post_id=post_id,
            username=username
        )

        post.no_of_likes = post.no_of_likes + 1
        post.save()

    else:
        like_filter.delete()

        if post.no_of_likes > 0:
            post.no_of_likes = post.no_of_likes - 1

        post.save()

    return redirect('/')


@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.filter(
        username=pk
    ).first()

    if not user_object:
        return redirect('/')

    user_profile, created = Profile.objects.get_or_create(
        user=user_object,
        defaults={
            'id_user': user_object.id
        }
    )

    user_posts = Post.objects.filter(user=pk)

    user_post_length = user_posts.count()

    follower = request.user.username
    user = pk

    follow_exists = FollowersCount.objects.filter(
        follower=follower,
        user=user
    ).exists()

    if follow_exists:
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_followers = FollowersCount.objects.filter(
        user=pk
    ).count()

    user_following = FollowersCount.objects.filter(
        follower=pk
    ).count()

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }

    return render(request, 'profile.html', context)


@login_required(login_url='signin')
def follow(request):

    if request.method != 'POST':
        return redirect('/')

    follower = request.POST.get('follower')
    user = request.POST.get('user')

    if not follower or not user:
        return redirect('/')

    follow_object = FollowersCount.objects.filter(
        follower=follower,
        user=user
    ).first()

    if follow_object:
        follow_object.delete()
    else:
        FollowersCount.objects.create(
            follower=follower,
            user=user
        )

    return redirect('/profile/' + user)


@login_required(login_url='signin')
def settings(request):

    user_profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            'id_user': request.user.id
        }
    )

    if request.method == 'POST':

        image = request.FILES.get('image')
        bio = request.POST.get('bio', '')
        location = request.POST.get('location', '')

        if image is not None:
            user_profile.profileimg = image

        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

        return redirect('settings')

    return render(
        request,
        'setting.html',
        {
            'user_profile': user_profile
        }
    )


def signup(request):

    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get(
            'username',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        password2 = request.POST.get(
            'password2',
            ''
        )

        if not username or not email or not password:
            messages.info(
                request,
                'All fields are required'
            )

            return redirect('signup')

        if password != password2:
            messages.info(
                request,
                'Password Not Matching'
            )

            return redirect('signup')

        if User.objects.filter(
            email=email
        ).exists():

            messages.info(
                request,
                'Email Taken'
            )

            return redirect('signup')

        if User.objects.filter(
            username=username
        ).exists():

            messages.info(
                request,
                'Username Taken'
            )

            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Profile.objects.get_or_create(
            user=user,
            defaults={
                'id_user': user.id
            }
        )

        user_login = auth.authenticate(
            username=username,
            password=password
        )

        if user_login is not None:
            auth.login(
                request,
                user_login
            )

            return redirect('settings')

        messages.info(
            request,
            'Account created. Please login.'
        )

        return redirect('signin')

    return render(request, 'signup.html')


def signin(request):

    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get(
            'username',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        user = auth.authenticate(
            username=username,
            password=password
        )

        if user is not None:

            # Important:
            # Creates missing profile for old/admin users.
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'id_user': user.id
                }
            )

            auth.login(
                request,
                user
            )

            return redirect('/')

        messages.info(
            request,
            'Credentials Invalid'
        )

        return redirect('signin')

    return render(request, 'signin.html')


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)

    return redirect('signin')