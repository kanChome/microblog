import os

os.environ["DATABASE_URL"] = "sqlite://"

from datetime import datetime, timezone, timedelta
import unittest
from app import app, db
from app.models import User, Post


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        user = User(username="susan", email="susan@example.com")
        user.set_password("cat")
        self.assertTrue(user.check_password("cat"))
        self.assertFalse(user.check_password("dog"))

    def test_avatar(self):
        user = User(username="john", email="john@example.com")
        self.assertEqual(
            user.avatar(128),
            "https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128",
        )

    def test_follow(self):
        oneUser = User(username="john", email="john@example.com")
        twoUser = User(username="susan", email="susan@example.com")
        db.session.add(oneUser)
        db.session.add(twoUser)
        db.session.commit()
        following = db.session.scalars(oneUser.following.select()).all()
        followers = db.session.scalars(twoUser.followers.select()).all()
        self.assertEqual(len(following), 0)
        self.assertEqual(len(followers), 0)

        oneUser.follow(twoUser)
        db.session.commit()
        self.assertTrue(oneUser.is_following(twoUser))
        self.assertEqual(oneUser.following_count(), 1)
        self.assertEqual(twoUser.followers_count(), 1)
        oneUser_following = db.session.scalars(oneUser.following.select()).all()
        twoUser_followers = db.session.scalars(twoUser.followers.select()).all()
        self.assertEqual(len(oneUser_following), 1)
        self.assertEqual(len(twoUser_followers), 1)
        self.assertEqual(oneUser_following[0].username, "susan")
        self.assertEqual(twoUser_followers[0].username, "john")

        oneUser.unfollow(twoUser)
        db.session.commit()
        self.assertFalse(oneUser.is_following(twoUser))
        self.assertEqual(oneUser.following_count(), 0)
        self.assertEqual(twoUser.followers_count(), 0)
        oneUser_following = db.session.scalars(oneUser.following.select()).all()
        twoUser_followers = db.session.scalars(twoUser.followers.select()).all()
        self.assertEqual(len(oneUser_following), 0)
        self.assertEqual(len(twoUser_followers), 0)

    def test_follow_posts(self):
        # ユーザーの作成
        user1 = User(username="john", email="john@example.com")
        user2 = User(username="susan", email="susan@example.com")
        user3 = User(username="mary", email="mary@example.com")
        db.session.add_all([user1, user2, user3])

        # 投稿の作成
        now = datetime.now(timezone.utc)
        post1 = Post(
            body="post from john", author=user1, timestamp=now + timedelta(seconds=1)
        )
        post2 = Post(
            body="post from susan", author=user2, timestamp=now + timedelta(seconds=2)
        )
        post3 = Post(
            body="post from mary", author=user3, timestamp=now + timedelta(seconds=3)
        )
        db.session.add_all([post1, post2, post3])
        db.session.commit()

        # フォローの作成
        user1.follow(user2)
        user1.follow(user3)
        user2.follow(user3)
        db.session.commit()

        # フォローしているユーザーの投稿を取得
        f1 = db.session.scalars(user1.following_posts()).all()
        f2 = db.session.scalars(user2.following_posts()).all()
        f3 = db.session.scalars(user3.following_posts()).all()
        self.assertEqual(f1, [post3, post2, post1])
        self.assertEqual(f2, [post3, post2])
        self.assertEqual(f3, [post3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
