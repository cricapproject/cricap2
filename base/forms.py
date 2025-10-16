from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Response, RESPONSE_CHOICES
from .models import DataDiri
from .models import Kecamatan
from .models import Desa

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        # 🚀 Jika emailnya adalah akun utama, jadikan superuser
        if user.email.lower().strip() == "cricapproject@gmail.com":
            user.is_superuser = True
            user.is_staff = True  # penting agar bisa akses admin panel

        if commit:
            user.save()
        return user


# Form untuk mengumpulkan jawaban responden
class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['response']
        widgets = {
            'response': forms.RadioSelect(choices=RESPONSE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        # Menambahkan pertanyaan ke form untuk identifikasi
        self.question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)


class DataDiriForm(forms.ModelForm):
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)

    kecamatan = forms.ModelChoiceField(
        queryset=Kecamatan.objects.all(),
        label="Pilih Kecamatan",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_kecamatan'})
    )

    desa = forms.ModelChoiceField(
        queryset=Desa.objects.none(),  # awalnya kosong, nanti diisi via JS/Ajax
        label="Pilih Desa/Kelurahan",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_desa'})
    )

    class Meta:
        model = DataDiri
        fields = [
            'nama',
            'usia',
            'jenis_kelamin',
            'status_perkawinan',
            'pendidikan',
            'alamat',
            'kecamatan',
            'desa',
            'pekerjaan',
            'latitude',
            'longitude',
        ]
        widgets = {
            'jenis_kelamin': forms.RadioSelect(),
            'status_perkawinan': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Hilangkan '---------' dari dropdown pendidikan & pekerjaan
        for field in ['pendidikan', 'pekerjaan']:
            if hasattr(self.fields[field], 'empty_label'):
                self.fields[field].empty_label = None

        # Kalau instance sudah ada kecamatan, isi queryset desa sesuai kecamatan
        if 'kecamatan' in self.data:
            try:
                kecamatan_id = int(self.data.get('kecamatan'))
                self.fields['desa'].queryset = Desa.objects.filter(kecamatan_id=kecamatan_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.kecamatan:
            self.fields['desa'].queryset = self.instance.kecamatan.desa_list.all()
