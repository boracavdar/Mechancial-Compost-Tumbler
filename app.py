import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import math

# =====================================================================
# 📌 SİSTEM PARAMETRELERİ (IE VE ME ORTAK VERİ HAVUZU)
# =====================================================================
# IE Parametreleri
GUNLUK_YEMEK_PORSIYONU = 10000      # IE-1: SKS Günlük ortalama porsiyon tahmini
PORSİYON_BASINA_ATIK_KG = 0.20      # IE-1: 1 porsiyondan çıkan atık katsayısı
KOMPOST_VERIM_ORANI = 0.60          # IE-2: Kütle dengesi (Mass Balance) sonrası hasat oranı
GUBRE_KG_FIYATI_TL = 5.0            # IE-3: Kompost kg bazlı tasarruf değeri
ILK_YATIRIM_MALIYETI_TL = 15000.0   # IE-3: Sistem kurulum CAPEX bedeli
KARBON_AZOT_ORANI_KATSAYISI = 0.40  # IE-2: Optimum C:N dengesi için karbon (talaş) çarpanı
DONGU_SURESI_GUN = 21               # IE-2: Kompostlaşma süreç süresi

# ME Parametreleri
TAMBUR_MAKS_KAPASITE_KG = 250.0     # ME-1: Tambur maksimum asimetrik yük kütlesi
TAMBUR_YARICAPI_M = 0.4             # ME-1/ME-2: Tambur yarıçapı varsayımı (metre)
TAMBUR_UZUNLUK_M = 1.2              # ME-1: Tambur uzunluğu (metre)
INSAN_KOL_KUVVETI_N = 150.0         # ME-2: Operatör manuel çevirme kuvveti (Newton)
KOL_UZUNLUGU_M = 0.3                # ME-2: Krank/Çevirme kolu uzunluğu (metre)
HEDEF_IC_SICAKLIK_C = 65.0          # ME-3: Termofilik evre hedef optimum sıcaklığı
DIS_ORTAM_SICAKLIK_C = 0.0          # ME-3: Kış şartları referans dış ortam sıcaklığı
YALITIM_K_KATSAYISI = 0.022         # ME-3: Poliüretan köpük ısı iletim katsayısı (W/m.K)
# =====================================================================

# --- VERİTABANI BAĞLANTISI (SQLite) ---
conn = sqlite3.connect('kompost_sistemi.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS uretim_partileri (
        parti_no INTEGER PRIMARY KEY AUTOINCREMENT,
        baslangic_tarihi DATE,
        bitis_tarihi DATE,
        atik_miktari_kg REAL,
        karbon_miktari_kg REAL,
        durum TEXT
    )
''')
conn.commit()

def parti_sil(p_no):
    c.execute("DELETE FROM uretim_partileri WHERE parti_no=?", (p_no,))
    conn.commit()

# --- ARAYÜZ ANA AYARLARI ---
st.set_page_config(page_title="MÜH401 Karar Destek Sistemi", layout="wide", page_icon="⚙️")
st.title("♻️ Mekanik Kompost Tamburu - Karar Destek Sistemi (DSS)")

# Kural 1: Geçici Veri Uyarısı
st.warning("**DİKKAT:** Sistemdeki mevcut kapasite, atık ve maliyet parametreleri (kg, TL vb.) şu an için tahmini (dummy) verilerdir. İlgili iş paketlerinden (IE-1 ve ME-1) gelecek kesin saha verileri beklenmektedir ve sisteme entegre edilecektir.")

# --- SOL MENÜ: YENİ VERİ GİRİŞİ ---
st.sidebar.header("📥 Operasyonel Veri Girişi (Batch)")
with st.sidebar.form("veri_giris_formu"):
    tarih = st.date_input("Yükleme Tarihi", datetime.today())
    atik_kg = st.number_input("Organik Atık Yükü (kg) [Azot]", min_value=0.0, max_value=TAMBUR_MAKS_KAPASITE_KG, format="%.1f")
    onerilen_karbon = atik_kg * KARBON_AZOT_ORANI_KATSAYISI
    
    if atik_kg > 0:
        st.info(f"💡 Optimum C:N Dengesi İçin Önerilen Karbon: **{onerilen_karbon:.1f} kg**")
        
    karbon_kg = st.number_input("Eklenen Karbon Yükü (kg) [Talaş]", min_value=0.0, value=float(onerilen_karbon) if atik_kg > 0 else 0.0, format="%.1f")
    kaydet_btn = st.form_submit_button("Üretim Döngüsünü Başlat")

    if kaydet_btn and atik_kg > 0:
        bitis = tarih + timedelta(days=DONGU_SURESI_GUN)
        c.execute("INSERT INTO uretim_partileri (baslangic_tarihi, bitis_tarihi, atik_miktari_kg, karbon_miktari_kg, durum) VALUES (?, ?, ?, ?, ?)",
                  (tarih, bitis, atik_kg, karbon_kg, 'Aktif'))
        conn.commit()
        st.success("Yeni üretim partisi sisteme kaydedildi.")
        st.rerun()

# --- VERİTABANINDAN AKTİF VERİLERİN ÇEKİLMESİ ---
df = pd.read_sql_query("SELECT * FROM uretim_partileri", conn)
if not df.empty:
    df['baslangic_tarihi'] = pd.to_datetime(df['baslangic_tarihi'])
    df['bitis_tarihi'] = pd.to_datetime(df['bitis_tarihi'])
    bugun = pd.to_datetime(datetime.today().date())
    df['gecen_gun'] = (bugun - df['baslangic_tarihi']).dt.days
    df['gecen_gun'] = df['gecen_gun'].apply(lambda x: min(max(x, 0), DONGU_SURESI_GUN))
    df = df.reset_index(drop=True)
    df['Gosterim_No'] = df.index + 1
    
    st.sidebar.markdown("---")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button(label="📥 DSS Raporunu Dışa Aktar (.csv)", data=csv, file_name='MÜH401_Sistem_Raporu.csv', mime='text/csv')

# =====================================================================
# Kural 3: SEKME (TAB) HİYERARŞİSİ
# =====================================================================
tabs = st.tabs([
    "🏠 WBS & Ekip", 
    "⚖️ IE-1: Kapasite", 
    "📋 IE-2: Çizelgeleme", 
    "💰 IE-3: Finans", 
    "📐 ME-1: Mekanik Tasarım", 
    "⚙️ ME-2: Kinematik", 
    "🔥 ME-3: Termodinamik"
])

tab_wbs, tab_ie1, tab_ie2, tab_ie3, tab_me1, tab_me2, tab_me3 = tabs

# -----------------------------------------------------------
# SEKME 1: WBS & EKİP
# -----------------------------------------------------------
with tab_wbs:
    st.header("Kurumsal Ekip Dağılımı ve İş Kırılım Yapısı (WBS)")
    st.markdown("Kampüs atık yönetimi projesi kapsamında görev alan disiplinler arası (Endüstri ve Makine) mühendislik ekibinin güncel organizasyon şeması aşağıda belirtilmiştir.")
    
    # Kural 2: Kesin Ekip Dağılımı
    st.markdown("""
    *   **Proje Lideri:** Yusuf Bora Çavdar
    *   **Endüstri Ekibi:** 
        *   **IE-1 (Kapasite & Talep):** Semih Bora Çiftçi & Efe Çamlık 
        *   **IE-2 (Çizelgeleme & Proje Yönetimi):** Yusuf Bora Çavdar 
        *   **IE-3 (Finans & ROI):** Azra Sıla Cömert
    *   **Makine Ekibi:** 
        *   **ME-1 (Kapasite, Kütle & Statik):** Çağatay Çetinkaya & Akif Emir Bilici 
        *   **ME-2 (Kinematik & Redüktör):** Mehmet Kayhan & Hüseyin Onur Çolaker 
        *   **ME-3 (Termodinamik & Isı Transferi):** Sezginhan Binay & Ramazan Çalgıcı
    """)

# -----------------------------------------------------------
# SEKME 2: IE-1 KAPASİTE
# -----------------------------------------------------------
with tab_ie1:
    st.header("IE-1: Tesis Kapasite ve Talep Modellemesi")
    st.markdown("SKS biriminden alınacak veriler doğrultusunda, kampüs genelindeki organik atık arzının karşılanması için gerekli teorik makine parkuru (tambur adedi) modellenmektedir.")
    
    gunluk_toplam_atik = GUNLUK_YEMEK_PORSIYONU * PORSİYON_BASINA_ATIK_KG
    gerekli_toplam_karbon = gunluk_toplam_atik * KARBON_AZOT_ORANI_KATSAYISI
    gunluk_toplam_kitle = gunluk_toplam_atik + gerekli_toplam_karbon
    toplam_aktif_kitle_ihtiyaci = gunluk_toplam_kitle * DONGU_SURESI_GUN 
    gerekli_tambur_adedi = math.ceil(toplam_aktif_kitle_ihtiyaci / TAMBUR_MAKS_KAPASITE_KG)
    
    st.latex(r"\text{Sistem İhtiyacı (Adet)} = \left\lceil \frac{\text{Günlük Atık Kütlesi (kg)} \times 21 \text{ Gün}}{\text{Birim Tambur Kapasitesi (ME-1)}} \right\rceil")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tahmini Tesis Yükü (Günlük)", f"{GUNLUK_YEMEK_PORSIYONU} Porsiyon")
    c2.metric("Sistemdeki Toplam Aktif Hacim (21 Gün)", f"{toplam_aktif_kitle_ihtiyaci:,.1f} kg")
    c3.metric("Optimum Tesis Makine İhtiyacı", f"{gerekli_tambur_adedi} Adet")

# -----------------------------------------------------------
# SEKME 3: IE-2 ÇİZELGELEME
# -----------------------------------------------------------
with tab_ie2:
    st.header("IE-2: Kesikli Üretim (Batch) Çizelgelemesi ve Kütle Dengesi")
    st.markdown("Üretim operasyonlarının Gantt mimarisi üzerinden anlık takibi, kütle dengesi (Mass Balance) ve vardiyalı personel iş emri yönetimi.")
    
    st.latex(r"M_{hasat} = (M_{azot} + M_{karbon}) \times \eta_{verim}")

    if not df.empty:
        df['Gosterim_Str'] = "Parti " + df['Gosterim_No'].astype(str)
        fig = px.timeline(df, x_start="baslangic_tarihi", x_end="bitis_tarihi", y="Gosterim_Str",
                          color="gecen_gun", color_continuous_scale="Viridis", height=300)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Saha Operasyonları ve İşçi Yönergeleri")
        cols = st.columns(3)
        for index, row in df.iterrows():
            with cols[index % 3]:
                with st.container(border=True):
                    # Detaylı Tarih ve Kütle Verileri
                    baslangic_str = row['baslangic_tarihi'].strftime('%d.%m.%Y')
                    bitis_str = row['bitis_tarihi'].strftime('%d.%m.%Y')
                    
                    st.markdown(f"### Parti #{row['Gosterim_No']} | Faz: {row['gecen_gun']}/21")
                    st.progress(row['gecen_gun'] / DONGU_SURESI_GUN)
                    
                    st.markdown(f"**📅 Süreç:** {baslangic_str} ➡️ {bitis_str}")
                    st.markdown(f"**🍏 Azot Kaynağı (Yemek):** {row['atik_miktari_kg']} kg")
                    st.markdown(f"**🪵 Karbon Kaynağı (Talaş):** {row['karbon_miktari_kg']} kg")
                    
                    toplam_girdi = row['atik_miktari_kg'] + row['karbon_miktari_kg']
                    beklenen_cikti = toplam_girdi * KOMPOST_VERIM_ORANI
                    st.markdown(f"🌱 **Beklenen Hasat (Kütle Dengesi):** {beklenen_cikti:.1f} kg")
                    
                    st.markdown("---")
                    st.markdown("👷 **İşçi Operasyon Yönergesi:**")
                    
                    if row['gecen_gun'] >= DONGU_SURESI_GUN:
                        st.error(f"🛑 SÜREÇ TAMAMLANDI. Tamburu bugün ({bitis_str}) boşaltın. Çıkan kompostu hasat alanına sevk edin.")
                    elif row['gecen_gun'] == 0:
                        st.info("🆕 Parti bugün yüklendi. Kapağı kilitleyip günün ilk havalandırma (döndürme) işlemlerini başlatın.")
                        st.markdown("- [ ] **10:00** (Kolu 3 tur çevir)\n- [ ] **14:00** (Kolu 3 tur çevir)\n- [ ] **18:00** (Kolu 3 tur çevir)")
                    else:
                        st.warning("⏳ Çürüme Fazı. Oksijen sirkülasyonu için belirlenen saatlerde manuel döndürme rutinine uyun.")
                        st.markdown("- [ ] **10:00** (Kolu 3 tur çevir)\n- [ ] **14:00** (Kolu 3 tur çevir)\n- [ ] **18:00** (Kolu 3 tur çevir)")
                    
                    if st.button("🗑️ Kaydı Sil", key=f"sil_{row['parti_no']}"):
                        parti_sil(row['parti_no'])
                        st.rerun()
    else:
        st.warning("Aktif üretim partisi (batch) bulunmuyor. Operasyonel veri girişi beklenmektedir.")

# -----------------------------------------------------------
# SEKME 4: IE-3 FİNANS
# -----------------------------------------------------------
with tab_ie3:
    st.header("IE-3: Mühendislik Ekonomisi ve Yatırım Getirisi (ROI)")
    st.markdown("Sabit sermaye yatırımı (CAPEX) ile süreç çıktılarından (OPEX tasarrufu) elde edilecek finansal faydanın Break-Even (Başa Baş) noktası analizleri.")
    
    toplam_capex = gerekli_tambur_adedi * ILK_YATIRIM_MALIYETI_TL
    st.latex(r"CAPEX = N_{tambur} \times C_{birim}")
    st.latex(r"ROI_{fayda} = \sum (M_{hasat} \times P_{gubre})")
    
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Toplam CAPEX ({gerekli_tambur_adedi} Makine)", f"{toplam_capex:,.2f} ₺")
    
    if not df.empty:
        toplam_beklenen_gubre = (df['atik_miktari_kg'] + df['karbon_miktari_kg']).sum() * KOMPOST_VERIM_ORANI
        tahmini_tasarruf = toplam_beklenen_gubre * GUBRE_KG_FIYATI_TL
        kalan_maliyet = toplam_capex - tahmini_tasarruf
        c2.metric("Süreç İçi Finansal Tasarruf", f"+ {tahmini_tasarruf:,.2f} ₺")
        c3.metric("Amortisman (Break-Even) Kalanı", f"{max(kalan_maliyet, 0):,.2f} ₺")
    else:
        st.info("Kapsamlı ROI analizi için aktif üretim verisi gerekmektedir.")

# -----------------------------------------------------------
# SEKME 5: ME-1 MEKANİK TASARIM
# -----------------------------------------------------------
with tab_me1:
    st.header("ME-1: Kütle, Statik Dayanım ve Şaft Tasarımı")
    st.markdown("Kompost tamburunun mekanik gövde hacmi, statik yük kapasitesi ve asimetrik kütleyi taşıyacak merkezi şaftın gerilme (Bending Stress) hesaplamaları.")
    
    tambur_hacmi = math.pi * (TAMBUR_YARICAPI_M ** 2) * TAMBUR_UZUNLUK_M
    
    st.latex(r"V_{tambur} = \pi \cdot r^2 \cdot L")
    st.latex(r"\sigma_{egilme} = \frac{M \cdot c}{I} \le \frac{S_y}{n}")
    
    col_m1_1, col_m1_2 = st.columns(2)
    col_m1_1.metric("Tambur Yarıçapı (r) & Uzunluk (L)", f"{TAMBUR_YARICAPI_M}m x {TAMBUR_UZUNLUK_M}m")
    col_m1_1.metric("Teorik İç Hacim (V)", f"{tambur_hacmi:.2f} m³")
    
    col_m1_2.metric("Malzeme Spesifikasyonu", "St37 Yapı Çeliği")
    col_m1_2.metric("Akma Dayanımı (Sy)", "≈ 235 MPa")
    col_m1_2.metric("Asimetrik Yük (Maksimum)", f"{TAMBUR_MAKS_KAPASITE_KG} kg")

# -----------------------------------------------------------
# SEKME 6: ME-2 KİNEMATİK
# -----------------------------------------------------------
with tab_me2:
    st.header("ME-2: Kinematik Analiz ve Redüktör (Dişli) Tasarımı")
    st.markdown("Maksimum kütle (asimetrik yük) altında varilin merkez eksende döndürülmesi için gereken tork ihtiyacı ve manuel (insan gücü) operasyon için dişli aktarım (redüksiyon) oranı optimizasyonu.")
    
    gerekli_tork = TAMBUR_MAKS_KAPASITE_KG * 9.81 * TAMBUR_YARICAPI_M
    insan_torku = INSAN_KOL_KUVVETI_N * KOL_UZUNLUGU_M
    reduksiyon_orani = math.ceil(gerekli_tork / insan_torku)
    
    st.latex(r"T_{gerekli} = m_{maks} \cdot g \cdot r_{tambur}")
    st.latex(r"T_{operator} = F_{insan} \cdot L_{kol}")
    st.latex(r"\text{Redüksiyon Oranı} (i) = \left\lceil \frac{T_{gerekli}}{T_{operator}} \right\rceil")
    
    col_m2_1, col_m2_2 = st.columns(2)
    col_m2_1.metric("Yerçekimi İvmeli Gerekli Tork", f"~{gerekli_tork:.1f} Nm")
    col_m2_1.metric("Operatör Kol Kuvveti (Girdi)", f"{INSAN_KOL_KUVVETI_N} N")
    
    col_m2_2.metric("Operatör Tork Üretimi", f"{insan_torku:.1f} Nm")
    col_m2_2.metric("Minimum Dişli Oranı (i)", f"1 : {reduksiyon_orani}")

# -----------------------------------------------------------
# SEKME 7: ME-3 TERMODİNAMİK
# -----------------------------------------------------------
with tab_me3:
    st.header("ME-3: Termodinamik ve Isı Transferi Analizi")
    st.markdown("Aerobik kompostlaşma fazı olan 'Termofilik Evre'nin korunabilmesi için gerekli yalıtım tasarımının Fourier Isı İletim Kanunu üzerinden modellenmesi.")
    
    st.latex(r"q = -k \cdot A \frac{dT}{dx}")
    st.latex(r"\Delta T = T_{ic} - T_{dis}")
    
    col_m3_1, col_m3_2 = st.columns(2)
    col_m3_1.metric("Kış Şartları Dış Ortam ($T_{dis}$)", f"{DIS_ORTAM_SICAKLIK_C} °C")
    col_m3_1.metric("Termofilik Evre İç Hedef ($T_{ic}$)", f"{HEDEF_IC_SICAKLIK_C} °C")
    col_m3_1.metric("Gerekli Delta T ($\Delta T$)", f"{HEDEF_IC_SICAKLIK_C - DIS_ORTAM_SICAKLIK_C} °C")
    
    col_m3_2.metric("Önerilen Yalıtım Malzemesi", "Poliüretan Köpük")
    col_m3_2.metric("Isı İletim Katsayısı (k)", f"{YALITIM_K_KATSAYISI} W/m·K")
    col_m3_2.info("Fourier denklemi ile dış yüzeye olan ısı kaybı minimize edilerek optimum yalıtım kalınlığı (dx) saptanacaktır.")
