import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from api.models import (
    Dish, Tag, Image,
    BrowsingHistory, LikeHistory, FavoriteHistory,
    CommentHistory, CommentImage,
    DietaryPreference,
)

User = get_user_model()

@pytest.mark.django_db
def test_create_dish():
    """
    测试 Dish 模型的基本创建:
    - 创建一条 Dish，验证 name、name_en、description 字段。
    """
    dish = Dish.objects.create(
        name="水煮鱼",
        name_en="Boiled Fish",
        description="川菜经典",
        description_en="A classic Sichuan dish."
    )
    assert dish.id is not None
    assert dish.name == "水煮鱼"
    assert dish.name_en == "Boiled Fish"
    assert dish.description == "川菜经典"
    assert dish.description_en == "A classic Sichuan dish."

@pytest.mark.django_db
def test_create_tag_and_associate_dish():
    """
    测试 Tag 和 Dish 的多对多关联:
    - 创建 Tag，并将其与 Dish 关联
    - 验证 dish.tags 中包含该 tag
    """
    dish = Dish.objects.create(name="回锅肉", description="辣味十足")
    tag = Tag.objects.create(name="辣", name_en="Spicy")
    dish.tags.add(tag)

    assert dish.tags.count() == 1
    assert dish.tags.first().name_en == "Spicy"

@pytest.mark.django_db
def test_create_image():
    """
    测试 Image 模型:
    - 为某个 Dish 创建关联的 Image 对象
    """
    dish = Dish.objects.create(name="宫保鸡丁", description="甜辣口味")
    image = Image.objects.create(dish=dish, image_url="http://example.com/image.jpg")

    assert image.id is not None
    assert image.dish == dish
    assert image.image_url == "http://example.com/image.jpg"

@pytest.mark.django_db
def test_browsing_history():
    """
    测试 BrowsingHistory 模型:
    - 创建用户/菜品后记录浏览历史
    - 检查其外键、时间戳、顺序
    """
    user = User.objects.create_user(username="testuser", password="testpass")
    dish = Dish.objects.create(name="麻婆豆腐", description="麻辣鲜香")
    bh = BrowsingHistory.objects.create(user=user, dish=dish)
    
    assert bh.id is not None
    assert bh.user.username == "testuser"
    assert bh.dish.name == "麻婆豆腐"
    # timestamp auto_now_add => 不为空
    assert bh.timestamp <= timezone.now()

@pytest.mark.django_db
def test_like_history():
    """
    测试 LikeHistory 模型:
    - 创建一条点赞历史
    """
    user = User.objects.create_user(username="liker", password="123456")
    dish = Dish.objects.create(name="水煮牛肉", description="麻辣口味")
    like = LikeHistory.objects.create(user=user, dish=dish)

    assert like.id is not None
    assert like.user == user
    assert like.dish == dish

@pytest.mark.django_db
def test_favorite_history():
    """
    测试 FavoriteHistory 模型:
    - 创建收藏历史, 并验证 dish -> favorite_histories 反向查询
    """
    user = User.objects.create_user(username="favuser", password="123456")
    dish = Dish.objects.create(name="辣子鸡", description="干辣椒炒鸡丁")
    fav = FavoriteHistory.objects.create(user=user, dish=dish)

    assert fav.id is not None
    assert fav.user == user
    assert fav.dish == dish

    # 通过 dish.favorite_histories 反向关系检查
    favorites = dish.favorite_histories.all()
    assert favorites.count() == 1
    assert favorites.first().user.username == "favuser"

@pytest.mark.django_db
def test_comment_history():
    """
    测试 CommentHistory 模型:
    - 创建评论(带rating)
    - 确认该评论关联dish的评论数，以及comment字段、rating等
    """
    user = User.objects.create_user(username="commenter", password="123456")
    dish = Dish.objects.create(name="西红柿炒蛋", description="经典家常菜")
    comment = CommentHistory.objects.create(
        user=user,
        dish=dish,
        comment="非常好吃",
        rating=5
    )
    assert comment.id is not None
    assert comment.comment == "非常好吃"
    assert comment.rating == 5
    # 通过 dish.comments 反向检查
    assert dish.comments.count() == 1
    assert dish.comments.first() == comment

@pytest.mark.django_db
def test_comment_image():
    """
    测试 CommentImage 模型:
    - 为评论添加图片URL
    """
    user = User.objects.create_user(username="u1", password="p1")
    dish = Dish.objects.create(name="鱼香肉丝", description="酸甜辣")
    cmt = CommentHistory.objects.create(user=user, dish=dish, comment="好吃", rating=4)
    img = CommentImage.objects.create(
        comment=cmt,
        image_url="http://example.com/comment_image.jpg"
    )

    assert img.id is not None
    assert img.comment == cmt
    assert img.image_url == "http://example.com/comment_image.jpg"
    # 反向 relationship
    assert cmt.images.count() == 1
    assert cmt.images.first() == img

@pytest.mark.django_db
def test_dietary_preference():
    """
    测试 DietaryPreference 模型:
    - 确保 user + tag 的组合唯一
    - 测试 preference choices
    """
    user = User.objects.create_user(username="dpuser", password="123456")
    tag1 = Tag.objects.create(name="素食", name_en="Vegetarian")
    pref = DietaryPreference.objects.create(user=user, tag=tag1, preference="LIKE")

    assert pref.id is not None
    assert pref.user == user
    assert pref.tag == tag1
    assert pref.preference == "LIKE"

    # 重复创建 => 触发 unique_together
    with pytest.raises(IntegrityError):
        DietaryPreference.objects.create(user=user, tag=tag1, preference="DISLIKE")

@pytest.mark.django_db
def test_delete_cascade():
    """
    测试级联删除:
    - 删除用户 / dish 后, 对应的 BrowsingHistory / Comment / LikeHistory / FavoriteHistory 是否被一起删除
    """
    user = User.objects.create_user(username="cascade", password="123456")
    dish = Dish.objects.create(name="茄子煲", description="家常菜")
    LikeHistory.objects.create(user=user, dish=dish)
    FavoriteHistory.objects.create(user=user, dish=dish)
    BrowsingHistory.objects.create(user=user, dish=dish)
    comment = CommentHistory.objects.create(user=user, dish=dish, comment="还不错", rating=3)

    # 初步断言
    assert LikeHistory.objects.count() == 1
    assert FavoriteHistory.objects.count() == 1
    assert BrowsingHistory.objects.count() == 1
    assert CommentHistory.objects.count() == 1

    # 删除 user => like/fav/browsing/comment 都应删除
    user.delete()
    assert LikeHistory.objects.count() == 0
    assert FavoriteHistory.objects.count() == 0
    assert BrowsingHistory.objects.count() == 0
    assert CommentHistory.objects.count() == 0

    # dish 依然在, 但反向外键对象都被删光
    assert Dish.objects.filter(name="茄子煲").exists()

@pytest.mark.django_db
def test_model_str_representation():
    """
    测试 __str__ 方法:
    - 只做基本字符串校验, 确保不会抛异常
    """
    user = User.objects.create_user(username="strtest", password="123")
    dish = Dish.objects.create(name="剁椒鱼头", description="湖南名菜")
    tag = Tag.objects.create(name="辣", name_en="HunanCuisine")
    like = LikeHistory.objects.create(user=user, dish=dish)
    fav = FavoriteHistory.objects.create(user=user, dish=dish)
    browse = BrowsingHistory.objects.create(user=user, dish=dish)
    cmt = CommentHistory.objects.create(user=user, dish=dish, comment="又辣又香", rating=4)
    cmt_img = CommentImage.objects.create(comment=cmt, image_url="http://example.com/cmt.jpg")
    dp = DietaryPreference.objects.create(user=user, tag=tag, preference="LIKE")

    assert str(dish) == "剁椒鱼头"
    assert str(tag) == "辣"
    assert "viewed" in str(browse)
    assert "liked" in str(like)
    assert "favorited" in str(fav)
    assert "commented on" in str(cmt)
    assert "Image for comment" in str(cmt_img)
    assert "strtest" in str(dp)
    assert "辣" in str(dp)

