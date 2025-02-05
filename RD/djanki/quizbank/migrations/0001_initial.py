# Generated by Django 4.2.10 on 2024-04-17 00:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('is_knowledge_point', models.BooleanField(default=False)),
                ('order', models.FloatField(default=0.0, help_text='用于设置显示顺序')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='QuestionType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_code', models.CharField(choices=[('SC', '单选题'), ('MC', '多选题'), ('FB', '填空题'), ('TF', '判断题'), ('CPFB', '程序填空题'), ('CP', '编程题'), ('SA', '简答题'), ('ES', '论述题')], max_length=5, unique=True)),
                ('description', models.CharField(max_length=101)),
            ],
        ),
        migrations.CreateModel(
            name='SupportObjective',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('description', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0, help_text='用于设置显示顺序')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_objectives', to='quizbank.course')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('summary', models.TextField()),
                ('content_markdown', models.TextField()),
                ('answer_markdown', models.TextField()),
                ('answer_json', models.JSONField()),
                ('explanation_markdown', models.TextField()),
                ('categories', models.ManyToManyField(limit_choices_to={'is_knowledge_point': True}, related_name='questions', to='quizbank.category')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quizbank.course')),
                ('question_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quizbank.questiontype')),
                ('support_objectives', models.ManyToManyField(related_name='questions', to='quizbank.supportobjective')),
            ],
        ),
        migrations.AddField(
            model_name='category',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='quizbank.course'),
        ),
        migrations.AddField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='quizbank.category'),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('parent', 'name')},
        ),
    ]
