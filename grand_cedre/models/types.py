from enum import Enum


class RoomType:
    individual = "individual"
    collective = "collective"


class RoomTypeEnum(Enum):
    individual = "Cabinet"
    collective = "Salle collective"

    def __str__(self):
        return self.name


class ContractType:
    standard = "standard"
    one_shot = "one_shot"
    exchange = "exchange"
    recurring = "recurring"
    flat_rate = "flat_rate"


class ContractTypeEnum(Enum):
    standard = "Standard"
    one_shot = "Réservation occasionelle"
    exchange = "Échange"
    recurring = "Occupation récurrente"
    flat_rate = "Forfait"


class PricingType:
    individual_modular = "individual_modular"
    collective_regular = "collective_regular"
    collective_occasional = "collective_occasional"
    flat_rate = "flat_rate"
    recurring = "recurring"
