from django.db import models
from django.contrib.auth.models import User

class LastLogin(models.Model):
    lastLoginTime = models.DateTimeField(null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

class Project(models.Model):

    projectName = models.TextField()

    # lastnik projekta
    product_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_owner')

    # skrbnik metodologije
    scrum_master = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scrum_master')

    description = models.TextField()

    def getStories(self):
        return Story.objects.filter(project_id=self)

    def getDevTeamMembers(self):
        return DevTeamMember.objects.filter(projectId_id=self)

    def getPosts(self):
        return Post.objects.filter(project_id=self).order_by('-time_posted')

    
    
    stories = property(getStories)

# dev team member without any special role
class DevTeamMember(models.Model):

    userId = models.ForeignKey(User, on_delete=models.CASCADE)

    projectId = models.ForeignKey(Project, on_delete=models.CASCADE)

    def getProjects(self):
        return Project.objects.filter(id=self)

    projects = property(getProjects)

class Sprint(models.Model):

    start = models.DateField()

    end = models.DateField()

    expectedSpeed = models.IntegerField()

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class Story(models.Model):

    name = models.TextField()

    description = models.TextField()

    # possible values: 'must have', 'should have', 'could have', 'won't have'
    priority = models.TextField()

    businessValue = models.IntegerField()

    # casovna zahtevnost
    timeCost = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    timeSpent = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    comment = models.TextField(null=True)

    # 'new', 'in progress', 'done', 'accepted', 'rejected', 'incomplete'
    developmentStatus = models.TextField()

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # do we need to save the state as was after the sprint comlpetion or can we rewire to new sprint in case of rejection
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, null=True)

    def getTasks(self):
        return Task.objects.filter(story_id=self)

    tasks = property(getTasks)

class Task(models.Model):

    story = models.ForeignKey(Story, on_delete=models.CASCADE)

    timeCost = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    description = models.TextField()

    assignedUser = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    # accepted, rejected, pending, free
    userConfirmed = models.TextField()

    done = models.BooleanField(default=False)

    def getTimeSpent(self):
        return TimeSpent.objects.filter(task_id=self)

    timeSpent = property(getTimeSpent)

class TimeSpent(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    time_spent = models.IntegerField(null=True)

    date = models.DateField()

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    description = models.TextField()

    time_posted = models.DateTimeField()

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
