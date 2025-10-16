from django.db import models
from django.contrib.auth.models import User

# Pilihan untuk response
RESPONSE_CHOICES = [
    ('SS', 'Sangat Setuju'),
    ('S', 'Setuju'),
    ('R', 'Ragu-Ragu'),
    ('TS', 'Tidak Setuju'),
    ('STS', 'Sangat Tidak Setuju')
]

class Section(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Question(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return f"{self.section.title} - {self.text}"


class SubQuestion(models.Model):
    main_question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="sub_questions"
    )
    text = models.TextField()

    def __str__(self):
        return f"{self.main_question.text} - {self.text}"


class Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sub_question = models.ForeignKey(SubQuestion, on_delete=models.CASCADE)
    response = models.CharField(max_length=3, choices=RESPONSE_CHOICES)

    def __str__(self):
        return f'{self.user.username} - {self.sub_question.text} - {self.get_response_display()}'


class Kecamatan(models.Model):
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama


class Desa(models.Model):
    kecamatan = models.ForeignKey(Kecamatan, on_delete=models.CASCADE, related_name="desa_list")
    nama = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nama} (Kec. {self.kecamatan.nama})"


class DataDiri(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100, blank=True, null=True)
    usia = models.IntegerField()

    jenis_kelamin = models.CharField(
        max_length=15,
        choices=[("Laki-laki", "Laki-laki"), ("Perempuan", "Perempuan")],
        default="Laki-laki"
    )

    status_perkawinan = models.CharField(
        max_length=20,
        choices=[
            ("Belum berkeluarga", "Belum berkeluarga"),
            ("Duda", "Duda"),
            ("Janda", "Janda"),
            ("Berkeluarga", "Berkeluarga"),
        ],
        default="Belum berkeluarga"
    )

    pendidikan = models.CharField(
        max_length=20,
        choices=[
            ("SLTP", "SLTP"),
            ("SLTA", "SLTA"),
            ("Diploma", "Diploma"),
            ("Sarjana", "Sarjana"),
            ("Pascasarjana", "Pascasarjana"),
        ]
    )
    alamat = models.CharField(max_length=100)
    kecamatan = models.ForeignKey(Kecamatan, on_delete=models.SET_NULL, null=True, blank=True)
    desa = models.ForeignKey(Desa, on_delete=models.SET_NULL, null=True, blank=True)

    pekerjaan = models.CharField(
        max_length=120,
        choices=[
            ("ASN/TNI/Polri/Pegawai BUMN", "ASN/TNI/Polri/Pegawai BUMN"),
            ("Karyawan swasta/Profesional non PNS", "Karyawan swasta/Profesional non PNS (dokter, notaris, pengacara, konsultan, dosen, arsitek)"),
            ("Pengusaha/Pedagang/Kontraktor", "Pengusaha/Pedagang/Kontraktor"),
            ("Buruh harian/Ojek Online/Petani/Nelayan/Peternak/Freelancer", "Buruh harian/Ojek Online/Petani/Nelayan/Peternak/Freelancer"),
            ("IRT/Pelajar/Mahasiswa/Belum (Tidak) Bekerja", "IRT/Pelajar/Mahasiswa/Belum (Tidak) Bekerja"),
        ]
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.nama or 'Anonim'} - {self.usia} Tahun"


class IRKResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=150, null=True, blank=True)      # snapshot nama
    pekerjaan = models.CharField(max_length=120, null=True, blank=True)  # snapshot pekerjaan
    kecamatan = models.CharField(max_length=150, null=True, blank=True)  # snapshot kecamatan (nama)
    desa = models.CharField(max_length=150, null=True, blank=True)       # snapshot desa (nama)
    irk = models.FloatField(null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.nama} - {self.pekerjaan} - {self.kecamatan}/{self.desa} - IRK: {self.irk} - {self.category} ({self.created_at})"
