import json
import os
from django.db import migrations
from django.conf import settings

def create_initial_data(apps, schema_editor):
    Tag = apps.get_model('api', 'Tag')
    Dish = apps.get_model('api', 'Dish')
    Image = apps.get_model('api', 'Image')

    # 构建JSON文件路径
    fixtures_dir = os.path.join(settings.BASE_DIR, 'api', 'fixtures')
    tags_file = os.path.join(fixtures_dir, 'tags.json')
    dishes_file = os.path.join(fixtures_dir, 'dishes.json')

    # 读取tags.json
    with open(tags_file, 'r', encoding='utf-8') as f:
        tags_data = json.load(f)

    # 读取dishes.json
    with open(dishes_file, 'r', encoding='utf-8') as f:
        dishes_data = json.load(f)

    # 创建标签对象
    tag_objects = {}
    for t_data in tags_data:
        t, _ = Tag.objects.get_or_create(name=t_data['name'], defaults={'name_en': t_data['name_en']})
        tag_objects[t.name] = t

    # 创建菜品和关联数据
    for dish_data in dishes_data:
        dish, _ = Dish.objects.get_or_create(
            name=dish_data['name'],
            defaults={
                'name_en': dish_data['name_en'],
                'description': dish_data['description'],
                'description_en': dish_data['description_en']
            }
        )
        # 添加标签
        dish_tags = [tag_objects[tag_name] for tag_name in dish_data['tags']]
        dish.tags.set(dish_tags)

        # 添加图片
        for image_url in dish_data['images']:
            Image.objects.get_or_create(dish=dish, image_url=image_url)

def reverse_func(apps, schema_editor):
    # 如果需要回滚逻辑，可在此实现
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_initial'),  # 根据实际依赖修改
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_func),
    ]
