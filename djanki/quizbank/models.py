from django.db import models


class QuestionType(models.Model):
    TYPE_CHOICES = [
        ("SC", "单选题"),
        ("MC", "多选题"),
        ("FB", "填空题"),
        ("TF", "判断题"),
        ("CPFB", "程序填空题"),
        ("CP", "编程题"),
        ("SA", "简答题"),
        ("ES", "论述题"),
    ]
    type_code = models.CharField(max_length=5, choices=TYPE_CHOICES, unique=True)
    description = models.CharField(max_length=101)

    def __str__(self):
        return self.description


class Course(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=256)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    is_knowledge_point = models.BooleanField(default=False)
    order = models.FloatField(default=0.0, help_text="用于设置显示顺序")

    class Meta:
        unique_together = ("parent", "name")
        ordering = ["order"]

    def __str__(self):
        return self.name


class SupportObjective(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="support_objectives"
    )
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    order = models.FloatField(default=0.0, help_text="用于设置显示顺序")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Question(models.Model):
    # 题目类型
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE)
    # 对应知识点（多对多关系，一个题目可以对应多个知识点）
    categories = models.ManyToManyField(
        Category,
        limit_choices_to={"is_knowledge_point": True},
        related_name="questions",
    )
    # 对应支撑目标（多对多关系，一个题目可以支撑多个目标）
    support_objectives = models.ManyToManyField(
        SupportObjective, related_name="questions"
    )
    # 简介，保存纯文本
    summary = models.TextField()
    # 题目内容，保存Markdown
    content_markdown = models.TextField()
    # 答案1，保存Markdown
    answer_markdown = models.TextField()
    # 答案2，保存json（可以用于存储结构化答案或多种答案选项）
    answer_json = models.JSONField()
    # 解析，保存Markdown
    explanation_markdown = models.TextField()

    def __str__(self):
        return f"{self.question_type}: {self.summary[:50]}"
