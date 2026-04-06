from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import UserFact, UserProfile

User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        label='Nombre',
        widget=forms.TextInput(attrs={'placeholder': 'Nombre', 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        max_length=150,
        label='Apellido',
        widget=forms.TextInput(attrs={'placeholder': 'Apellido', 'autocomplete': 'family-name'}),
    )
    sex = forms.ChoiceField(
        choices=UserProfile.SEX_CHOICES,
        label='Sexo',
        required=False,
    )
    birth_date = forms.DateField(
        label='Fecha de nacimiento',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.sex = self.cleaned_data.get('sex', '')
            profile.birth_date = self.cleaned_data.get('birth_date')
            profile.save()
        return user

_input_cls = 'input input-bordered w-full'
_textarea_cls = 'textarea textarea-bordered w-full'


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['system_prompt', 'assistant_name', 'avatar_emoji']
        widgets = {
            'system_prompt': forms.Textarea(attrs={
                'class': _textarea_cls,
                'rows': 4,
                'placeholder': 'Ej: Eres un pirata divertido que habla con muchos "¡Arrr!" y te llamas Barbanegra.',
            }),
            'assistant_name': forms.TextInput(attrs={
                'class': _input_cls,
                'placeholder': 'Ej: Barbanegra',
            }),
            'avatar_emoji': forms.TextInput(attrs={
                'class': _input_cls,
                'placeholder': '🤖',
                'maxlength': '10',
            }),
        }


class UserFactForm(forms.ModelForm):
    class Meta:
        model = UserFact
        fields = ['category', 'key', 'value']
        widgets = {
            'category': forms.TextInput(attrs={
                'class': _input_cls,
                'placeholder': 'Ej: amigo, color, tema',
            }),
            'key': forms.TextInput(attrs={
                'class': _input_cls,
                'placeholder': 'Ej: Mejor amigo',
            }),
            'value': forms.TextInput(attrs={
                'class': _input_cls,
                'placeholder': 'Ej: Carlos',
            }),
        }
