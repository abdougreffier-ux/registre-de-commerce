"""
L'app ``rejets`` ne modélise pas d'entité propre : le rejet est un état
(``StatutInscription.REJETEE``) porté par l'inscription elle-même, motivé
par un des motifs limitatifs de l'article 80 (``Inscription.motif_rejet``).

Cette app expose uniquement des vues de consultation et des agrégats
(suivi des rejets pour le greffe et l'auditeur). Elle n'introduit aucune
règle nouvelle.
"""
