from django.db import migrations, models


def update_hash(apps, schema_editor):
    from ..util import get_hash
    import json

    Task = apps.get_model('workers', 'Task')

    for task in Task.objects.all():
        task.task_hash = get_hash(
            task.handler,
            json.loads(task.args),
            json.loads(task.kwargs),
        )
        task.save()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('workers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='repeat',
            field=models.BigIntegerField(choices=[
                (3600, 'hourly'),
                (86400, 'daily'),
                (604800, 'weekly'),
                (1209600, 'every 2 weeks'),
                (2419200, 'every 4 weeks'),
                (0, 'never'),
            ], default=0)
        ),
        migrations.AddField(
            model_name='task',
            name='task_hash',
            field=models.CharField(max_length=40, default='', db_index=True)
        ),
        migrations.RunPython(update_hash),
        migrations.AlterField(
            model_name='task',
            name='task_hash',
            field=models.CharField(max_length=40, db_index=True)
        ),
    ]
