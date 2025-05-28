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
    Category,
    Article,
    Tag,
    Comment,
)

from ..db import DBSession, setup_engine
from ..utils.password import hash_password


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
    Base.metadata.create_all(engine)

    with transaction.manager:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=hash_password('admin123'),
            full_name='Administrator',
            is_admin=True,
            created_at=datetime.utcnow()
        )
        DBSession.add(admin)
        
        # Create regular user
        user = User(
            username='user',
            email='user@example.com',
            password_hash=hash_password('user123'),
            full_name='Regular User',
            created_at=datetime.utcnow()
        )
        DBSession.add(user)
        
        # Flush untuk mendapatkan ID user
        DBSession.flush()
        
        print(f"Created users with IDs: admin={admin.id}, user={user.id}")

        # Create categories
        categories = [
            Category(name='NBA', slug='nba', description='National Basketball Association news and updates'),
            Category(name='IBL', slug='ibl', description='Indonesian Basketball League news and updates'),
            Category(name='FIBA', slug='fiba', description='International Basketball Federation news and updates'),
            Category(name='Tutorial', slug='tutorial', description='Basketball tips, tricks, and tutorials'),
            Category(name='Analysis', slug='analysis', description='In-depth basketball analysis and opinion')
        ]
        for category in categories:
            DBSession.add(category)
        
        # Flush untuk mendapatkan ID kategori
        DBSession.flush()
        
        print(f"Created {len(categories)} categories")

        # Create some tags
        tags = [
            Tag(name='Lakers'),
            Tag(name='Warriors'),
            Tag(name='Pelita Jaya'),
            Tag(name='Satria Muda'),
            Tag(name='Shooting'),
            Tag(name='Defense'),
            Tag(name='Strategy')
        ]
        for tag in tags:
            DBSession.add(tag)
        
        # Flush untuk mendapatkan ID tag
        DBSession.flush()
        
        print(f"Created {len(tags)} tags")

        # Create some sample articles
        article1 = Article(
            title='Lakers Defeat Warriors in Thrilling Overtime',
            slug='lakers-defeat-warriors-thrilling-overtime',
            excerpt='The Los Angeles Lakers pulled off a stunning victory against the Golden State Warriors in an overtime thriller.',
            content='<p>In a game that had fans on the edge of their seats, the Los Angeles Lakers defeated the Golden State Warriors 120-118 in overtime. LeBron James led the charge with 32 points, 10 rebounds, and 11 assists, securing a triple-double in the process.</p><p>The Warriors, led by Stephen Curry with 29 points, fought hard but ultimately fell short in the extra period. The game featured 15 lead changes and was tied 10 times, showcasing the competitive nature of this rivalry.</p><p>"It was a battle out there tonight," said James after the game. "Both teams left everything on the floor, and we were fortunate to come out with the win."</p>',
            image_url='https://source.unsplash.com/random/1200x800/?basketball,lakers',
            status='published',
            author_id=admin.id,  # Gunakan ID yang sudah ada
            category_id=categories[0].id,  # Gunakan ID kategori NBA
            views=245,
            created_at=datetime.utcnow(),
            published_at=datetime.utcnow()
        )
        DBSession.add(article1)
        DBSession.flush()  # Flush untuk mendapatkan ID artikel
        
        # Tambahkan tags ke artikel setelah artikel di-flush
        article1.tags.extend([tags[0], tags[1]])
        
        article2 = Article(
            title='Pelita Jaya Dominates in IBL Season Opener',
            slug='pelita-jaya-dominates-ibl-season-opener',
            excerpt='Pelita Jaya Basketball showcased their championship form in the IBL 2023 season opener.',
            content='<p>Pelita Jaya Basketball started their Indonesian Basketball League (IBL) 2023 campaign with a dominant 87-65 victory over Bima Perkasa. The defending champions showed why they are favorites to retain their title with an impressive all-around performance.</p><p>Led by point guard Andakara Prastawa with 22 points and 7 assists, Pelita Jaya controlled the game from start to finish. Their defensive intensity was particularly noteworthy, forcing 18 turnovers and converting them into 24 points.</p><p>"We wanted to set the tone for the season," said head coach Johannis Winar. "This is just the beginning, and we have a lot of work ahead of us, but I am pleased with how the team executed tonight."</p>',
            image_url='https://source.unsplash.com/random/1200x800/?basketball,indonesia',
            status='published',
            author_id=user.id,  # Gunakan ID yang sudah ada
            category_id=categories[1].id,  # Gunakan ID kategori IBL
            views=187,
            created_at=datetime.utcnow(),
            published_at=datetime.utcnow()
        )
        DBSession.add(article2)
        DBSession.flush()  # Flush untuk mendapatkan ID artikel
        
        # Tambahkan tags ke artikel setelah artikel di-flush
        article2.tags.extend([tags[2], tags[3]])
        
        article3 = Article(
            title='5 Essential Shooting Drills for Basketball Players',
            slug='5-essential-shooting-drills-basketball-players',
            excerpt='Improve your shooting percentage with these five essential drills that every basketball player should practice.',
            content='<p>Shooting is arguably the most important skill in basketball. Whether youre a beginner or an experienced player, these five shooting drills will help you improve your accuracy and consistency.</p><h3>1. Form Shooting</h3><p>Start close to the basket and focus on perfect form: balanced stance, elbow in, follow-through with a snap of the wrist. Take 25 shots from 3-5 feet away.</p><h3>2. Star Shooting</h3><p>Place five cones in a star pattern around the three-point line. Take five shots from each position, moving quickly between spots.</p><h3>3. Pull-Up Jumpers</h3><p>Start at half-court, dribble to the free-throw line, and pull up for a jumper. Alternate sides and angles.</p><h3>4. Catch and Shoot</h3><p>Have a partner pass you the ball at different spots on the court. Catch and shoot immediately without dribbling.</p><h3>5. Pressure Free Throws</h3><p>After each drill, shoot two free throws. This simulates game situations where you need to make free throws while tired.</p>',
            image_url='https://source.unsplash.com/random/1200x800/?basketball,shooting',
            status='published',
            author_id=admin.id,  # Gunakan ID yang sudah ada
            category_id=categories[3].id,  # Gunakan ID kategori Tutorial
            views=312,
            created_at=datetime.utcnow(),
            published_at=datetime.utcnow()
        )
        DBSession.add(article3)
        DBSession.flush()  # Flush untuk mendapatkan ID artikel
        
        # Tambahkan tags ke artikel setelah artikel di-flush
        article3.tags.extend([tags[4], tags[6]])
        
        print(f"Created 3 articles")

        # Add some comments
        comment1 = Comment(
            text="Great article! The Lakers really showed their championship mentality in this game.",
            user_id=user.id,  # Gunakan ID yang sudah ada
            article_id=article1.id,  # Gunakan ID artikel yang sudah ada
            is_approved=True,
            created_at=datetime.utcnow()
        )
        DBSession.add(comment1)
        
        comment2 = Comment(
            text="I was at this game and the atmosphere was electric! LeBron's performance in overtime was incredible.",
            user_id=admin.id,  # Gunakan ID yang sudah ada
            article_id=article1.id,  # Gunakan ID artikel yang sudah ada
            is_approved=True,
            created_at=datetime.utcnow()
        )
        DBSession.add(comment2)
        
        comment3 = Comment(
            text="Pelita Jaya looks unstoppable this season. Their defense is on another level.",
            user_id=admin.id,  # Gunakan ID yang sudah ada
            article_id=article2.id,  # Gunakan ID artikel yang sudah ada
            is_approved=True,
            created_at=datetime.utcnow()
        )
        DBSession.add(comment3)
        
        comment4 = Comment(
            text="I've been using these shooting drills with my youth team and we've seen great improvement!",
            user_id=user.id,  # Gunakan ID yang sudah ada
            article_id=article3.id,  # Gunakan ID artikel yang sudah ada
            is_approved=True,
            created_at=datetime.utcnow()
        )
        DBSession.add(comment4)
        
        # Flush untuk mendapatkan ID komentar
        DBSession.flush()
        
        # Add a reply to a comment
        comment5 = Comment(
            text="Which drill do you find most effective for beginners?",
            user_id=admin.id,  # Gunakan ID yang sudah ada
            article_id=article3.id,  # Gunakan ID artikel yang sudah ada
            parent_id=comment4.id,  # Gunakan ID komentar yang sudah ada
            is_approved=True,
            created_at=datetime.utcnow()
        )
        DBSession.add(comment5)
        
        print(f"Created 5 comments")
        print('Database initialized successfully!')


if __name__ == '__main__':
    main()
