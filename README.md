# BMKG Weather for Home Assistant

> **⚠️ Disclaimer:** Ini adalah integrasi **tidak resmi (unofficial / third-party)** dan **tidak berafiliasi dengan, didukung, atau disponsori oleh BMKG** (Badan Meteorologi, Klimatologi, dan Geofisika Indonesia). Data yang ditampilkan berasal dari API publik BMKG. Penggunaan data tunduk pada kebijakan BMKG. Proyek ini bukan produk resmi BMKG.

Custom integration untuk Home Assistant yang menampilkan data cuaca, gempa bumi, dan peringatan dini dari **BMKG** (Badan Meteorologi, Klimatologi, dan Geofisika Indonesia).

---

## Fitur

| Kategori | Data |
|----------|------|
| **Prakiraan Cuaca** | Suhu, kelembapan, kecepatan & arah angin, curah hujan, tutupan awan, jarak pandang, kondisi cuaca |
| **Weather Card** | Entity `weather.*` dengan forecast 3-jam — support weather card standar HA |
| **Gempa Bumi** | Gempa terdekat dari lokasi HA (jarak haversine), gempa terbaru nasional, magnitudo, kedalaman, wilayah, skala MMI, shakemap |
| **Peta Gempa** | Semua gempa muncul sebagai pin di HA Map (geo_location platform) |
| **Peringatan Dini** | Jumlah peringatan aktif (provinsi & nasional), judul + detail CAP (severity, urgency, area) |

---

## Entities yang Dihasilkan

### Weather Entity (1 entity)
| Entity ID | Keterangan |
|-----------|------------|
| `weather.bmkg_*` | Cuaca saat ini + forecast 3-jam. Gunakan di **Weather Forecast Card** |

### Binary Sensor (1 entity)
| Entity ID | Keterangan |
|-----------|------------|
| `binary_sensor.bmkg_*_home_in_alert_area` | `on` jika koordinat HA berada di dalam polygon area peringatan CAP aktif. Attributes: `event`, `severity`, `effective`, `expires`, `area_desc`, `web`, `cap_code` |

### Geo Location (dinamis)
Pin gempa otomatis muncul di **Map Card**. Jumlah pin = jumlah gempa di API (biasanya 15 gempa terakhir yang dirasakan). Setiap pin berisi magnitudo, kedalaman, wilayah, dan link shakemap.

---

## Sensor (22 sensor)

### Prakiraan Cuaca (9 sensor)
| Entity ID | Satuan | Keterangan |
|-----------|--------|------------|
| `sensor.bmkg_*_temperature` | °C | Suhu udara |
| `sensor.bmkg_*_humidity` | % | Kelembapan udara |
| `sensor.bmkg_*_wind_speed` | km/h | Kecepatan angin |
| `sensor.bmkg_*_wind_direction` | ° | Arah angin (derajat) |
| `sensor.bmkg_*_precipitation` | mm/h | Curah hujan |
| `sensor.bmkg_*_cloud_cover` | % | Tutupan awan |
| `sensor.bmkg_*_visibility` | m | Jarak pandang |
| `sensor.bmkg_*_weather_condition` | — | Kondisi cuaca (English) |
| `sensor.bmkg_*_weather_code` | — | Kode cuaca BMKG |

### Gempa Bumi (8 sensor)
| Entity ID | Keterangan |
|-----------|------------|
| `sensor.bmkg_*_nearest_earthquake_magnitude` | Magnitudo gempa terdekat dari HA |
| `sensor.bmkg_*_nearest_earthquake_distance` | Jarak gempa terdekat (km) |
| `sensor.bmkg_*_nearest_earthquake_depth` | Kedalaman gempa terdekat |
| `sensor.bmkg_*_nearest_earthquake_location` | Wilayah gempa terdekat |
| `sensor.bmkg_*_nearest_earthquake_felt` | Wilayah terdampak (skala MMI) |
| `sensor.bmkg_*_latest_earthquake_magnitude` | Magnitudo gempa terbaru nasional |
| `sensor.bmkg_*_latest_earthquake_location` | Wilayah gempa terbaru nasional |
| `sensor.bmkg_*_latest_earthquake_felt` | Wilayah terdampak gempa terbaru |

### Peringatan Dini Cuaca / Nowcast (5 sensor)
| Entity ID | Keterangan |
|-----------|------------|
| `sensor.bmkg_*_active_warnings_province` | Jumlah peringatan aktif di provinsi |
| `sensor.bmkg_*_active_warnings_national` | Total peringatan aktif nasional |
| `sensor.bmkg_*_province_warning_title` | Judul peringatan terbaru provinsi |
| `sensor.bmkg_*_province_warning_description` | Deskripsi peringatan terbaru provinsi (maks. 255 karakter — teks lengkap di attribute `description`) |
| `sensor.bmkg_*_latest_national_warning_title` | Judul peringatan terbaru nasional |

---

## Sumber Data

| Data | URL | Update |
|------|-----|--------|
| Prakiraan Cuaca | `https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}` | Setiap 3 jam |
| Gempa Dirasakan | `https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json` | Setiap 5 menit |
| Peringatan Dini (ID) | `https://www.bmkg.go.id/alerts/nowcast/id` (RSS) | Setiap 15 menit (dapat diatur) |
| Peringatan Dini (EN) | `https://www.bmkg.go.id/alerts/nowcast/en` (RSS) | Setiap 15 menit (dapat diatur) |
| Detail CAP | `https://www.bmkg.go.id/alerts/nowcast/{lang}/{kode}_alert.xml` | Via RSS link |
| Shakemap | `https://static.bmkg.go.id/{kode_shakemap}.jpg` | Via atribut sensor |

---

## Instalasi

### Langkah 0 — Temukan Kode ADM4 Anda

Kode **ADM4** adalah kode administrasi level kelurahan/desa yang digunakan BMKG untuk menentukan lokasi prakiraan cuaca. Format: `PP.KK.KEC.XXXX` (provinsi · kota/kabupaten · kecamatan · kelurahan).

**Cara paling mudah menemukan kode ADM4:**

1. Buka URL berikut di browser (ganti `gambir` dengan nama wilayah Anda):
   ```
   https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=31.71.01.1001
   ```
   Jika data cuaca muncul (JSON dengan `"lokasi"`, `"data"`, dll.), kode itu benar.

2. Untuk mencari kode wilayah lain, coba ubah segmen angka satu per satu, atau gunakan referensi kode wilayah Kemendagri (Permendagri) yang tersedia di internet — kode BPS/Kemendagri sama dengan struktur ADM4 BMKG.

3. **Referensi cepat wilayah populer:**

   | Kelurahan | Kode ADM4 |
   |-----------|-----------|
   | Gambir, Jakarta Pusat | `31.71.01.1001` |
   | Menteng, Jakarta Pusat | `31.71.01.1002` |
   | Bandung Wetan, Kota Bandung | `32.73.01.1001` |
   | Denpasar Utara, Kota Denpasar | `51.71.01.1001` |
   | Danurejan, Kota Yogyakarta | `34.71.01.1001` |
   | Genteng, Kota Surabaya | `35.78.01.1001` |
   | Pontianak Kota | `61.71.01.1001` |
   | Makassar, Kota Makassar | `73.71.01.1001` |
   | Jayapura Utara | `91.71.01.1001` |

   > Tips: angka pertama = kode provinsi BPS, dua angka berikut = kota/kab, dua berikut = kecamatan.

---

### Instalasi Manual

Metode ini cocok jika Anda mengakses file HA via **Samba**, **SSH**, atau **File Manager** (add-on).

**Langkah-langkah:**

1. **Download** source code integrasi ini:
   - Klik **Code → Download ZIP** di halaman GitHub repository
   - Atau jalankan di terminal:
     ```bash
     git clone https://github.com/mamulazmi/bmkg_id.git
     ```

2. **Salin folder** `custom_components/bmkg_id/` ke direktori `config/custom_components/` di Home Assistant Anda:
   ```
   # Struktur yang benar di HA:
   config/
   └── custom_components/
       └── bmkg_id/          ← salin folder ini
           ├── __init__.py
           ├── manifest.json
           ├── sensor.py
           └── ...
   ```

   - **Via Samba**: Buka `\\homeassistant\config\custom_components\` dari Windows Explorer dan paste folder `bmkg_id`
   - **Via SSH**: `scp -r custom_components/bmkg_id/ homeassistant:/config/custom_components/`
   - **Via File Manager add-on**: Upload ke `/config/custom_components/bmkg_id/`

3. **Restart Home Assistant**:
   - **Settings → System → Restart** (atau klik ikon power → Restart)
   - Tunggu HA selesai restart penuh

4. **Tambahkan integrasi**:
   - Buka **Settings → Devices & Services**
   - Klik tombol **+ Add Integration** (pojok kanan bawah)
   - Ketik **"BMKG"** di kolom pencarian
   - Pilih **BMKG Weather**

5. **Isi kode ADM4**:
   - Masukkan kode ADM4 kelurahan Anda (lihat Langkah 0)
   - Klik **Submit**
   - Integrasi akan memvalidasi kode dan membuat entry baru

6. Selesai! 22 sensor + 1 weather entity + pin gempa di map muncul otomatis di **Settings → Devices & Services → BMKG Weather**.

---

### Instalasi via HACS (Custom Repository)

Jika Anda sudah menginstal **HACS** (Home Assistant Community Store):

1. Buka HACS di sidebar HA Anda
2. Klik menu **⋮ (tiga titik)** → **Custom repositories**
3. Isi form:
   - **Repository**: `https://github.com/mamulazmi/bmkg_id`
   - **Category**: `Integration`
   - Klik **Add**
4. Kembali ke halaman utama HACS → **Integrations**
5. Cari **"BMKG Weather"** → klik **Download**
6. Restart Home Assistant
7. Lanjut ke langkah 4–6 pada instalasi manual di atas

---

### Options
Semua opsi berikut dapat diubah kapan saja via:
**Settings → Devices & Services → BMKG Weather → Configure**

| Opsi | Keterangan | Default |
|------|------------|---------|
| **Kode ADM4** | Lokasi prakiraan cuaca | — |
| **Bahasa Peringatan Dini** | `id` (Indonesia) atau `en` (English) untuk nowcast alert | `id` |
| **Interval Update Peringatan** | Frekuensi polling nowcast (10–60 menit, step 5) | 15 menit |

> **Catatan rate limit BMKG:** Batas akses API BMKG adalah 60 permintaan per menit per IP. Interval minimum 10 menit sudah aman. Jangan set di bawah itu.

---

## Atribut Sensor

### Sensor Cuaca
```yaml
utc_datetime: "2026-04-29 15:00:00"
local_datetime: "2026-04-29 22:00:00"
analysis_date: "2026-04-29T12:00:00"
weather_desc: "Cerah Berawan"          # deskripsi Indonesia
weather_icon: "https://api-apps.bmkg.go.id/storage/icon/cuaca/..."
wind_direction_from: "E"
visibility_text: "9 km"
provinsi: "DKI Jakarta"
kotkab: "Kota Jakarta Pusat"
kecamatan: "Gambir"
desa: "Gambir"
latitude: -6.2088
longitude: 106.8456
```

### Sensor Gempa
```yaml
datetime: "2026-04-29T10:09:04+00:00"
magnitude: "4.3"
kedalaman: "6 km"
wilayah: "Pusat gempa berada di darat 10 km Barat Laut ..."
dirasakan: "III Kota A, II Kota B"
coordinates: "-2.54,121.06"
distance_from_ha_km: 342.1       # hanya pada sensor "nearest"
shakemap_url: "https://static.bmkg.go.id/20260429170904.mmi.jpg"
```

### Sensor Peringatan Dini
```yaml
# Atribut RSS:
title: "Hujan Lebat disertai Petir di DKI Jakarta"
description: "Hujan lebat akan terjadi pada ..."
author: "cuaca.ekstrem@bmkg.go.id (BMKG)"
pub_date: "2026-04-29T21:40:00+07:00"
cap_code: "CJK20260429001"
link: "https://www.bmkg.go.id/alerts/nowcast/id/CJK20260429001_alert.xml"
# Atribut CAP XML (hanya muncul saat ada peringatan aktif provinsi):
event: "Hujan Lebat dan Petir"
headline: "Hujan Lebat disertai Petir"
cap_description: "Hujan lebat disertai petir akan terjadi pada ..."  # deskripsi lengkap dari CAP
severity: "Moderate"          # Extreme / Severe / Moderate / Minor / Unknown
urgency: "Immediate"          # Immediate / Expected / Future / Past / Unknown
certainty: "Observed"         # Observed / Likely / Possible / Unlikely / Unknown
effective: "2026-04-29T21:30:00+07:00"   # waktu mulai (ISO 8601)
expires: "2026-04-29T23:30:00+07:00"     # waktu berakhir (ISO 8601)
sender_name: "Badan Meteorologi Klimatologi dan Geofisika"
web: "https://nowcasting.bmkg.go.id/infografis/CJK/2026/04/29/infografis.jpg"
area_desc: "Jakarta Pusat, Jakarta Selatan"
polygon:                       # koordinat lat,lon area terdampak
  - "-6.121,106.774 -6.134,106.789 ..."
```

---

## Contoh Automation

### Notifikasi Gempa di Sekitar Rumah
```yaml
automation:
  - alias: "Notifikasi Gempa Dekat"
    trigger:
      - platform: state
        entity_id: sensor.bmkg_gambir_nearest_earthquake_magnitude
    condition:
      - condition: numeric_state
        entity_id: sensor.bmkg_gambir_nearest_earthquake_distance
        below: 100  # dalam 100 km
      - condition: numeric_state
        entity_id: sensor.bmkg_gambir_nearest_earthquake_magnitude
        above: 4.0
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Gempa Terdeteksi"
          message: >
            M{{ states('sensor.bmkg_gambir_nearest_earthquake_magnitude') }}
            {{ state_attr('sensor.bmkg_gambir_nearest_earthquake_magnitude', 'wilayah') }}
            Jarak: {{ states('sensor.bmkg_gambir_nearest_earthquake_distance') }} km
```

### Notifikasi Peringatan Cuaca Provinsi
```yaml
automation:
  - alias: "Peringatan Cuaca BMKG"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bmkg_gambir_active_warnings_province
        above: 0
    action:
      - service: notify.mobile_app
        data:
          title: "⛈️ Peringatan Cuaca BMKG"
          message: "{{ states('sensor.bmkg_gambir_province_warning_title') }}"
```

### Notifikasi Saat Rumah Masuk Area Peringatan (Polygon-based)
```yaml
automation:
  - alias: "BMKG Alert di Area Rumah"
    trigger:
      - platform: state
        entity_id: binary_sensor.bmkg_gambir_home_in_alert_area
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "⛈️ Peringatan Cuaca di Lokasi Anda"
          message: >
            {{ state_attr('binary_sensor.bmkg_gambir_home_in_alert_area', 'event') }}
            — {{ state_attr('binary_sensor.bmkg_gambir_home_in_alert_area', 'area_desc') }}
            (s/d {{ state_attr('binary_sensor.bmkg_gambir_home_in_alert_area', 'expires') }})
```

---

## Pengembangan

### Struktur File
```
custom_components/bmkg_id/
├── __init__.py              # Setup/unload integration
├── manifest.json            # Metadata HA (version: 1.1.3)
├── config_flow.py           # UI wizard + options
├── coordinator.py           # Polling cuaca (3 jam)
├── earthquake_coordinator.py # Polling gempa (5 menit)
├── nowcast_coordinator.py   # Polling peringatan (15 menit) + CAP cache
├── api.py                   # HTTP clients (cuaca, gempa, nowcast/RSS/CAP XML)
├── const.py                 # Konstanta dan URL
├── data.py                  # Typed dataclass
├── entity.py                # Base entity + DeviceInfo
├── sensor.py                # Entry point semua sensor
├── earthquake_sensor.py     # Sensor gempa
├── nowcast_sensor.py        # Sensor peringatan dini
├── weather.py               # WeatherEntity + BMKG condition mapping
├── binary_sensor.py         # Binary sensor: home in alert polygon area
├── geo_location.py          # Geo location pins gempa di HA Map
├── icon.png                 # Logo integrasi (256x256)
├── images/
│   ├── icon.png             # Sumber logo
│   └── icon.svg             # Logo vektor
├── strings.json             # UI strings
└── translations/
    ├── en.json
    └── id.json
```

### Menjalankan Tests
```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[test]"
.venv/bin/pytest tests/ -v
.venv/bin/pytest tests/test_api.py -v      # unit tests tanpa HA
.venv/bin/pytest --cov=custom_components/bmkg_id tests/
```

---

## Lisensi

MIT License — Data cuaca dan gempa © BMKG Indonesia
