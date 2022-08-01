from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow

from .forms import PostForm, CommentForm

quantity_posts: int = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    template_index = 'posts/index.html'
    posts_index = Post.objects.all()
    paginator_index = Paginator(posts_index, quantity_posts)
    page_number_index = request.GET.get('page')
    page_obj_index = paginator_index.get_page(page_number_index)
    context_index = {
        'posts': posts_index,
        'page_obj': page_obj_index,
    }
    return render(request, template_index, context_index)


def group_posts(request, slug):
    template_group = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts_group = group.posts.all()
    paginator_group = Paginator(posts_group, quantity_posts)
    page_number_group = request.GET.get('page')
    page_obj_group = paginator_group.get_page(page_number_group)
    context_group = {
        'group': group,
        'posts': posts_group,
        'page_obj': page_obj_group,
    }
    return render(request, template_group, context_group)


def profile(request, username):
    template_profile = 'posts/profile.html'
    profile = get_object_or_404(User, username=username)
    posts_profile = profile.posts_for_author.all()
    paginator_profile = Paginator(posts_profile, quantity_posts)
    page_number_profile = request.GET.get('page')
    page_obj_profile = paginator_profile.get_page(page_number_profile)
    following = False
    if (
        request.user.is_authenticated
    ) and (profile.following.filter(user=request.user)):
        following = True
    context_profile = {
        'profile': profile,
        'posts': posts_profile,
        'page_obj': page_obj_profile,
        'following': following
    }
    return render(request, template_profile, context_profile)


def post_detail(request, post_id):
    template_post_detail = 'posts/post_detail.html'
    post_for_id = Post.objects.get(id=post_id)
    form_comment = CommentForm()
    comments_post = post_for_id.comments.all()
    context_post_detail = {
        'posts': post_for_id,
        'form': form_comment,
        'comments': comments_post
    }
    return render(request, template_post_detail, context_post_detail)


@login_required
def post_create(request):
    template_post_create = 'posts/create_post.html'
    template_successful = 'posts:profile'
    form_post_create = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    context_post_create = {
        'form': form_post_create,
    }
    if request.method == 'POST':
        if form_post_create.is_valid():
            post = form_post_create.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(template_successful, request.user.username)

        return render(request, template_post_create, context_post_create)
    return render(request, template_post_create, context_post_create)


@login_required
def post_edit(request, post_id):
    template_post_edit = 'posts/create_post.html'
    template_successful = 'posts:post_detail'
    post_for_id = get_object_or_404(Post, id=post_id)
    if request.user != post_for_id.author:
        return redirect(template_successful, post_id=post_id)
    form_post_edit = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post_for_id
    )
    context_post_edit = {
        'form': form_post_edit,
        'post': post_for_id,
        'is_edit': True,
    }
    if request.method == 'POST':
        if form_post_edit.is_valid():
            form_post_edit.save()
            return redirect(template_successful, post_id=post_id)

        return render(request, template_post_edit, context_post_edit)

    return render(request, template_post_edit, context_post_edit)


@login_required
def add_comment(request, post_id):
    template_add_comment = 'posts:post_detail'
    post_for_id = get_object_or_404(Post, id=post_id)
    form_add_comment = CommentForm(request.POST or None)
    if form_add_comment.is_valid():
        comment = form_add_comment.save(commit=False)
        comment.author = request.user
        comment.post = post_for_id
        comment.save()
    return redirect(template_add_comment, post_id=post_id)


@login_required
def follow_index(request):
    template_follow_index = 'posts/follow.html'
    follow_posts = Post.objects.filter(author__following__user=request.user)
    paginator_follow = Paginator(follow_posts, quantity_posts)
    page_number_follow = request.GET.get('page')
    page_obj_follow = paginator_follow.get_page(page_number_follow)
    context = {
        'posts': follow_posts,
        'page_obj': page_obj_follow,
    }
    return render(request, template_follow_index, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user == author:
        return redirect('posts:profile', username=username)
    if author != user:
        Follow.objects.get_or_create(
            author=author,
            user=request.user
        )
        return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following_user = Follow.objects.filter(
        user=request.user,
        author=author
    )
    following_user.delete()
    return redirect('posts:profile', username=username)
