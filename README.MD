# HoopsNewsID

## Deskripsi Aplikasi Web

HoopsNewsID adalah platform web interaktif yang menyediakan berita terkini, artikel mendalam, dan ruang komunitas bagi para penggemar basket di Indonesia. Aplikasi ini menggabungkan informasi terpercaya dan fitur diskusi untuk menciptakan pengalaman lengkap bagi pengguna dalam mengikuti perkembangan dunia basket, khususnya liga-liga lokal seperti IBL Indonesia, serta berita internasional ala Bleacher Report.

Dengan teknologi modern seperti React untuk frontend dan Pyramid untuk backend, HoopsNewsID menawarkan performa cepat dan antarmuka yang responsif serta mudah digunakan di berbagai perangkat.

---

## Dependensi Paket

### Frontend

- **React** — Library UI untuk membangun antarmuka pengguna  
- **Redux Toolkit** — Manajemen state global yang efisien  
- **React Router** — Routing dan navigasi halaman  
- **Axios** — HTTP client untuk komunikasi dengan backend  
- **Tailwind CSS** — Framework CSS utility-first untuk styling  
- **Date-fns** — Manipulasi dan format tanggal  
- **React Icons** — Ikon SVG untuk UI  
- **Vite** — Build tool untuk pengembangan frontend cepat

### Backend

- **Python 3.8+**  
- **Pyramid** — Framework web Python untuk membangun REST API  
- **SQLAlchemy** — ORM untuk interaksi dengan database PostgreSQL  
- **Alembic** — Manajemen migrasi skema database  
- **Marshmallow** — Validasi dan serialisasi data  
- **psycopg2** — PostgreSQL database adapter  
- **transaction & zope.sqlalchemy** — Manajemen transaksi database  
- **Unidecode** — Membuat slug URL-friendly dari teks  
- **Waitress** — WSGI server untuk deployment

---

## Fitur Utama

### Frontend

- **Berita & Artikel:** Menampilkan berita basket terbaru dan artikel berkualitas yang dikategorikan dengan baik.  
- **Forum Komunitas:** Fitur diskusi berbasis thread dan komentar untuk interaksi pengguna.  
- **Profil Pengguna:** Halaman profil dengan informasi dan aktivitas pengguna.  
- **Autentikasi & Otorisasi:** Sistem login dengan peran pengguna (admin dan user biasa).  
- **Manajemen Konten Admin:** Halaman admin untuk membuat, mengedit, dan menghapus artikel, kategori, komentar, dan mengelola pengguna.  
- **Responsif & Modern:** UI yang cepat dan responsif dengan desain modern menggunakan Tailwind CSS.

### Backend

- **REST API Lengkap:** Endpoint untuk artikel, kategori, user, komentar, dan komunitas.  
- **Manajemen Artikel:** CRUD artikel dengan validasi dan slug otomatis.  
- **Manajemen Kategori & Komentar:** CRUD kategori dan moderasi komentar.  
- **Autentikasi JWT:** Sistem autentikasi token JWT untuk keamanan API.  
- **Manajemen Komunitas:** Fitur thread dan komentar untuk forum basket.  
- **Transaksi Database:** Pengelolaan transaksi yang aman dan konsisten menggunakan Pyramid dan SQLAlchemy.  
- **Migrasi Database:** Penggunaan Alembic untuk migrasi skema database.

---

## Referensi

- [IBL Indonesia](https://iblindonesia.com) — Sebagai inspirasi konten dan fokus lokal pada liga basket Indonesia.  
- [Bleacher Report](https://bleacherreport.com) — Sebagai referensi gaya penyajian berita dan artikel basket internasional.  
- [React](https://reactjs.org) — Library frontend utama.  
- [Pyramid Framework](https://trypyramid.com) — Framework backend yang digunakan.  
- [Tailwind CSS](https://tailwindcss.com) — Framework CSS untuk styling.  
- [Redux Toolkit](https://redux-toolkit.js.org) — Manajemen state di frontend.  
