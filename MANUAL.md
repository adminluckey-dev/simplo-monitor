# Panduan Pengguna — Simplo Monitor (CMMS)

Panduan ini untuk operator dan administrator yang memakai dashboard harian. Simplo Monitor memantau kamera NX Witness dan gateway jaringan, mencatat gangguan, lalu membantu membuat work order serta jadwal preventive maintenance.

Alamat aplikasi di jaringan lokal biasanya `http://<ip-server>:8080`. Contoh di situs: `http://192.168.100.224:8080`.

## 1. Masuk dan keluar

1. Buka alamat dashboard di browser.
2. Isi **Username** dan **Password**, lalu klik **Masuk**.
3. Sesi login berlaku 7 hari di browser yang sama.
4. Keluar lewat tombol **Logout** di kiri bawah.

Akun pertama yang dibuat sistem (kalau belum ada user sama sekali):

| Username | Password | Level |
|---|---|---|
| `admin` | `admin1234` | Administrator |

Ganti password itu segera lewat **User Management** setelah login pertama.

Menu yang tampil mengikuti hak akses akun. Administrator melihat semua menu. Operator hanya melihat menu yang dicentang saat akun dibuat.

## 2. Arti warna status

Setiap perangkat punya satu dari tiga kondisi:

| Warna | Label | Artinya |
|---|---|---|
| Hijau | Online & Sehat | Terhubung, dan untuk CCTV sedang merekam dengan jadwal rekam aktif |
| Oranye | Perlu Perhatian | Masih hidup, tetapi ada yang kurang. Contoh CCTV: tidak merekam atau jadwal rekam mati. Bisa juga NX bilang offline sementara IP kamera masih menjawab |
| Merah | Gangguan Aktif | Offline atau tidak terjangkau |

Kategori perangkat: **Network**, **CCTV**, **Access**, **Alarm**.

Untuk CCTV, sistem tidak hanya percaya status NX. Server juga mengetuk IP kamera langsung. Kalau IP tidak menjawab, kartu menjadi gangguan meski NX masih menulis Online. Kalau IP menjawab tetapi NX offline, kartu menjadi perhatian.

Gateway WiFi/LTE (perangkat Network) tidak langsung merah karena satu ping gagal. Status Offline baru muncul setelah dua pemeriksaan gagal berturut-turut.

## 3. Dashboard

Ini layar utama setelah login. Angka di atas diperbarui otomatis (interval default sekitar 10 detik, mengikuti pengaturan server).

Empat kartu ringkasan:

- **Total Perangkat** — semua aset yang sedang dipantau.
- **Online & Sehat** — jumlah hijau plus persentasenya.
- **Perlu Perhatian** — jumlah oranye.
- **Gangguan Aktif** — jumlah merah.

Filter di atas grid:

- **Semua**, **Gangguan**, **Perlu perhatian**
- **Network**, **CCTV**, **Access**, **Alarm**
- **REC** — hanya yang sedang merekam

Urutan bisa diubah lewat **Urut**: prioritas masalah, nama, atau status. Prioritas masalah menaruh gangguan di depan.

Klik sebuah kartu untuk membuka panel kanan:

- Status koneksi, recording, lokasi, IP, vendor, MAC, jadwal rekam
- Untuk CCTV: hasil deteksi IP langsung
- Untuk router: latency, internet, SSID, dan detail jaringan lain
- Informasi aset (kategori, lokasi detail, tanggal pasang, garansi, kontrak maintenance)
- Indikator status dan kronologi hari ini
- **Buka di NX Witness** — membuka kamera di NX (perangkat kamera)
- **Refresh status** — menarik ulang data dari NX dan router

**Mode Dinding** di kanan atas membuat tampilan fullscreen, cocok untuk monitor ruang kontrol. Tekan lagi atau keluar dari fullscreen browser untuk kembali.

Banner kuning/merah di atas grid muncul jika NX belum bisa dihubungi. Selama mode demo aktif, angka di layar adalah contoh, bukan kondisi lapangan.

## 4. Manajemen Asset

Menu ini adalah daftar resmi perangkat yang dipantau. Dashboard hanya menampilkan aset yang ada di sini (ditambah status hidup dari NX/router).

### Menambah perangkat

1. Klik **+ Tambah Perangkat**.
2. Isi nama, kategori, lokasi, dan IP.
3. Lengkapi detail lokasi, vendor, model, MAC, tanggal pemasangan, akhir garansi, dan akhir kontrak maintenance bila ada.
4. Klik **Simpan Perangkat**.

Tanggal akhir garansi dan maintenance menentukan label di tabel:

- **Aktif** — hari ini masih di dalam tanggal akhir (inklusif).
- **Tidak aktif** — tanggal akhir sudah lewat.
- **Belum diisi** — tanggal kosong.

### Mengubah atau menghapus

- **Edit** membuka form yang sama.
- **Hapus** mengeluarkan perangkat dari monitoring. Sistem meminta konfirmasi.

### Impor dari Live

**Impor dari Live** menyalin perangkat yang sedang terlihat dari NX/router ke daftar aset. Pakai ini saat inventaris masih kosong atau ada kamera baru di NX yang belum tercatat. Data yang sudah ada tidak ditimpa sembarangan; yang baru ditambahkan.

Saat server pertama kali jalan dan tabel aset masih kosong, sistem mengisi aset sekali dari perangkat yang sedang hidup. Setelah itu, tambah dan hapus lewat menu ini.

## 5. Tim Teknisi

Daftar orang yang bisa ditugaskan di work order dan catatan PM.

1. Klik **+ Tambah Baru**.
2. Isi nama, nomor HP, email, dan ID Telegram (opsional).
3. Centang keahlian: Network, CCTV, Access, Alarm. Boleh lebih dari satu.
4. Klik **Simpan Teknisi**.

Email wajib terisi kalau teknisi harus menerima work order lewat email. Keahlian menentukan teknisi mana yang muncul saat membuat WO untuk suatu kategori, dan siapa yang dipilih oleh auto-WO.

**Edit** dan **Hapus** ada di baris masing-masing.

## 6. Work Order

Work order adalah perintah kerja: kategori, tanggal, jam, satu aset, satu teknisi, dan catatan.

### Membuat manual

1. Klik **+ Buat Work Order**.
2. Isi tanggal dan jam.
3. Pilih **Kategori**. Dropdown aset dan teknisi baru terisi setelah kategori dipilih. Teknisi yang muncul adalah yang punya keahlian kategori itu.
4. Pilih aset dan teknisi.
5. Tulis catatan / instruksi.
6. Klik **Simpan & Kirim Email**.

Nomor WO dibuat otomatis. Status kolom **Email** menunjukkan hasil pengiriman, misalnya terkirim, teknisi tanpa email, atau gagal. **Re-send Email** mengirim ulang. **Hapus** menghapus WO setelah konfirmasi.

### Auto Generate WO

Di bagian atas halaman Work Order ada dua angka:

| Field | Fungsi |
|---|---|
| Ambang (menit) | Berapa lama gangguan atau perlu perhatian harus berlangsung sebelum WO otomatis dibuat. `0` mematikan fitur ini. |
| Jeda (menit) | Jarak minimum antar WO otomatis untuk aset yang sama. Default 60 menit. Mencegah WO berulang saat status berkedip. |

Klik **Simpan Setting** setelah mengubah angka. Batas maksimum 10080 menit (7 hari).

WO otomatis hanya dibuat jika semua ini terpenuhi:

1. Auto-WO menyala (ambang lebih dari 0).
2. Aset sudah ada di Manajemen Asset dan kondisinya gangguan atau perlu perhatian.
3. Kondisi itu sudah berlangsung melewati ambang.
4. Belum ada WO terbuka untuk aset itu.
5. Jeda sejak WO terakhir untuk aset itu sudah lewat.
6. Ada teknisi dengan keahlian yang sama dan belum terikat WO terbuka. Sistem memilih nama yang urut paling awal.

Catatan WO otomatis diawali **Auto Generate WO**. Email tetap dikirim ke teknisi yang ditugaskan.

## 7. Jadwal PM

Preventive maintenance dijadwalkan per aset.

1. Klik **+ Jadwal PM**.
2. Pilih aset.
3. Pilih interval: bulanan (30), triwulan (90), semester (180), tahunan (365), atau kustom (isi jumlah hari).
4. Isi tanggal **Jadwal berikutnya**.
5. Biarkan **Aktif** tercentang.
6. Isi catatan cakupan atau nomor kontrak bila perlu.
7. Klik **Simpan Jadwal**.

Status di tabel:

| Status | Arti |
|---|---|
| Sesuai jadwal | Jadwal berikutnya masih lebih dari 7 hari |
| Segera | Jatuh tempo dalam 7 hari ke depan |
| Terlambat | Tanggal jadwal berikutnya sudah lewat |
| Nonaktif | Centang Aktif dimatikan |

Kolom **Kontrak** mengikuti tanggal akhir maintenance di data aset.

### Mencatat service

1. Buka baris jadwal (service record).
2. Isi tanggal service, teknisi (opsional), dan catatan hasil kerja.
3. Klik **Catat Service**.

Service record menggeser jadwal berikutnya sesuai interval. Riwayat bisa dihapus per baris. Menghapus jadwal PM juga menghapus service record-nya.

## 8. Statistik

Menunjukkan berapa lama perangkat sehat, perhatian, dan gangguan pada rentang tanggal. Angka dihitung dari histori insiden, bukan dari tebakan.

1. Isi **Dari** dan **Sampai**.
2. Pilih satu perangkat atau **Semua perangkat**.
3. Klik **Terapkan**.

Empat angka:

- **Persentase Sehat** — porsi waktu hijau.
- **Uptime** — sehat ditambah perhatian.
- **Downtime** — porsi waktu gangguan.
- **Perangkat** — jumlah yang masuk hitungan, plus label rentang tanggal.

Di bawahnya ada pita timeline, grafik harian, dan tabel per perangkat (sehat, uptime, downtime, distribusi warna).

## 9. Laporan

Histori kejadian: gangguan mulai, perhatian mulai, pulih, dan perubahan status.

1. Isi **Dari**, **Sampai**, dan perangkat.
2. Klik **Terapkan**.
3. **Export PDF** mengunduh laporan sesuai filter yang sedang tampil.

Kolom tabel: waktu, jenis kejadian, device, lokasi, status, keterangan.

Rentang default kalau tanggal dikosongkan adalah 7 hari terakhir sampai hari ini. Ini berlaku juga di Statistik.

## 10. Setting Notifikasi

### Email

Dipakai untuk mengirim work order ke teknisi.

1. Centang **Aktifkan**.
2. SMTP Host biasanya `smtp.gmail.com`, port `587`.
3. Isi email pengirim dan **App Password** Gmail (bukan password login Gmail biasa).
4. Isi nama pengirim dan from email.
5. Kolom penerima dipisah koma. Pengiriman WO tetap memakai email yang tersimpan di data teknisi.
6. **Simpan Email**, lalu **Kirim Tes Email** untuk memastikan SMTP jalan.

Kalau password dibiarkan kosong saat menyimpan ulang, password lama tetap dipakai.

### Telegram

1. Buat bot lewat @BotFather dan salin token.
2. Centang **Aktifkan**.
3. Isi Bot Token dan Chat ID (lebih dari satu dipisah koma).
4. **Simpan Telegram**, lalu **Kirim Tes Telegram**.

ID Telegram di data teknisi adalah catatan kontak. Pesan tes memakai Chat ID di halaman ini.

## 11. User Management

Hanya administrator yang melihat menu ini.

1. Klik **+ Tambah User**.
2. Isi username (tanpa spasi), nama lengkap, dan password minimal 6 karakter.
3. Pilih level:
   - **Administrator** — semua menu.
   - **Operator** — centang menu yang boleh dibuka. Minimal satu menu. User Management tidak bisa diberikan ke operator.
4. Biarkan **Aktif** tercentang.
5. Klik **Simpan User**.

Saat mengedit, kosongkan password jika tidak ingin menggantinya. User nonaktif tidak bisa login. Sistem menolak menghapus administrator aktif yang terakhir.

## 12. Rutinitas yang disarankan

**Awal shift**

1. Login dan lihat empat angka di dashboard.
2. Filter **Gangguan**, lalu **Perlu perhatian**.
3. Buka kartu merah: catat IP, lokasi, dan kronologi.
4. Cek Work Order: apakah auto-WO sudah terbit dan email teknisi berstatus terkirim.
5. Cek Jadwal PM untuk baris **Terlambat** dan **Segera**.

**Saat ada gangguan baru**

1. Konfirmasi di panel detail (dan, untuk CCTV, deteksi IP langsung).
2. Kalau auto-WO belum menyala atau teknisi yang dipilih otomatis tidak sesuai, buat WO manual.
3. Pastikan email teknisi terisi dan Setting Notifikasi email sudah dites.

**Akhir periode**

1. Buka Statistik untuk rentang minggu atau bulan.
2. Export PDF dari Laporan untuk arsip.

## 13. Jika tampilan tidak sesuai lapangan

| Yang terlihat | Yang dicek |
|---|---|
| Banner NX gagal, data terasa palsu | Password NX di `.env` server. Selama fallback demo aktif, layar bukan kondisi asli |
| Kamera hijau di NX tetapi merah di CMMS | IP kamera dari server CMMS. CMMS menandai gangguan jika port kamera tidak menjawab |
| Kamera merah di NX tetapi oranye di CMMS | IP masih hidup. Status perhatian berarti “IP OK”, jaringan kamera belum mati total |
| Router berkedip offline | Butuh dua gagal beruntun. Cek kabel/WiFi host CMMS ke `192.168.1.1` |
| Auto-WO tidak terbit | Ambang masih 0, aset belum ada di Manajemen Asset, belum melewati ambang/jeda, sudah ada WO terbuka, atau tidak ada teknisi bebas dengan keahlian itu |
| Email WO gagal | Aktifkan email, tes SMTP, dan pastikan teknisi punya alamat email |
| Menu tidak muncul | Akun operator. Minta administrator menambah hak akses menu |
| Login ditolak | Username/password, atau akun dinonaktifkan |

Health server bisa dicek di `http://<ip-server>:8080/api/health`.
