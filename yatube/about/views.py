from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import CreationForm


class AboutAuthorView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:author')
    template_name = 'about/author.html'


class AboutTechView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:tech')
    template_name = 'about/tech.html'
