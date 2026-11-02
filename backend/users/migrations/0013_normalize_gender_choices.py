from django.db import migrations, models


def normalize_gender(apps, schema_editor):
    users = apps.get_model('users', 'User').objects.using(schema_editor.connection.alias)
    # 只清理已移除的选项；其他历史值需人工核对，不能猜测或改成男/女。
    if users.filter(gender__isnull=False).exclude(gender__in=['男', '女', '', '暂不填写']).exists():
        raise RuntimeError('存在非男/女的历史性别值，请核对后再执行 users.0013；未自动清理这些值。')
    users.filter(gender__in=['', '暂不填写']).update(gender=None)


class Migration(migrations.Migration):
    dependencies = [('users', '0012_user_career_goal_user_other_skills_user_profile_and_more')]

    operations = [
        migrations.RunPython(normalize_gender, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user', name='gender',
            field=models.CharField(blank=True, choices=[('男', '男'), ('女', '女')], max_length=10, null=True, verbose_name='性别'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(
                check=models.Q(gender__in=['男', '女']) | models.Q(gender__isnull=True),
                name='users_gender_valid_or_null',
            ),
        ),
    ]
