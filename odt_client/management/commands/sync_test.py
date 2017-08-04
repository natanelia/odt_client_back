from django.core.management.base import BaseCommand, CommandError
from ta.reference import ValueRef
from ta_models.ta.models import TA_ReferencingTest
from ta_models.goblin.apps.catalogue.models import *
from ta_models.accounts.models import *

class Command(BaseCommand):

    def handle(self, *args, **options):
        # a = TA_ReferencingTest.objects.get(id=5)
        # print a
        # a.state = ValueRef('California')
        # a.save()


        a = TA_ReferencingTest.objects.all()
        for b in a:
            print b.state
            print b.id

        # products = TA_Product.objects.all()
        # for product in products:
        #     print product



        account = TA_Account.objects.all()
        for a in account:
            print a.__dict__
            
        product = TA_Product.objects.get(id=5)
        print product.id
        print product.__dict__
        print product.parent.__dict__