from datetime import timedelta, timezone
from django.db import models
from quizbank.models import Course, Question
from login.models import User

# Create your models here.

# 学习记录
class LearningRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="题目")
    ef = models.FloatField(default=2.5, verbose_name="易度系数(EF)")
    interval = models.IntegerField(default=1, verbose_name="复习间隔（天数）")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="记录创建时间")
    next_review_date = models.DateTimeField(verbose_name="下一次复习日期")
    last_review_date = models.DateTimeField(verbose_name="最后一次复习日期")
    repetition = models.IntegerField(default=0, verbose_name="复习次数")
    last_quality = models.IntegerField(default=0, verbose_name="最后一次质量评分")
    last_review_date = models.DateField(verbose_name="最后一次复习日期")
    status = models.CharField(
        max_length=10,
        choices=[
            ('learning', '未学习'),
            ('reviewing', '复习中'),
            ('mastered', '已掌握')
        ],
        default='learning',
        verbose_name="状态"
    )

    class Meta:
        indexes = [
            models.Index(fields=['user', 'next_review_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.question.id} - {self.status}"

    def save(self, *args, **kwargs):
        """在保存记录时更新复习状态。"""
        self.update_status()
        super().save(*args, **kwargs)

    # 更新状态
    def update_status(self):
        """根据EF和复习间隔等参数自动更新状态。"""
        if self.last_quality >= 4 and self.interval > 30:
            self.status = 'mastered'
        else:
            self.status = 'reviewing'

    # SM-2算法核心
    def update_learning_parameters(self, quality_score):
        if quality_score < 0 or quality_score > 5:
            raise ValueError("响应质量必须在0到5之间")

        # 更新ef值
        self.ef = max(1.3, self.ef + (0.1 - (5 - quality_score) * (0.08 + (5 - quality_score) * 0.02)))

        # 计算重复间隔
        if self.repetition == 0:
            self.interval = 1
        elif self.repetition == 1:
            self.interval = 6
        else:
            self.interval *= self.ef

        self.repetition += 1
        self.last_quality = quality_score
        self.next_review_date = timezone.now().date() + timedelta(days=self.interval)
        self.update_status()

        self.save()        

# 学习情况
class CourseLearningStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_learning_statuses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learning_statuses')
    learning = models.IntegerField(default=0, verbose_name="未学习的试题数量")
    reviewing = models.IntegerField(default=0, verbose_name="复习中的试题数量")
    mastered = models.IntegerField(default=0, verbose_name="已掌握的试题数量")

    class Meta:
        unique_together = ('user', 'course')  # 确保每个用户对每个课程只有一条记录
        verbose_name = "课程学习状态"
        verbose_name_plural = "课程学习状态"

    def __str__(self):
        return f"{self.user.username} - {self.course} - Unlearned: {self.learning}, Reviewing: {self.reviewing}, Mastered: {self.mastered}"