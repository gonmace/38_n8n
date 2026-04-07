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
        fields = [
            'system_prompt', 'assistant_name', 'avatar_emoji',
            'use_structured_prompt',
            'prompt_rol', 'prompt_contexto', 'prompt_comportamiento',
            'prompt_formato', 'prompt_restricciones',
        ]
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
            'prompt_rol': forms.Textarea(attrs={
                'class': _textarea_cls, 'rows': 3,
                'placeholder': 'Ej: Eres un experto en nutrición infantil con 10 años de experiencia. Tu nombre es Nutri y eres amable y paciente.',
            }),
            'prompt_contexto': forms.Textarea(attrs={
                'class': _textarea_cls, 'rows': 3,
                'placeholder': 'Ej: Asistes a padres de familia en la app NutriKids. Ayudas a planificar comidas saludables para niños de 3 a 12 años.',
            }),
            'prompt_comportamiento': forms.Textarea(attrs={
                'class': _textarea_cls, 'rows': 3,
                'placeholder': 'Ej: Responde siempre con empatía. Usa lenguaje simple. Sugiere consultar al pediatra para casos médicos.',
            }),
            'prompt_formato': forms.Textarea(attrs={
                'class': _textarea_cls, 'rows': 3,
                'placeholder': 'Ej: Respuestas cortas (máx 3 párrafos). En español. Usa listas cuando sea útil. Sin markdown excesivo.',
            }),
            'prompt_restricciones': forms.Textarea(attrs={
                'class': _textarea_cls, 'rows': 3,
                'placeholder': 'Ej: No diagnostiques enfermedades. No recomiendes suplementos sin base médica. No hables de política.',
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
