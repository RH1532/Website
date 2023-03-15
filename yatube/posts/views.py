from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, Follow, User

POSTS_PER_PAGE = 10


def page_obj(object, request):
    return Paginator(object, POSTS_PER_PAGE).get_page(request.GET.get('page'))


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': page_obj(Post.objects.all(), request),
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_obj(group.posts.all(), request),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (
        request.user.is_authenticated
        and request.user != author
        and Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    )
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': page_obj(author.posts.all(), request),
        'following': following
    })


def post_detail(request, post_id):
    return render(request, 'posts/post_detail.html', {
        'post': get_object_or_404(
            Post,
            id=post_id,
        ),
        'form': CommentForm(request.POST or None)
    })


@login_required
def post_create(request):
    form = PostForm(
        data=request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
        })
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(
        request,
        'posts/create_post.html', {
            'form': form,
            'post': post,
        }
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    return render(
        request,
        'posts/follow.html',
        {
            'page_obj': page_obj(
                Post.objects.filter(author__following__user=request.user),
                request
            )
        }
    )


@login_required
def profile_follow(request, username):
    if username != request.user.username:
        Follow.objects.get_or_create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    ).delete()
    return redirect('posts:profile', username=username)
