from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Blog(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    word_count = models.PositiveIntegerField(default=0)


    def __str__(self):
        return self.title

    def count_words(self, text):

        return len(text.split())

    def save(self, *args, **kwargs):

        self.word_count = self.count_words(self.content)
        super().save(*args, **kwargs)


class BlogPermission(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission_type = models.CharField(max_length=50, choices=[('Full Access', 'Full Access'), ('Watch Only', 'Watch Only')])

    class Meta:
        unique_together = ('blog', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.permission_type} for {self.blog.title}"


@receiver(post_save, sender=Blog)
def assign_author_permission(sender, instance, created, **kwargs):
    if created:
        BlogPermission.objects.create(
            blog=instance,
            user=instance.author,
            permission_type="Full Access"
        )
