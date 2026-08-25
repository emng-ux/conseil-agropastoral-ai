-- Migration : support multi-organisations
--
-- Objectif : permettre à plusieurs organisations clientes de partager la même
-- base Supabase, chacune totalement cloisonnée des autres, sans rien casser
-- pour l'organisation existante (ses données restent valides, avec
-- organization_id = NULL, traitées comme "organisation historique unique"
-- tant que ORGANIZATION_ID n'est pas configuré côté application).
--
-- À exécuter dans Supabase : Table Editor... non, SQL Editor -> coller ce
-- fichier -> Run. Ne PAS exécuter avant d'avoir testé la branche
-- feature/multi-organisations en conditions réelles.

-- 1. Table des organisations elles-mêmes (remplace à terme org_settings,
--    qui ne gérait qu'un seul enregistrement global).
create table if not exists organizations (
    id text primary key,                    -- identifiant court, ex. "efa_moungo"
    nom_organisation text not null,
    logo_base64 text,
    devise text not null default 'FCFA',
    llm_provider text not null default 'anthropic',
    created_at timestamptz not null default now()
);

-- 2. Rattachement de chaque table existante à une organisation.
--    Nullable : les lignes déjà existantes (organisation historique) restent
--    valides avec organization_id = NULL.
alter table if exists users
    add column if not exists organization_id text references organizations(id);

alter table if exists diagnostics
    add column if not exists organization_id text references organizations(id);

alter table if exists messages
    add column if not exists organization_id text references organizations(id);

alter table if exists activity_log
    add column if not exists organization_id text references organizations(id);

-- 3. Index pour que le filtrage par organisation reste rapide même avec
--    beaucoup de diagnostics/messages cumulés.
create index if not exists idx_users_org on users(organization_id);
create index if not exists idx_diagnostics_org on diagnostics(organization_id);
create index if not exists idx_messages_org on messages(organization_id);
create index if not exists idx_activity_log_org on activity_log(organization_id);

-- 4. Sécurité renforcée : empêcher au niveau de la base elle-même (pas
--    seulement dans le code Python) qu'une requête mal filtrée expose des
--    données d'une autre organisation. Étape à finaliser après les tests
--    applicatifs -- nécessite l'activation de Row Level Security et une
--    politique par table. Laissé en commentaire volontairement : à activer
--    seulement une fois le cloisonnement testé de bout en bout côté
--    application, car RLS peut bloquer des accès légitimes si mal configuré.
--
-- alter table diagnostics enable row level security;
-- create policy diagnostics_org_isolation on diagnostics
--     using (organization_id = current_setting('request.jwt.claims.organization_id', true));
