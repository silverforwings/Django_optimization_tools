# Generated by Django 2.2 on 2020-09-03 11:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('basketapp', '0003_auto_20200903_1330'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basketitem',
            options={'ordering': ['product'], 'verbose_name': 'корзина', 'verbose_name_plural': 'корзины'},
        ),
        migrations.AlterField(
            model_name='basketitem',
            name='mod_datetime',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата изменения'),
        ),
        migrations.AlterField(
            model_name='basketitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mainapp.Product', verbose_name='Продукт'),
        ),
        migrations.AlterField(
            model_name='basketitem',
            name='quantity',
            field=models.PositiveIntegerField(default=0, verbose_name='Количество'),
        ),
        migrations.AlterField(
            model_name='basketitem',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
    ]
