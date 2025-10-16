from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse, JsonResponse
import requests
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
import folium
import pandas as pd
import geopandas as gpd
from django.db.models import Count, Avg
from django.db.models import Sum, FloatField, ExpressionWrapper
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages

from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegistrationForm, DataDiriForm
from .models import Question, Response, Section, SubQuestion, DataDiri, IRKResult, Desa, Kecamatan

# -------------------------------
# News & Home
# -------------------------------@login_required
def news_view(request):
    url = 'https://newsapi.org/v2/everything?q=keuangan&apiKey=e5cac2437c82460babf1d584b37eb92c'
    try:
        response = requests.get(url, timeout=4)
        data = response.json()
        articles = data.get('articles', [])
    except Exception:
        articles = []
    return render(request, 'news.html', {'articles': articles})


def home(request):
    url = 'https://newsapi.org/v2/everything?q=keuangan&apiKey=e5cac2437c82460babf1d584b37eb92c'
    try:
        response = requests.get(url, timeout=4)
        data = response.json()
        articles = data.get('articles', [])[:3]
    except Exception:
        articles = []
    return render(request, 'home.html', {'articles': articles})
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.shortcuts import redirect

def logout_view(request):
    auth_logout(request)
    messages.success(request, "Anda berhasil logout.")
    return redirect('login')

# -------------------------------
# Auth
# -------------------------------
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register_view.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            if user.is_superuser:
                return redirect('dashboard-home')  # admin -> dashboard admin
            else:
                return redirect('survey_user')     # user biasa -> survey_user
    else:
        form = AuthenticationForm()

    return render(request, 'login_view.html', {'form': form})


from django.contrib.auth.decorators import login_required

@login_required
def dashboard_home_view(request):
    # 🔒 Cegah akses user biasa
    if not request.user.is_superuser:
        messages.warning(request, "Anda tidak memiliki akses ke halaman dashboard admin.")
        return redirect('survey')  # arahkan ke halaman lain sesuai kebutuhanmu

    # Jika admin -> tampilkan dashboard
    irk_results = IRKResult.objects.all().order_by('-id')
    results_with_name = [
        {
            'nama': result.nama or "-",
            'irk': result.irk,
            'category': result.category,
            'kecamatan': result.kecamatan or "-",
            'desa': result.desa or "-"
        }
        for result in irk_results
    ]

    total_rendah = sum(1 for r in results_with_name if r['category'] == 'Rendah')
    total_sedang = sum(1 for r in results_with_name if r['category'] == 'Sedang')
    total_tinggi = sum(1 for r in results_with_name if r['category'] == 'Tinggi')

    return render(request, 'dashboard_home.html', {
        'results_with_name': results_with_name,
        'total_rendah': total_rendah,
        'total_sedang': total_sedang,
        'total_tinggi': total_tinggi,
    })

# -------------------------------
# Dashboard & Report untuk USER BIASA
# -------------------------------
@login_required
def dashboard_home_user_view(request):
    # 🔒 Cegah akses admin
    if request.user.is_superuser:
        messages.warning(request, "Halaman ini hanya untuk pengguna biasa.")
        return redirect('dashboard-home')  # admin diarahkan ke dashboard admin

    # Ambil data IRK user
    user_results = IRKResult.objects.filter(user=request.user).order_by('-id')
    results_with_name = [
        {
            'nama': result.nama or "-",
            'irk': result.irk,
            'category': result.category,
            'kecamatan': result.kecamatan or "-",
            'desa': result.desa or "-"
        }
        for result in user_results
    ]

    return render(request, 'dashboard_home_user.html', {
        'results_with_name': results_with_name,
        'total_survey': len(results_with_name),
        'category': results_with_name[0]['category'] if results_with_name else "Belum Ada Data",
    })


@login_required
def report_user_view(request):
    if request.user.is_superuser:
        messages.warning(request, "Halaman ini hanya untuk pengguna biasa.")
        return redirect('report_user')

    context = calculate_average_response(request)

    context = calculate_average_response(request)

    report_context = {
        # 🔹 Data pribadi pengguna
        "nama": context["nama"],
        "usia": context["usia"],
        "pekerjaan": context["pekerjaan"],
        "irk": context["irk"],
        "category": context["category"],
        "latitude": context["latitude"],
        "longitude": context["longitude"],

        # 🔹 Data statistik dan visualisasi
        "pekerjaan_distribution": context["pekerjaan_distribution"],
        "avg_irk_pekerjaan": context["avg_irk_pekerjaan"],
        "avg_irk_all": context["avg_irk_all"],
        "pekerjaan_percentage": context["pekerjaan_percentage"],
        "avg_irk_per_pekerjaan": context["avg_irk_per_pekerjaan"],
        "pie_labels": context["pie_labels"],
        "pie_values": context["pie_values"],
        "samples_kecamatan": context["samples_kecamatan"],
        "samples_desa": context["samples_desa"],
        "map_html": context["map_html"],
        "level": context["level"],
        "total_orang": context["total_orang"],
    }

    return render(request, "report_user.html", report_context)

@login_required
def survey_user_view(request):
    # Cegah akses admin
    if request.user.is_superuser:
        messages.warning(request, "Halaman ini hanya untuk pengguna biasa.")
        return redirect('survey')

    # Kalau user biasa → tampilkan halaman survei user
    return render(request, 'survey_user.html')


# -------------------------------
# Maps & Reports
# -------------------------------
@login_required
def map_views(request):
    template = loader.get_template('map_view.html')
    return HttpResponse(template.render())

# -------------------------------
# Survey
# -------------------------------
@login_required
def survey_views(request):
    return render(request, 'survey.html', {'user': request.user.username})

@login_required
def survey_1_views(request):
    template = loader.get_template('survey_1.html')
    return HttpResponse(template.render())

@login_required
def survey_2_views(request):
    template = loader.get_template('survey_2.html')
    return HttpResponse(template.render())

@login_required
def load_desa(request):
    kecamatan_id = request.GET.get('kecamatan')
    desa = Desa.objects.filter(kecamatan_id=kecamatan_id).values('id', 'nama')
    return JsonResponse(list(desa), safe=False)

@login_required
def get_desa_by_kecamatan(request, kecamatan_id):
    desa_list = Desa.objects.filter(kecamatan_id=kecamatan_id).values("id", "nama")
    return JsonResponse(list(desa_list), safe=False)

@login_required
def survey_3_views(request):
    user = request.user
    if request.method == "POST":
        form = DataDiriForm(request.POST)
        if form.is_valid():
            data_diri = form.save(commit=False)
            data_diri.user = user
            data_diri.save()
            return redirect('survey_4')
    else:
        form = DataDiriForm()
    return render(request, 'survey_3.html', {'form': form})

@login_required
def survey_4_views(request):
    section = Section.objects.all()
    main_question = Question.objects.all()
    sub_questions = SubQuestion.objects.all()

    if request.method == 'POST':
        for sub_question in sub_questions:
            response_value = request.POST.get(f'question_{sub_question.id}')
            if response_value:
                response, created = Response.objects.get_or_create(
                    user=request.user,
                    sub_question=sub_question,
                    defaults={'response': response_value}
                )
                if not created:
                    response.response = response_value
                    response.save()

        # ⬇️ Langsung hitung rata-rata setelah survei selesai
        return redirect('rata_rata_copy')

    context = {
        'section': section,
        'main_question': main_question,
        'sub_questions': sub_questions,
        'username': request.user.username
    }
    return render(request, 'survey_4.html', context)


# -------------------------------
# Distribusi Pekerjaan
# -------------------------------

def get_pekerjaan_distribution():
    data = (
        DataDiri.objects
        .values("pekerjaan")
        .annotate(count=Count("id"))
        .order_by("pekerjaan")
    )
    total = sum(d["count"] for d in data)
    return [
        {
            "pekerjaan": d["pekerjaan"],
            "count": d["count"],
            "percentage": round((d["count"] / total) * 100, 2) if total > 0 else 0
        }
        for d in data
    ]

# -------------------------------
# Kalkulasi IRK
# -------------------------------

def categorize_irk(irk):
    if irk is None:
        return "Belum Ada Data"
    
    try:
        irk = float(irk)
    except (ValueError, TypeError):
        return "Nilai tidak valid"
    
    if 0 <= irk < 40:
        return "Rendah"
    elif 40 <= irk < 60:
        return "Sedang"
    elif 60 <= irk <= 100:
        return "Tinggi"
    else:
        return "Nilai tidak valid"
    
from django.conf import settings
import os

def generate_map(level="desa"):
    shp_path = os.path.join(settings.BASE_DIR, "staticfiles", "shp", "ADMINISTRASIDESA_AR_25K.shp")
    if not os.path.exists(shp_path):
        return "<p style='color:red'>❌ Shapefile tidak ditemukan. Pastikan ada di /static/shp/</p>"

    gdf = gpd.read_file(shp_path)

    # Ambil IRK dari database
    irk_data_desa = IRKResult.objects.values("desa").annotate(avg_irk=Avg("irk"))
    irk_data_kec = IRKResult.objects.values("kecamatan").annotate(avg_irk=Avg("irk"))

    irk_df_desa = pd.DataFrame(list(irk_data_desa))
    irk_df_kec = pd.DataFrame(list(irk_data_kec))

    # Normalisasi nama
    gdf["NAMOBJ"] = gdf["NAMOBJ"].str.strip().str.upper()
    gdf["WADMKC"] = gdf["WADMKC"].str.strip().str.upper()
    irk_df_desa["desa"] = irk_df_desa["desa"].str.strip().str.upper()
    irk_df_kec["kecamatan"] = irk_df_kec["kecamatan"].str.strip().str.upper()

    gdf_desa = gdf.merge(irk_df_desa, left_on="NAMOBJ", right_on="desa", how="left")
    gdf_kec = gdf.merge(irk_df_kec, left_on="WADMKC", right_on="kecamatan", how="left")

    m = folium.Map(location=[-7.87, 112.53], zoom_start=12, tiles="cartodbpositron")

    def get_color(irk):
        if irk is None: return "#CCCCCC"
        if irk < 40: return "#FFD700"   # Rendah
        elif irk < 60: return "#ADFF2F" # Sedang
        return "#32CD32"                # Tinggi

    # Tambah layer desa
    if level in ["desa", "both"]:
        folium.GeoJson(
            gdf_desa.to_json(),
            name="Desa",
            style_function=lambda feature: {
                "fillColor": get_color(feature["properties"].get("avg_irk")),
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["NAMOBJ", "avg_irk"],
                aliases=["Desa:", "IRK Rata-rata:"],
                localize=True
            )
        ).add_to(m)

    # Tambah layer kecamatan
    if level in ["kecamatan", "both"]:
        folium.GeoJson(
            gdf_kec.to_json(),
            name="Kecamatan",
            style_function=lambda feature: {
                "fillColor": get_color(feature["properties"].get("avg_irk")),
                "color": "black",
                "weight": 2,
                "fillOpacity": 0.4,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["WADMKC", "avg_irk"],
                aliases=["Kecamatan:", "IRK Rata-rata:"],
                localize=True
            )
        ).add_to(m)

    # Tambahkan kontrol layer
    folium.LayerControl(collapsed=False).add_to(m)

    # ✅ Taruh legend di bagian paling akhir
    legend_html = """
     <div style="
         position: fixed; 
         bottom: 20px; left: 20px; width: 150px; height: 130px; 
         border:2px solid grey; z-index:9999; font-size:14px;
         background:white; padding:10px; border-radius:8px;">
         <b>Keterangan IRK</b><br>
         <i style="background:#FFD700;width:15px;height:15px;float:left;margin-right:5px;"></i> Rendah (<40)<br>
         <i style="background:#ADFF2F;width:15px;height:15px;float:left;margin-right:5px;"></i> Sedang (40-59)<br>
         <i style="background:#32CD32;width:15px;height:15px;float:left;margin-right:5px;"></i> Tinggi (60-100)<br>
         <i style="background:#CCCCCC;width:15px;height:15px;float:left;margin-right:5px;"></i> Belum Ada Data<br>
     </div>
     """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m._repr_html_()


def get_samples_by_wilayah(level="kecamatan"):
    if level not in ["kecamatan", "desa"]:
        raise ValueError("level harus 'kecamatan' atau 'desa'")

    wilayah_qs = (
        IRKResult.objects
        .values(level)
        .annotate(avg_irk=Avg("irk"))
        .order_by("avg_irk")
    )
    total = wilayah_qs.count()

    if total == 0:
        return {"tinggi": [], "sedang": [], "rendah": [], "all": []}

    wilayah_list = [
        {
            level: w[level] or "-",
            "avg_irk": round(w["avg_irk"], 2) if w["avg_irk"] else 0,
            "category": categorize_irk(w["avg_irk"]),
        }
        for w in wilayah_qs
    ]

    samples = {"tinggi": [], "sedang": [], "rendah": [], "all": wilayah_list}
    if level == "kecamatan":
        if total <= 9:
            # Langsung assign ke samples tanpa variabel tambahan
            samples["tinggi"] = sorted([w for w in wilayah_list if w["avg_irk"] >= 60], 
                                    key=lambda x: x["avg_irk"], reverse=True)
            samples["sedang"] = sorted([w for w in wilayah_list if 40 <= w["avg_irk"] < 60], 
                                    key=lambda x: x["avg_irk"], reverse=True)
            samples["rendah"] = sorted([w for w in wilayah_list if w["avg_irk"] < 40], 
                                    key=lambda x: x["avg_irk"])
        else:
            # Definisikan variabel terlebih dahulu
            tinggi = [w for w in wilayah_list if w["avg_irk"] >= 60]
            sedang = [w for w in wilayah_list if 40 <= w["avg_irk"] < 60]
            rendah = [w for w in wilayah_list if w["avg_irk"] < 40]

            # Tinggi: ambil 3 tertinggi
            samples["tinggi"] = sorted(tinggi, key=lambda x: x["avg_irk"], reverse=True)[:3]
            
            # Rendah: ambil 3 terendah
            samples["rendah"] = sorted(rendah, key=lambda x: x["avg_irk"])[:3]

            # Sedang: ambil 3 tertinggi dalam kategori sedang
            sedang_sorted = sorted(sedang, key=lambda x: x["avg_irk"], reverse=True)
            if len(sedang_sorted) >= 3:
                samples["sedang"] = sedang_sorted[:3]
            else:
                samples["sedang"] = sedang_sorted

    elif level == "desa":
        tinggi = [w for w in wilayah_list if w["avg_irk"] >= 60]
        sedang = [w for w in wilayah_list if 40 <= w["avg_irk"] < 60]
        rendah = [w for w in wilayah_list if w["avg_irk"] < 40]

        samples["tinggi"] = sorted(tinggi, key=lambda x: x["avg_irk"], reverse=True)[:3]
        samples["rendah"] = sorted(rendah, key=lambda x: x["avg_irk"], reverse=True)[:3]

        sedang_sorted = sorted(sedang, key=lambda x: x["avg_irk"], reverse=True)
        if len(sedang_sorted) >= 3:
            samples["sedang"] = [sedang_sorted[0], sedang_sorted[len(sedang_sorted)//2], sedang_sorted[-1]]
        else:
            samples["sedang"] = sedang_sorted

    # 🔥 Filter nilai kosong / tanda strip / 0
    for key in ["tinggi", "sedang", "rendah", "all"]:
        samples[key] = [
            s for s in samples[key]
            if s[level] not in ["", "-"] and (s["avg_irk"] or 0) > 0
        ]

    return samples

def calculate_average_response(request):
    user = request.user
    responses = Response.objects.filter(user=user)

    # Data diri user
    try:
        data_diri = DataDiri.objects.filter(user=user).latest('id')
        nama = data_diri.nama
        pekerjaan = data_diri.pekerjaan
        usia = data_diri.usia
        latitude = data_diri.latitude
        longitude = data_diri.longitude
        kecamatan_name = data_diri.kecamatan.nama if data_diri.kecamatan else None
        desa_name = data_diri.desa.nama if data_diri.desa else None
    except DataDiri.DoesNotExist:
        nama, pekerjaan, usia = "-", "-", "-"
        latitude, longitude = None, None
        kecamatan_name, desa_name = None, None

    # Hitung IRK
    response_mapping = {'SS': 5, 'S': 4, 'R': 3, 'TS': 2, 'STS': 1}
    if not responses.exists():
        irk = 0.0
        category = "Belum Ada Data"
    else:
        scores = [response_mapping[r.response] for r in responses]
        if len(scores) != 16:
            return HttpResponse("Jumlah jawaban tidak lengkap!")

        weights = [0.412, 0.302, 0.425, 0.087, 0.109, 0.056, 0.389, 0.106,
                   0.454, 0.436, 0.051, 0.023, 0.056, 0.156, 0.068, 0.036]
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        irk = (weighted_sum / sum(weights)) * 20
        category = categorize_irk(irk)

    IRKResult.objects.create(
        user=user,
        nama=nama,
        pekerjaan=pekerjaan,
        kecamatan=kecamatan_name,
        desa=desa_name,
        irk=irk,
        category=category
    )

    pekerjaan_distribution = get_pekerjaan_distribution()

    irk_per_pekerjaan = (
        IRKResult.objects
        .values("pekerjaan")
        .annotate(avg_irk=Avg("irk"))
        .order_by("pekerjaan")
    )

    category_color_mapping = {
        "Rendah": "#FFD700",
        "Sedang": "#ADFF2F",
        "Tinggi": "#32CD32",
        "Belum Ada Data": "#CCCCCC"
    }

    avg_irk_per_pekerjaan = [
        {
            "pekerjaan": d["pekerjaan"] or "-",
            "avg_irk": round(d["avg_irk"], 2) if d["avg_irk"] else 0,
            "category": categorize_irk(d["avg_irk"]),
            "color": category_color_mapping.get(categorize_irk(d["avg_irk"]), "#999999")
        }
        for d in irk_per_pekerjaan
    ]

    avg_irk_all = IRKResult.objects.aggregate(global_avg=Avg('irk'))["global_avg"] or 0
    avg_irk_pekerjaan = next((d["avg_irk"] for d in avg_irk_per_pekerjaan if d["pekerjaan"] == pekerjaan), 0)
    pekerjaan_percentage = next((d["percentage"] for d in pekerjaan_distribution if d["pekerjaan"] == pekerjaan), 0)

    # --- ambil samples per kecamatan & desa ---
    samples_kecamatan = get_samples_by_wilayah(level="kecamatan")
    samples_desa = get_samples_by_wilayah(level="desa")
    # --- Tambahkan daftar desa untuk setiap kecamatan ---
    for kategori in ["tinggi", "sedang", "rendah"]:
        for kec in samples_kecamatan[kategori]:
            desa_list = Desa.objects.filter(
                kecamatan__nama=kec["kecamatan"]
            ).values("id", "nama")
            kec["desa_list"] = list(desa_list)


    # ambil level dari query parameter
    level = request.GET.get("level", "desa")
    total_orang = DataDiri.objects.count()  # ✅ jumlah seluruh responden

    context = {
        "nama": nama,
        "usia": usia,
        "pekerjaan": pekerjaan,
        "irk": irk,
        "category": category,
        "latitude": latitude,
        "longitude": longitude,
        "pekerjaan_distribution": pekerjaan_distribution,
        "avg_irk_pekerjaan": avg_irk_pekerjaan,
        "avg_irk_all": avg_irk_all,
        "pekerjaan_percentage": pekerjaan_percentage,
        "avg_irk_per_pekerjaan": avg_irk_per_pekerjaan,
        "pie_labels": [d["pekerjaan"] for d in avg_irk_per_pekerjaan],
        "pie_values": [d["avg_irk"] for d in avg_irk_per_pekerjaan],
        "samples_kecamatan": samples_kecamatan,
        "samples_desa": samples_desa,
        "map_html": generate_map(level),   # ✅ pakai variabel, bukan string
        "level": level   ,                  # ✅ koma sudah ditambahkan
        "total_orang": total_orang, 
    }

    return context

# -------------------------------
# Maps & Reports
# -------------------------------
from django.shortcuts import render
from django.http import HttpResponse
@login_required
def rata_rata_views(request):
    context = calculate_average_response(request)

    # Kalau kamu mau otomatis langsung ke thankyou tanpa menampilkan hasil:
    # return redirect('thankyou')

    # Kalau mau tampilkan hasil dulu baru tombol ke thankyou:
    if request.method == "POST":
        return redirect('thankyou')

    return render(request, "rata-rata - Copy.html", context)

@login_required
def report_views(request):
    context = calculate_average_response(request)

    report_context = {
        # 🔹 Data pribadi pengguna
        "nama": context["nama"],
        "usia": context["usia"],
        "pekerjaan": context["pekerjaan"],
        "irk": context["irk"],
        "category": context["category"],
        "latitude": context["latitude"],
        "longitude": context["longitude"],

        # 🔹 Data statistik dan visualisasi
        "pekerjaan_distribution": context["pekerjaan_distribution"],
        "avg_irk_pekerjaan": context["avg_irk_pekerjaan"],
        "avg_irk_all": context["avg_irk_all"],
        "pekerjaan_percentage": context["pekerjaan_percentage"],
        "avg_irk_per_pekerjaan": context["avg_irk_per_pekerjaan"],
        "pie_labels": context["pie_labels"],
        "pie_values": context["pie_values"],
        "samples_kecamatan": context["samples_kecamatan"],
        "samples_desa": context["samples_desa"],
        "map_html": context["map_html"],
        "level": context["level"],
        "total_orang": context["total_orang"],
    }

    return render(request, "report.html", report_context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def thankyou(request):
    # cek apakah user adalah staff/admin
    if request.user.is_staff:
        report_url = 'report'  # url name untuk admin
    else:
        report_url = 'report_user'       # url name untuk user biasa

    context = {
        'report_url': report_url
    }
    return render(request, 'thankyou.html', context)


