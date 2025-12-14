from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ProductInput:
    code_barre: str | None
    libelle: str
    prix_achat_ht: float | None
    prix_vente_ttc: float | None
    tva: float | None = None
    unite: Any = None
    conditionnement: Any = None
    invoice_id: str | None = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code_barre": self.code_barre,
            "nom": self.libelle,
            "prix_achat": self.prix_achat_ht,
            "prix_vente": self.prix_vente_ttc,
            "tva": self.tva,
            "unite": self.unite,
            "conditionnement": self.conditionnement,
            "invoice_id": self.invoice_id,
            # Alias pour compat produit_loader
            "codes": self.code_barre,
        }


def from_row(row: Dict[str, Any]) -> ProductInput:
    return ProductInput(
        code_barre=row.get("code_barre") or row.get("codes"),
        libelle=row.get("libelle") or row.get("nom") or "",
        prix_achat_ht=row.get("prix_achat_ht") or row.get("prix_achat"),
        prix_vente_ttc=row.get("prix_vente_ttc") or row.get("prix_vente"),
        tva=row.get("tva"),
        unite=row.get("unite"),
        conditionnement=row.get("conditionnement") or row.get("qte_init"),
        invoice_id=row.get("invoice_id"),
    )
