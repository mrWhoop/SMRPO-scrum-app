from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):

    projectName = models.TextField()

    # lastnik projekta
    product_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_owner')

    # skrbnik metodologije
    scrum_master = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scrum_master')

# dev team member without any special role
class DevTeamMember(models.Model):

    userId = models.ForeignKey(User, on_delete=models.CASCADE)

    projectId = models.ForeignKey(Project, on_delete=models.CASCADE)

class Sprint(models.Model):

    start = models.DateTimeField()

    end = models.DateTimeField()

    expectedSpeed = models.IntegerField()

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class Story(models.Model):

    name = models.TextField(unique = True)

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

class Task(models.Model):

    story = models.ForeignKey(Story, on_delete=models.CASCADE)

    time_spent = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    description = models.TextField()

    assignedUser = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    userConfirmed = models.BooleanField(default=False)
