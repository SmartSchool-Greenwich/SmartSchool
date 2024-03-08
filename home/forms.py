from django import forms
from .models import Comment, ContributionFiles

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment',]
class FileForm(forms.ModelForm):
    class Meta:
        model = ContributionFiles
        fields = ['word', 'img']          