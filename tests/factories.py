# Use factory to generate sample data

"""
Test Factory to make fake objects for testing
"""
import factory
#from basefactory import BaseFactory

from factory.fuzzy import FuzzyChoice
from service.models import Pprofile, Pname, Paddress, Gender

class NameFactory(factory.Factory):
    """ Creates fake personal name """
    class Meta:
        model = Pname

    id = factory.Sequence(lambda n: n)
    family = factory.Faker("last_name")
    given_1 = factory.Faker("first_name")

    #Pprofile = factory.SubFactory(PatFactory, name=[])


class AddressFactory(factory.Factory):
    """ Creates fake personal address """
    class Meta:
        model = Paddress

    id = factory.Sequence(lambda n: n)
    line_1 = factory.Faker("street_address")
    city = factory.Faker("city")
    state = factory.Faker("state_abbr")
    postalCode = factory.Faker("postalcode")

    #Pprofile = factory.SubFactory(PatFactory, addresses=[])

class PatFactory(factory.Factory):
#class PatFactory(BaseFactory):
    """ Creates fake pets that you don't have to feed """

    class Meta:
        model = Pprofile

    id = factory.Sequence(lambda n: n)
    phone_home = factory.Faker("phone_number")
    email = factory.Faker("email")
    state = factory.Faker("state_abbr")
    postalcode = factory.Faker("postalcode")
    DOB = factory.Faker("birthdate")
    active = FuzzyChoice(choices=[True, False])
    gender = FuzzyChoice(choices=[Gender.male, Gender.female, Gender.unknown])

    name = factory.List([
        factory.SubFactory(NameFactory)
    ])

    #name = factory.RelatedFactoryList(NameFactory, factory_related_name='pprofile', size=1)

    address = factory.List([
        factory.SubFactory(AddressFactory),
        factory.SubFactory(AddressFactory),
        factory.SubFactory(AddressFactory),
    ])

    #address = factory.RelatedFactoryList(AddressFactory, factory_related_name='pprofile', size=3)
