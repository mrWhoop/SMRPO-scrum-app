from django.db import models


class Project(models.Model):

    # lastnik projekta
    product_owner = models.TextField

    # skrbnik metodologije
    scrum_master = models.TextField

# dev team member without any special role
class DevTeamMember(models.Model):

    userId = models.IntegerField() # for now, waiting on user management stuff

    projectId = models.ForeignKey(Project, on_delete=models.CASCADE)

class Sprint(models.Model):

    start = models.DateTimeField()

    end = models.DateTimeField()

    expectedSpeed = models.IntegerField()

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class Story(models.Model):

    name = models.TextField

    description = models.TextField

    # possible values: 'must have', 'should have', 'could have', 'won't have'
    priority = models.TextField

    businessValue = models.IntegerField

    # casovna zahtevnost
    timeCost = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    timeSpent = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    assignedUser = models.IntegerField

    userConfirmed = models.BooleanField(default=False)

    comment = models.TextField

    # 'new', 'in progress', 'done', 'accepted', 'rejected', 'incomlete'
    developmentStatus = models.TextField

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # do we need to save the state as was after the sprint comlpetion or can we rewire to new sprint in case of rejection
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, null=True)