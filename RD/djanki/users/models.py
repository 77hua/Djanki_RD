from datetime import timedelta
from django.utils import timezone
from django.db import models
from quizbank.models import Course, Question
from login.models import User

# Create your models here.

# 学习记录
class LearningRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="题目")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="所属课程")
    ef = models.FloatField(default=2.5, verbose_name="易度系数(EF)")
    interval = models.IntegerField(default=1, verbose_name="复习间隔（天数）")
    created_at = models.DateField(auto_now_add=True, verbose_name="记录创建时间")
    next_review_date = models.DateField(verbose_name="下一次复习日期")
    last_review_date = models.DateField(verbose_name="最后一次复习日期")
    repetition = models.IntegerField(default=0, verbose_name="复习次数")
    last_quality = models.IntegerField(default=0, verbose_name="最后一次质量评分")
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
        return f"{self.user.username} - {self.course.name} - {self.status}"

    def save(self, *args, **kwargs):
        """在保存记录时更新复习状态。"""
        self.update_status()
        super().save(*args, **kwargs)

    def update_status(self):
        # 规定：最后一次响应质量等于5 且 复习间隔大于30天的题目，归为：已掌握
        if self.last_quality == 5 and self.interval > 30:
            self.status = 'mastered'
        else:
            self.status = 'reviewing'
    # 算法核心
    def update_learning_parameters(self, quality_score):
        if quality_score < 0 or quality_score > 5:
            raise ValueError("响应质量必须在0到5之间")
        # 如果评分低于3，重置学习状态但不改变EF值
        if quality_score < 3:
            self.repetition = 0
            self.interval = 1
        elif quality_score < 4:
            # 如果评分等于3，保持间隔interval，增加复习次数
            self.repetition += 1
            self.ef = max(1.3, self.ef + (0.1 - (5 - quality_score) * (0.08 + (5 - quality_score) * 0.02)))
        else:
            # 只有评分达到4或以上时，按照SM-2算法更新EF和间隔
            self.ef = max(1.3, self.ef + (0.1 - (5 - quality_score) * (0.08 + (5 - quality_score) * 0.02)))
            if self.repetition == 0:
                self.interval = 1
            elif self.repetition == 1:
                self.interval = 6
            else:
                self.interval = int(self.ef * self.interval)
            self.repetition += 1

        self.last_quality = quality_score
        self.next_review_date = timezone.now().date() + timedelta(days=self.interval)
        self.update_status()
        self.save()
