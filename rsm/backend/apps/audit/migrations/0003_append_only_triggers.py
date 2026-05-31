"""
Migration — pose des triggers PostgreSQL interdisant UPDATE et DELETE sur la
table du journal d'audit. Défense complémentaire à l'override applicatif.

Art. 79, § 5.2 du TDR : toute modification rétroactive du journal doit être
techniquement impossible, indépendamment de l'application.
"""
from django.db import migrations

SQL_UP = """
CREATE OR REPLACE FUNCTION rsm_audit_interdire_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '42501',
        MESSAGE = 'Journal d''audit inalterable : UPDATE/DELETE interdit (article 79).';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS rsm_audit_pas_update ON audit_entreeaudit;
CREATE TRIGGER rsm_audit_pas_update
BEFORE UPDATE ON audit_entreeaudit
FOR EACH ROW EXECUTE FUNCTION rsm_audit_interdire_mutation();

DROP TRIGGER IF EXISTS rsm_audit_pas_delete ON audit_entreeaudit;
CREATE TRIGGER rsm_audit_pas_delete
BEFORE DELETE ON audit_entreeaudit
FOR EACH ROW EXECUTE FUNCTION rsm_audit_interdire_mutation();
"""

SQL_DOWN = """
DROP TRIGGER IF EXISTS rsm_audit_pas_update ON audit_entreeaudit;
DROP TRIGGER IF EXISTS rsm_audit_pas_delete ON audit_entreeaudit;
DROP FUNCTION IF EXISTS rsm_audit_interdire_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_initial"),
    ]
    operations = [
        migrations.RunSQL(SQL_UP, reverse_sql=SQL_DOWN),
    ]
