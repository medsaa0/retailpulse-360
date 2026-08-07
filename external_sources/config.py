"""Configuration des sources externes simulées."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalSourcesConfig:
    """Paramètres de génération des sources externes."""

    seed: int = 42

    # Environ 8 % des lignes éligibles produisent un retour.
    return_rate: float = 0.08

    # Nombre de jours d'historique d'inventaire.
    inventory_days: int = 30

    # Historique utilisé pour les événements de livraison.
    delivery_history_days: int = 90

    def validate(self) -> None:
        """Valider les paramètres."""

        if not 0 <= self.return_rate <= 1:
            raise ValueError("return_rate doit être compris entre 0 et 1.")

        if self.inventory_days <= 0:
            raise ValueError("inventory_days doit être strictement positif.")

        if self.delivery_history_days <= 0:
            raise ValueError("delivery_history_days doit être strictement positif.")
