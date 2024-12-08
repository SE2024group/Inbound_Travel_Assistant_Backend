# web/api/management/commands/init_data.py

from django.core.management.base import BaseCommand
from api.models import Tag, Dish, Image

class Command(BaseCommand):
    help = 'Initialize data'

    def handle(self, *args, **kwargs):
        # 创建标签
        tags = [
            {'id': 1, 'name': '辣', 'name_en': 'Spicy'},
            # ... 其他标签
        ]
        for tag_data in tags:
            Tag.objects.update_or_create(id=tag_data['id'], defaults=tag_data)

        # 创建菜品和关联数据
        dishes = [
            {
                'name': '泡菜',
                'name_en': 'Sichuan Pickles',
                'description': '一种传统的四川开胃菜...',
                'description_en': 'A traditional Sichuan appetizer...',
                'tags': [3, 4, 6],
                'images': ['http://example.com/images/paocai1.jpg']
            },
            # ... 其他菜品
        ]
        for dish_data in dishes:
            dish, created = Dish.objects.get_or_create(
                name=dish_data['name'],
                defaults={
                    'name_en': dish_data['name_en'],
                    'description': dish_data['description'],
                    'description_en': dish_data['description_en']
                }
            )
            tag_objects = Tag.objects.filter(id__in=dish_data['tags'])
            dish.tags.set(tag_objects)
            for image_url in dish_data['images']:
                Image.objects.get_or_create(dish=dish, image_url=image_url)

        self.stdout.write(self.style.SUCCESS('数据初始化成功！'))
