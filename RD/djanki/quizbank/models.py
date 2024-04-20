from django.db import models


# 题目类型
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

# 课程
class Course(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# 知识点
class Category(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="categories" # 所属课程
    )
    name = models.CharField(max_length=256) # 知识点名称
    parent = models.ForeignKey( # 父级知识点，允许为空，表示顶级分类
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    is_knowledge_point = models.BooleanField(default=False) # 是否为知识点
    order = models.FloatField(default=0.0, help_text="用于设置显示顺序")

    class Meta:
        unique_together = ("parent", "name") # 设置parent和name的组合唯一，保证同一父分类下没有重名的子分类
        ordering = ["order"]

    def __str__(self):
        return self.name

# 支撑目标
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

# 问题
class Question(models.Model):
    # 题目类型
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE)
    # 对应知识点（多对多关系，一个题目可以对应多个知识点）
    categories = models.ManyToManyField(
        Category,
        limit_choices_to={"is_knowledge_point": True},
        related_name="questions",
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
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

# 问题中的图片
class QuestionImage(models.Model):
    question = models.ForeignKey(Question, related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField(max_length=1024)

    def __str__(self):
        return f"Image for {self.question.id}"