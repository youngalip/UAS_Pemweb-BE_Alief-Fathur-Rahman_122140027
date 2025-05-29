# hoopsnewsid/scripts/initialize_threads.py

import os
import sys
import transaction
from datetime import datetime

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from pyramid.scripts.common import parse_vars

from ..models import (
    Base,
    User,
    Thread,
    Comment
)

from ..db import DBSession, setup_engine


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if argv is None:
        argv = sys.argv

    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, name='main', options=options)

    print("Config URI:", config_uri)
    print("Loaded settings keys:", list(settings.keys()))
    print("SQLAlchemy URL:", settings.get('sqlalchemy.url'))

    engine = setup_engine(settings)
    
    # Tidak perlu create_all karena tabel sudah ada dari migrasi
    # Base.metadata.create_all(engine)

    with transaction.manager:
        # Cek apakah sudah ada thread di database
        thread_count = DBSession.query(Thread).count()
        if thread_count > 0:
            print(f"Thread sudah ada di database ({thread_count} thread). Lewati inisialisasi.")
            return
        
        # Ambil user untuk author thread
        admin = DBSession.query(User).filter_by(username='admin').first()
        user = DBSession.query(User).filter_by(username='user').first()
        
        if not admin or not user:
            print("User admin atau user tidak ditemukan. Pastikan initialize_db.py sudah dijalankan.")
            return
        
        # Buat thread contoh
        threads = [
            Thread(
                title="Selamat Datang di Forum Komunitas HoopsNewsID",
                content="<p>Halo semua,</p><p>Selamat datang di forum komunitas HoopsNewsID! Forum ini dibuat sebagai tempat diskusi untuk semua penggemar basket di Indonesia.</p><p>Silakan memperkenalkan diri dan mulai diskusi tentang topik basket favorit Anda.</p><p>Salam Olahraga!</p>",
                user_id=admin.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Thread(
                title="Diskusi: Siapa MVP NBA Musim Ini?",
                content="<p>Dengan musim NBA yang sedang berlangsung, siapa menurut kalian yang pantas menjadi MVP tahun ini?</p><p>Saya pribadi melihat beberapa kandidat kuat seperti Nikola Jokic, Joel Embiid, dan Giannis Antetokounmpo.</p><p>Bagaimana pendapat kalian?</p>",
                user_id=user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Thread(
                title="Perkembangan IBL Musim 2023",
                content="<p>Bagaimana pendapat kalian tentang perkembangan IBL musim ini?</p><p>Tim mana yang menurut kalian paling berpeluang menjadi juara? Dan pemain muda mana yang paling menarik untuk diikuti?</p>",
                user_id=admin.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
        ]
        
        for thread in threads:
            DBSession.add(thread)
        
        # Flush untuk mendapatkan ID thread
        DBSession.flush()
        
        print(f"Created {len(threads)} threads")
        
        # Tambahkan komentar ke thread
        comments = [
            Comment(
                content="Terima kasih atas sambutannya! Saya penggemar berat basket sejak kecil dan senang bisa bergabung dengan komunitas ini.",
                user_id=user.id,
                thread_id=threads[0].id,
                is_approved=True,
                created_at=datetime.utcnow()
            ),
            Comment(
                content="Menurut saya Jokic masih yang terdepan untuk MVP. Triple-double machine dan efisiensinya luar biasa.",
                user_id=admin.id,
                thread_id=threads[1].id,
                is_approved=True,
                created_at=datetime.utcnow()
            ),
            Comment(
                content="Saya lebih condong ke Embiid. Dominasinya di kedua sisi lapangan sangat mengesankan.",
                user_id=user.id,
                thread_id=threads[1].id,
                is_approved=True,
                created_at=datetime.utcnow()
            ),
            Comment(
                content="Pelita Jaya masih jadi favorit juara menurut saya. Tapi Satria Muda juga punya peluang besar.",
                user_id=user.id,
                thread_id=threads[2].id,
                is_approved=True,
                created_at=datetime.utcnow()
            ),
        ]
        
        for comment in comments:
            DBSession.add(comment)
        
        # Tambahkan balasan komentar
        reply = Comment(
            content="Setuju, tapi jangan lupakan Luka Doncic juga. Statistiknya luar biasa musim ini!",
            user_id=admin.id,
            thread_id=threads[1].id,
            parent_id=comments[1].id,  # Balas ke komentar Jokic
            is_approved=True,
            created_at=datetime.utcnow()
        )
        DBSession.add(reply)
        
        print(f"Created {len(comments) + 1} comments for threads")
        print('Thread data initialized successfully!')


if __name__ == '__main__':
    main()
