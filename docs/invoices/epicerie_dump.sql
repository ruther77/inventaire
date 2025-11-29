--
-- PostgreSQL database dump
--

\restrict SXTHT6JLyzxavKCDEFIlbOwAoiF8xp3PdPXN7HbgrYMrVUlf0azQS08ym9iFgiZ

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-0+deb13u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: type_cat; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.type_cat AS ENUM (
    'Epicerie sucree',
    'Epicerie salee',
    'Alcool',
    'Autre',
    'Afrique',
    'Boissons',
    'Hygiene'
);


ALTER TYPE public.type_cat OWNER TO postgres;

--
-- Name: type_mouvement; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.type_mouvement AS ENUM (
    'ENTREE',
    'SORTIE',
    'TRANSFERT',
    'INVENTAIRE'
);


ALTER TYPE public.type_mouvement OWNER TO postgres;

--
-- Name: update_stock_actuel(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_stock_actuel() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Mettre à jour le stock dans la table produits
    UPDATE produits
    SET stock_actuel = stock_actuel + CASE
        WHEN NEW.type = 'ENTREE' THEN NEW.quantite
        WHEN NEW.type = 'SORTIE' THEN -NEW.quantite
        -- Ajoutez ici d'autres types si nécessaire (ex: INVENTAIRE, TRANSFERT)
        ELSE 0
    END
    WHERE id = NEW.produit_id;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_stock_actuel() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: mouvements_stock; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mouvements_stock (
    id integer NOT NULL,
    produit_id integer NOT NULL,
    type public.type_mouvement NOT NULL,
    quantite numeric(12,3) NOT NULL,
    source text,
    date_mvt timestamp without time zone DEFAULT now() NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT mouvements_stock_quantite_check CHECK ((quantite > (0)::numeric))
);


ALTER TABLE public.mouvements_stock OWNER TO postgres;

--
-- Name: mouvements_stock_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.mouvements_stock_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mouvements_stock_id_seq OWNER TO postgres;

--
-- Name: mouvements_stock_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.mouvements_stock_id_seq OWNED BY public.mouvements_stock.id;


--
-- Name: produits; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.produits (
    id integer NOT NULL,
    nom text NOT NULL,
    categorie public.type_cat DEFAULT 'Autre'::public.type_cat,
    prix_achat numeric(10,2),
    prix_vente numeric(10,2),
    tva numeric(5,2) DEFAULT 0,
    seuil_alerte numeric(12,3) DEFAULT 0,
    actif boolean DEFAULT true,
    stock_actuel numeric(12,3) DEFAULT 0,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT produits_prix_achat_check CHECK ((prix_achat >= (0)::numeric)),
    CONSTRAINT produits_prix_vente_check CHECK ((prix_vente >= (0)::numeric)),
    CONSTRAINT produits_seuil_alerte_check CHECK ((seuil_alerte >= (0)::numeric)),
    CONSTRAINT produits_stock_actuel_check CHECK ((stock_actuel >= (0)::numeric)),
    CONSTRAINT produits_tva_check CHECK ((tva >= (0)::numeric))
);


ALTER TABLE public.produits OWNER TO postgres;

--
-- Name: produits_barcodes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.produits_barcodes (
    id integer NOT NULL,
    produit_id integer NOT NULL,
    code text NOT NULL,
    symbologie text,
    pays_iso2 character(2),
    is_principal boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.produits_barcodes OWNER TO postgres;

--
-- Name: produits_barcodes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.produits_barcodes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.produits_barcodes_id_seq OWNER TO postgres;

--
-- Name: produits_barcodes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.produits_barcodes_id_seq OWNED BY public.produits_barcodes.id;


--
-- Name: produits_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.produits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.produits_id_seq OWNER TO postgres;

--
-- Name: produits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.produits_id_seq OWNED BY public.produits.id;


--
-- Name: v_stock_courant; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_stock_courant AS
 SELECT p.id,
    p.nom,
    p.categorie,
    p.prix_achat,
    p.prix_vente,
    p.tva,
    p.seuil_alerte,
    p.actif,
    COALESCE(sum(
        CASE
            WHEN (m.type = ANY (ARRAY['ENTREE'::public.type_mouvement, 'INVENTAIRE'::public.type_mouvement, 'TRANSFERT'::public.type_mouvement])) THEN m.quantite
            WHEN (m.type = 'SORTIE'::public.type_mouvement) THEN (- m.quantite)
            ELSE (0)::numeric
        END), (0)::numeric) AS stock
   FROM (public.produits p
     LEFT JOIN public.mouvements_stock m ON ((m.produit_id = p.id)))
  GROUP BY p.id, p.nom, p.categorie, p.prix_achat, p.prix_vente, p.tva, p.seuil_alerte, p.actif
  ORDER BY p.nom;


ALTER VIEW public.v_stock_courant OWNER TO postgres;

--
-- Name: stock_courant; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.stock_courant AS
 SELECT id,
    nom,
    categorie,
    prix_achat,
    prix_vente,
    tva,
    seuil_alerte,
    actif,
    stock
   FROM public.v_stock_courant;


ALTER VIEW public.stock_courant OWNER TO postgres;

--
-- Name: v_alertes_rupture; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_alertes_rupture AS
 SELECT id,
    nom,
    categorie,
    (stock)::numeric(12,3) AS stock,
    seuil_alerte
   FROM public.v_stock_courant s
  WHERE (((stock)::numeric(12,3) <= COALESCE(seuil_alerte, (0)::numeric)) AND (actif = true))
  ORDER BY ((stock)::numeric(12,3));


ALTER VIEW public.v_alertes_rupture OWNER TO postgres;

--
-- Name: v_inventaire_negatif; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_inventaire_negatif AS
 SELECT id,
    nom,
    categorie,
    prix_achat,
    prix_vente,
    tva,
    seuil_alerte,
    actif,
    stock
   FROM public.v_stock_courant
  WHERE (stock < (0)::numeric)
  ORDER BY stock;


ALTER VIEW public.v_inventaire_negatif OWNER TO postgres;

--
-- Name: v_mouvements_recents; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_mouvements_recents AS
 SELECT m.id,
    m.date_mvt,
    m.type,
    m.quantite,
    m.source,
    p.id AS produit_id,
    p.nom,
    p.categorie
   FROM (public.mouvements_stock m
     JOIN public.produits p ON ((p.id = m.produit_id)))
  ORDER BY m.date_mvt DESC
 LIMIT 500;


ALTER VIEW public.v_mouvements_recents OWNER TO postgres;

--
-- Name: v_produits_codes; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_produits_codes AS
 SELECT p.id,
    p.nom,
    p.categorie,
    p.prix_achat,
    p.prix_vente,
    p.tva,
    p.actif,
    COALESCE(string_agg(pb.code, ', '::text ORDER BY pb.is_principal DESC, pb.code), ''::text) AS codes
   FROM (public.produits p
     LEFT JOIN public.produits_barcodes pb ON ((pb.produit_id = p.id)))
  GROUP BY p.id, p.nom, p.categorie, p.prix_achat, p.prix_vente, p.tva, p.actif
  ORDER BY p.nom;


ALTER VIEW public.v_produits_codes OWNER TO postgres;

--
-- Name: v_prod_barcodes; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_prod_barcodes AS
 SELECT id,
    nom,
    categorie,
    prix_achat,
    prix_vente,
    tva,
    actif,
    codes
   FROM public.v_produits_codes;


ALTER VIEW public.v_prod_barcodes OWNER TO postgres;

--
-- Name: v_produits_sans_barcode; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_produits_sans_barcode AS
 SELECT p.id,
    p.nom,
    p.categorie,
    p.prix_achat,
    p.prix_vente,
    p.tva,
    p.seuil_alerte,
    p.actif,
    p.stock_actuel,
    p.created_at,
    p.updated_at
   FROM (public.produits p
     LEFT JOIN public.produits_barcodes pb ON ((pb.produit_id = p.id)))
  WHERE (pb.id IS NULL)
  ORDER BY p.nom;


ALTER VIEW public.v_produits_sans_barcode OWNER TO postgres;

--
-- Name: v_rotation_30j; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_rotation_30j AS
 SELECT p.id,
    p.nom,
    sum(
        CASE
            WHEN (m.type = 'ENTREE'::public.type_mouvement) THEN m.quantite
            ELSE (0)::numeric
        END) AS entrees_30j,
    sum(
        CASE
            WHEN (m.type = 'SORTIE'::public.type_mouvement) THEN m.quantite
            ELSE (0)::numeric
        END) AS sorties_30j
   FROM (public.produits p
     LEFT JOIN public.mouvements_stock m ON (((m.produit_id = p.id) AND (m.date_mvt >= (now() - '30 days'::interval)))))
  GROUP BY p.id, p.nom
  ORDER BY (sum(
        CASE
            WHEN (m.type = 'SORTIE'::public.type_mouvement) THEN m.quantite
            ELSE (0)::numeric
        END)) DESC NULLS LAST;


ALTER VIEW public.v_rotation_30j OWNER TO postgres;

--
-- Name: v_stock_produits; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_stock_produits AS
 SELECT id,
    nom,
    categorie,
    prix_vente,
    tva,
    seuil_alerte,
    stock_actuel AS quantite_stock
   FROM public.produits p
  WHERE (actif = true);


ALTER VIEW public.v_stock_produits OWNER TO postgres;

--
-- Name: v_top_ventes_30j; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_top_ventes_30j AS
 SELECT p.id,
    p.nom,
    sum(
        CASE
            WHEN (m.type = 'SORTIE'::public.type_mouvement) THEN m.quantite
            ELSE (0)::numeric
        END) AS qte_sorties_30j
   FROM (public.produits p
     LEFT JOIN public.mouvements_stock m ON (((m.produit_id = p.id) AND (m.date_mvt >= (now() - '30 days'::interval)))))
  GROUP BY p.id, p.nom
  ORDER BY (sum(
        CASE
            WHEN (m.type = 'SORTIE'::public.type_mouvement) THEN m.quantite
            ELSE (0)::numeric
        END)) DESC NULLS LAST;


ALTER VIEW public.v_top_ventes_30j OWNER TO postgres;

--
-- Name: v_valorisation_stock; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_valorisation_stock AS
 SELECT id,
    nom,
    categorie,
    stock,
    prix_achat,
    round((stock * COALESCE(prix_achat, (0)::numeric)), 2) AS valeur_achat
   FROM public.v_stock_courant s
  WHERE (stock > (0)::numeric)
  ORDER BY (round((stock * COALESCE(prix_achat, (0)::numeric)), 2)) DESC;


ALTER VIEW public.v_valorisation_stock OWNER TO postgres;

--
-- Name: mouvements_stock id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mouvements_stock ALTER COLUMN id SET DEFAULT nextval('public.mouvements_stock_id_seq'::regclass);


--
-- Name: produits id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produits ALTER COLUMN id SET DEFAULT nextval('public.produits_id_seq'::regclass);


--
-- Name: produits_barcodes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produits_barcodes ALTER COLUMN id SET DEFAULT nextval('public.produits_barcodes_id_seq'::regclass);


--
-- Data for Name: mouvements_stock; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mouvements_stock (id, produit_id, type, quantite, source, date_mvt, created_at) FROM stdin;
1	2	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
2	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
3	13	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
4	18	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
5	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
6	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
7	19	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
8	21	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
9	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
10	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
11	22	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
12	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
13	23	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
14	44	ENTREE	10.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
15	3	ENTREE	10.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
16	45	ENTREE	5.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
17	3	ENTREE	5.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
18	3	ENTREE	9.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
19	46	ENTREE	9.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
20	47	ENTREE	7.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
21	3	ENTREE	7.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
22	48	ENTREE	18.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
23	3	ENTREE	18.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
24	51	ENTREE	8.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
25	3	ENTREE	8.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
26	52	ENTREE	4.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
27	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
28	3	ENTREE	5.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
29	3	ENTREE	5.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
30	68	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
31	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
32	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
33	70	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
34	3	ENTREE	8.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
35	71	ENTREE	8.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
36	3	ENTREE	26.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
37	72	ENTREE	26.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
38	73	ENTREE	7.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
39	3	ENTREE	7.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
40	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
41	77	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
42	78	ENTREE	6.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
43	3	ENTREE	6.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
44	3	ENTREE	7.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
45	3	ENTREE	7.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
46	80	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
47	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
48	81	ENTREE	7.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
49	3	ENTREE	7.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
50	82	ENTREE	11.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
51	3	ENTREE	11.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
52	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
53	83	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
54	84	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
55	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
56	3	ENTREE	6.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
57	85	ENTREE	6.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
58	86	ENTREE	4.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
59	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
60	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
61	87	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
62	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
63	88	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
64	89	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
65	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
66	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
67	90	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
68	91	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
69	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
70	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
71	92	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
72	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
73	94	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
74	3	ENTREE	5.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
75	3	ENTREE	5.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
76	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
77	126	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
78	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
79	131	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
80	3	ENTREE	8.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
81	3	ENTREE	8.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
82	3	ENTREE	17.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
83	154	ENTREE	17.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
84	155	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
85	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
86	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
87	157	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
88	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
89	158	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
90	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
91	161	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
92	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
93	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
94	162	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
95	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
96	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
97	166	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
98	167	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
99	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
100	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
101	168	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
102	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
103	169	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
104	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
105	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
106	170	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
107	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
108	172	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
109	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
110	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
111	173	ENTREE	4.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
112	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
113	175	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
114	3	ENTREE	6.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
115	176	ENTREE	6.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
116	177	ENTREE	5.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
117	3	ENTREE	5.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
118	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
119	178	ENTREE	5.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
120	3	ENTREE	5.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
121	180	ENTREE	6.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
122	3	ENTREE	6.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
123	181	ENTREE	10.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
124	3	ENTREE	10.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
125	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
126	182	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
127	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
128	183	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
129	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
130	184	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
131	3	ENTREE	10.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
132	201	ENTREE	10.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
133	205	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
134	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
135	216	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
136	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
137	217	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
138	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
139	218	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
140	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
141	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
142	225	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
143	226	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
144	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
145	227	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
146	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
147	231	ENTREE	5.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
148	3	ENTREE	5.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
149	241	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
150	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
151	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
152	242	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
153	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
154	244	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
155	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
156	246	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
157	247	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
158	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
159	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
160	252	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
161	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
162	3	ENTREE	1.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
163	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
164	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
165	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
166	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
167	256	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
168	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
169	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
170	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
171	3	ENTREE	2.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
172	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
173	3	ENTREE	4.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
174	262	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
175	263	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
176	264	ENTREE	4.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
177	265	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
178	3	ENTREE	3.000	Import facture - code nan	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
179	281	ENTREE	11.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
180	284	ENTREE	7.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
181	287	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
182	288	ENTREE	1.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
183	292	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
184	293	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
185	294	ENTREE	2.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
186	295	ENTREE	3.000	Import facture - création	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
187	297	ENTREE	5.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
188	298	ENTREE	25.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
189	299	ENTREE	15.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
190	300	ENTREE	19.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
191	301	ENTREE	4.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
192	302	ENTREE	29.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
193	303	ENTREE	6.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
194	304	ENTREE	3.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
195	305	ENTREE	2.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
196	308	ENTREE	7.000	Import facture - création	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
197	309	ENTREE	22.000	Import facture - création	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
198	310	ENTREE	3.000	Import facture - création	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
199	311	ENTREE	8.000	Import facture - création	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
200	312	ENTREE	7.000	Import facture - création	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
201	313	ENTREE	8.000	Import facture - création	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
202	314	ENTREE	12.000	Import facture - création	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
203	315	ENTREE	530.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
204	316	ENTREE	160.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
205	317	ENTREE	63.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
206	318	ENTREE	17.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
207	319	ENTREE	58.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
208	320	ENTREE	60.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
209	321	ENTREE	48.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
210	322	ENTREE	29.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
211	323	ENTREE	13.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
212	324	ENTREE	12.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
213	325	ENTREE	14.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
214	326	ENTREE	12.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
215	329	ENTREE	19.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
216	330	ENTREE	15.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
217	331	ENTREE	20.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
218	332	ENTREE	13.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
219	334	ENTREE	13.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
220	336	ENTREE	7.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
221	337	ENTREE	3.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
222	338	ENTREE	3.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
223	339	ENTREE	2.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
224	340	ENTREE	2.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
225	341	ENTREE	7.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
226	342	ENTREE	7.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
227	343	ENTREE	4.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
228	345	ENTREE	6.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
229	346	ENTREE	5.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
230	347	ENTREE	5.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
231	348	ENTREE	4.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
232	349	ENTREE	22.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
233	350	ENTREE	15.000	Import facture - création	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
234	352	ENTREE	377.000	Import facture - création	2025-10-30 12:07:11.398554	2025-10-30 12:07:11.398554
235	353	ENTREE	8.000	Import facture - création	2025-10-30 12:07:11.398554	2025-10-30 12:07:11.398554
236	315	ENTREE	442.000	Import facture - code 5010327325125	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
237	316	ENTREE	190.000	Import facture - code 3211200184743	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
238	317	ENTREE	70.000	Import facture - code 3439495507928	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
239	354	ENTREE	30.000	Import facture - création	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
240	355	ENTREE	27.000	Import facture - création	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
241	356	ENTREE	5.000	Import facture - création	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
242	357	ENTREE	5.000	Import facture - création	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
243	358	ENTREE	10.000	Import facture - création	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
244	359	ENTREE	20.000	Import facture - création	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
245	361	ENTREE	24.000	Import facture - création	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
246	310	ENTREE	3.000	Import facture	2025-10-30 12:08:00.448408	2025-10-30 12:08:00.448408
247	363	ENTREE	10.000	Import facture - création	2025-10-30 12:08:00.448408	2025-10-30 12:08:00.448408
248	315	ENTREE	451.000	Import facture - code 5010327325125	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
249	365	ENTREE	7.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
250	366	ENTREE	84.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
251	316	ENTREE	128.000	Import facture - code 3211200184743	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
252	367	ENTREE	17.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
253	368	ENTREE	39.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
254	369	ENTREE	32.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
255	370	ENTREE	16.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
256	371	ENTREE	238.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
257	320	ENTREE	20.000	Import facture - code 5410228203582	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
258	354	ENTREE	30.000	Import facture - code 5410228223580	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
259	372	ENTREE	5.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
260	321	ENTREE	26.000	Import facture - code 3155930400530	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
261	373	ENTREE	17.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
262	374	ENTREE	19.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
263	375	ENTREE	7.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
264	376	ENTREE	8.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
265	377	ENTREE	15.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
266	378	ENTREE	22.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
267	379	ENTREE	22.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
268	380	ENTREE	13.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
269	381	ENTREE	10.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
270	382	ENTREE	8.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
271	383	ENTREE	14.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
272	384	ENTREE	6.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
273	385	ENTREE	10.000	Import facture - création	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
274	315	ENTREE	451.000	Import facture - code 5010327325125	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
275	316	ENTREE	64.000	Import facture - code 3211200184743	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
276	367	ENTREE	17.000	Import facture - code 3175529657725	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
277	368	ENTREE	47.000	Import facture - code 3259354102060	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
278	369	ENTREE	16.000	Import facture - code 03179077103147	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
279	370	ENTREE	16.000	Import facture - code 03179077103154	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
280	386	ENTREE	33.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
281	387	ENTREE	16.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
282	388	ENTREE	13.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
283	389	ENTREE	5.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
284	390	ENTREE	5.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
285	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
286	391	ENTREE	9.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
287	392	ENTREE	4.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
288	393	ENTREE	11.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
289	345	ENTREE	6.000	Import facture - code 3439496604015	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
290	346	ENTREE	5.000	Import facture - code 3439496603995	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
291	347	ENTREE	5.000	Import facture - code 3439496604008	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
292	394	ENTREE	17.000	Import facture - création	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
293	361	ENTREE	25.000	Import facture - code 3439496810997	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
294	395	ENTREE	86.000	Import facture - création	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
295	396	ENTREE	387.000	Import facture - création	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
296	397	ENTREE	20.000	Import facture - création	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
297	398	ENTREE	10.000	Import facture - création	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
298	318	ENTREE	14.000	Import facture - code 3259356633067	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
299	399	ENTREE	226.000	Import facture - création	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
300	371	ENTREE	79.000	Import facture - code 3439495600360	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
301	315	ENTREE	451.000	Import facture - code 5010327325125	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
302	400	ENTREE	103.000	Import facture - création	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
303	366	ENTREE	47.000	Import facture - code 3257150100228	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
304	316	ENTREE	128.000	Import facture - code 3211200184743	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
305	368	ENTREE	47.000	Import facture - code 3259354102060	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
306	386	ENTREE	33.000	Import facture - code 3439495501568	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
307	389	ENTREE	5.000	Import facture - code 03439495113495	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
308	356	ENTREE	5.000	Import facture - code 3439496607221	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
309	401	ENTREE	2.000	Import facture - création	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
310	361	ENTREE	25.000	Import facture - code 3439496810997	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
311	402	ENTREE	85.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
312	315	ENTREE	406.000	Import facture - code 5010327325125	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
313	403	ENTREE	7.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
314	404	ENTREE	7.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
315	405	ENTREE	7.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
316	406	ENTREE	22.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
317	407	ENTREE	76.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
318	408	ENTREE	10.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
319	409	ENTREE	14.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
320	410	ENTREE	14.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
321	316	ENTREE	192.000	Import facture - code 3211200184743	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
322	411	ENTREE	25.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
323	367	ENTREE	17.000	Import facture - code 3175529657725	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
324	369	ENTREE	32.000	Import facture - code 03179077103147	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
325	412	ENTREE	35.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
326	413	ENTREE	20.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
327	414	ENTREE	11.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
328	397	ENTREE	40.000	Import facture - code 3439495508345	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
329	370	ENTREE	32.000	Import facture - code 03179077103154	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
330	415	ENTREE	21.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
331	373	ENTREE	17.000	Import facture - code 3439495405064	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
332	374	ENTREE	17.000	Import facture - code 3439495403794	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
333	416	ENTREE	6.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
334	375	ENTREE	7.000	Import facture - code 3439495405040	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
335	417	ENTREE	8.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
336	376	ENTREE	8.000	Import facture - code 3439495406320	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
337	377	ENTREE	15.000	Import facture - code 3439495406368	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
338	418	ENTREE	44.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
339	419	ENTREE	12.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
340	391	ENTREE	9.000	Import facture - code 3439495102796	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
341	382	ENTREE	8.000	Import facture - code 4337182248705	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
342	420	ENTREE	64.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
343	330	ENTREE	15.000	Import facture - code 5000159555722	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
344	383	ENTREE	14.000	Import facture - code 3281130011129	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
345	421	ENTREE	15.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
346	422	ENTREE	13.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
347	423	ENTREE	14.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
348	424	ENTREE	12.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
349	425	ENTREE	11.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
350	426	ENTREE	10.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
351	427	ENTREE	14.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
352	336	ENTREE	8.000	Import facture - code 8445290872036	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
353	356	ENTREE	5.000	Import facture - code 3439496607221	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
354	357	ENTREE	5.000	Import facture - code 3439496000657	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
355	345	ENTREE	6.000	Import facture - code 3439496604015	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
356	428	ENTREE	4.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
357	429	ENTREE	4.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
358	430	ENTREE	8.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
359	431	ENTREE	9.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
360	432	ENTREE	2.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
361	433	ENTREE	6.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
362	435	ENTREE	14.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
363	394	ENTREE	17.000	Import facture - code 4337182138341	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
364	436	ENTREE	8.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
365	437	ENTREE	7.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
366	438	ENTREE	6.000	Import facture - création	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
367	315	ENTREE	225.000	Import facture - code 5010327325125	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
368	439	ENTREE	97.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
369	440	ENTREE	123.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
370	316	ENTREE	64.000	Import facture - code 3211200184743	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
371	441	ENTREE	13.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
372	367	ENTREE	17.000	Import facture - code 3175529657725	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
373	369	ENTREE	14.000	Import facture - code 03179077103147	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
374	397	ENTREE	20.000	Import facture - code 3439495508345	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
375	370	ENTREE	29.000	Import facture - code 03179077103154	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
376	399	ENTREE	221.000	Import facture - code 3049614222252	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
377	442	ENTREE	112.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
378	354	ENTREE	30.000	Import facture - code 5410228223580	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
379	352	ENTREE	194.000	Import facture - code 3119783018823	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
380	443	ENTREE	12.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
381	444	ENTREE	19.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
382	445	ENTREE	7.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
383	446	ENTREE	10.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
384	447	ENTREE	7.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
385	448	ENTREE	7.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
386	449	ENTREE	7.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
387	450	ENTREE	7.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
388	451	ENTREE	18.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
389	383	ENTREE	14.000	Import facture - code 3281130011129	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
390	345	ENTREE	6.000	Import facture - code 3439496604015	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
391	346	ENTREE	5.000	Import facture - code 3439496603995	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
392	361	ENTREE	25.000	Import facture - code 3439496810997	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
393	452	ENTREE	18.000	Import facture - création	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
394	453	ENTREE	30.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
395	315	ENTREE	451.000	Import facture - code 5010327325125	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
396	454	ENTREE	125.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
397	440	ENTREE	103.000	Import facture - code 5000267024325	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
398	455	ENTREE	337.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
399	456	ENTREE	21.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
400	457	ENTREE	53.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
401	458	ENTREE	23.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
402	459	ENTREE	267.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
403	460	ENTREE	4.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
404	461	ENTREE	4.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
405	462	ENTREE	4.000	Import facture - création	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
406	354	ENTREE	45.000	Import facture - code 5410228223580	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
407	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
408	418	ENTREE	49.000	Import facture - code 3075711382018	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
409	383	ENTREE	14.000	Import facture - code 3281130011129	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
410	345	ENTREE	6.000	Import facture - code 3439496604015	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
411	346	ENTREE	5.000	Import facture - code 3439496603995	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
412	347	ENTREE	5.000	Import facture - code 3439496604008	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
413	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
414	463	ENTREE	23.000	Import facture - création	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
415	464	ENTREE	20.000	Import facture - création	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
416	465	ENTREE	22.000	Import facture - création	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
417	466	ENTREE	23.000	Import facture - création	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
418	321	ENTREE	26.000	Import facture - code 3155930400530	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
419	467	ENTREE	4.000	Import facture - création	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
420	468	ENTREE	4.000	Import facture - création	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
421	469	ENTREE	69.000	Import facture - création	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
422	470	ENTREE	64.000	Import facture - création	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
423	315	ENTREE	135.000	Import facture - code 5010327325125	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
424	471	ENTREE	103.000	Import facture - création	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
425	472	ENTREE	34.000	Import facture - création	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
426	455	ENTREE	255.000	Import facture - code 05000299225332	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
427	473	ENTREE	149.000	Import facture - création	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
428	474	ENTREE	210.000	Import facture - création	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
429	475	ENTREE	115.000	Import facture - création	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
430	477	ENTREE	5.000	Import facture - création	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
431	439	ENTREE	97.000	Import facture - code 3099873045864	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
432	365	ENTREE	7.000	Import facture - code 3147697510607	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
433	365	ENTREE	7.000	Import facture	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
434	409	ENTREE	29.000	Import facture - code 3147690093602	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
435	410	ENTREE	29.000	Import facture - code 3147690094708	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
436	320	ENTREE	30.000	Import facture - code 5410228203582	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
437	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
438	478	ENTREE	20.000	Import facture - création	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
439	321	ENTREE	79.000	Import facture - code 3155930400530	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
440	322	ENTREE	30.000	Import facture - code 3119783016690	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
441	479	ENTREE	73.000	Import facture - création	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
442	480	ENTREE	51.000	Import facture - création	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
443	481	ENTREE	49.000	Import facture - création	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
444	379	ENTREE	31.000	Import facture - code 8002270116551	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
445	482	ENTREE	13.000	Import facture - création	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
446	316	ENTREE	128.000	Import facture - code 3211200184743	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
447	399	ENTREE	221.000	Import facture - code 3049614222252	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
448	354	ENTREE	60.000	Import facture - code 5410228223580	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
449	352	ENTREE	77.000	Import facture - code 3119783018823	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
450	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
451	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
452	391	ENTREE	9.000	Import facture - code 3439495102796	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
453	336	ENTREE	8.000	Import facture - code 8445290872036	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
454	361	ENTREE	25.000	Import facture - code 3439496810997	2025-10-30 12:12:16.376798	2025-10-30 12:12:16.376798
455	316	ENTREE	64.000	Import facture - code 3211200184743	2025-10-30 12:12:27.379196	2025-10-30 12:12:27.379196
456	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 12:12:27.379196	2025-10-30 12:12:27.379196
457	359	ENTREE	20.000	Import facture - code 4337182249290	2025-10-30 12:12:27.379196	2025-10-30 12:12:27.379196
458	483	ENTREE	350.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
459	459	ENTREE	55.000	Import facture - code 5011013100613	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
460	484	ENTREE	123.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
461	485	ENTREE	47.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
462	367	ENTREE	16.000	Import facture - code 3175529657725	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
463	368	ENTREE	74.000	Import facture - code 3259354102060	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
464	369	ENTREE	15.000	Import facture - code 03179077103147	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
465	397	ENTREE	20.000	Import facture - code 3439495508345	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
466	354	ENTREE	12.000	Import facture - code 5410228223580	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
467	352	ENTREE	96.000	Import facture - code 3119783018823	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
468	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
469	486	ENTREE	5.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
470	487	ENTREE	5.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
471	488	ENTREE	11.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
472	489	ENTREE	9.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
473	490	ENTREE	11.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
474	491	ENTREE	11.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
475	492	ENTREE	11.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
476	450	ENTREE	7.000	Import facture - code 5053990155361	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
477	493	ENTREE	4.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
478	494	ENTREE	5.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
479	306	ENTREE	5.000	Import facture	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
480	495	ENTREE	10.000	Import facture - création	2025-10-30 12:15:47.724561	2025-10-30 12:15:47.724561
481	320	ENTREE	10.000	Import facture - code 5410228203582	2025-10-30 12:16:27.234871	2025-10-30 12:16:27.234871
482	354	ENTREE	15.000	Import facture - code 5410228223580	2025-10-30 12:16:27.234871	2025-10-30 12:16:27.234871
483	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:16:27.234871	2025-10-30 12:16:27.234871
484	496	ENTREE	23.000	Import facture - création	2025-10-30 12:16:27.234871	2025-10-30 12:16:27.234871
485	497	ENTREE	99.000	Import facture - création	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
486	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
487	498	ENTREE	29.000	Import facture - création	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
488	352	ENTREE	239.000	Import facture - code 3119783018823	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
489	499	ENTREE	5.000	Import facture - création	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
490	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
491	380	ENTREE	12.000	Import facture - code 3179730004804	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
492	500	ENTREE	90.000	Import facture - création	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
493	501	ENTREE	24.000	Import facture - création	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
494	502	ENTREE	18.000	Import facture - création	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
495	503	ENTREE	24.000	Import facture - création	2025-10-30 12:16:40.566579	2025-10-30 12:16:40.566579
496	497	ENTREE	99.000	Import facture - code 3211200196883	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
497	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
498	498	ENTREE	29.000	Import facture - code 5000213003756	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
499	352	ENTREE	239.000	Import facture - code 3119783018823	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
500	499	ENTREE	5.000	Import facture - code 8850389110515	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
501	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
502	380	ENTREE	12.000	Import facture - code 3179730004804	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
503	500	ENTREE	90.000	Import facture - code 3439495011388	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
504	501	ENTREE	24.000	Import facture - code 3276650013203	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
505	502	ENTREE	18.000	Import facture - code 3439495107906	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
506	503	ENTREE	24.000	Import facture - code 8715700120065	2025-10-30 12:17:04.703977	2025-10-30 12:17:04.703977
507	497	ENTREE	99.000	Import facture - code 3211200196883	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
508	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
509	498	ENTREE	29.000	Import facture - code 5000213003756	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
510	352	ENTREE	239.000	Import facture - code 3119783018823	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
511	499	ENTREE	5.000	Import facture - code 8850389110515	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
512	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
513	380	ENTREE	12.000	Import facture - code 3179730004804	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
514	500	ENTREE	90.000	Import facture - code 3439495011388	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
515	501	ENTREE	24.000	Import facture - code 3276650013203	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
516	502	ENTREE	18.000	Import facture - code 3439495107906	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
517	503	ENTREE	24.000	Import facture - code 8715700120065	2025-10-30 12:17:10.232276	2025-10-30 12:17:10.232276
518	320	ENTREE	54.000	Import facture - code 5410228203582	2025-10-30 12:17:25.049296	2025-10-30 12:17:25.049296
519	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:17:25.049296	2025-10-30 12:17:25.049296
520	321	ENTREE	53.000	Import facture - code 3155930400530	2025-10-30 12:17:25.049296	2025-10-30 12:17:25.049296
521	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
522	504	ENTREE	9.000	Import facture - création	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
523	505	ENTREE	11.000	Import facture - création	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
524	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
525	507	ENTREE	2.000	Import facture - création	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
526	508	ENTREE	24.000	Import facture - création	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
527	509	ENTREE	3.000	Import facture - création	2025-10-30 12:18:04.059187	2025-10-30 12:18:04.059187
528	315	ENTREE	164.000	Import facture - code 5010327325125	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
529	365	ENTREE	7.000	Import facture - code 3147697510607	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
530	409	ENTREE	56.000	Import facture - code 3147690093602	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
531	510	ENTREE	93.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
532	511	ENTREE	30.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
533	512	ENTREE	13.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
534	388	ENTREE	26.000	Import facture - code 3438935000135	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
535	513	ENTREE	2.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
536	514	ENTREE	12.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
537	481	ENTREE	43.000	Import facture - code 5449000017673	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
538	515	ENTREE	12.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
539	516	ENTREE	5.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
540	390	ENTREE	5.000	Import facture - code 03439495112917	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
541	393	ENTREE	14.000	Import facture - code 3168930104285	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
542	490	ENTREE	11.000	Import facture - code 05053990107476	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
543	492	ENTREE	12.000	Import facture - code 05053990161614	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
544	517	ENTREE	38.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
545	451	ENTREE	39.000	Import facture - code 8000500121467	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
546	518	ENTREE	16.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
547	329	ENTREE	17.000	Import facture - code 04008400264004	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
548	519	ENTREE	9.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
549	520	ENTREE	9.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
550	331	ENTREE	19.000	Import facture - code 5000159461801	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
551	521	ENTREE	21.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
552	522	ENTREE	3.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
553	524	ENTREE	5.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
554	356	ENTREE	5.000	Import facture - code 3439496607221	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
555	357	ENTREE	5.000	Import facture - code 3439496000657	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
556	525	ENTREE	82.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
557	526	ENTREE	4.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
558	345	ENTREE	6.000	Import facture - code 3439496604015	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
559	347	ENTREE	5.000	Import facture - code 3439496604008	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
560	527	ENTREE	39.000	Import facture - création	2025-10-30 12:18:34.198825	2025-10-30 12:18:34.198825
561	528	ENTREE	16.000	Import facture - création	2025-10-30 12:19:18.313605	2025-10-30 12:19:18.313605
562	402	ENTREE	424.000	Import facture - code 5000299225004	2025-10-30 12:19:57.146464	2025-10-30 12:19:57.146464
563	529	ENTREE	1.000	Import facture - création	2025-10-30 12:19:57.146464	2025-10-30 12:19:57.146464
564	483	ENTREE	209.000	Import facture - code 5010103802550	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
565	409	ENTREE	39.000	Import facture - code 3147690093602	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
566	484	ENTREE	99.000	Import facture - code 3211200152551	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
567	530	ENTREE	27.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
568	531	ENTREE	52.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
569	478	ENTREE	23.000	Import facture - code 03119783018847	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
570	479	ENTREE	95.000	Import facture - code 9002490205997	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
571	532	ENTREE	8.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
572	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
573	517	ENTREE	17.000	Import facture - code 8000500073698	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
574	420	ENTREE	17.000	Import facture - code 08000500121467	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
575	533	ENTREE	14.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
576	331	ENTREE	17.000	Import facture - code 5000159461801	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
577	534	ENTREE	20.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
578	535	ENTREE	10.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
579	536	ENTREE	33.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
580	537	ENTREE	10.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
581	538	ENTREE	6.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
582	539	ENTREE	9.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
583	543	ENTREE	10.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
584	544	ENTREE	17.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
585	545	ENTREE	8.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
586	546	ENTREE	2.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
587	547	ENTREE	9.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
588	548	ENTREE	11.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
589	549	ENTREE	10.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
590	522	ENTREE	2.000	Import facture - code 3439496603513	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
591	551	ENTREE	8.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
592	357	ENTREE	5.000	Import facture - code 3439496000657	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
593	553	ENTREE	3.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
594	554	ENTREE	2.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
595	555	ENTREE	4.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
596	556	ENTREE	6.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
597	557	ENTREE	15.000	Import facture - création	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
598	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 12:20:31.953437	2025-10-30 12:20:31.953437
599	496	ENTREE	35.000	Import facture - code 3119780268382	2025-10-30 12:20:31.953437	2025-10-30 12:20:31.953437
600	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 12:20:31.953437	2025-10-30 12:20:31.953437
601	558	ENTREE	8.000	Import facture - création	2025-10-30 12:20:31.953437	2025-10-30 12:20:31.953437
602	502	ENTREE	6.000	Import facture - code 3439495107906	2025-10-30 12:20:31.953437	2025-10-30 12:20:31.953437
603	559	ENTREE	7.000	Import facture - création	2025-10-30 12:20:31.953437	2025-10-30 12:20:31.953437
604	509	ENTREE	3.000	Import facture - code 3439495401448	2025-10-30 12:21:44.199334	2025-10-30 12:21:44.199334
605	315	ENTREE	164.000	Import facture - code 5010327325125	2025-10-30 12:22:52.856173	2025-10-30 12:22:52.856173
606	560	ENTREE	24.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
607	315	ENTREE	362.000	Import facture - code 5010327325125	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
608	561	ENTREE	94.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
609	562	ENTREE	4.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
610	563	ENTREE	81.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
611	564	ENTREE	125.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
612	565	ENTREE	62.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
613	456	ENTREE	65.000	Import facture - code 05010327248059	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
614	566	ENTREE	45.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
615	366	ENTREE	22.000	Import facture - code 3257150100228	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
616	409	ENTREE	42.000	Import facture - code 3147690093602	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
617	410	ENTREE	42.000	Import facture - code 3147690094708	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
618	461	ENTREE	4.000	Import facture	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
619	567	ENTREE	4.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
620	462	ENTREE	4.000	Import facture	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
621	484	ENTREE	102.000	Import facture - code 3211200152551	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
622	510	ENTREE	46.000	Import facture - code 3176484042434	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
623	568	ENTREE	47.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
624	368	ENTREE	79.000	Import facture - code 3259354102060	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
625	569	ENTREE	28.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
626	570	ENTREE	47.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
627	318	ENTREE	43.000	Import facture - code 3259356633067	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
628	571	ENTREE	215.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
629	320	ENTREE	65.000	Import facture - code 5410228203582	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
630	354	ENTREE	91.000	Import facture - code 5410228223580	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
631	498	ENTREE	151.000	Import facture - code 5000213003756	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
632	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
633	321	ENTREE	54.000	Import facture - code 3155930400530	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
634	479	ENTREE	24.000	Import facture - code 9002490205997	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
635	481	ENTREE	21.000	Import facture - code 5449000017673	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
636	444	ENTREE	19.000	Import facture - code 3124488151492	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
637	380	ENTREE	13.000	Import facture - code 3179730004804	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
638	572	ENTREE	5.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
639	573	ENTREE	26.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
640	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
641	574	ENTREE	3.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
642	557	ENTREE	14.000	Import facture - code 3439496806365	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
643	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
644	361	ENTREE	21.000	Import facture - code 3439496810997	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
645	575	ENTREE	3.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
646	576	ENTREE	12.000	Import facture - création	2025-10-30 12:23:12.672006	2025-10-30 12:23:12.672006
647	484	ENTREE	51.000	Import facture - code 3211200152551	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
648	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
649	577	ENTREE	74.000	Import facture - création	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
650	372	ENTREE	6.000	Import facture	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
651	496	ENTREE	121.000	Import facture - code 3119780268382	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
652	558	ENTREE	17.000	Import facture - code 3439497020371	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
653	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
654	578	ENTREE	5.000	Import facture - création	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
655	360	ENTREE	5.000	Import facture	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
656	579	ENTREE	3.000	Import facture - création	2025-10-30 12:23:32.662946	2025-10-30 12:23:32.662946
657	580	ENTREE	51.000	Import facture - création	2025-10-30 12:23:54.959145	2025-10-30 12:23:54.959145
658	581	ENTREE	34.000	Import facture - création	2025-10-30 12:23:54.959145	2025-10-30 12:23:54.959145
659	402	ENTREE	138.000	Import facture - code 5000299225004	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
660	315	ENTREE	214.000	Import facture - code 5010327325125	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
661	582	ENTREE	11.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
662	583	ENTREE	99.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
663	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
664	584	ENTREE	36.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
665	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
666	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
667	585	ENTREE	7.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
668	586	ENTREE	7.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
669	587	ENTREE	25.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
670	588	ENTREE	46.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
671	589	ENTREE	30.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
672	397	ENTREE	20.000	Import facture - code 3439495508345	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
673	511	ENTREE	14.000	Import facture - code 3439499001736	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
674	590	ENTREE	15.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
675	320	ENTREE	45.000	Import facture - code 5410228203582	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
676	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
677	591	ENTREE	17.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
678	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
679	488	ENTREE	11.000	Import facture - code 3439495407310	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
680	592	ENTREE	14.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
681	593	ENTREE	9.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
682	532	ENTREE	8.000	Import facture	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
683	594	ENTREE	9.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
684	595	ENTREE	17.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
685	558	ENTREE	4.000	Import facture - code 3439497020371	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
686	596	ENTREE	11.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
687	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
688	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
689	502	ENTREE	25.000	Import facture - code 3439495107906	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
690	477	ENTREE	5.000	Import facture	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
691	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
692	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
693	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
694	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
695	597	ENTREE	28.000	Import facture - création	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
696	361	ENTREE	22.000	Import facture - code 3439496810997	2025-10-30 12:24:14.204165	2025-10-30 12:24:14.204165
697	365	ENTREE	7.000	Import facture	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
698	598	ENTREE	7.000	Import facture - création	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
699	458	ENTREE	29.000	Import facture - code 7312040017355	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
700	409	ENTREE	13.000	Import facture - code 3147690093602	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
701	410	ENTREE	13.000	Import facture - code 3147690094708	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
702	599	ENTREE	17.000	Import facture - création	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
703	600	ENTREE	174.000	Import facture - création	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
704	481	ENTREE	19.000	Import facture - code 5449000017673	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
705	450	ENTREE	7.000	Import facture - code 5053990155361	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
706	601	ENTREE	3.000	Import facture - création	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
707	602	ENTREE	3.000	Import facture - création	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
708	483	ENTREE	350.000	Import facture - code 5010103802550	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
709	459	ENTREE	55.000	Import facture - code 5011013100613	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
710	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
711	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
712	367	ENTREE	16.000	Import facture - code 3175529657725	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
713	368	ENTREE	74.000	Import facture - code 3259354102060	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
714	369	ENTREE	15.000	Import facture - code 03179077103147	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
715	397	ENTREE	20.000	Import facture - code 3439495508345	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
716	354	ENTREE	12.000	Import facture - code 5410228223580	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
717	352	ENTREE	96.000	Import facture - code 3119783018823	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
718	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
719	486	ENTREE	5.000	Import facture - code 8850389112816	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
720	487	ENTREE	5.000	Import facture - code 8850389115374	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
721	488	ENTREE	11.000	Import facture - code 3439495407310	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
722	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
723	490	ENTREE	11.000	Import facture - code 05053990107476	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
724	491	ENTREE	11.000	Import facture - code 05053990107629	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
725	492	ENTREE	11.000	Import facture - code 05053990161614	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
726	450	ENTREE	7.000	Import facture - code 5053990155361	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
727	493	ENTREE	4.000	Import facture - code 3439496500768	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
728	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
729	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
730	495	ENTREE	10.000	Import facture - code 3281513541618	2025-10-30 12:25:08.974104	2025-10-30 12:25:08.974104
731	320	ENTREE	10.000	Import facture - code 5410228203582	2025-10-30 12:29:12.505267	2025-10-30 12:29:12.505267
732	354	ENTREE	15.000	Import facture - code 5410228223580	2025-10-30 12:29:12.505267	2025-10-30 12:29:12.505267
733	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:29:12.505267	2025-10-30 12:29:12.505267
734	496	ENTREE	23.000	Import facture - code 3119780268382	2025-10-30 12:29:12.505267	2025-10-30 12:29:12.505267
735	580	ENTREE	51.000	Import facture - code 3211209139232	2025-10-30 12:29:33.975649	2025-10-30 12:29:33.975649
736	581	ENTREE	34.000	Import facture - code 3522091156000	2025-10-30 12:29:33.975649	2025-10-30 12:29:33.975649
737	354	ENTREE	63.000	Import facture - code 5410228223580	2025-10-30 12:29:49.62647	2025-10-30 12:29:49.62647
738	352	ENTREE	79.000	Import facture - code 3119783018823	2025-10-30 12:29:49.62647	2025-10-30 12:29:49.62647
739	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:29:49.62647	2025-10-30 12:29:49.62647
740	603	ENTREE	39.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
741	483	ENTREE	418.000	Import facture - code 5010103802550	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
742	604	ENTREE	30.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
743	409	ENTREE	26.000	Import facture - code 3147690093602	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
744	484	ENTREE	199.000	Import facture - code 3211200152551	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
745	605	ENTREE	129.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
746	591	ENTREE	34.000	Import facture - code 03119783012012	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
747	606	ENTREE	17.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
748	352	ENTREE	95.000	Import facture - code 3119783018823	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
749	479	ENTREE	71.000	Import facture - code 9002490205997	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
750	607	ENTREE	13.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
751	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
752	608	ENTREE	21.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
753	609	ENTREE	7.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
754	610	ENTREE	5.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
755	390	ENTREE	5.000	Import facture	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
756	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
757	502	ENTREE	18.000	Import facture - code 3439495107906	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
758	611	ENTREE	12.000	Import facture - création	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
759	490	ENTREE	21.000	Import facture - code 05053990107476	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
760	492	ENTREE	11.000	Import facture - code 05053990161614	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
761	448	ENTREE	7.000	Import facture - code 5053990156016	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
762	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
763	600	ENTREE	174.000	Import facture - code 3185370374733	2025-10-30 12:30:14.808307	2025-10-30 12:30:14.808307
764	352	ENTREE	175.000	Import facture - code 3119783018823	2025-10-30 12:30:14.808307	2025-10-30 12:30:14.808307
765	613	ENTREE	39.000	Import facture - création	2025-10-30 12:30:14.808307	2025-10-30 12:30:14.808307
766	610	ENTREE	5.000	Import facture	2025-10-30 12:30:14.808307	2025-10-30 12:30:14.808307
767	361	ENTREE	22.000	Import facture - code 3439496810997	2025-10-30 12:30:14.808307	2025-10-30 12:30:14.808307
768	320	ENTREE	54.000	Import facture - code 5410228203582	2025-10-30 12:30:56.777536	2025-10-30 12:30:56.777536
769	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:30:56.777536	2025-10-30 12:30:56.777536
770	321	ENTREE	53.000	Import facture - code 3155930400530	2025-10-30 12:30:56.777536	2025-10-30 12:30:56.777536
771	320	ENTREE	54.000	Import facture - code 5410228203582	2025-10-30 12:31:20.923212	2025-10-30 12:31:20.923212
772	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:31:20.923212	2025-10-30 12:31:20.923212
773	321	ENTREE	53.000	Import facture - code 3155930400530	2025-10-30 12:31:20.923212	2025-10-30 12:31:20.923212
774	365	ENTREE	7.000	Import facture - code 3147697510607	2025-10-30 12:31:31.948532	2025-10-30 12:31:31.948532
775	410	ENTREE	56.000	Import facture - code 3147690094708	2025-10-30 12:31:31.948532	2025-10-30 12:31:31.948532
776	549	ENTREE	26.000	Import facture - code 3103228037722	2025-10-30 12:31:31.948532	2025-10-30 12:31:31.948532
777	320	ENTREE	9.000	Import facture - code 5410228203582	2025-10-30 12:31:46.439703	2025-10-30 12:31:46.439703
778	320	ENTREE	36.000	Import facture - code 5410228203582	2025-10-30 12:31:59.94359	2025-10-30 12:31:59.94359
779	486	ENTREE	6.000	Import facture - code 8850389112816	2025-10-30 12:31:59.94359	2025-10-30 12:31:59.94359
780	595	ENTREE	17.000	Import facture - code 3124488195168	2025-10-30 12:31:59.94359	2025-10-30 12:31:59.94359
781	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 12:31:59.94359	2025-10-30 12:31:59.94359
782	615	ENTREE	153.000	Import facture - création	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
783	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
784	320	ENTREE	86.000	Import facture - code 5410228203582	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
785	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
786	496	ENTREE	49.000	Import facture - code 3119780268382	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
787	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
788	488	ENTREE	3.000	Import facture - code 3439495407310	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
789	594	ENTREE	9.000	Import facture - code 3124488194659	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
790	558	ENTREE	4.000	Import facture - code 3439497020371	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
791	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
792	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
793	616	ENTREE	98.000	Import facture - création	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
794	617	ENTREE	8.000	Import facture - création	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
795	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
796	618	ENTREE	10.000	Import facture - création	2025-10-30 12:32:17.747406	2025-10-30 12:32:17.747406
797	402	ENTREE	424.000	Import facture - code 5000299225004	2025-10-30 12:32:35.31423	2025-10-30 12:32:35.31423
798	529	ENTREE	1.000	Import facture - code 3434030033627	2025-10-30 12:32:35.31423	2025-10-30 12:32:35.31423
799	402	ENTREE	424.000	Import facture - code 5000299225004	2025-10-30 13:04:26.678541	2025-10-30 13:04:26.678541
800	529	ENTREE	1.000	Import facture - code 3434030033627	2025-10-30 13:04:26.678541	2025-10-30 13:04:26.678541
801	320	ENTREE	54.000	Import facture - code 5410228203582	2025-10-30 13:05:28.701221	2025-10-30 13:05:28.701221
802	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:05:28.701221	2025-10-30 13:05:28.701221
803	321	ENTREE	53.000	Import facture - code 3155930400530	2025-10-30 13:05:28.701221	2025-10-30 13:05:28.701221
804	365	ENTREE	7.000	Import facture - code 3147697510607	2025-10-30 13:05:40.667214	2025-10-30 13:05:40.667214
805	410	ENTREE	56.000	Import facture - code 3147690094708	2025-10-30 13:05:40.667214	2025-10-30 13:05:40.667214
806	549	ENTREE	26.000	Import facture - code 3103228037722	2025-10-30 13:05:40.667214	2025-10-30 13:05:40.667214
807	320	ENTREE	9.000	Import facture - code 5410228203582	2025-10-30 13:05:59.322354	2025-10-30 13:05:59.322354
808	320	ENTREE	36.000	Import facture - code 5410228203582	2025-10-30 13:06:17.870524	2025-10-30 13:06:17.870524
809	486	ENTREE	6.000	Import facture - code 8850389112816	2025-10-30 13:06:17.870524	2025-10-30 13:06:17.870524
810	595	ENTREE	17.000	Import facture - code 3124488195168	2025-10-30 13:06:17.870524	2025-10-30 13:06:17.870524
811	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:06:17.870524	2025-10-30 13:06:17.870524
812	615	ENTREE	153.000	Import facture - code 05010327325125	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
813	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
814	320	ENTREE	86.000	Import facture - code 5410228203582	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
815	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
816	496	ENTREE	49.000	Import facture - code 3119780268382	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
817	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
818	488	ENTREE	3.000	Import facture - code 3439495407310	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
819	594	ENTREE	9.000	Import facture - code 3124488194659	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
820	558	ENTREE	4.000	Import facture - code 3439497020371	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
821	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
822	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
823	616	ENTREE	98.000	Import facture - code 3439495005523	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
824	617	ENTREE	8.000	Import facture - code 4337182153580	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
825	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
826	618	ENTREE	10.000	Import facture - code 3346024708605	2025-10-30 13:06:43.136884	2025-10-30 13:06:43.136884
827	615	ENTREE	153.000	Import facture - code 05010327325125	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
828	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
829	320	ENTREE	86.000	Import facture - code 5410228203582	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
830	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
831	496	ENTREE	49.000	Import facture - code 3119780268382	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
832	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
833	488	ENTREE	3.000	Import facture - code 3439495407310	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
834	594	ENTREE	9.000	Import facture - code 3124488194659	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
835	558	ENTREE	4.000	Import facture - code 3439497020371	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
836	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
837	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
838	616	ENTREE	98.000	Import facture - code 3439495005523	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
839	617	ENTREE	8.000	Import facture - code 4337182153580	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
840	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
841	618	ENTREE	10.000	Import facture - code 3346024708605	2025-10-30 13:07:02.010451	2025-10-30 13:07:02.010451
842	402	ENTREE	424.000	Import facture - code 5000299225004	2025-10-30 13:07:16.039007	2025-10-30 13:07:16.039007
843	529	ENTREE	1.000	Import facture - code 3434030033627	2025-10-30 13:07:16.039007	2025-10-30 13:07:16.039007
844	484	ENTREE	51.000	Import facture - code 3211200152551	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
845	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
846	577	ENTREE	74.000	Import facture - code 3760123280952	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
847	372	ENTREE	6.000	Import facture - code 3080213000759	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
848	496	ENTREE	121.000	Import facture - code 3119780268382	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
849	558	ENTREE	17.000	Import facture - code 3439497020371	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
850	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
851	578	ENTREE	5.000	Import facture - code 3378920010285	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
852	360	ENTREE	5.000	Import facture - code 4337182004981	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
853	579	ENTREE	3.000	Import facture - code 8718951542938	2025-10-30 13:07:33.623868	2025-10-30 13:07:33.623868
854	402	ENTREE	36.000	Import facture - code 5000299225004	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
855	315	ENTREE	65.000	Import facture - code 5010327325125	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
856	620	ENTREE	61.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
857	621	ENTREE	14.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
858	582	ENTREE	12.000	Import facture - code 3012991301001	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
859	622	ENTREE	21.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
860	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
861	510	ENTREE	56.000	Import facture - code 3176484042434	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
862	368	ENTREE	74.000	Import facture - code 3259354102060	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
863	369	ENTREE	55.000	Import facture - code 03179077103147	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
864	623	ENTREE	43.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
865	605	ENTREE	83.000	Import facture - code 3292054430019	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
866	354	ENTREE	30.000	Import facture - code 5410228223580	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
867	498	ENTREE	30.000	Import facture - code 5000213003756	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
868	352	ENTREE	99.000	Import facture - code 3119783018823	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
869	418	ENTREE	53.000	Import facture - code 3075711382018	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
870	624	ENTREE	8.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
871	625	ENTREE	9.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
872	626	ENTREE	14.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
873	516	ENTREE	5.000	Import facture - code 13077311522068	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
874	627	ENTREE	8.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
875	628	ENTREE	17.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
876	629	ENTREE	15.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
877	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
878	502	ENTREE	27.000	Import facture - code 3439495107906	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
879	630	ENTREE	10.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
880	631	ENTREE	2.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
881	632	ENTREE	3.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
882	527	ENTREE	34.000	Import facture - code 4337182138075	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
883	633	ENTREE	5.000	Import facture - création	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
884	306	ENTREE	5.000	Import facture	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
885	495	ENTREE	10.000	Import facture - code 3281513541618	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
886	361	ENTREE	21.000	Import facture - code 3439496810997	2025-10-30 13:08:21.170149	2025-10-30 13:08:21.170149
887	634	ENTREE	98.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
888	484	ENTREE	185.000	Import facture - code 3211200152551	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
889	510	ENTREE	56.000	Import facture - code 3176484042434	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
890	636	ENTREE	49.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
891	485	ENTREE	49.000	Import facture - code 3262151637079	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
892	637	ENTREE	18.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
893	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
894	577	ENTREE	74.000	Import facture - code 3760123280952	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
895	638	ENTREE	68.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
896	590	ENTREE	15.000	Import facture - code 03179077103161	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
897	639	ENTREE	13.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
898	388	ENTREE	13.000	Import facture - code 3438935000135	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
899	352	ENTREE	113.000	Import facture - code 3119783018823	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
900	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
901	322	ENTREE	29.000	Import facture - code 3119783016690	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
902	640	ENTREE	14.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
903	641	ENTREE	10.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
904	642	ENTREE	11.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
905	481	ENTREE	21.000	Import facture - code 5449000017673	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
906	594	ENTREE	10.000	Import facture - code 3124488194659	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
907	444	ENTREE	38.000	Import facture - code 3124488151492	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
908	445	ENTREE	7.000	Import facture - code 7613035833289	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
909	380	ENTREE	13.000	Import facture - code 3179730004804	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
910	644	ENTREE	7.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
911	517	ENTREE	38.000	Import facture - code 8000500073698	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
912	451	ENTREE	33.000	Import facture - code 8000500121467	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
913	535	ENTREE	12.000	Import facture - code 5000159304238	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
914	648	ENTREE	4.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
915	650	ENTREE	5.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
916	651	ENTREE	8.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
917	652	ENTREE	5.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
918	653	ENTREE	13.000	Import facture - création	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
919	554	ENTREE	1.000	Import facture - code 3439496603797	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
920	555	ENTREE	4.000	Import facture - code 3760049795646	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
921	527	ENTREE	23.000	Import facture - code 4337182138075	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
922	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
923	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 13:08:54.596243	2025-10-30 13:08:54.596243
924	634	ENTREE	98.000	Import facture - code 5000267024202	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
925	484	ENTREE	185.000	Import facture - code 3211200152551	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
926	510	ENTREE	56.000	Import facture - code 3176484042434	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
927	636	ENTREE	49.000	Import facture - code 03262151637079	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
928	485	ENTREE	49.000	Import facture - code 3262151637079	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
929	637	ENTREE	18.000	Import facture - code 03179072001141	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
930	655	ENTREE	30.000	Import facture - création	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
931	577	ENTREE	74.000	Import facture - code 3760123280952	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
932	638	ENTREE	68.000	Import facture - code 3262151791078	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
933	590	ENTREE	15.000	Import facture - code 03179077103161	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
934	639	ENTREE	13.000	Import facture - code 03438935000128	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
935	388	ENTREE	13.000	Import facture - code 3438935000135	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
936	352	ENTREE	113.000	Import facture - code 3119783018823	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
937	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
938	322	ENTREE	29.000	Import facture - code 3119783016690	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
939	640	ENTREE	14.000	Import facture - code 3439495407846	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
940	641	ENTREE	10.000	Import facture - code 3124488196264	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
941	642	ENTREE	11.000	Import facture - code 5449000098887	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
942	481	ENTREE	21.000	Import facture - code 5449000017673	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
943	594	ENTREE	10.000	Import facture - code 3124488194659	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
944	444	ENTREE	38.000	Import facture - code 3124488151492	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
945	445	ENTREE	7.000	Import facture - code 7613035833289	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
946	380	ENTREE	13.000	Import facture - code 3179730004804	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
947	644	ENTREE	7.000	Import facture - code 7613032910501	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
948	517	ENTREE	38.000	Import facture - code 8000500073698	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
949	451	ENTREE	33.000	Import facture - code 8000500121467	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
950	535	ENTREE	12.000	Import facture - code 5000159304238	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
951	648	ENTREE	4.000	Import facture - code 5000159516273	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
952	650	ENTREE	5.000	Import facture - code 7613035449176	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
953	651	ENTREE	8.000	Import facture - code 7613035958425	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
954	652	ENTREE	5.000	Import facture - code 8724900260341	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
955	653	ENTREE	13.000	Import facture - code 4009900456623	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
956	554	ENTREE	1.000	Import facture - code 3439496603797	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
957	555	ENTREE	4.000	Import facture - code 3760049795646	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
958	527	ENTREE	23.000	Import facture - code 4337182138075	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
959	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
960	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 13:09:19.982452	2025-10-30 13:09:19.982452
961	656	ENTREE	64.000	Import facture - création	2025-10-30 13:10:43.512798	2025-10-30 13:10:43.512798
962	315	ENTREE	324.000	Import facture - code 5010327325125	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
963	365	ENTREE	7.000	Import facture - code 3147697510607	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
964	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
965	367	ENTREE	17.000	Import facture - code 3175529657725	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
966	368	ENTREE	74.000	Import facture - code 3259354102060	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
967	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
968	657	ENTREE	479.000	Import facture - création	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
969	571	ENTREE	419.000	Import facture - code 3049614033872	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
970	600	ENTREE	191.000	Import facture - code 3185370374733	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
971	658	ENTREE	16.000	Import facture - création	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
972	354	ENTREE	29.000	Import facture - code 5410228223580	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
973	530	ENTREE	14.000	Import facture - code 03119783018243	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
974	352	ENTREE	189.000	Import facture - code 3119783018823	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
975	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
976	478	ENTREE	25.000	Import facture - code 03119783018847	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
977	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
978	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
979	495	ENTREE	10.000	Import facture - code 3281513541618	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
980	659	ENTREE	3.000	Import facture - création	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
981	361	ENTREE	22.000	Import facture - code 3439496810997	2025-10-30 13:10:55.050915	2025-10-30 13:10:55.050915
982	315	ENTREE	324.000	Import facture - code 5010327325125	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
983	365	ENTREE	7.000	Import facture - code 3147697510607	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
984	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
985	367	ENTREE	17.000	Import facture - code 3175529657725	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
986	368	ENTREE	74.000	Import facture - code 3259354102060	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
987	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
988	657	ENTREE	479.000	Import facture - code 3661419217242	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
989	571	ENTREE	419.000	Import facture - code 3049614033872	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
990	600	ENTREE	191.000	Import facture - code 3185370374733	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
991	658	ENTREE	16.000	Import facture - code 3261570002109	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
992	354	ENTREE	29.000	Import facture - code 5410228223580	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
993	530	ENTREE	14.000	Import facture - code 03119783018243	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
994	352	ENTREE	189.000	Import facture - code 3119783018823	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
995	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
996	478	ENTREE	25.000	Import facture - code 03119783018847	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
997	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
998	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
999	495	ENTREE	10.000	Import facture - code 3281513541618	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
1000	659	ENTREE	3.000	Import facture - code 3439496810942	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
1001	361	ENTREE	22.000	Import facture - code 3439496810997	2025-10-30 13:21:35.225351	2025-10-30 13:21:35.225351
1002	615	ENTREE	153.000	Import facture - code 05010327325125	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1003	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1004	320	ENTREE	86.000	Import facture - code 5410228203582	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1005	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1006	496	ENTREE	49.000	Import facture - code 3119780268382	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1007	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1008	488	ENTREE	3.000	Import facture - code 3439495407310	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1009	594	ENTREE	9.000	Import facture - code 3124488194659	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1010	558	ENTREE	4.000	Import facture - code 3439497020371	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1011	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1012	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1013	616	ENTREE	98.000	Import facture - code 3439495005523	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1014	617	ENTREE	8.000	Import facture - code 4337182153580	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1015	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1016	618	ENTREE	10.000	Import facture - code 3346024708605	2025-10-30 13:21:51.464527	2025-10-30 13:21:51.464527
1017	402	ENTREE	424.000	Import facture - code 5000299225004	2025-10-30 13:22:12.34506	2025-10-30 13:22:12.34506
1018	529	ENTREE	1.000	Import facture - code 3434030033627	2025-10-30 13:22:12.34506	2025-10-30 13:22:12.34506
1019	484	ENTREE	51.000	Import facture - code 3211200152551	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1020	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1021	577	ENTREE	74.000	Import facture - code 3760123280952	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1022	372	ENTREE	6.000	Import facture - code 3080213000759	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1023	496	ENTREE	121.000	Import facture - code 3119780268382	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1024	558	ENTREE	17.000	Import facture - code 3439497020371	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1025	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1026	578	ENTREE	5.000	Import facture - code 3378920010285	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1027	360	ENTREE	5.000	Import facture - code 4337182004981	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1028	579	ENTREE	3.000	Import facture - code 8718951542938	2025-10-30 13:22:28.042271	2025-10-30 13:22:28.042271
1029	484	ENTREE	51.000	Import facture - code 3211200152551	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1030	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1031	577	ENTREE	74.000	Import facture - code 3760123280952	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1032	372	ENTREE	6.000	Import facture - code 3080213000759	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1033	496	ENTREE	121.000	Import facture - code 3119780268382	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1034	558	ENTREE	17.000	Import facture - code 3439497020371	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1035	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1036	578	ENTREE	5.000	Import facture - code 3378920010285	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1037	360	ENTREE	5.000	Import facture - code 4337182004981	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1038	579	ENTREE	3.000	Import facture - code 8718951542938	2025-10-30 13:22:28.810574	2025-10-30 13:22:28.810574
1039	402	ENTREE	36.000	Import facture - code 5000299225004	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1040	315	ENTREE	65.000	Import facture - code 5010327325125	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1041	620	ENTREE	61.000	Import facture - code 3245990250203	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1042	621	ENTREE	14.000	Import facture - code 3439495304213	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1043	582	ENTREE	12.000	Import facture - code 3012991301001	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1044	622	ENTREE	21.000	Import facture - code 3163937016005	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1045	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1046	510	ENTREE	56.000	Import facture - code 3176484042434	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1047	368	ENTREE	74.000	Import facture - code 3259354102060	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1048	369	ENTREE	55.000	Import facture - code 03179077103147	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1049	623	ENTREE	43.000	Import facture - code 3450301173403	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1050	605	ENTREE	83.000	Import facture - code 3292054430019	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1051	354	ENTREE	30.000	Import facture - code 5410228223580	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1052	498	ENTREE	30.000	Import facture - code 5000213003756	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1053	352	ENTREE	99.000	Import facture - code 3119783018823	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1054	418	ENTREE	53.000	Import facture - code 3075711382018	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1055	624	ENTREE	8.000	Import facture - code 3439495121933	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1056	625	ENTREE	9.000	Import facture - code 3439495121957	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1057	626	ENTREE	14.000	Import facture - code 3439495121926	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1058	516	ENTREE	5.000	Import facture - code 13077311522068	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1059	627	ENTREE	8.000	Import facture - code 3439495110159	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1060	628	ENTREE	17.000	Import facture - code 3439495113051	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1061	629	ENTREE	15.000	Import facture - code 3439495113174	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1062	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1063	502	ENTREE	27.000	Import facture - code 3439495107906	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1064	630	ENTREE	10.000	Import facture - code 3439495125887	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1065	631	ENTREE	2.000	Import facture - code 3439496607283	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1066	632	ENTREE	3.000	Import facture - code 3439496607313	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1067	527	ENTREE	34.000	Import facture - code 4337182138075	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1068	633	ENTREE	5.000	Import facture - code 3439496824116	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1069	306	ENTREE	5.000	Import facture - code 4337182021858	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1070	495	ENTREE	10.000	Import facture - code 3281513541618	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1071	361	ENTREE	21.000	Import facture - code 3439496810997	2025-10-30 13:23:18.387594	2025-10-30 13:23:18.387594
1072	634	ENTREE	98.000	Import facture - code 5000267024202	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1073	484	ENTREE	185.000	Import facture - code 3211200152551	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1074	510	ENTREE	56.000	Import facture - code 3176484042434	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1075	636	ENTREE	49.000	Import facture - code 03262151637079	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1076	485	ENTREE	49.000	Import facture - code 3262151637079	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1077	637	ENTREE	18.000	Import facture - code 03179072001141	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1078	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1079	577	ENTREE	74.000	Import facture - code 3760123280952	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1080	638	ENTREE	68.000	Import facture - code 3262151791078	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1081	590	ENTREE	15.000	Import facture - code 03179077103161	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1082	639	ENTREE	13.000	Import facture - code 03438935000128	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1083	388	ENTREE	13.000	Import facture - code 3438935000135	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1084	352	ENTREE	113.000	Import facture - code 3119783018823	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1085	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1086	322	ENTREE	29.000	Import facture - code 3119783016690	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1087	640	ENTREE	14.000	Import facture - code 3439495407846	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1088	641	ENTREE	10.000	Import facture - code 3124488196264	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1089	642	ENTREE	11.000	Import facture - code 5449000098887	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1090	481	ENTREE	21.000	Import facture - code 5449000017673	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1091	594	ENTREE	10.000	Import facture - code 3124488194659	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1092	444	ENTREE	38.000	Import facture - code 3124488151492	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1093	445	ENTREE	7.000	Import facture - code 7613035833289	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1094	380	ENTREE	13.000	Import facture - code 3179730004804	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1095	644	ENTREE	7.000	Import facture - code 7613032910501	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1096	517	ENTREE	38.000	Import facture - code 8000500073698	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1097	451	ENTREE	33.000	Import facture - code 8000500121467	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1098	535	ENTREE	12.000	Import facture - code 5000159304238	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1099	648	ENTREE	4.000	Import facture - code 5000159516273	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1100	650	ENTREE	5.000	Import facture - code 7613035449176	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1101	651	ENTREE	8.000	Import facture - code 7613035958425	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1102	652	ENTREE	5.000	Import facture - code 8724900260341	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1103	653	ENTREE	13.000	Import facture - code 4009900456623	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1104	554	ENTREE	1.000	Import facture - code 3439496603797	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1105	555	ENTREE	4.000	Import facture - code 3760049795646	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1106	527	ENTREE	23.000	Import facture - code 4337182138075	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1107	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1108	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 13:23:51.882142	2025-10-30 13:23:51.882142
1109	583	ENTREE	99.000	Import facture - code 3211200044801	2025-10-30 13:25:48.928759	2025-10-30 13:25:48.928759
1110	583	ENTREE	49.000	Import facture - code 3211200044801	2025-10-30 13:26:23.013776	2025-10-30 13:26:23.013776
1111	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:26:23.013776	2025-10-30 13:26:23.013776
1112	315	ENTREE	766.000	Import facture - code 5010327325125	2025-10-30 13:26:43.680317	2025-10-30 13:26:43.680317
1113	498	ENTREE	907.000	Import facture - code 5000213003756	2025-10-30 13:27:03.356302	2025-10-30 13:27:03.356302
1114	315	ENTREE	164.000	Import facture - code 5010327325125	2025-10-30 13:27:21.452371	2025-10-30 13:27:21.452371
1115	352	ENTREE	449.000	Import facture - code 3119783018823	2025-10-30 13:27:31.977723	2025-10-30 13:27:31.977723
1116	315	ENTREE	461.000	Import facture - code 5010327325125	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1117	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1118	660	ENTREE	119.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1119	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1120	661	ENTREE	135.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1121	571	ENTREE	215.000	Import facture - code 3049614033872	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1122	605	ENTREE	86.000	Import facture - code 3292054430019	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1123	320	ENTREE	65.000	Import facture - code 5410228203582	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1124	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1125	321	ENTREE	53.000	Import facture - code 3155930400530	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1126	532	ENTREE	19.000	Import facture - code 5449000002921	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1127	662	ENTREE	16.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1128	663	ENTREE	38.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1129	490	ENTREE	11.000	Import facture - code 05053990107476	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1130	491	ENTREE	12.000	Import facture - code 05053990107629	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1131	492	ENTREE	12.000	Import facture - code 05053990161614	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1132	517	ENTREE	38.000	Import facture - code 8000500073698	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1133	451	ENTREE	39.000	Import facture - code 8000500121467	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1134	519	ENTREE	9.000	Import facture - code 5000159419383	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1135	520	ENTREE	9.000	Import facture - code 5000159418553	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1136	664	ENTREE	7.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1137	343	ENTREE	6.000	Import facture - code 3439496002323	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1138	357	ENTREE	5.000	Import facture - code 3439496000657	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1139	632	ENTREE	7.000	Import facture - code 3439496607313	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1140	347	ENTREE	5.000	Import facture - code 3439496604008	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1141	666	ENTREE	2.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1142	667	ENTREE	3.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1143	668	ENTREE	20.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1144	495	ENTREE	10.000	Import facture - code 3281513541618	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1145	505	ENTREE	11.000	Import facture - code 3439496802862	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1146	361	ENTREE	21.000	Import facture - code 3439496810997	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1147	669	ENTREE	3.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1148	670	ENTREE	5.000	Import facture - création	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
1149	671	ENTREE	25.000	Import facture - création	2025-10-30 13:28:09.868901	2025-10-30 13:28:09.868901
1150	320	ENTREE	9.000	Import facture - code 5410228203582	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1151	498	ENTREE	30.000	Import facture - code 5000213003756	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1152	672	ENTREE	166.000	Import facture - création	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1153	673	ENTREE	8.000	Import facture - création	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1154	674	ENTREE	11.000	Import facture - création	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1155	675	ENTREE	19.000	Import facture - création	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1156	676	ENTREE	2.000	Import facture - création	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1157	594	ENTREE	10.000	Import facture - code 3124488194659	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1158	444	ENTREE	22.000	Import facture - code 3124488151492	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1159	677	ENTREE	28.000	Import facture - création	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
1160	483	ENTREE	424.000	Import facture - code 5010103802550	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1161	484	ENTREE	61.000	Import facture - code 3211200152551	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1162	367	ENTREE	16.000	Import facture - code 3175529657725	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1163	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1164	655	ENTREE	15.000	Import facture - code 3179077103147	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1165	590	ENTREE	15.000	Import facture - code 03179077103161	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1166	605	ENTREE	180.000	Import facture - code 3292054430019	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1167	320	ENTREE	18.000	Import facture - code 5410228203582	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1168	372	ENTREE	5.000	Import facture	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1169	352	ENTREE	83.000	Import facture - code 3119783018823	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1170	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1171	678	ENTREE	62.000	Import facture - création	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1172	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1173	502	ENTREE	13.000	Import facture - code 3439495107906	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1174	527	ENTREE	23.000	Import facture - code 4337182138075	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1175	679	ENTREE	2.000	Import facture - création	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1176	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1177	680	ENTREE	2.000	Import facture - création	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
1178	483	ENTREE	420.000	Import facture - code 5010103802550	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1179	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1180	367	ENTREE	32.000	Import facture - code 3175529657725	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1181	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1182	681	ENTREE	7.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1183	369	ENTREE	61.000	Import facture - code 03179077103147	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1184	590	ENTREE	15.000	Import facture - code 03179077103161	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1185	322	ENTREE	24.000	Import facture - code 3119783016690	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1186	682	ENTREE	7.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1187	683	ENTREE	4.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1188	684	ENTREE	7.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1189	678	ENTREE	62.000	Import facture - code 3439495022209	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1190	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1191	502	ENTREE	27.000	Import facture - code 3439495107906	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1192	686	ENTREE	5.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1193	449	ENTREE	7.000	Import facture	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1194	527	ENTREE	37.000	Import facture - code 4337182138075	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1195	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1196	556	ENTREE	6.000	Import facture - code 3573972500504	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1197	688	ENTREE	5.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1198	689	ENTREE	6.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1199	690	ENTREE	9.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1200	557	ENTREE	15.000	Import facture - code 3439496806365	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1201	691	ENTREE	1.000	Import facture - création	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1202	361	ENTREE	22.000	Import facture - code 3439496810997	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
1203	497	ENTREE	99.000	Import facture - code 3211200196883	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1204	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1205	498	ENTREE	29.000	Import facture - code 5000213003756	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1206	352	ENTREE	239.000	Import facture - code 3119783018823	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1207	499	ENTREE	5.000	Import facture - code 8850389110515	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1208	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1209	380	ENTREE	12.000	Import facture - code 3179730004804	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1210	500	ENTREE	90.000	Import facture - code 3439495011388	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1211	501	ENTREE	24.000	Import facture - code 3276650013203	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1212	502	ENTREE	18.000	Import facture - code 3439495107906	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1213	503	ENTREE	24.000	Import facture - code 8715700120065	2025-10-30 13:29:19.956974	2025-10-30 13:29:19.956974
1214	497	ENTREE	99.000	Import facture - code 3211200196883	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1215	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1216	498	ENTREE	29.000	Import facture - code 5000213003756	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1217	352	ENTREE	239.000	Import facture - code 3119783018823	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1218	499	ENTREE	5.000	Import facture - code 8850389110515	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1219	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1220	380	ENTREE	12.000	Import facture - code 3179730004804	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1221	500	ENTREE	90.000	Import facture - code 3439495011388	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1222	501	ENTREE	24.000	Import facture - code 3276650013203	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1223	502	ENTREE	18.000	Import facture - code 3439495107906	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1224	503	ENTREE	24.000	Import facture - code 8715700120065	2025-10-30 13:29:20.668268	2025-10-30 13:29:20.668268
1225	483	ENTREE	314.000	Import facture - code 5010103802550	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1226	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1227	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1228	354	ENTREE	37.000	Import facture - code 5410228223580	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1229	352	ENTREE	191.000	Import facture - code 3119783018823	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1230	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1231	607	ENTREE	11.000	Import facture - code 3124488186852	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1232	692	ENTREE	9.000	Import facture - création	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1233	693	ENTREE	32.000	Import facture - création	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1234	390	ENTREE	5.000	Import facture	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1235	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1236	306	ENTREE	5.000	Import facture	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1237	694	ENTREE	25.000	Import facture - création	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1238	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1239	695	ENTREE	26.000	Import facture - création	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1240	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
1241	620	ENTREE	114.000	Import facture - code 3245990250203	2025-10-30 13:30:29.970994	2025-10-30 13:30:29.970994
1242	696	ENTREE	99.000	Import facture - création	2025-10-30 13:30:29.970994	2025-10-30 13:30:29.970994
1243	402	ENTREE	138.000	Import facture - code 5000299225004	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1244	315	ENTREE	214.000	Import facture - code 5010327325125	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1245	582	ENTREE	11.000	Import facture - code 3012991301001	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1246	583	ENTREE	99.000	Import facture - code 3211200044801	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1247	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1248	584	ENTREE	36.000	Import facture - code 3175529644848	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1249	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1250	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1251	585	ENTREE	7.000	Import facture - code 3760255776002	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1252	586	ENTREE	7.000	Import facture - code 03258690006094	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1253	587	ENTREE	25.000	Import facture - code 3286171703125	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1254	588	ENTREE	46.000	Import facture - code 3430430007343	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1255	589	ENTREE	30.000	Import facture - code 3760050843015	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1256	397	ENTREE	20.000	Import facture - code 3439495508345	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1257	511	ENTREE	14.000	Import facture - code 3439499001736	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1258	590	ENTREE	15.000	Import facture - code 03179077103161	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1259	320	ENTREE	45.000	Import facture - code 5410228203582	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1260	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1261	591	ENTREE	17.000	Import facture - code 03119783012012	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1262	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1263	488	ENTREE	11.000	Import facture - code 3439495407310	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1264	592	ENTREE	14.000	Import facture - code 5000112617979	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1265	593	ENTREE	9.000	Import facture - code 05449000089120	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1266	532	ENTREE	8.000	Import facture - code 05449000002921	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1267	594	ENTREE	9.000	Import facture - code 3124488194659	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1268	595	ENTREE	17.000	Import facture - code 3124488195168	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1269	558	ENTREE	4.000	Import facture - code 3439497020371	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1270	596	ENTREE	11.000	Import facture - code 03179730004804	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1271	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1272	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1273	502	ENTREE	25.000	Import facture - code 3439495107906	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1274	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1275	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1276	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1277	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1278	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1279	597	ENTREE	28.000	Import facture - code 3522091155102	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1280	361	ENTREE	22.000	Import facture - code 3439496810997	2025-10-30 13:30:46.850961	2025-10-30 13:30:46.850961
1281	315	ENTREE	329.000	Import facture - code 5010327325125	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1282	561	ENTREE	94.000	Import facture - code 05099873123454	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1283	562	ENTREE	4.000	Import facture - code 3147690094104	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1284	563	ENTREE	27.000	Import facture - code 05010103236041	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1285	365	ENTREE	7.000	Import facture - code 3147697510607	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1286	365	ENTREE	7.000	Import facture - code 03147691302390	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1287	697	ENTREE	76.000	Import facture - création	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1288	409	ENTREE	56.000	Import facture - code 3147690093602	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1289	465	ENTREE	11.000	Import facture - code 5011013100156	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1290	484	ENTREE	205.000	Import facture - code 3211200152551	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1291	320	ENTREE	65.000	Import facture - code 5410228203582	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1292	372	ENTREE	6.000	Import facture - code 3080213000759	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1293	478	ENTREE	50.000	Import facture - code 03119783018847	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1294	698	ENTREE	5.000	Import facture - création	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1295	496	ENTREE	68.000	Import facture - code 3119780268382	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1296	322	ENTREE	87.000	Import facture - code 3119783016690	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1297	699	ENTREE	10.000	Import facture - création	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1298	479	ENTREE	48.000	Import facture - code 9002490205997	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1299	488	ENTREE	14.000	Import facture - code 3439495407310	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1300	700	ENTREE	2.000	Import facture - création	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1301	701	ENTREE	18.000	Import facture - création	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1302	378	ENTREE	18.000	Import facture - code 5000112557091	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1303	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
1304	560	ENTREE	24.000	Import facture - code 3107872000507	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1305	315	ENTREE	362.000	Import facture - code 5010327325125	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1306	561	ENTREE	94.000	Import facture - code 05099873123454	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1307	562	ENTREE	4.000	Import facture - code 3147690094104	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1308	563	ENTREE	81.000	Import facture - code 05010103236041	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1309	564	ENTREE	125.000	Import facture - code 05099873120422	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1310	565	ENTREE	62.000	Import facture - code 05010327250021	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1311	456	ENTREE	65.000	Import facture - code 05010327248059	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1312	566	ENTREE	45.000	Import facture - code 5000299297353	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1313	366	ENTREE	22.000	Import facture - code 3257150100228	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1314	409	ENTREE	42.000	Import facture - code 3147690093602	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1315	410	ENTREE	42.000	Import facture - code 3147690094708	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1316	461	ENTREE	4.000	Import facture - code 3011932000829	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1317	567	ENTREE	4.000	Import facture - code 3011932000843	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1318	462	ENTREE	4.000	Import facture - code 3011932000805	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1319	484	ENTREE	102.000	Import facture - code 3211200152551	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1320	510	ENTREE	46.000	Import facture - code 3176484042434	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1321	568	ENTREE	47.000	Import facture - code 3251091501038	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1322	368	ENTREE	79.000	Import facture - code 3259354102060	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1323	569	ENTREE	28.000	Import facture - code 3439495507638	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1324	570	ENTREE	47.000	Import facture - code 3439499000920	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1325	318	ENTREE	43.000	Import facture - code 3259356633067	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1326	571	ENTREE	215.000	Import facture - code 3049614033872	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1327	320	ENTREE	65.000	Import facture - code 5410228203582	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1328	354	ENTREE	91.000	Import facture - code 5410228223580	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1329	498	ENTREE	151.000	Import facture - code 5000213003756	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1330	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1331	321	ENTREE	54.000	Import facture - code 3155930400530	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1332	479	ENTREE	24.000	Import facture - code 9002490205997	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1333	481	ENTREE	21.000	Import facture - code 5449000017673	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1334	444	ENTREE	19.000	Import facture - code 3124488151492	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1335	380	ENTREE	13.000	Import facture - code 3179730004804	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1336	572	ENTREE	5.000	Import facture - code 3017760111805	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1337	573	ENTREE	26.000	Import facture - code 7613037928532	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1338	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1339	574	ENTREE	3.000	Import facture - code 8420499102801	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1340	557	ENTREE	14.000	Import facture - code 3439496806365	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1341	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1342	361	ENTREE	21.000	Import facture - code 3439496810997	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1343	575	ENTREE	3.000	Import facture - code 3166720014998	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1344	576	ENTREE	12.000	Import facture - code 3439496800882	2025-10-30 13:31:35.960803	2025-10-30 13:31:35.960803
1345	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:33:37.981849	2025-10-30 13:33:37.981849
1346	496	ENTREE	35.000	Import facture - code 3119780268382	2025-10-30 13:33:37.981849	2025-10-30 13:33:37.981849
1347	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:33:37.981849	2025-10-30 13:33:37.981849
1348	558	ENTREE	8.000	Import facture - code 3439497020371	2025-10-30 13:33:37.981849	2025-10-30 13:33:37.981849
1349	502	ENTREE	6.000	Import facture - code 3439495107906	2025-10-30 13:33:37.981849	2025-10-30 13:33:37.981849
1350	559	ENTREE	7.000	Import facture - code 3288360005591	2025-10-30 13:33:37.981849	2025-10-30 13:33:37.981849
1351	315	ENTREE	267.000	Import facture - code 5010327325125	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1352	702	ENTREE	16.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1353	703	ENTREE	16.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1354	488	ENTREE	1.000	Import facture - code 3439495407310	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1355	315	ENTREE	178.000	Import facture - code 5010327325125	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1356	320	ENTREE	88.000	Import facture - code 5410228203582	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1357	483	ENTREE	67.000	Import facture - code 5010103802550	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1358	704	ENTREE	179.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1359	483	ENTREE	67.000	Import facture - code 5010103802550	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1360	705	ENTREE	63.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1361	706	ENTREE	72.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1362	707	ENTREE	20.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1363	509	ENTREE	3.000	Import facture - code 3439495401448	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1364	708	ENTREE	18.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1365	709	ENTREE	5.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1366	402	ENTREE	79.000	Import facture - code 5000299225004	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1367	463	ENTREE	132.000	Import facture - code 0080432402931	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1368	710	ENTREE	119.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1369	711	ENTREE	7.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1370	462	ENTREE	4.000	Import facture - code 3011932000805	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1371	713	ENTREE	4.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1372	583	ENTREE	49.000	Import facture - code 3211200044801	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1373	510	ENTREE	84.000	Import facture - code 3176484042434	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1374	368	ENTREE	39.000	Import facture - code 3259354102060	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1375	369	ENTREE	27.000	Import facture - code 03179077103147	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1376	586	ENTREE	7.000	Import facture	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1377	588	ENTREE	38.000	Import facture - code 3430430007343	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1378	714	ENTREE	485.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1379	715	ENTREE	171.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1380	716	ENTREE	33.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1381	511	ENTREE	56.000	Import facture - code 3439499001736	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1382	318	ENTREE	28.000	Import facture - code 3259356633067	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1383	354	ENTREE	65.000	Import facture - code 5410228223580	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1384	498	ENTREE	148.000	Import facture - code 5000213003756	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1385	352	ENTREE	478.000	Import facture - code 3119783018823	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1386	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1387	496	ENTREE	119.000	Import facture - code 3119780268382	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1388	322	ENTREE	24.000	Import facture - code 3119783016690	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1389	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1390	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1391	717	ENTREE	6.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1392	488	ENTREE	11.000	Import facture - code 3439495407310	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1393	593	ENTREE	9.000	Import facture	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1394	481	ENTREE	37.000	Import facture - code 5449000017673	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1395	594	ENTREE	8.000	Import facture - code 3124488194659	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1396	489	ENTREE	14.000	Import facture - code 3439497020357	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1397	596	ENTREE	22.000	Import facture - code 03179730004804	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1398	418	ENTREE	86.000	Import facture - code 3075711382018	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1399	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1400	502	ENTREE	25.000	Import facture - code 3439495107906	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1401	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1402	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1403	719	ENTREE	4.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1404	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1405	361	ENTREE	22.000	Import facture - code 3439496810997	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1406	720	ENTREE	92.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1407	368	ENTREE	19.000	Import facture - code 3259354102060	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1408	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1409	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1410	607	ENTREE	12.000	Import facture - code 3124488186852	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1411	558	ENTREE	8.000	Import facture - code 3439497020371	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1412	503	ENTREE	24.000	Import facture - code 8715700120065	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1413	721	ENTREE	5.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1414	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1415	722	ENTREE	17.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1416	618	ENTREE	10.000	Import facture - code 3346024708605	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1417	315	ENTREE	735.000	Import facture - code 5010327325125	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1418	315	ENTREE	490.000	Import facture - code 5010327325125	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1419	459	ENTREE	55.000	Import facture - code 5011013100613	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1420	484	ENTREE	99.000	Import facture - code 3211200152551	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1421	723	ENTREE	7.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1422	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1423	369	ENTREE	15.000	Import facture - code 03179077103147	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1424	320	ENTREE	65.000	Import facture - code 5410228203582	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1425	354	ENTREE	25.000	Import facture - code 5410228223580	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1426	498	ENTREE	86.000	Import facture - code 5000213003756	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1427	352	ENTREE	239.000	Import facture - code 3119783018823	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1428	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1429	496	ENTREE	59.000	Import facture - code 3119780268382	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1430	486	ENTREE	6.000	Import facture - code 8850389112816	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1431	487	ENTREE	5.000	Import facture - code 8850389115374	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1432	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1433	607	ENTREE	13.000	Import facture - code 3124488186852	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1434	532	ENTREE	8.000	Import facture - code 5449000002921	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1435	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1436	501	ENTREE	24.000	Import facture - code 3276650013203	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1437	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1438	306	ENTREE	5.000	Import facture	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1439	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1440	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1441	718	ENTREE	1.000	Import facture	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1442	724	ENTREE	7.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1443	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1444	725	ENTREE	35.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1445	726	ENTREE	5.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1446	385	ENTREE	11.000	Import facture - code 3439496807805	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1447	483	ENTREE	174.000	Import facture - code 5010103802550	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1448	484	ENTREE	59.000	Import facture - code 3211200152551	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1449	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1450	727	ENTREE	18.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1451	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1452	354	ENTREE	25.000	Import facture - code 5410228223580	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1453	352	ENTREE	95.000	Import facture - code 3119783018823	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1454	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1455	373	ENTREE	12.000	Import facture - code 3439495405064	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1456	374	ENTREE	13.000	Import facture - code 3439495403794	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1457	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1458	728	ENTREE	6.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1459	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1460	377	ENTREE	13.000	Import facture - code 3439495406368	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1461	729	ENTREE	12.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1462	481	ENTREE	19.000	Import facture - code 5449000017673	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1463	730	ENTREE	9.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1464	594	ENTREE	9.000	Import facture - code 3124488194659	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1465	731	ENTREE	16.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1466	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1467	732	ENTREE	28.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1468	678	ENTREE	62.000	Import facture - code 3439495022209	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1469	502	ENTREE	20.000	Import facture - code 3439495107906	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1470	652	ENTREE	5.000	Import facture - code 8724900260341	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1471	733	ENTREE	29.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1472	734	ENTREE	13.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1473	547	ENTREE	9.000	Import facture - code 8724900500881	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1474	735	ENTREE	10.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1475	736	ENTREE	15.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1476	737	ENTREE	9.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1477	738	ENTREE	9.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1478	427	ENTREE	12.000	Import facture - code 6931722310297	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1479	739	ENTREE	26.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1480	527	ENTREE	18.000	Import facture - code 4337182138075	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1481	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1482	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1483	556	ENTREE	6.000	Import facture - code 3573972500504	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1484	385	ENTREE	23.000	Import facture - code 3439496807805	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1485	659	ENTREE	7.000	Import facture - code 3439496810942	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1486	438	ENTREE	25.000	Import facture - code 3439496807065	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1487	740	ENTREE	4.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1488	741	ENTREE	5.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1489	483	ENTREE	350.000	Import facture - code 5010103802550	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1490	459	ENTREE	55.000	Import facture - code 5011013100613	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1491	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1492	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1493	367	ENTREE	16.000	Import facture - code 3175529657725	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1494	368	ENTREE	74.000	Import facture - code 3259354102060	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1495	369	ENTREE	15.000	Import facture - code 03179077103147	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1496	397	ENTREE	20.000	Import facture - code 3439495508345	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1497	354	ENTREE	12.000	Import facture - code 5410228223580	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1498	352	ENTREE	96.000	Import facture - code 3119783018823	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1499	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1500	486	ENTREE	5.000	Import facture - code 8850389112816	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1501	487	ENTREE	5.000	Import facture - code 8850389115374	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1502	488	ENTREE	11.000	Import facture - code 3439495407310	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1503	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1504	490	ENTREE	11.000	Import facture - code 05053990107476	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1505	491	ENTREE	11.000	Import facture - code 05053990107629	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1506	492	ENTREE	11.000	Import facture - code 05053990161614	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1507	450	ENTREE	7.000	Import facture - code 5053990155361	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1508	493	ENTREE	4.000	Import facture - code 3439496500768	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1509	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1510	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1511	495	ENTREE	10.000	Import facture - code 3281513541618	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1512	315	ENTREE	486.000	Import facture - code 5010327325125	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1513	454	ENTREE	143.000	Import facture - code 20080432402935	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1514	440	ENTREE	121.000	Import facture - code 5000267024325	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1515	621	ENTREE	14.000	Import facture - code 3439495304213	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1516	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1517	367	ENTREE	17.000	Import facture - code 3175529657725	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1518	657	ENTREE	359.000	Import facture - code 3661419217242	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1519	742	ENTREE	18.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1520	743	ENTREE	32.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1521	705	ENTREE	34.000	Import facture - code 3049610004104	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1522	512	ENTREE	26.000	Import facture - code 3438935000128	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1523	388	ENTREE	26.000	Import facture - code 3438935000135	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1524	352	ENTREE	189.000	Import facture - code 3119783018823	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1525	418	ENTREE	61.000	Import facture - code 3075711382018	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1526	527	ENTREE	33.000	Import facture - code 4337182138075	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1527	361	ENTREE	22.000	Import facture - code 3439496810997	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1528	744	ENTREE	292.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1529	365	ENTREE	7.000	Import facture - code 03147691302390	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1530	530	ENTREE	25.000	Import facture - code 03119783018243	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1531	478	ENTREE	25.000	Import facture - code 03119783018847	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1532	321	ENTREE	27.000	Import facture - code 3155930400530	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1533	745	ENTREE	10.000	Import facture - création	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1534	700	ENTREE	2.000	Import facture - code 5000112639995	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1535	378	ENTREE	37.000	Import facture - code 5000112557091	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1536	315	ENTREE	494.000	Import facture - code 5010327325125	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1537	366	ENTREE	22.000	Import facture - code 3257150100228	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1538	484	ENTREE	123.000	Import facture - code 3211200152551	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1539	367	ENTREE	35.000	Import facture - code 3175529657725	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1540	369	ENTREE	15.000	Import facture - code 03179077103147	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1541	320	ENTREE	65.000	Import facture - code 5410228203582	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1542	354	ENTREE	45.000	Import facture - code 5410228223580	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1543	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1544	321	ENTREE	81.000	Import facture - code 3155930400530	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1545	488	ENTREE	14.000	Import facture - code 3439495407310	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1546	378	ENTREE	21.000	Import facture - code 5000112557091	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1547	444	ENTREE	23.000	Import facture - code 3124488151492	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1548	381	ENTREE	10.000	Import facture - code 3439495111699	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1549	391	ENTREE	13.000	Import facture - code 3439495102796	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1550	574	ENTREE	2.000	Import facture - code 8420499102801	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1551	361	ENTREE	21.000	Import facture - code 3439496810997	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1552	315	ENTREE	164.000	Import facture - code 5010327325125	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1553	365	ENTREE	7.000	Import facture - code 3147697510607	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1554	409	ENTREE	56.000	Import facture - code 3147690093602	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1555	510	ENTREE	93.000	Import facture - code 3176484042434	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1556	511	ENTREE	30.000	Import facture - code 3439499001736	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1557	512	ENTREE	13.000	Import facture - code 3438935000128	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1558	388	ENTREE	26.000	Import facture - code 3438935000135	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1559	513	ENTREE	2.000	Import facture - code 5601164900349	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1560	514	ENTREE	12.000	Import facture - code 0054308184412	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1561	481	ENTREE	43.000	Import facture - code 5449000017673	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1562	515	ENTREE	12.000	Import facture - code 3254382048342	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1563	516	ENTREE	5.000	Import facture - code 13077311522068	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1564	390	ENTREE	5.000	Import facture - code 03439495112917	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1565	393	ENTREE	14.000	Import facture - code 3168930104285	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1566	490	ENTREE	11.000	Import facture - code 05053990107476	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1567	492	ENTREE	12.000	Import facture - code 05053990161614	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1568	517	ENTREE	38.000	Import facture - code 8000500073698	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1569	451	ENTREE	39.000	Import facture - code 8000500121467	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1570	518	ENTREE	16.000	Import facture - code 04008400223612	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1571	329	ENTREE	17.000	Import facture - code 04008400264004	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1572	519	ENTREE	9.000	Import facture - code 5000159419383	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1573	520	ENTREE	9.000	Import facture - code 5000159418553	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1574	331	ENTREE	19.000	Import facture - code 5000159461801	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1575	521	ENTREE	21.000	Import facture - code 4009900522113	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1576	522	ENTREE	3.000	Import facture - code 3439496603513	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1577	524	ENTREE	5.000	Import facture - code 3439496622323	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1578	356	ENTREE	5.000	Import facture - code 3439496607221	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1579	357	ENTREE	5.000	Import facture - code 3439496000657	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1580	525	ENTREE	82.000	Import facture - code 3439496620626	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1581	526	ENTREE	4.000	Import facture - code 3587220005130	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1582	345	ENTREE	6.000	Import facture - code 3439496604015	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1583	347	ENTREE	5.000	Import facture - code 3439496604008	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1584	527	ENTREE	39.000	Import facture - code 4337182138075	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1585	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1586	655	ENTREE	15.000	Import facture - code 3179077103147	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1587	370	ENTREE	14.000	Import facture - code 03179077103154	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1588	320	ENTREE	43.000	Import facture - code 5410228203582	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1589	354	ENTREE	39.000	Import facture - code 5410228223580	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1590	352	ENTREE	15.000	Import facture - code 3119783018823	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1591	496	ENTREE	29.000	Import facture - code 3119780268382	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1592	322	ENTREE	47.000	Import facture - code 3119783016690	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1593	416	ENTREE	13.000	Import facture - code 3439495403824	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1594	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1595	488	ENTREE	1.000	Import facture - code 3439495407310	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1596	558	ENTREE	8.000	Import facture - code 3439497020371	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1597	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1598	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1599	502	ENTREE	6.000	Import facture - code 3439495107906	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1600	722	ENTREE	17.000	Import facture - code 3439496820125	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1601	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1602	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1603	496	ENTREE	35.000	Import facture - code 3119780268382	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1604	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1605	558	ENTREE	8.000	Import facture - code 3439497020371	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1606	502	ENTREE	6.000	Import facture - code 3439495107906	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1607	559	ENTREE	7.000	Import facture - code 3288360005591	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1608	470	ENTREE	113.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1609	746	ENTREE	334.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1610	320	ENTREE	12.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1611	352	ENTREE	88.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1612	496	ENTREE	22.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1613	747	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1614	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1615	748	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1616	749	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1617	402	ENTREE	79.000	Import facture - code 5000299225004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1618	315	ENTREE	490.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1619	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1620	320	ENTREE	43.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1621	354	ENTREE	28.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1622	352	ENTREE	159.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1623	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1624	322	ENTREE	47.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1625	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1626	750	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1627	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1628	558	ENTREE	8.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1629	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1630	751	ENTREE	93.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1631	381	ENTREE	8.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1632	502	ENTREE	25.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1633	306	ENTREE	5.000	Import facture - code 4337182021858	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1634	556	ENTREE	13.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1635	752	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1636	753	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1637	754	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1638	315	ENTREE	327.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1639	583	ENTREE	59.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1640	510	ENTREE	50.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1641	636	ENTREE	47.000	Import facture - code 03262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1642	755	ENTREE	45.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1643	320	ENTREE	8.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1644	352	ENTREE	150.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1645	496	ENTREE	11.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1646	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1647	756	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1648	402	ENTREE	79.000	Import facture - code 5000299225004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1649	315	ENTREE	306.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1650	757	ENTREE	18.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1651	462	ENTREE	4.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1652	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1653	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1654	655	ENTREE	25.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1655	742	ENTREE	17.000	Import facture - code 3483080006327	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1656	511	ENTREE	16.000	Import facture - code 3439499001736	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1657	758	ENTREE	37.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1658	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1659	354	ENTREE	28.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1660	352	ENTREE	278.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1661	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1662	496	ENTREE	34.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1663	759	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1664	416	ENTREE	6.000	Import facture - code 3439495403824	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1665	728	ENTREE	6.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1666	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1667	760	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1668	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1669	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1670	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1671	616	ENTREE	98.000	Import facture - code 3439495005523	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1672	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1673	381	ENTREE	8.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1674	502	ENTREE	18.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1675	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1676	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1677	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1678	719	ENTREE	3.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1679	761	ENTREE	7.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1680	762	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1681	763	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1682	764	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1683	749	ENTREE	6.000	Import facture - code 3439496809991	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1684	352	ENTREE	297.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1685	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1686	478	ENTREE	39.000	Import facture - code 03119783018847	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1687	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1688	479	ENTREE	21.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1689	489	ENTREE	18.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1690	315	ENTREE	367.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1691	584	ENTREE	36.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1692	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1693	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1694	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1695	416	ENTREE	6.000	Import facture - code 3439495403824	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1696	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1697	728	ENTREE	6.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1698	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1699	380	ENTREE	22.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1700	765	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1701	557	ENTREE	10.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1702	465	ENTREE	31.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1703	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1704	584	ENTREE	36.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1705	723	ENTREE	7.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1706	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1707	320	ENTREE	43.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1708	354	ENTREE	65.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1709	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1710	496	ENTREE	23.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1711	607	ENTREE	12.000	Import facture - code 3124488186852	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1712	593	ENTREE	9.000	Import facture - code 5449000089120	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1713	558	ENTREE	4.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1714	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1715	500	ENTREE	90.000	Import facture - code 3439495011388	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1716	766	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1717	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1718	502	ENTREE	5.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1719	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1720	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1721	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1722	485	ENTREE	94.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1723	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1724	723	ENTREE	7.000	Import facture - code 03258690014075	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1725	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1726	742	ENTREE	17.000	Import facture - code 3483080006327	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1727	318	ENTREE	46.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1728	320	ENTREE	43.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1729	354	ENTREE	39.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1730	352	ENTREE	478.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1731	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1732	496	ENTREE	22.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1733	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1734	488	ENTREE	7.000	Import facture - code 3439495407310	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1735	558	ENTREE	12.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1736	613	ENTREE	39.000	Import facture - code 3439495005530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1737	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1738	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1739	502	ENTREE	18.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1740	306	ENTREE	5.000	Import facture - code 4337182021858	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1741	306	ENTREE	5.000	Import facture - code 4337182021896	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1742	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1743	597	ENTREE	24.000	Import facture - code 3522091155102	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1744	767	ENTREE	16.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1745	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1746	315	ENTREE	297.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1747	320	ENTREE	43.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1748	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1749	768	ENTREE	95.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1750	583	ENTREE	124.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1751	723	ENTREE	7.000	Import facture - code 3258690014075	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1752	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1753	655	ENTREE	26.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1754	769	ENTREE	71.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1755	770	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1756	352	ENTREE	59.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1757	496	ENTREE	33.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1758	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1759	373	ENTREE	11.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1760	374	ENTREE	12.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1761	771	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1762	772	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1763	416	ENTREE	6.000	Import facture - code 3439495403824	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1764	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1765	728	ENTREE	5.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1766	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1767	773	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1768	481	ENTREE	36.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1769	774	ENTREE	10.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1770	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1771	775	ENTREE	18.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1772	751	ENTREE	46.000	Import facture - code 8423243004581	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1773	610	ENTREE	4.000	Import facture - code 18437003623551	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1774	776	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1775	390	ENTREE	5.000	Import facture - code 3439497006849	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1776	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1777	502	ENTREE	23.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1778	777	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1779	556	ENTREE	6.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1780	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1781	361	ENTREE	18.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1782	402	ENTREE	76.000	Import facture - code 5000299225004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1783	315	ENTREE	238.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1784	778	ENTREE	239.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1785	600	ENTREE	162.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1786	315	ENTREE	183.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1787	571	ENTREE	195.000	Import facture - code 3049614033872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1788	600	ENTREE	172.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1789	315	ENTREE	153.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1790	620	ENTREE	28.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1791	583	ENTREE	59.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1792	510	ENTREE	42.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1793	779	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1794	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1795	369	ENTREE	14.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1796	780	ENTREE	19.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1797	781	ENTREE	15.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1798	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1799	758	ENTREE	18.000	Import facture - code 3192370092000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1800	590	ENTREE	14.000	Import facture - code 03179077103161	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1801	782	ENTREE	93.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1802	354	ENTREE	39.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1803	352	ENTREE	185.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1804	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1805	783	ENTREE	23.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1806	784	ENTREE	45.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1807	785	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1808	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1809	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1810	693	ENTREE	42.000	Import facture - code 4337182170112	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1811	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1812	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1813	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1814	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1815	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1816	620	ENTREE	28.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1817	483	ENTREE	69.000	Import facture - code 5010103802550	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1818	315	ENTREE	122.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1819	489	ENTREE	14.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1820	787	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1821	438	ENTREE	5.000	Import facture - code 3439496807065	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1822	397	ENTREE	19.000	Import facture - code 3439495508345	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1823	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1824	591	ENTREE	16.000	Import facture - code 03119783012012	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1825	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1826	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1827	771	ENTREE	7.000	Import facture - code 3439495402810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1828	416	ENTREE	6.000	Import facture - code 3439495403824	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1829	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1830	788	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1831	789	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1832	728	ENTREE	6.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1833	790	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1834	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1835	791	ENTREE	16.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1836	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1837	596	ENTREE	10.000	Import facture - code 03179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1838	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1839	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1840	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1841	622	ENTREE	18.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1842	558	ENTREE	12.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1843	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1844	556	ENTREE	6.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1845	787	ENTREE	2.000	Import facture - code 3595531012501	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1846	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1847	792	ENTREE	80.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1848	793	ENTREE	15.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1849	710	ENTREE	226.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1850	365	ENTREE	7.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1851	711	ENTREE	7.000	Import facture - code 3147690060703	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1852	582	ENTREE	11.000	Import facture - code 3012991301001	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1853	622	ENTREE	20.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1854	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1855	485	ENTREE	48.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1856	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1857	369	ENTREE	89.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1858	794	ENTREE	16.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1859	769	ENTREE	71.000	Import facture - code 3760123281461	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1860	795	ENTREE	40.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1861	354	ENTREE	50.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1862	591	ENTREE	16.000	Import facture - code 03119783012012	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1863	352	ENTREE	295.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1864	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1865	496	ENTREE	44.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1866	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1867	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1868	418	ENTREE	52.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1869	381	ENTREE	8.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1870	796	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1871	797	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1872	798	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1873	799	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1874	800	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1875	574	ENTREE	1.000	Import facture - code 8420499102801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1876	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1877	719	ENTREE	3.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1878	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1879	385	ENTREE	20.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1880	620	ENTREE	85.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1881	801	ENTREE	52.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1882	802	ENTREE	37.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1883	600	ENTREE	160.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1884	315	ENTREE	122.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1885	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1886	784	ENTREE	22.000	Import facture - code 3770007850744	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1887	378	ENTREE	16.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1888	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1889	315	ENTREE	245.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1890	746	ENTREE	68.000	Import facture - code 5000267116662	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1891	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1892	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1893	803	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1894	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1895	352	ENTREE	145.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1896	454	ENTREE	114.000	Import facture - code 20080432402935	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1897	710	ENTREE	113.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1898	711	ENTREE	7.000	Import facture - code 3147690060703	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1899	622	ENTREE	20.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1900	583	ENTREE	124.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1901	510	ENTREE	158.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1902	584	ENTREE	27.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1903	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1904	369	ENTREE	29.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1905	600	ENTREE	162.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1906	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1907	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1908	352	ENTREE	221.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1909	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1910	496	ENTREE	22.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1911	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1912	701	ENTREE	36.000	Import facture - code 05000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1913	418	ENTREE	52.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1914	502	ENTREE	19.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1915	573	ENTREE	10.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1916	724	ENTREE	7.000	Import facture - code 3342690043309	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1917	556	ENTREE	9.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1918	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1919	385	ENTREE	9.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1920	361	ENTREE	18.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1921	805	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1922	806	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1923	306	ENTREE	5.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1924	809	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1925	315	ENTREE	367.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1926	463	ENTREE	22.000	Import facture - code 0080432402931	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1927	811	ENTREE	39.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1928	583	ENTREE	59.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1929	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1930	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1931	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1932	812	ENTREE	72.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1933	586	ENTREE	7.000	Import facture - code 3258690006094	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1934	795	ENTREE	43.000	Import facture - code 3450301167655	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1935	511	ENTREE	14.000	Import facture - code 3439499001736	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1936	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1937	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1938	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1939	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1940	728	ENTREE	17.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1941	378	ENTREE	18.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1942	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1943	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1944	500	ENTREE	90.000	Import facture - code 3439495011388	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1945	813	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1946	610	ENTREE	4.000	Import facture - code 18437003623551	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1947	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1948	627	ENTREE	8.000	Import facture - code 3439495110159	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1949	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1950	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1951	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1952	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1953	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1954	601	ENTREE	3.000	Import facture - code 3166720012659	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1955	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1956	470	ENTREE	181.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1957	746	ENTREE	234.000	Import facture - code 5000267116662	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1958	700	ENTREE	2.000	Import facture - code 5000112639995	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1959	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1960	814	ENTREE	13.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1961	672	ENTREE	13.000	Import facture - code 03119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1962	470	ENTREE	98.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1963	454	ENTREE	114.000	Import facture - code 20080432402935	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1964	793	ENTREE	27.000	Import facture - code 5010103800457	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1965	622	ENTREE	21.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1966	583	ENTREE	59.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1967	510	ENTREE	105.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1968	779	ENTREE	7.000	Import facture - code 3460270056768	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1969	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1970	815	ENTREE	32.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1971	769	ENTREE	72.000	Import facture - code 3760123281461	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1972	816	ENTREE	19.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1973	817	ENTREE	16.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1974	320	ENTREE	38.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1975	354	ENTREE	65.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1976	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1977	672	ENTREE	231.000	Import facture - code 03119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1978	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1979	496	ENTREE	45.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1980	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1981	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1982	378	ENTREE	18.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1983	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1984	418	ENTREE	64.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1985	381	ENTREE	8.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1986	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1987	306	ENTREE	5.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1988	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1989	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1990	726	ENTREE	5.000	Import facture - code 3439496804453	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1991	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1992	385	ENTREE	20.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1993	818	ENTREE	54.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1994	819	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1995	510	ENTREE	105.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1996	584	ENTREE	27.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1997	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1998	369	ENTREE	59.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1999	820	ENTREE	47.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2000	370	ENTREE	14.000	Import facture - code 03179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2001	320	ENTREE	8.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2002	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2003	352	ENTREE	295.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2004	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2005	496	ENTREE	44.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2006	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2007	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2008	378	ENTREE	36.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2009	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2010	751	ENTREE	50.000	Import facture - code 8423243004581	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2011	821	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2012	680	ENTREE	2.000	Import facture - code 3059942033482	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2013	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2014	361	ENTREE	18.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2015	402	ENTREE	138.000	Import facture - code 5000299225004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2016	315	ENTREE	398.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2017	583	ENTREE	99.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2018	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2019	411	ENTREE	23.000	Import facture - code 3451201439910	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2020	795	ENTREE	43.000	Import facture - code 3450301167655	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2021	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2022	607	ENTREE	9.000	Import facture - code 3124488186852	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2023	558	ENTREE	8.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2024	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2025	776	ENTREE	7.000	Import facture - code 3038351887107	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2026	390	ENTREE	5.000	Import facture - code 3439497006849	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2027	751	ENTREE	46.000	Import facture - code 8423243004581	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2028	615	ENTREE	153.000	Import facture - code 05010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2029	597	ENTREE	28.000	Import facture - code 3522091155102	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2030	823	ENTREE	30.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2031	824	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2032	792	ENTREE	89.000	Import facture - code 05099873127360	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2033	454	ENTREE	126.000	Import facture - code 20080432402935	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2034	811	ENTREE	18.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2035	825	ENTREE	21.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2036	620	ENTREE	28.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2037	465	ENTREE	20.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2038	622	ENTREE	20.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2039	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2040	369	ENTREE	13.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2041	826	ENTREE	10.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2042	370	ENTREE	13.000	Import facture - code 03179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2043	827	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2044	828	ENTREE	30.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2045	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2046	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2047	352	ENTREE	250.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2048	372	ENTREE	5.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2049	591	ENTREE	16.000	Import facture - code 03119783012012	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2050	496	ENTREE	40.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2051	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2052	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2053	418	ENTREE	46.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2054	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2055	502	ENTREE	17.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2056	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2057	573	ENTREE	21.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2058	719	ENTREE	3.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2059	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2060	361	ENTREE	18.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2061	315	ENTREE	245.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2062	811	ENTREE	39.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2063	365	ENTREE	7.000	Import facture - code 3147690059004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2064	582	ENTREE	11.000	Import facture - code 3012991301001	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2065	622	ENTREE	21.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2066	584	ENTREE	55.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2067	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2068	369	ENTREE	40.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2069	795	ENTREE	43.000	Import facture - code 3450301167655	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2070	816	ENTREE	42.000	Import facture - code 3439495504354	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2071	569	ENTREE	23.000	Import facture - code 3439495507638	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2072	370	ENTREE	13.000	Import facture - code 03179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2073	511	ENTREE	14.000	Import facture - code 3439499001736	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2074	829	ENTREE	22.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2075	782	ENTREE	140.000	Import facture - code 3185370283905	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2076	600	ENTREE	172.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2077	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2078	352	ENTREE	557.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2079	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2080	322	ENTREE	46.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2081	373	ENTREE	10.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2082	374	ENTREE	11.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2083	728	ENTREE	12.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2084	376	ENTREE	11.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2085	377	ENTREE	11.000	Import facture - code 3439495406368	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2086	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2087	488	ENTREE	5.000	Import facture - code 3439495407310	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2088	593	ENTREE	9.000	Import facture - code 05449000089120	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2089	532	ENTREE	8.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2090	701	ENTREE	16.000	Import facture - code 05000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2091	378	ENTREE	16.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2092	594	ENTREE	19.000	Import facture - code 3124488194659	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2093	558	ENTREE	12.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2094	445	ENTREE	3.000	Import facture - code 7613035833289	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2095	380	ENTREE	23.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2096	613	ENTREE	39.000	Import facture - code 3439495005530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2097	751	ENTREE	93.000	Import facture - code 8423243004581	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2098	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2099	627	ENTREE	8.000	Import facture - code 3439495110159	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2100	390	ENTREE	5.000	Import facture - code 3439497006849	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2101	381	ENTREE	9.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2102	502	ENTREE	44.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2103	556	ENTREE	6.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2104	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2105	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2106	830	ENTREE	19.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2107	831	ENTREE	99.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2108	832	ENTREE	51.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2109	833	ENTREE	105.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2110	603	ENTREE	7.000	Import facture - code 5000299610688	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2111	811	ENTREE	37.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2112	584	ENTREE	27.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2113	723	ENTREE	7.000	Import facture - code 03258690014075	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2114	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2115	369	ENTREE	14.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2116	743	ENTREE	30.000	Import facture - code 3439495501407	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2117	706	ENTREE	32.000	Import facture - code 5410228212805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2118	352	ENTREE	147.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2119	372	ENTREE	5.000	Import facture - code 03080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2120	701	ENTREE	18.000	Import facture - code 05000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2121	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2122	776	ENTREE	7.000	Import facture - code 3038351887107	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2123	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2124	707	ENTREE	13.000	Import facture - code 7613037935080	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2125	710	ENTREE	113.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2126	584	ENTREE	27.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2127	369	ENTREE	29.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2128	706	ENTREE	32.000	Import facture - code 5410228212805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2129	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2130	352	ENTREE	147.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2131	372	ENTREE	5.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2132	321	ENTREE	22.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2133	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2134	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2135	693	ENTREE	17.000	Import facture - code 4337182170112	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2136	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2137	834	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2138	835	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2139	556	ENTREE	5.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2140	836	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2141	837	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2142	695	ENTREE	26.000	Import facture - code 5410508209419	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2143	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2144	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2145	315	ENTREE	214.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2146	510	ENTREE	84.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2147	485	ENTREE	47.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2148	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2149	779	ENTREE	7.000	Import facture - code 3460270056768	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2150	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2151	758	ENTREE	18.000	Import facture - code 3192370092000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2152	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2153	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2154	352	ENTREE	77.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2155	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2156	321	ENTREE	22.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2157	378	ENTREE	16.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2158	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2159	380	ENTREE	22.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2160	838	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2161	610	ENTREE	4.000	Import facture - code 18437003623551	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2162	381	ENTREE	8.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2163	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2164	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2165	839	ENTREE	34.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2166	840	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2167	756	ENTREE	6.000	Import facture - code 3439495202939	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2168	841	ENTREE	35.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2169	843	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2170	844	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2171	845	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2172	846	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2173	846	ENTREE	5.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2174	352	ENTREE	154.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2175	849	ENTREE	96.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2176	599	ENTREE	2.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2177	622	ENTREE	41.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2178	510	ENTREE	42.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2179	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2180	369	ENTREE	14.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2181	569	ENTREE	44.000	Import facture - code 3439495507638	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2182	354	ENTREE	53.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2183	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2184	352	ENTREE	290.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2185	372	ENTREE	5.000	Import facture - code 03080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2186	496	ENTREE	55.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2187	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2188	791	ENTREE	15.000	Import facture - code 3249778013462	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2189	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2190	378	ENTREE	48.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2191	850	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2192	851	ENTREE	38.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2193	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2194	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2195	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2196	573	ENTREE	14.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2197	852	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2198	853	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2199	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2200	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2201	385	ENTREE	9.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2202	361	ENTREE	18.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2203	445	ENTREE	6.000	Import facture - code 7613035833289	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2204	596	ENTREE	10.000	Import facture - code 03179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2205	706	ENTREE	59.000	Import facture - code 5410228212805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2206	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2207	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2208	321	ENTREE	89.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2209	402	ENTREE	79.000	Import facture - code 5000299225004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2210	561	ENTREE	80.000	Import facture - code 05099873123454	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2211	710	ENTREE	92.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2212	571	ENTREE	195.000	Import facture - code 3049614033872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2213	354	ENTREE	39.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2214	352	ENTREE	216.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2215	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2216	784	ENTREE	45.000	Import facture - code 3770007850744	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2217	378	ENTREE	18.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2218	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2219	776	ENTREE	7.000	Import facture - code 3038351887107	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2220	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2221	854	ENTREE	20.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2222	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2223	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2224	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2225	855	ENTREE	21.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2226	856	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2227	857	ENTREE	101.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2228	858	ENTREE	80.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2229	583	ENTREE	62.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2230	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2231	485	ENTREE	46.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2232	859	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2233	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2234	655	ENTREE	14.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2235	860	ENTREE	19.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2236	861	ENTREE	51.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2237	862	ENTREE	78.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2238	758	ENTREE	17.000	Import facture - code 3192370092000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2239	571	ENTREE	176.000	Import facture - code 3049614033872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2240	600	ENTREE	155.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2241	354	ENTREE	40.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2242	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2243	352	ENTREE	217.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2244	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2245	863	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2246	773	ENTREE	5.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2247	851	ENTREE	7.000	Import facture - code 3075711380083	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2248	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2249	390	ENTREE	5.000	Import facture - code 3439497006849	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2250	502	ENTREE	5.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2251	573	ENTREE	10.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2252	719	ENTREE	3.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2253	691	ENTREE	2.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2254	385	ENTREE	9.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2255	864	ENTREE	64.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2256	865	ENTREE	10.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2257	866	ENTREE	21.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2258	867	ENTREE	16.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2259	315	ENTREE	275.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2260	746	ENTREE	137.000	Import facture - code 5000267116662	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2261	561	ENTREE	89.000	Import facture - code 05099873123454	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2262	849	ENTREE	119.000	Import facture - code 5000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2263	510	ENTREE	84.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2264	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2265	779	ENTREE	7.000	Import facture - code 3460270056768	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2266	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2267	817	ENTREE	18.000	Import facture - code 3439495501971	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2268	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2269	320	ENTREE	17.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2270	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2271	321	ENTREE	22.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2272	532	ENTREE	6.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2273	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2274	692	ENTREE	9.000	Import facture - code 7613034579959	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2275	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2276	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2277	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2278	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2279	656	ENTREE	13.000	Import facture - code 4337182087878	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2280	869	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2281	870	ENTREE	17.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2282	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2283	655	ENTREE	14.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2284	871	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2285	320	ENTREE	25.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2286	352	ENTREE	237.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2287	784	ENTREE	39.000	Import facture - code 3770007850744	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2288	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2289	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2290	850	ENTREE	9.000	Import facture - code 3700123301714	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2291	775	ENTREE	14.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2292	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2293	873	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2294	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2295	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2296	874	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2297	875	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2298	522	ENTREE	2.000	Import facture - code 3439496603513	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2299	345	ENTREE	6.000	Import facture - code 3439496604015	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2300	346	ENTREE	5.000	Import facture - code 3439496603995	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2301	876	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2302	719	ENTREE	3.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2303	877	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2304	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2305	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2306	352	ENTREE	888.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2307	857	ENTREE	101.000	Import facture - code 5000267120478	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2308	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2309	586	ENTREE	7.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2310	878	ENTREE	125.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2311	571	ENTREE	180.000	Import facture - code 3049614033872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2312	600	ENTREE	160.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2313	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2314	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2315	352	ENTREE	261.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2316	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2317	773	ENTREE	11.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2318	532	ENTREE	6.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2319	701	ENTREE	16.000	Import facture - code 05000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2320	378	ENTREE	16.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2321	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2322	418	ENTREE	36.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2323	610	ENTREE	4.000	Import facture - code 8437003623554	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2324	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2325	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2326	502	ENTREE	29.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2327	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2328	573	ENTREE	7.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2329	879	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2330	556	ENTREE	6.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2331	880	ENTREE	18.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2332	881	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2333	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2334	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2335	385	ENTREE	9.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2336	315	ENTREE	183.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2337	723	ENTREE	7.000	Import facture - code 3258690014075	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2338	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2339	369	ENTREE	12.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2340	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2341	352	ENTREE	92.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2342	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2343	496	ENTREE	22.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2344	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2345	882	ENTREE	27.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2346	883	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2347	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2348	558	ENTREE	4.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2349	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2350	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2351	747	ENTREE	8.000	Import facture - code 3439495111880	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2352	721	ENTREE	5.000	Import facture - code 3275560101550	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2353	618	ENTREE	10.000	Import facture - code 3346024708605	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2354	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2355	365	ENTREE	7.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2356	582	ENTREE	23.000	Import facture - code 3012991301001	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2357	465	ENTREE	26.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2358	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2359	411	ENTREE	23.000	Import facture - code 3451201439910	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2360	884	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2361	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2362	816	ENTREE	21.000	Import facture - code 3439495504354	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2363	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2364	320	ENTREE	51.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2365	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2366	352	ENTREE	405.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2367	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2368	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2369	489	ENTREE	18.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2370	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2371	502	ENTREE	6.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2372	306	ENTREE	5.000	Import facture - code 4337182021896	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2373	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2374	656	ENTREE	18.000	Import facture - code 4337182087878	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2375	620	ENTREE	171.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2376	352	ENTREE	145.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2377	620	ENTREE	57.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2378	869	ENTREE	28.000	Import facture - code 3163937010003	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2379	723	ENTREE	7.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2380	369	ENTREE	14.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2381	871	ENTREE	14.000	Import facture - code 3179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2382	590	ENTREE	14.000	Import facture - code 03179077103161	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2383	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2384	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2385	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2386	352	ENTREE	237.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2387	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2388	784	ENTREE	19.000	Import facture - code 3770007850744	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2389	886	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2390	378	ENTREE	18.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2391	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2392	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2393	502	ENTREE	5.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2394	887	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2395	573	ENTREE	10.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2396	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2397	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2398	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2399	315	ENTREE	29.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2400	439	ENTREE	14.000	Import facture - code 3099873045864	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2401	620	ENTREE	28.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2402	465	ENTREE	9.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2403	889	ENTREE	54.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2404	352	ENTREE	116.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2405	891	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2406	892	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2407	893	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2408	894	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2409	895	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2410	896	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2411	897	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2412	898	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2413	428	ENTREE	1.000	Import facture - code 3587220003525	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2414	347	ENTREE	5.000	Import facture - code 3439496604008	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2415	483	ENTREE	34.000	Import facture - code 5010103802550	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2416	315	ENTREE	459.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2417	583	ENTREE	99.000	Import facture - code 3211200044801	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2418	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2419	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2420	586	ENTREE	7.000	Import facture - code 3258690006094	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2421	318	ENTREE	31.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2422	320	ENTREE	25.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2423	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2424	591	ENTREE	17.000	Import facture - code 03119783012012	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2425	352	ENTREE	270.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2426	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2427	784	ENTREE	45.000	Import facture - code 3770007850744	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2428	479	ENTREE	42.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2429	488	ENTREE	5.000	Import facture - code 3439495407310	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2430	750	ENTREE	12.000	Import facture - code 5449000214928	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2431	899	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2432	594	ENTREE	9.000	Import facture - code 3124488194659	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2433	558	ENTREE	12.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2434	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2435	693	ENTREE	64.000	Import facture - code 4337182170112	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2436	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2437	900	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2438	306	ENTREE	5.000	Import facture - code 4337182022015	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2439	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2440	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2441	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2442	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2443	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2444	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2445	498	ENTREE	59.000	Import facture - code 5000213003756	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2446	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2447	496	ENTREE	29.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2448	373	ENTREE	12.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2449	374	ENTREE	13.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2450	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2451	728	ENTREE	6.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2452	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2453	377	ENTREE	13.000	Import facture - code 3439495406368	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2454	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2455	750	ENTREE	12.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2456	593	ENTREE	9.000	Import facture - code 5449000089120	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2457	532	ENTREE	8.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2458	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2459	678	ENTREE	62.000	Import facture - code 3439495022209	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2460	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2461	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2462	901	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2463	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2464	306	ENTREE	5.000	Import facture - code 4337182021858	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2465	902	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2466	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2467	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2468	315	ENTREE	367.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2469	463	ENTREE	38.000	Import facture - code 0080432402931	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2470	811	ENTREE	39.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2471	497	ENTREE	99.000	Import facture - code 3211200196883	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2472	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2473	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2474	369	ENTREE	15.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2475	871	ENTREE	29.000	Import facture - code 3179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2476	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2477	758	ENTREE	18.000	Import facture - code 3192370092000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2478	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2479	354	ENTREE	39.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2480	498	ENTREE	28.000	Import facture - code 5000213003756	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2481	352	ENTREE	270.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2482	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2483	321	ENTREE	45.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2484	373	ENTREE	12.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2485	374	ENTREE	13.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2486	416	ENTREE	6.000	Import facture - code 3439495403824	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2487	728	ENTREE	6.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2488	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2489	903	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2490	558	ENTREE	8.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2491	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2492	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2493	502	ENTREE	6.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2494	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2495	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2496	904	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2497	792	ENTREE	89.000	Import facture - code 05099873127360	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2498	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2499	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2500	369	ENTREE	14.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2501	569	ENTREE	22.000	Import facture - code 3439495507638	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2502	397	ENTREE	19.000	Import facture - code 3439495508345	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2503	352	ENTREE	290.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2504	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2505	591	ENTREE	16.000	Import facture - code 03119783012012	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2506	373	ENTREE	10.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2507	374	ENTREE	11.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2508	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2509	728	ENTREE	6.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2510	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2511	905	ENTREE	15.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2512	701	ENTREE	18.000	Import facture - code 05000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2513	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2514	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2515	906	ENTREE	28.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2516	907	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2517	748	ENTREE	10.000	Import facture - code 3270720021631	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2518	573	ENTREE	7.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2519	879	ENTREE	3.000	Import facture - code 7613036868082	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2520	724	ENTREE	7.000	Import facture - code 3342690043309	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2521	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2522	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2523	385	ENTREE	19.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2524	823	ENTREE	23.000	Import facture - code 4894597971241	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2525	904	ENTREE	14.000	Import facture - code 4894597971364	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2526	908	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2527	711	ENTREE	7.000	Import facture - code 3147690060703	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2528	620	ENTREE	114.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2529	622	ENTREE	41.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2530	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2531	909	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2532	858	ENTREE	80.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2533	454	ENTREE	126.000	Import facture - code 20080432402935	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2534	910	ENTREE	62.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2535	911	ENTREE	46.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2536	485	ENTREE	46.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2537	584	ENTREE	37.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2538	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2539	369	ENTREE	28.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2540	586	ENTREE	7.000	Import facture - code 03258691629582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2541	816	ENTREE	41.000	Import facture - code 3439495504354	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2542	569	ENTREE	107.000	Import facture - code 3439495507638	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2543	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2544	354	ENTREE	40.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2545	352	ENTREE	363.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2546	372	ENTREE	5.000	Import facture - code 03080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2547	374	ENTREE	12.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2548	479	ENTREE	23.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2549	378	ENTREE	36.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2550	489	ENTREE	13.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2551	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2552	678	ENTREE	36.000	Import facture - code 3439495022209	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2553	906	ENTREE	15.000	Import facture - code 4337182010289	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2554	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2555	573	ENTREE	7.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2556	879	ENTREE	7.000	Import facture - code 7613036868082	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2557	912	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2558	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2559	913	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2560	914	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2561	361	ENTREE	18.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2562	470	ENTREE	122.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2563	315	ENTREE	208.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2564	811	ENTREE	38.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2565	915	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2566	916	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2567	917	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2568	470	ENTREE	113.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2569	584	ENTREE	13.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2570	723	ENTREE	7.000	Import facture - code 3258690014075	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2571	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2572	655	ENTREE	29.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2573	320	ENTREE	17.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2574	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2575	352	ENTREE	147.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2576	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2577	918	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2578	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2579	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2580	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2581	445	ENTREE	3.000	Import facture - code 7613035833289	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2582	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2583	693	ENTREE	35.000	Import facture - code 4337182170112	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2584	381	ENTREE	8.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2585	798	ENTREE	5.000	Import facture - code 3439495120318	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2586	522	ENTREE	2.000	Import facture - code 3439496603513	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2587	632	ENTREE	1.000	Import facture - code 3439496607313	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2588	919	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2589	495	ENTREE	8.000	Import facture - code 3281513541618	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2590	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2591	920	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2592	921	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2593	470	ENTREE	45.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2594	746	ENTREE	66.000	Import facture - code 5000267116662	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2595	600	ENTREE	324.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2596	706	ENTREE	59.000	Import facture - code 5410228212805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2597	352	ENTREE	147.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2598	321	ENTREE	44.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2599	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2600	439	ENTREE	29.000	Import facture - code 3099873045864	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2601	463	ENTREE	42.000	Import facture - code 0080432402931	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2602	710	ENTREE	180.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2603	582	ENTREE	11.000	Import facture - code 3012991301001	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2604	461	ENTREE	4.000	Import facture - code 3011932000829	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2605	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2606	584	ENTREE	27.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2607	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2608	569	ENTREE	26.000	Import facture - code 3439495507638	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2609	397	ENTREE	19.000	Import facture - code 3439495508345	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2610	706	ENTREE	34.000	Import facture - code 5410228212805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2611	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2612	352	ENTREE	442.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2613	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2614	496	ENTREE	55.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2615	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2616	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2617	378	ENTREE	16.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2618	906	ENTREE	17.000	Import facture - code 4337182010289	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2619	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2620	573	ENTREE	3.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2621	557	ENTREE	10.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2622	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2623	315	ENTREE	551.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2624	454	ENTREE	114.000	Import facture - code 20080432402935	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2625	497	ENTREE	49.000	Import facture - code 3211200196883	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2626	584	ENTREE	36.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2627	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2628	369	ENTREE	30.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2629	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2630	782	ENTREE	140.000	Import facture - code 3185370283905	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2631	320	ENTREE	43.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2632	354	ENTREE	39.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2633	352	ENTREE	162.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2634	496	ENTREE	68.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2635	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2636	373	ENTREE	12.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2637	374	ENTREE	13.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2638	479	ENTREE	21.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2639	922	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2640	488	ENTREE	1.000	Import facture - code 3439495407310	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2641	607	ENTREE	9.000	Import facture - code 3124488186852	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2642	750	ENTREE	12.000	Import facture - code 5449000214928	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2643	594	ENTREE	18.000	Import facture - code 3124488194659	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2644	558	ENTREE	20.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2645	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2646	663	ENTREE	38.000	Import facture - code 4820078571051	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2647	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2648	419	ENTREE	10.000	Import facture - code 3439495108811	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2649	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2650	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2651	361	ENTREE	19.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2652	923	ENTREE	15.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2653	889	ENTREE	54.000	Import facture - code 3185370000335	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2654	354	ENTREE	40.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2655	352	ENTREE	118.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2656	372	ENTREE	5.000	Import facture - code 03080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2657	496	ENTREE	33.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2658	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2659	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2660	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2661	385	ENTREE	9.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2662	924	ENTREE	16.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2663	925	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2664	571	ENTREE	380.000	Import facture - code 3049614033872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2665	315	ENTREE	183.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2666	746	ENTREE	68.000	Import facture - code 5000267116662	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2667	926	ENTREE	176.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2668	315	ENTREE	766.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2669	315	ENTREE	183.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2670	746	ENTREE	137.000	Import facture - code 5000267116662	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2671	368	ENTREE	49.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2672	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2673	352	ENTREE	309.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2674	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2675	373	ENTREE	12.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2676	489	ENTREE	13.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2677	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2678	747	ENTREE	9.000	Import facture - code 3439495111880	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2679	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2680	381	ENTREE	8.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2681	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2682	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2683	306	ENTREE	5.000	Import facture - code 4337182021872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2684	719	ENTREE	3.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2685	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2686	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2687	811	ENTREE	19.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2688	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2689	369	ENTREE	13.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2690	370	ENTREE	14.000	Import facture - code 03179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2691	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2692	496	ENTREE	113.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2693	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2694	445	ENTREE	3.000	Import facture - code 7613035833289	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2695	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2696	927	ENTREE	15.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2697	315	ENTREE	214.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2698	320	ENTREE	17.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2699	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2700	321	ENTREE	45.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2701	928	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2702	929	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2703	930	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2704	488	ENTREE	3.000	Import facture - code 3439495407310	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2705	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2706	502	ENTREE	12.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2707	463	ENTREE	38.000	Import facture - code 0080432402931	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2708	811	ENTREE	37.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2709	711	ENTREE	7.000	Import facture - code 3147690060703	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2710	931	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2711	461	ENTREE	4.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2712	462	ENTREE	4.000	Import facture - code 3011932000904	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2713	660	ENTREE	43.000	Import facture - code 3262156015148	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2714	584	ENTREE	13.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2715	655	ENTREE	14.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2716	932	ENTREE	116.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2717	933	ENTREE	201.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2718	934	ENTREE	244.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2719	590	ENTREE	14.000	Import facture - code 03179077103161	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2720	935	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2721	706	ENTREE	14.000	Import facture - code 5410228212805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2722	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2723	591	ENTREE	16.000	Import facture - code 03119783012012	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2724	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2725	352	ENTREE	147.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2726	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2727	496	ENTREE	22.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2728	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2729	532	ENTREE	6.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2730	418	ENTREE	52.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2731	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2732	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2733	573	ENTREE	10.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2734	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2735	361	ENTREE	18.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2736	571	ENTREE	195.000	Import facture - code 3049614033872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2737	381	ENTREE	8.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2738	721	ENTREE	5.000	Import facture - code 3275560101550	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2739	315	ENTREE	153.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2740	439	ENTREE	31.000	Import facture - code 3099873045864	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2741	811	ENTREE	39.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2742	465	ENTREE	42.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2743	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2744	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2745	354	ENTREE	39.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2746	498	ENTREE	57.000	Import facture - code 5000213003756	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2747	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2748	496	ENTREE	49.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2749	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2750	373	ENTREE	11.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2751	374	ENTREE	12.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2752	728	ENTREE	11.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2753	479	ENTREE	47.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2754	488	ENTREE	3.000	Import facture - code 3439495407310	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2755	607	ENTREE	12.000	Import facture - code 3124488186852	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2756	593	ENTREE	29.000	Import facture - code 5449000089120	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2757	532	ENTREE	8.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2758	378	ENTREE	18.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2759	594	ENTREE	28.000	Import facture - code 3124488194659	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2760	558	ENTREE	29.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2761	380	ENTREE	11.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2762	775	ENTREE	40.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2763	501	ENTREE	22.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2764	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2765	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2766	494	ENTREE	5.000	Import facture - code 3439496823850	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2767	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2768	793	ENTREE	14.000	Import facture - code 5010103800457	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2769	849	ENTREE	113.000	Import facture - code 5000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2770	818	ENTREE	53.000	Import facture - code 05011013100613	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2771	584	ENTREE	37.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2772	320	ENTREE	25.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2773	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2774	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2775	672	ENTREE	158.000	Import facture - code 03119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2776	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2777	321	ENTREE	39.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2778	322	ENTREE	20.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2779	378	ENTREE	18.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2780	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2781	418	ENTREE	36.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2782	936	ENTREE	13.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2783	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2784	799	ENTREE	5.000	Import facture - code 3439495120400	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2785	632	ENTREE	1.000	Import facture - code 3439496607313	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2786	937	ENTREE	33.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2787	556	ENTREE	2.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2788	938	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2789	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2790	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2791	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2792	939	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2793	470	ENTREE	22.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2794	746	ENTREE	133.000	Import facture - code 5000267116662	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2795	470	ENTREE	318.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2796	710	ENTREE	119.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2797	622	ENTREE	21.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2798	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2799	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2800	655	ENTREE	27.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2801	871	ENTREE	14.000	Import facture - code 3179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2802	600	ENTREE	172.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2803	320	ENTREE	51.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2804	354	ENTREE	39.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2805	352	ENTREE	185.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2806	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2807	773	ENTREE	1.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2808	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2809	489	ENTREE	9.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2810	851	ENTREE	26.000	Import facture - code 3075711380083	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2811	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2812	776	ENTREE	12.000	Import facture - code 3038351887107	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2813	798	ENTREE	5.000	Import facture - code 3439495120318	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2814	940	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2815	941	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2816	942	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2817	385	ENTREE	10.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2818	849	ENTREE	96.000	Import facture - code 5000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2819	365	ENTREE	7.000	Import facture - code 3147690059004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2820	711	ENTREE	7.000	Import facture - code 3147690060703	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2821	622	ENTREE	41.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2822	510	ENTREE	52.000	Import facture - code 3176484042434	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2823	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2824	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2825	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2826	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2827	352	ENTREE	435.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2828	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2829	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2830	784	ENTREE	44.000	Import facture - code 3770007850744	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2831	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2832	701	ENTREE	36.000	Import facture - code 05000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2833	850	ENTREE	4.000	Import facture - code 3700123301714	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2834	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2835	418	ENTREE	36.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2836	909	ENTREE	2.000	Import facture - code 3265478446003	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2837	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2838	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2839	573	ENTREE	10.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2840	385	ENTREE	9.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2841	710	ENTREE	96.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2842	365	ENTREE	7.000	Import facture - code 3147690059004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2843	711	ENTREE	7.000	Import facture - code 3147690060703	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2844	582	ENTREE	11.000	Import facture - code 3012991301001	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2845	599	ENTREE	2.000	Import facture - code 3020881641106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2846	622	ENTREE	20.000	Import facture - code 3163937016005	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2847	485	ENTREE	46.000	Import facture - code 3262151637079	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2848	584	ENTREE	37.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2849	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2850	369	ENTREE	28.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2851	569	ENTREE	44.000	Import facture - code 3439495507638	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2852	706	ENTREE	44.000	Import facture - code 5410228212805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2853	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2854	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2855	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2856	378	ENTREE	36.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2857	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2858	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2859	906	ENTREE	28.000	Import facture - code 4337182010289	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2860	873	ENTREE	5.000	Import facture - code 3038351886902	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2861	943	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2862	900	ENTREE	7.000	Import facture - code 3490941705671	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2863	879	ENTREE	7.000	Import facture - code 7613036868082	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2864	556	ENTREE	3.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2865	385	ENTREE	19.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2866	944	ENTREE	21.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2867	306	ENTREE	5.000	Import facture - code 4337182021834	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2868	923	ENTREE	15.000	Import facture - code 3147690044703	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2869	320	ENTREE	17.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2870	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2871	352	ENTREE	197.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2872	470	ENTREE	45.000	Import facture - code 5000267102573	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2873	315	ENTREE	59.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2874	746	ENTREE	200.000	Import facture - code 5000267116662	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2875	461	ENTREE	4.000	Import facture - code 3011932000829	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2876	567	ENTREE	4.000	Import facture - code 3011932000843	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2877	462	ENTREE	4.000	Import facture - code 3011932000805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2878	584	ENTREE	27.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2879	369	ENTREE	29.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2880	871	ENTREE	29.000	Import facture - code 3179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2881	354	ENTREE	66.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2882	352	ENTREE	147.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2883	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2884	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2885	479	ENTREE	46.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2886	747	ENTREE	9.000	Import facture - code 3439495111880	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2887	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2888	946	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2889	947	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2890	390	ENTREE	5.000	Import facture - code 3439497006849	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2891	798	ENTREE	5.000	Import facture - code 3439495120318	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2892	948	ENTREE	18.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2893	949	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2894	667	ENTREE	3.000	Import facture - code 3660071100022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2895	315	ENTREE	337.000	Import facture - code 5010327325125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2896	439	ENTREE	31.000	Import facture - code 3099873045864	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2897	532	ENTREE	8.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2898	489	ENTREE	23.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2899	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2900	950	ENTREE	23.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2901	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2902	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2903	951	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2904	952	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2905	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2906	863	ENTREE	2.000	Import facture - code 3225350000501	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2907	953	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2908	954	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2909	955	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2910	930	ENTREE	2.000	Import facture - code 3439495400298	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2911	837	ENTREE	6.000	Import facture - code 3760251129192	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2912	956	ENTREE	22.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2913	792	ENTREE	83.000	Import facture - code 05099873127360	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2914	957	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2915	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2916	723	ENTREE	7.000	Import facture - code 3258691592879	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2917	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2918	370	ENTREE	11.000	Import facture - code 03179077103154	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2919	958	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2920	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2921	770	ENTREE	17.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2922	352	ENTREE	116.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2923	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2924	959	ENTREE	25.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2925	321	ENTREE	22.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2926	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2927	773	ENTREE	1.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2928	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2929	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2930	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2931	960	ENTREE	10.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2932	775	ENTREE	11.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2933	610	ENTREE	4.000	Import facture - code 8437003623554	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2934	502	ENTREE	17.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2935	961	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2936	962	ENTREE	15.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2937	963	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2938	964	ENTREE	13.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2939	965	ENTREE	24.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2940	941	ENTREE	1.000	Import facture - code 3662093119068	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2941	718	ENTREE	1.000	Import facture - code 3439496820088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2942	556	ENTREE	5.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2943	966	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2944	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2945	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2946	466	ENTREE	18.000	Import facture - code 3119780268276	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2947	967	ENTREE	23.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2948	372	ENTREE	5.000	Import facture - code 3080216054278	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2949	373	ENTREE	11.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2950	968	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2951	377	ENTREE	11.000	Import facture - code 3439495406368	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2952	532	ENTREE	15.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2953	969	ENTREE	34.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2954	970	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2955	759	ENTREE	6.000	Import facture - code 3439495404784	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2956	772	ENTREE	6.000	Import facture - code 3439495405026	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2957	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2958	788	ENTREE	7.000	Import facture - code 3439495405408	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2959	789	ENTREE	6.000	Import facture - code 3439495405125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2960	728	ENTREE	6.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2961	968	ENTREE	6.000	Import facture - code 3439495405484	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2962	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2963	717	ENTREE	3.000	Import facture - code 3439495401233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2964	971	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2965	532	ENTREE	6.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2966	851	ENTREE	6.000	Import facture - code 3075711380083	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2967	972	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2968	973	ENTREE	74.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2969	632	ENTREE	3.000	Import facture - code 3439496607313	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2970	975	ENTREE	21.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2971	976	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2972	919	ENTREE	3.000	Import facture - code 8420499102689	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2973	718	ENTREE	1.000	Import facture - code 3439496820088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2974	556	ENTREE	2.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2975	978	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2976	979	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2977	980	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2978	981	ENTREE	62.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2979	982	ENTREE	41.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2980	983	ENTREE	14.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2981	656	ENTREE	15.000	Import facture - code 4337182087878	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2982	984	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2983	824	ENTREE	3.000	Import facture - code 3281519550621	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2984	985	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2985	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2986	584	ENTREE	37.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2987	320	ENTREE	8.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2988	354	ENTREE	40.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2989	352	ENTREE	178.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2990	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2991	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2992	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2993	303	ENTREE	6.000	Import facture - code 3760151050565	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2994	556	ENTREE	2.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2995	438	ENTREE	5.000	Import facture - code 3439496807065	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2996	508	ENTREE	20.000	Import facture - code 4337182096900	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2997	857	ENTREE	93.000	Import facture - code 5000267120478	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2998	463	ENTREE	42.000	Import facture - code 0080432402931	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
2999	465	ENTREE	9.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3000	957	ENTREE	12.000	Import facture - code 3175529648709	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3001	986	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3002	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3003	354	ENTREE	40.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3004	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3005	352	ENTREE	235.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3006	959	ENTREE	25.000	Import facture - code 3119782991295	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3007	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3008	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3009	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3010	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3011	596	ENTREE	11.000	Import facture - code 03179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3012	502	ENTREE	9.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3013	987	ENTREE	34.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3014	311	ENTREE	6.000	Import facture - code 3760298920004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3015	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3016	454	ENTREE	115.000	Import facture - code 20080432402935	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3017	793	ENTREE	15.000	Import facture - code 5010103800457	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3018	849	ENTREE	113.000	Import facture - code 5000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3019	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3020	369	ENTREE	13.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3021	816	ENTREE	17.000	Import facture - code 3439495504354	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3022	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3023	320	ENTREE	25.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3024	354	ENTREE	40.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3025	352	ENTREE	223.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3026	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3027	959	ENTREE	25.000	Import facture - code 3119782991295	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3028	496	ENTREE	10.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3029	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3030	773	ENTREE	1.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3031	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3032	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3033	556	ENTREE	2.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3034	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3035	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3036	741	ENTREE	5.000	Import facture - code 3439494400640	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3037	849	ENTREE	192.000	Import facture - code 5000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3038	957	ENTREE	8.000	Import facture - code 3175529648709	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3039	986	ENTREE	17.000	Import facture - code 3175529652195	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3040	655	ENTREE	11.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3041	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3042	321	ENTREE	66.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3043	479	ENTREE	24.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3044	773	ENTREE	5.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3045	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3046	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3047	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3048	775	ENTREE	22.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3049	936	ENTREE	13.000	Import facture - code 3439495110357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3050	502	ENTREE	5.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3051	988	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3052	989	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3053	556	ENTREE	2.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3054	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3055	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3056	361	ENTREE	17.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3057	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3058	369	ENTREE	23.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3059	320	ENTREE	17.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3060	354	ENTREE	38.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3061	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3062	352	ENTREE	290.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3063	321	ENTREE	22.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3064	773	ENTREE	5.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3065	929	ENTREE	1.000	Import facture - code 3439495401370	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3066	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3067	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3068	502	ENTREE	5.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3069	719	ENTREE	6.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3070	438	ENTREE	5.000	Import facture - code 3439496807065	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3071	320	ENTREE	25.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3072	773	ENTREE	1.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3073	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3074	711	ENTREE	7.000	Import facture - code 3147690060703	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3075	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3076	320	ENTREE	38.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3077	354	ENTREE	13.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3078	321	ENTREE	66.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3079	373	ENTREE	11.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3080	374	ENTREE	14.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3081	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3082	376	ENTREE	12.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3083	377	ENTREE	11.000	Import facture - code 3439495406368	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3084	481	ENTREE	17.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3085	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3086	791	ENTREE	16.000	Import facture - code 3249778013462	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3087	489	ENTREE	13.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3088	990	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3089	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3090	438	ENTREE	5.000	Import facture - code 3439496807065	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3091	584	ENTREE	37.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3092	655	ENTREE	44.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3093	839	ENTREE	135.000	Import facture - code 3185370457054	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3094	991	ENTREE	69.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3095	770	ENTREE	16.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3096	352	ENTREE	174.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3097	959	ENTREE	50.000	Import facture - code 3119782991295	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3098	496	ENTREE	33.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3099	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3100	773	ENTREE	5.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3101	378	ENTREE	17.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3102	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3103	992	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3104	936	ENTREE	13.000	Import facture - code 3439495110357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3105	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3106	502	ENTREE	17.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3107	799	ENTREE	5.000	Import facture - code 3439495120400	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3108	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3109	961	ENTREE	17.000	Import facture - code 4337182017639	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3110	852	ENTREE	2.000	Import facture - code 3700222905868	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3111	853	ENTREE	2.000	Import facture - code 3700222905875	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3112	556	ENTREE	2.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3113	993	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3114	361	ENTREE	17.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3115	994	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3116	995	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3117	869	ENTREE	13.000	Import facture - code 3163937010003	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3118	599	ENTREE	2.000	Import facture - code 3020881641106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3119	996	ENTREE	12.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3120	466	ENTREE	9.000	Import facture - code 3119780268276	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3121	967	ENTREE	23.000	Import facture - code 5601164900714	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3122	372	ENTREE	5.000	Import facture - code 3080216054278	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3123	373	ENTREE	11.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3124	377	ENTREE	11.000	Import facture - code 3439495406368	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3125	997	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3126	998	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3127	999	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3128	1000	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3129	1001	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3130	1002	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3131	706	ENTREE	23.000	Import facture - code 5410228212805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3132	354	ENTREE	28.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3133	770	ENTREE	9.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3134	352	ENTREE	130.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3135	496	ENTREE	22.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3136	1005	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3137	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3138	532	ENTREE	6.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3139	791	ENTREE	16.000	Import facture - code 3249778013462	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3140	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3141	960	ENTREE	10.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3142	684	ENTREE	4.000	Import facture - code 03439495010985	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3143	1006	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3144	1007	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3145	798	ENTREE	5.000	Import facture - code 3439495120318	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3146	1008	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3147	1009	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3148	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3149	1010	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3150	1011	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3151	1012	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3152	439	ENTREE	15.000	Import facture - code 3099873045864	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3153	463	ENTREE	42.000	Import facture - code 0080432402931	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3154	811	ENTREE	75.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3155	1013	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3156	986	ENTREE	12.000	Import facture - code 3175529652195	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3157	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3158	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3159	369	ENTREE	13.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3160	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3161	354	ENTREE	53.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3162	352	ENTREE	196.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3163	959	ENTREE	25.000	Import facture - code 3119782991295	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3164	496	ENTREE	61.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3165	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3166	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3167	728	ENTREE	6.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3168	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3169	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3170	700	ENTREE	2.000	Import facture - code 5000112639995	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3171	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3172	1014	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3173	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3174	502	ENTREE	9.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3175	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3176	961	ENTREE	12.000	Import facture - code 4337182017639	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3177	1015	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3178	1012	ENTREE	4.000	Import facture - code 3760251128348	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3179	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3180	656	ENTREE	13.000	Import facture - code 4337182087878	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3181	1016	ENTREE	1.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3182	858	ENTREE	92.000	Import facture - code 05099873105306	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3183	793	ENTREE	12.000	Import facture - code 5010103800457	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3184	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3185	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3186	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3187	600	ENTREE	137.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3188	320	ENTREE	17.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3189	354	ENTREE	40.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3190	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3191	352	ENTREE	89.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3192	372	ENTREE	5.000	Import facture - code 03080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3193	959	ENTREE	25.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3194	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3195	481	ENTREE	17.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3196	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3197	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3198	936	ENTREE	26.000	Import facture - code 3439495110357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3199	502	ENTREE	17.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3200	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3201	996	ENTREE	12.000	Import facture - code 5410228258520	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3202	352	ENTREE	39.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3203	970	ENTREE	8.000	Import facture - code 3439495206814	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3204	402	ENTREE	38.000	Import facture - code 5000299225004	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3205	705	ENTREE	111.000	Import facture - code 3049610004104	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3206	532	ENTREE	15.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3207	903	ENTREE	8.000	Import facture - code 5449000174567	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3208	477	ENTREE	5.000	Import facture - code 3439496809939	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3209	857	ENTREE	113.000	Import facture - code 5000267120478	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3210	858	ENTREE	92.000	Import facture - code 05099873105306	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3211	1018	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3212	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3213	723	ENTREE	7.000	Import facture - code 3258691592879	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3214	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3215	655	ENTREE	23.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3216	320	ENTREE	17.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3217	770	ENTREE	17.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3218	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3219	321	ENTREE	44.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3220	773	ENTREE	5.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3221	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3222	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3223	502	ENTREE	5.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3224	1019	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3225	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3226	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3227	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3228	655	ENTREE	11.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3229	770	ENTREE	17.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3230	352	ENTREE	174.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3231	773	ENTREE	7.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3232	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3233	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3234	775	ENTREE	13.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3235	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3236	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3237	718	ENTREE	1.000	Import facture - code 3439496820088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3238	438	ENTREE	5.000	Import facture - code 3439496807065	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3239	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3240	723	ENTREE	7.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3241	368	ENTREE	79.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3242	655	ENTREE	29.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3243	816	ENTREE	86.000	Import facture - code 3439495504354	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3244	320	ENTREE	8.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3245	354	ENTREE	38.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3246	959	ENTREE	50.000	Import facture - code 3119782991295	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3247	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3248	374	ENTREE	14.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3249	886	ENTREE	5.000	Import facture - code 4000177211328	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3250	376	ENTREE	12.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3251	1020	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3252	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3253	532	ENTREE	13.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3254	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3255	1021	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3256	1022	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3257	1023	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3258	776	ENTREE	5.000	Import facture - code 3038351887107	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3259	1024	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3260	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3261	799	ENTREE	5.000	Import facture - code 3439495120400	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3262	879	ENTREE	3.000	Import facture - code 7613036868082	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3263	912	ENTREE	7.000	Import facture - code 7613034365774	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3264	852	ENTREE	3.000	Import facture - code 3700222905868	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3265	853	ENTREE	3.000	Import facture - code 3700222905875	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3266	787	ENTREE	3.000	Import facture - code 3595531012501	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3267	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3268	1025	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3269	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3270	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3271	462	ENTREE	4.000	Import facture - code 3011932000805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3272	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3273	368	ENTREE	59.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3274	569	ENTREE	23.000	Import facture - code 3439495507638	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3275	320	ENTREE	34.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3276	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3277	770	ENTREE	17.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3278	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3279	496	ENTREE	80.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3280	322	ENTREE	46.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3281	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3282	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3283	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3284	502	ENTREE	23.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3285	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3286	573	ENTREE	10.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3287	961	ENTREE	12.000	Import facture - code 4337182017639	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3288	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3289	1025	ENTREE	7.000	Import facture - code 3439496822549	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3290	361	ENTREE	17.000	Import facture - code 3439496810997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3291	439	ENTREE	15.000	Import facture - code 3099873045864	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3292	811	ENTREE	37.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3293	994	ENTREE	11.000	Import facture - code 5010103800259	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3294	365	ENTREE	7.000	Import facture - code 3147690061007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3295	869	ENTREE	13.000	Import facture - code 3163937010003	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3296	466	ENTREE	8.000	Import facture - code 3119780268276	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3297	967	ENTREE	23.000	Import facture - code 5601164900714	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3298	372	ENTREE	5.000	Import facture - code 3080216054278	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3299	496	ENTREE	22.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3300	971	ENTREE	2.000	Import facture - code 3439495401400	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3301	775	ENTREE	13.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3302	1026	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3303	919	ENTREE	3.000	Import facture - code 8420499102689	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3304	1027	ENTREE	2.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3305	1028	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3306	986	ENTREE	12.000	Import facture - code 3175529652195	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3307	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3308	369	ENTREE	29.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3309	958	ENTREE	11.000	Import facture - code 3439495506099	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3310	320	ENTREE	19.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3311	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3312	352	ENTREE	149.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3313	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3314	321	ENTREE	22.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3315	322	ENTREE	23.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3316	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3317	700	ENTREE	2.000	Import facture - code 5000112639995	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3318	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3319	596	ENTREE	10.000	Import facture - code 03179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3320	906	ENTREE	22.000	Import facture - code 4337182010289	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3321	936	ENTREE	26.000	Import facture - code 3439495110357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3322	390	ENTREE	5.000	Import facture - code 3439497006849	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3323	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3324	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3325	719	ENTREE	3.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3326	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3327	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3328	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3329	858	ENTREE	92.000	Import facture - code 05099873105306	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3330	454	ENTREE	128.000	Import facture - code 20080432402935	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3331	620	ENTREE	28.000	Import facture - code 3245990250203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3332	621	ENTREE	12.000	Import facture - code 3439495304213	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3333	1029	ENTREE	16.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3334	600	ENTREE	152.000	Import facture - code 3185370374733	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3335	320	ENTREE	43.000	Import facture - code 5410228203582	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3336	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3337	1030	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3338	1031	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3339	522	ENTREE	2.000	Import facture - code 3439496603513	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3340	345	ENTREE	6.000	Import facture - code 3439496604015	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3341	346	ENTREE	5.000	Import facture - code 3439496603995	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3342	584	ENTREE	24.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3343	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3344	655	ENTREE	39.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3345	352	ENTREE	223.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3346	1032	ENTREE	15.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3347	496	ENTREE	30.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3348	953	ENTREE	1.000	Import facture - code 3439495400274	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3349	773	ENTREE	5.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3350	929	ENTREE	1.000	Import facture - code 3439495401370	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3351	509	ENTREE	2.000	Import facture - code 3439495401448	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3352	971	ENTREE	2.000	Import facture - code 3439495401400	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3353	481	ENTREE	18.000	Import facture - code 5449000017673	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3354	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3355	502	ENTREE	17.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3356	754	ENTREE	8.000	Import facture - code 3439496822600	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3357	1033	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3358	352	ENTREE	72.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3359	961	ENTREE	8.000	Import facture - code 4337182017639	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3360	599	ENTREE	2.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3361	1032	ENTREE	15.000	Import facture - code 03119783017482	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3362	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3363	599	ENTREE	2.000	Import facture - code 3020881621108	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3364	655	ENTREE	29.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3365	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3366	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3367	321	ENTREE	22.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3368	879	ENTREE	3.000	Import facture - code 7613036868082	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3369	961	ENTREE	8.000	Import facture - code 4337182017639	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3370	1034	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3371	691	ENTREE	1.000	Import facture - code 3288360005676	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3372	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3373	465	ENTREE	10.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3374	1035	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3375	1036	ENTREE	4.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3376	438	ENTREE	5.000	Import facture - code 3439496807065	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3377	741	ENTREE	5.000	Import facture - code 3439494400640	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3378	584	ENTREE	55.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3379	655	ENTREE	59.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3380	770	ENTREE	8.000	Import facture - code 3119780259106	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3381	352	ENTREE	73.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3382	372	ENTREE	5.000	Import facture - code 03080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3383	321	ENTREE	21.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3384	378	ENTREE	16.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3385	380	ENTREE	10.000	Import facture - code 3179730004804	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3386	775	ENTREE	14.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3387	1037	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3388	949	ENTREE	12.000	Import facture - code 8000500282069	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3389	852	ENTREE	2.000	Import facture - code 3700222905868	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3390	853	ENTREE	2.000	Import facture - code 3700222905875	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3391	719	ENTREE	6.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3392	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3393	793	ENTREE	15.000	Import facture - code 5010103800457	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3394	1038	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3395	869	ENTREE	13.000	Import facture - code 3163937010003	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3396	462	ENTREE	4.000	Import facture - code 3011932000805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3397	957	ENTREE	12.000	Import facture - code 3175529648709	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3398	569	ENTREE	28.000	Import facture - code 3439495507638	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3399	513	ENTREE	2.000	Import facture - code 5601164900349	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3400	698	ENTREE	5.000	Import facture - code 7501064191459	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3401	530	ENTREE	38.000	Import facture - code 03119783018243	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3402	967	ENTREE	11.000	Import facture - code 5601164900714	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3403	372	ENTREE	5.000	Import facture - code 3080216054278	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3404	1040	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3405	1041	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3406	416	ENTREE	6.000	Import facture - code 3439495403824	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3407	968	ENTREE	6.000	Import facture - code 3439495405484	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3408	791	ENTREE	16.000	Import facture - code 3249778013462	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3409	1026	ENTREE	4.000	Import facture - code 3439497007075	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3410	438	ENTREE	5.000	Import facture - code 3439496807065	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3411	454	ENTREE	114.000	Import facture - code 20080432402935	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3412	793	ENTREE	14.000	Import facture - code 5010103800457	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3413	710	ENTREE	90.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3414	1043	ENTREE	47.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3415	405	ENTREE	7.000	Import facture - code 8410414000466	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3416	465	ENTREE	20.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3417	869	ENTREE	14.000	Import facture - code 3163937010003	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3418	461	ENTREE	4.000	Import facture - code 3011932000829	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3419	567	ENTREE	4.000	Import facture - code 3011932000843	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3420	462	ENTREE	4.000	Import facture - code 3011932000805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3421	584	ENTREE	37.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3422	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3423	1044	ENTREE	63.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3424	352	ENTREE	72.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3425	496	ENTREE	32.000	Import facture - code 3119780268382	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3426	373	ENTREE	11.000	Import facture - code 3439495405064	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3427	374	ENTREE	12.000	Import facture - code 3439495403794	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3428	375	ENTREE	6.000	Import facture - code 3439495405040	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3429	789	ENTREE	6.000	Import facture - code 3439495405125	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3430	728	ENTREE	11.000	Import facture - code 3439495405088	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3431	376	ENTREE	6.000	Import facture - code 3439495406320	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3432	479	ENTREE	21.000	Import facture - code 9002490205997	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3433	905	ENTREE	15.000	Import facture - code 03249778013462	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3434	700	ENTREE	2.000	Import facture - code 5000112639995	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3435	378	ENTREE	16.000	Import facture - code 5000112557091	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3436	489	ENTREE	8.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3437	1045	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3438	573	ENTREE	7.000	Import facture - code 7613037928532	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3439	912	ENTREE	7.000	Import facture - code 7613034365774	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3440	1046	ENTREE	31.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3441	468	ENTREE	40.000	Import facture	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3442	372	ENTREE	5.000	Import facture - code 3080216054278	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3443	858	ENTREE	89.000	Import facture - code 05099873105306	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3444	354	ENTREE	53.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3445	352	ENTREE	87.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3446	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3447	532	ENTREE	7.000	Import facture - code 5449000002921	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3448	418	ENTREE	33.000	Import facture - code 3075711382018	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3449	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3450	796	ENTREE	7.000	Import facture - code 3439497009291	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3451	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3452	632	ENTREE	1.000	Import facture - code 3439496607313	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3453	1048	ENTREE	11.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3454	1049	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3455	690	ENTREE	8.000	Import facture - code 3439496821399	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3456	1050	ENTREE	5.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3457	557	ENTREE	12.000	Import facture - code 3439496806365	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3458	726	ENTREE	5.000	Import facture - code 3439496804453	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3459	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3460	1051	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3461	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3462	438	ENTREE	5.000	Import facture - code 3439496807065	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3463	858	ENTREE	89.000	Import facture - code 05099873105306	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3464	958	ENTREE	11.000	Import facture - code 3439495506099	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3465	318	ENTREE	15.000	Import facture - code 3259356633067	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3466	558	ENTREE	3.000	Import facture - code 3439497020371	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3467	719	ENTREE	6.000	Import facture - code 5410555073810	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3468	986	ENTREE	25.000	Import facture - code 3175529652195	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3469	1052	ENTREE	10.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3470	1053	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3471	710	ENTREE	96.000	Import facture - code 05000267024240	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3472	465	ENTREE	21.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3473	957	ENTREE	8.000	Import facture - code 3175529648709	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3474	368	ENTREE	24.000	Import facture - code 3259354102060	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3475	655	ENTREE	23.000	Import facture - code 3179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3476	397	ENTREE	18.000	Import facture - code 3439495508345	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3477	354	ENTREE	26.000	Import facture - code 5410228223580	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3478	372	ENTREE	5.000	Import facture - code 3080210001872	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3479	321	ENTREE	44.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3480	322	ENTREE	22.000	Import facture - code 3119783016690	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3481	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3482	775	ENTREE	11.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3483	501	ENTREE	21.000	Import facture - code 3276650013203	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3484	907	ENTREE	5.000	Import facture - code 3038351887008	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3485	381	ENTREE	7.000	Import facture - code 3439495111699	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3486	502	ENTREE	11.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3487	777	ENTREE	6.000	Import facture - code 3439495106299	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3488	556	ENTREE	2.000	Import facture - code 3573972500504	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3489	764	ENTREE	3.000	Import facture - code 3288360000022	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3490	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3491	463	ENTREE	21.000	Import facture - code 0080432402931	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3492	811	ENTREE	18.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3493	1054	ENTREE	8.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3494	465	ENTREE	9.000	Import facture - code 5011013100156	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3495	352	ENTREE	26.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3496	953	ENTREE	1.000	Import facture - code 3439495400274	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3497	1055	ENTREE	6.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3498	306	ENTREE	5.000	Import facture - code 4337182021858	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3499	1056	ENTREE	3.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3500	360	ENTREE	15.000	Import facture - code 4337182004981	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3501	956	ENTREE	28.000	Import facture - code 0026102878514	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3502	1057	ENTREE	29.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3503	1058	ENTREE	9.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3504	584	ENTREE	18.000	Import facture - code 3175529644848	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3505	369	ENTREE	29.000	Import facture - code 03179077103147	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3506	352	ENTREE	58.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3507	321	ENTREE	21.000	Import facture - code 3155930400530	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3508	969	ENTREE	17.000	Import facture - code 3179730103989	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3509	352	ENTREE	29.000	Import facture - code 3119783018823	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3510	951	ENTREE	7.000	Import facture - code 3439494400626	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3511	811	ENTREE	48.000	Import facture - code 5000267024233	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3512	1059	ENTREE	18.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3513	372	ENTREE	5.000	Import facture - code 03080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3514	372	ENTREE	5.000	Import facture - code 3080210003425	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3515	773	ENTREE	3.000	Import facture - code 3439495400281	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3516	700	ENTREE	2.000	Import facture - code 5000112639995	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3517	489	ENTREE	4.000	Import facture - code 3439497020357	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3518	960	ENTREE	11.000	Import facture - code 3179730005306	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3519	775	ENTREE	13.000	Import facture - code 3265478167007	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3520	502	ENTREE	5.000	Import facture - code 3439495107906	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3521	1060	ENTREE	7.000	Import facture - création	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
3522	385	ENTREE	8.000	Import facture - code 3439496807805	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
\.


--
-- Data for Name: produits; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.produits (id, nom, categorie, prix_achat, prix_vente, tva, seuil_alerte, actif, stock_actuel, created_at, updated_at) FROM stdin;
1	BELLE F - MAQUEREAUX FLT 169G	Boissons	0.00	1.99	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
2	JW RED LABEL1L	Autre	0.00	27.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
297	SCE BIGY BURGER	Autre	9.00	9.00	20.00	0.000	t	5.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
298	SUCRE SOLNEIGE 5KG ST LOUIS 25 490 1	Autre	1.00	1.00	20.00	0.000	t	25.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
299	MC BOUCHEE RESTAU MGV X48 0 313 48	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
4	$8717438769837	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
300	PIDY 96 MINI TARTELETTES FINES NEUTRE BORD DROIT 19 890 1	Autre	1.00	1.00	20.00	0.000	t	19.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
301	NAPPAGE NEUTRE 0 9KG STAND.-VAR. 4 350 1	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
302	CREME UHT 35% 1L MC BK AP 4 898 6	Autre	1.00	1.00	20.00	0.000	t	29.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
304	40 VERRINE 4 CL PS CRISTAL 1 800 1	Autre	2.00	2.00	20.00	0.000	t	3.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
305	500 BROCHETTE 15CM 2 510 1	Autre	1.00	1.00	20.00	0.000	t	2.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
307	MPRO 25 BARQ ALU+COUV	Autre	21.00	21.00	20.00	0.000	t	0.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
308	MPRO 50 BARQ ALU+COUV	Autre	8.00	8.00	20.00	0.000	t	7.000	2025-10-30 12:05:49.521322	2025-10-30 12:05:49.521322
309	MINI BURGER 8X24G DULCESOL 1 630 1	Autre	14.00	14.00	20.00	0.000	t	22.000	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
312	MEL CJ MC C.750/	Autre	9.00	9.00	5.50	0.000	t	7.000	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
313	SAL ICEBERG MC DEMIPAL PC	Autre	2.00	2.00	20.00	0.000	t	8.000	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
314	45 VERRINE 7 CL PS CRISTAL 4 280 1	Autre	3.00	3.00	20.00	0.000	t	12.000	2025-10-30 12:06:22.270134	2025-10-30 12:06:22.270134
319	CHABLIS EMILE DURAND 75CL T 0 750 9 800 6	Autre	1.00	1.00	20.00	0.000	t	58.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
336	NESCAFE DOLCE GUSTO LUNGO X30 7 810 1	Autre	1.00	1.00	20.00	0.000	t	23.000	2025-10-30 12:06:46.790014	2025-10-30 12:12:16.376798
323	OASIS POMME /CASSIS /FRAM 2L 2 237 6	Autre	1.00	1.00	20.00	0.000	t	13.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
324	OASI POMM /CASS /FRAM 50CL PET 1 017 12	Autre	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
325	COCACOLA CHERRY SLIM 33CL 0 617 24	Autre	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
326	7UP CHERRY BTE 33CL SLIM 0 540 24	Autre	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
752	500 PAILLE PAP EMBAL 20CM 5 940 1	Autre	1.00	1.00	20.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
753	75 GOB CARTON BLANC DA 15CL 3 820 1	Autre	1.00	1.00	20.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
316	HT MEDOC CH ARCINS CB 75CL T 0 750 8 917 6	Autre	1.00	1.00	20.00	0.000	t	1118.000	2025-10-30 12:06:46.790014	2025-10-30 12:12:27.379196
332	M&M'S CRISPY 36G 0 562 24	Autre	1.00	1.00	20.00	0.000	t	13.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
755	TOUR PRIGNAC MIL 75CL AOC H M T 0 750 7 590 6	Autre	1.00	1.00	20.00	0.000	t	45.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
334	TUBO KG 30 MAD NATURE INDIV. 13 160 1	Autre	1.00	1.00	20.00	0.000	t	13.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
337	YOP 50CL VANILLE 1 300 1	Autre	3.00	3.00	20.00	0.000	t	3.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
338	YOP 50CL FRAISE 1 300 1	Autre	3.00	3.00	20.00	0.000	t	3.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
339	YOP FRAISE	Autre	8.00	8.00	20.00	0.000	t	2.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
340	YOP FRAMBOISE	Autre	8.00	8.00	20.00	0.000	t	2.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
341	SKYR A BOIRE FRUIT ROUGE	Autre	2.00	2.00	20.00	0.000	t	7.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
757	PORTO CRUZ BLC 18D 75CL I 0 750 6 280 1	Alcool	3.00	3.00	20.00	0.000	t	18.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
504	MPRO 5 PLAT OVAL ALU 43X29 4 890 1	Autre	2.00	2.00	20.00	0.000	t	9.000	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
317	BRG.CHARD V.VIGNOT 75CL T 0 750 5 310 6	Autre	2.00	2.00	20.00	0.000	t	133.000	2025-10-30 12:06:46.790014	2025-10-30 12:07:45.054577
310	FLEURS PLANTES 3 990 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 12:06:22.270134	2025-10-30 12:08:00.448408
506	50 BTE PULPE	Autre	7.00	7.00	20.00	0.000	t	0.000	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
507	MARQU CHALK VITRINE PTE CONIQ 2 740 1	Autre	1.00	1.00	20.00	0.000	t	2.000	2025-10-30 12:17:42.01398	2025-10-30 12:17:42.01398
330	MALTESERS SACHET 37G 0 631 25	Autre	1.00	1.00	20.00	0.000	t	30.000	2025-10-30 12:06:46.790014	2025-10-30 12:10:16.733895
1061	TOURNESOL COLZA	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1062	MIX BISCUITS SALES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1063	VIDE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1064	SALEE SACHET 800G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1065	TORTILLA CHILI 450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
505	MPRO 5 PLAT OVAL ALU 35X24 3 760 1	Autre	3.00	3.00	20.00	0.000	t	22.000	2025-10-30 12:17:42.01398	2025-10-30 13:27:52.525104
1066	MOULU KG SAXO (	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
342	SKYR A BOIRE VANILLE	Autre	2.00	2.00	20.00	0.000	t	7.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
760	GILBERT SUCRE DE CANNE 1L 2 670 1	Autre	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
348	CAROTTES RONDELLES 2.5KG MC 4 530 1	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
349	TENDER CRUNCH PLT SPIC HAL 1KG 11 080 1	Autre	2.00	2.00	20.00	0.000	t	22.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
350	WING PLT TEXMEX 2 5KG HAL CERT 15 270 1	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 12:06:46.790014	2025-10-30 12:06:46.790014
353	SCHROUMPF PIK TUBO X210 8 690 1	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 12:07:11.398554	2025-10-30 12:07:11.398554
762	MPRO ASSOUPLISS LINGE 60D 3L 4 620 1	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
331	M M'S PEANUT 45G SACHETS 0 566 36	Autre	1.00	1.00	10.00	0.000	t	75.000	2025-10-30 12:06:46.790014	2025-10-30 13:35:24.289083
763	WCNET PRO 4 BLOC OCEAN 4 530 1	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
749	MPRO LV MAIN 5L 1 426 5	Autre	1.00	1.00	20.00	0.000	t	13.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
5	7UP Cherry 33 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
765	LAIT UHT 1/2ECR BIO* 1L BT L 1 195 6	Autre	2.00	2.00	10.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
6	7UP Free Saveur Citron & Citron Vert 1,5 L	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
7	7UP Free Saveur Citron & Citron Vert 33 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
8	7UP Free Saveur Citron & Citron Vert 50 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
9	7UP Saveur Citron & Citron Vert 1,5 L	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
10	7UP Saveur Citron & Citron Vert 33 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
11	7UP Saveur Cocktail Exotique 33 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
12	7UP Saveur Mojito Citron Vert & Menthe 33 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
528	CAROTTES RAPEES METRO CHEF 1KG 2 690 1	Autre	6.00	6.00	20.00	0.000	t	16.000	2025-10-30 12:19:18.313605	2025-10-30 12:19:18.313605
766	RIZ BASMATI 5 KGS MC 2 596 5	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
343	CREME FRAI EP 15% 50CL ROCHAM 1 620 1	Autre	4.00	4.00	10.00	0.000	t	10.000	2025-10-30 12:06:46.790014	2025-10-30 13:27:52.525104
517	KINDER BUENO 0 649 30	Autre	2.00	2.00	10.00	0.000	t	245.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
518	KINDER MAXI T1 CHOCOLAT 0 472 36	Autre	1.00	1.00	20.00	0.000	t	32.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
329	KINDER COUNTRY 0 490 40	Autre	1.00	1.00	10.00	0.000	t	53.000	2025-10-30 12:06:46.790014	2025-10-30 13:35:24.289083
519	BALISTO LAIT MIEL AMANDE 0 492 20	Autre	1.00	1.00	10.00	0.000	t	27.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
520	BALISTO MUESLI MIX 37G 0 492 20	Autre	1.00	1.00	10.00	0.000	t	27.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
521	SKITTLES FRUITS 45 G 0 592 36	Autre	1.00	1.00	20.00	0.000	t	42.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
524	TOAST BRIOCHE	Autre	2.00	2.00	0.00	0.000	t	10.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
1089	ECHALOTE 6% 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1090	AOP 7% 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1091	MODENA IGP 6% 5L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
767	RETRO REPULSIF ULTRASON MOUCHE 16 300 1	Autre	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
355	OEUF 30 M SOL ARO 0 227 30	Autre	4.00	4.00	20.00	0.000	t	27.000	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
13	ABSOLUT 700ML	Autre	0.00	22.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
542	MALABAR BARBE APAPA	Autre	2.00	2.00	5.50	0.000	t	0.000	2025-10-30 12:20:16.389747	2025-10-30 13:05:40.667214
359	EPINARD BRANCHE PALET 2.5KG MC 5 130 4	Autre	1.00	1.00	20.00	0.000	t	40.000	2025-10-30 12:07:45.054577	2025-10-30 12:12:27.379196
358	EPINARD BRANCHE PALET 2.5KG MC 5 140 1	Autre	2.00	2.00	20.00	0.000	t	10.000	2025-10-30 12:07:45.054577	2025-10-30 12:07:45.054577
395	SIRENE GISCOURS 18 MGX 75CL T 0 750 21 510 1	Autre	4.00	4.00	20.00	0.000	t	86.000	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
362	ARO FILM ALIMENTA	Autre	3.00	3.00	20.00	0.000	t	0.000	2025-10-30 12:08:00.448408	2025-10-30 12:08:00.448408
363	200 CHARLOTTE BLC 10 920 1	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 12:08:00.448408	2025-10-30 12:08:00.448408
768	JDANIELS HONEY35D 70CLX6 +6VER D 35 0 0 245 0 700 15 963 6	Autre	1.00	1.00	20.00	0.000	t	95.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
533	SNICKERS 50G 0 462 32	Autre	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
396	SIRENE GISCOURS 18 MGX 75CL T 0 750 21 510 6	Autre	3.00	3.00	20.00	0.000	t	387.000	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
534	TOBLERONE LAIT 50G 0 848 24	Autre	1.00	1.00	20.00	0.000	t	20.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
379	SAN PELL 50CL PET 0 478 24	Autre	3.00	3.00	20.00	0.000	t	53.000	2025-10-30 12:08:25.252336	2025-10-30 12:11:53.816872
1142	LENTILLES VERTES DE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
774	COCA COLA 1L PET X9// 1 130 9	Autre	1.00	1.00	10.00	0.000	t	10.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
398	ATLANTIQ IGP OCEADE BLC 75CL T 0 750 1 830 6	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 12:09:02.576379	2025-10-30 12:09:02.576379
399	CH V. CLICQUOT BRUT 75CL M 0 750 37 715 6	Autre	1.00	1.00	20.00	0.000	t	668.000	2025-10-30 12:09:02.576379	2025-10-30 12:12:16.376798
384	ALLUMETTE FUM BOIS HETR 1KG MC 6 460 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 12:08:25.252336	2025-10-30 12:08:25.252336
1143	BALLOTIN 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
529	SAC CAISSE PP RECYCLE METRO 1 490 1	Autre	1.00	1.00	20.00	0.000	t	5.000	2025-10-30 12:19:57.146464	2025-10-30 13:22:12.34506
387	IGP MED BLC C. DAUPHINS 25CL T 0 250 1 350 12	Autre	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
536	CHOCOBOX 62 BARRES 2020 33 390 1	Autre	1.00	1.00	20.00	0.000	t	33.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
371	CH V.PELLETIER BRT 75CL M 0 750 13 275 6	Autre	1.00	1.00	20.00	0.000	t	317.000	2025-10-30 12:08:25.252336	2025-10-30 12:09:02.576379
531	BAVR ORIG BTE 8.6D 50CL B 8 6 0 043 0 500 1 102 24	Autre	2.00	2.00	20.00	0.000	t	52.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
392	LAY'S BARBECUE	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 12:08:39.842775	2025-10-30 12:08:39.842775
537	CROCODILES SAC 2KG 10 190 1	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
538	ROCH. OEUF PLAT POCHE 1.5KG 6 840 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
539	CROCOPIK VRAC 2KG 9 740 1	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
386	BRG.ALIG V.VIGNOT 75CL T 0 750 5 500 6	Autre	1.00	1.00	20.00	0.000	t	66.000	2025-10-30 12:08:39.842775	2025-10-30 12:09:38.699924
389	VINAIGRE BLANC 8° - 1L ARO 0 490 12	Alcool	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 12:08:39.842775	2025-10-30 12:09:38.699924
1144	LAIT BALLOTIN 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1145	PAYS ALPIN 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
541	MALABAR TUTTI FRUTTI X	Autre	2.00	2.00	5.50	0.000	t	0.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
543	HAPPY LIFE 2KG 10 610 1	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
1146	SACHET CUISSON	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
544	MENTOS MENTHE ROULEAU 0 445 40	Boissons	1.00	1.00	20.00	0.000	t	17.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
1147	KIT BURRITOS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
382	RIOBA MAYO BUCH	Autre	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 12:08:25.252336	2025-10-30 12:10:16.733895
1148	SAUCE FAJITA 430 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1150	NATURE 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1151	MED 315 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
535	M&M'S CRISPY 36G 0 438 24	Autre	1.00	1.00	10.00	0.000	t	46.000	2025-10-30 12:20:16.389747	2025-10-30 13:23:51.882142
540	MALABAR MENTHE BTE	Autre	2.00	2.00	5.50	0.000	t	0.000	2025-10-30 12:20:16.389747	2025-10-30 13:05:40.667214
400	WH JWALKER BLACK 12A 40D 70CL S 40 0 0 280 0 700 17 190 6	Autre	1.00	1.00	20.00	0.000	t	103.000	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
401	PAIN HOT DOG BRIOCHE 6X45G MC 2 020 1	Autre	1.00	1.00	20.00	0.000	t	2.000	2025-10-30 12:09:38.699924	2025-10-30 12:09:38.699924
403	VDK WYBOROWA	Autre	3.00	3.00	20.00	0.000	t	7.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
404	VODKA SMIRNOFF	Alcool	3.00	3.00	20.00	0.000	t	7.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
406	VODKA ABSOLUT BLUE 40D 70CL S 40 0 0 280 0 700 11 020 1	Alcool	2.00	2.00	20.00	0.000	t	22.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
407	VODKA BELVEDERE BIO* 40D 20CL S 40 0 0 080 0 200 9 590 1	Alcool	8.00	8.00	20.00	0.000	t	76.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
408	RHUM STJAMES PAILLE 40D 70CL G 40 0 0 280 0 700 10 580 1	Alcool	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
553	BRIOCH' BURGER SESAM 4X62G LFD 0 413 4	Autre	2.00	2.00	20.00	0.000	t	3.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
412	MEDOC PUY VALLON RGE 75CL T 0 750 2 990 6	Autre	2.00	2.00	20.00	0.000	t	35.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
413	IGP MED RSE CLAIR ESTEL 75CL T 0 750 3 390 6	Autre	1.00	1.00	20.00	0.000	t	20.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
414	PAYSOC CINS RSEMIL DELLAC75CL T 0 750 1 990 6	Autre	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
415	CHARDONNAY IGP LOIR 75CL T 0 750 3 590 6	Autre	1.00	1.00	20.00	0.000	t	21.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
417	RIOBA BOISS POM KIWI TO 25CL 0 690 12	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
554	BURGER LC 6 X 50G METRO CHEF 0 197 6	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 12:20:16.389747	2025-10-30 13:23:51.882142
421	FREEDENT WHITE MENTHVERT10D 0 523 30	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
422	CHEW.GUM FRAISE BOIS DRG 0 665 20	Autre	1.00	1.00	20.00	0.000	t	13.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
423	FREEDENT MENTHE VERTE 10DR 0 494 30	Autre	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
424	HWD 10 DR S/S GREENFRESH 0 602 20	Autre	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
425	HWD STYLE CHLORO 12 GUMS B 0 611 18	Autre	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
426	HWD STYLE COCKTAIL 12 GUM 0 602 18	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
1181	OLIVE 20% 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
429	PAIN HOT DOG BRIOCHE 4X85G MC 2 350 1	Autre	2.00	2.00	20.00	0.000	t	4.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
430	JB CUIT TORCHON SUPDD 10TRX90G 8 950 1	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
431	SPICY PLT PANE 1KG S_AT HALAL 9 570 1	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
432	MILANESE VOLAILLE 8X	Autre	1.00	1.00	20.00	0.000	t	2.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
555	4 VIENNOISES FENDUES	Autre	3.00	3.00	0.00	0.000	t	16.000	2025-10-30 12:20:16.389747	2025-10-30 13:23:51.882142
383	30 MADELEINES CHOCO TUBO 1KG 14 320 1	Autre	1.00	1.00	20.00	0.000	t	56.000	2025-10-30 12:08:25.252336	2025-10-30 12:10:59.277817
778	CHAMPAGNE R.DE RUINART 75 CL 3 0 750 39 990 6	Alcool	1.00	1.00	20.00	0.000	t	239.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
549	MINI HAPPY LIFE 40G MINI 0 361 30	Autre	2.00	2.00	20.00	0.000	t	62.000	2025-10-30 12:20:16.389747	2025-10-30 13:05:40.667214
560	WHISKY W.PEEL 40D 70CL S 40 0 0 280 0 700 8 030 1	Alcool	3.00	3.00	20.00	0.000	t	48.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
420	KINDER BUENO WHITE 0 714 30	Autre	1.00	1.00	20.00	0.000	t	81.000	2025-10-30 12:10:16.733895	2025-10-30 12:20:16.389747
545	CHEWING GUM MENTHOL 11 TAB. 0 412 20	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
546	BARQUETTE DRAGIBUS	Autre	1.00	1.00	20.00	0.000	t	2.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
548	SCHTROUMPF 40G TB 0 398 30	Autre	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
550	SACHET SOUR OCTOPUS 12 X	Autre	1.00	1.00	20.00	0.000	t	0.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
551	TOAST NATURE	Autre	2.00	2.00	20.00	0.000	t	8.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
552	PAIN MIE	Autre	5.00	5.00	20.00	0.000	t	0.000	2025-10-30 12:20:16.389747	2025-10-30 12:20:16.389747
364	ARO ALU	Autre	2.00	2.00	20.00	0.000	t	0.000	2025-10-30 12:08:00.448408	2025-10-30 12:20:16.389747
562	WHISKY LABEL	Alcool	5.00	5.00	20.00	0.000	t	12.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
1182	BIO 75 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1183	ET GRAINES BIO 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
547	SUC. ROCK FRUITFLEUR TB100 9 720 1	Autre	1.00	1.00	20.00	0.000	t	18.000	2025-10-30 12:20:16.389747	2025-10-30 13:35:24.289083
1184	NOIR BALLOTIN 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1186	ET SON DUO DE RIZ	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1188	BASMATI 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
563	WHISKY JB 40D 20CL S 40 0 0 080 0 200 4 540 6	Alcool	3.00	3.00	20.00	0.000	t	189.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
427	UNICORN DIPPER 1 218 12	Autre	1.00	1.00	20.00	0.000	t	26.000	2025-10-30 12:10:16.733895	2025-10-30 13:35:24.289083
1189	10MN 4X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
564	WH J.DANIEL S 35CL 40D S 40 0 0 140 0 350 10 434 12	Autre	1.00	1.00	20.00	0.000	t	250.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
1190	FOND VEAU 110G	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1191	FOND VOLAILLE 110G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1192	FUMET POISSON 90G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
433	CORDON DE VOLAILLE 1KG HALAL 6 520 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
434	DONUTS POULET 8X	Autre	1.00	1.00	20.00	0.000	t	0.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
435	SCISSE FRANCF X20 BN 1.1KG ENV 1 266 11 340	Autre	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
394	EPINARDS HACHES 2.5KG MC 4 323 4	Autre	1.00	1.00	20.00	0.000	t	34.000	2025-10-30 12:08:39.842775	2025-10-30 12:10:16.733895
436	CRISPERS 2.5KG MCCAIN 8 370 1	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
437	WINGS PLT CRUNCH SPICY 1KG HAL 7 320 1	Autre	1.00	1.00	20.00	0.000	t	7.000	2025-10-30 12:10:16.733895	2025-10-30 12:10:16.733895
568	FORT MIRAIL MIL 75CL ST EST T 0 750 7 990 6	Autre	1.00	1.00	20.00	0.000	t	94.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
441	ROCHE MAZET MERLOT 75CL IGP T 0 750 2 330 6	Autre	1.00	1.00	20.00	0.000	t	13.000	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
442	CH FEUILLATE TRADITION BRT 75C M 0 750 18 800 6	Autre	1.00	1.00	20.00	0.000	t	112.000	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
443	OASIS TROPICAL 50CL PET 1 034 12	Autre	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
446	BUCHETTE 4G C3 KG BS 10 010 1	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
447	PRINGLES BBQ	Autre	1.00	1.00	20.00	0.000	t	7.000	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
14	ANJU MOONG 1KG	Autre	0.00	5.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
15	ANJU URID 1KG	Autre	0.00	5.80	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
452	SIGMA 15 RL 60X46X12 THER SBPA 18 180 1	Autre	1.00	1.00	20.00	0.000	t	18.000	2025-10-30 12:10:43.935296	2025-10-30 12:10:43.935296
453	WH JACK DANIEL'S 40D 35CL S 40 0 0 140 0 350 10 130 1	Autre	3.00	3.00	20.00	0.000	t	30.000	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
1210	CHIPS BOLOGNAISE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
456	WH GRANTS TRIPLE WOOD 40D 20CL S 40 0 0 080 0 200 3 623 6	Autre	3.00	3.00	20.00	0.000	t	151.000	2025-10-30 12:10:59.277817	2025-10-30 13:31:35.960803
457	WH JACK DANIEL'S 40D 20CL S 40 0 0 080 0 200 6 630 8	Autre	1.00	1.00	20.00	0.000	t	53.000	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
16	ANNAM DIAMOND 1KG	Autre	0.00	3.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
410	RHUM AMBRE LM 40D 20CL X6 G 40 0 0 080 0 200 2 498 6	Alcool	3.00	3.00	20.00	0.000	t	252.000	2025-10-30 12:10:16.733895	2025-10-30 13:31:35.960803
460	MARTINI ROSATO	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 12:10:59.277817	2025-10-30 12:10:59.277817
458	VODKA ABSOLUT 40D 35CL S 40 0 0 140 0 350 7 850 1	Alcool	4.00	4.00	20.00	0.000	t	52.000	2025-10-30 12:10:59.277817	2025-10-30 12:24:35.062022
459	BAILEYS IRISH CREME 17D 70CL S 17 0 0 119 0 700 11 150 6	Autre	1.00	1.00	20.00	0.000	t	487.000	2025-10-30 12:10:59.277817	2025-10-30 13:35:24.289083
17	ANNY SARDINE OIL	Autre	0.00	1.30	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
455	WHISKY CHIVAS 18ANS 40D 70CL S 40 0 0 280 0 700 37 530 3	Alcool	2.00	2.00	20.00	0.000	t	592.000	2025-10-30 12:10:59.277817	2025-10-30 12:11:39.640331
450	PRINGLES CREAM OIGNON	Autre	1.00	1.00	0.00	0.000	t	35.000	2025-10-30 12:10:43.935296	2025-10-30 13:35:24.289083
449	PRINGLES PAPRIKA	Autre	1.00	1.00	0.00	0.000	t	14.000	2025-10-30 12:10:43.935296	2025-10-30 13:28:58.358722
1211	CHIPS ANCIENNE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
440	WH JWALKER BLACK 12A 40D 70CL S 40 0 0 280 0 700 20 628 6	Autre	1.00	1.00	20.00	0.000	t	347.000	2025-10-30 12:10:43.935296	2025-10-30 13:35:24.289083
18	ANTIE BOUILLON POULE 1KG	Autre	0.00	5.50	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
444	SCHWEPPES IT PET 4X50CL 0 828 24	Autre	1.00	1.00	10.00	0.000	t	216.000	2025-10-30 12:10:43.935296	2025-10-30 13:35:24.289083
780	VENTOUX T.AMBRE75CL RSEMIL DAR T 0 750 3 290 6	Autre	1.00	1.00	20.00	0.000	t	19.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
451	KINDER BUENO WHITE 0 630 30	Autre	2.00	2.00	10.00	0.000	t	234.000	2025-10-30 12:10:43.935296	2025-10-30 13:35:24.289083
781	PAYS D'OC VIOGNML DELLAC 75CL T 0 750 2 610 6	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
448	PRINGLES ORIGINAL	Alcool	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 12:10:43.935296	2025-10-30 12:30:02.473798
1212	SURGELE POMMES X4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
570	TOURAINE SAUV M.LAURENT 75CL T 0 750 3 950 6	Autre	2.00	2.00	20.00	0.000	t	94.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
1213	SURGELES CHOCOLAT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1214	MAIS DOUX BTE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1215	ECHALOTE 75 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1216	VINAIGRE JUS CITRON	Alcool	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1219	ARABICA PREMIUM	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1220	CLASSIQUE ROBUSTA	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
464	BS TI MANGUE PASSION 32D 70CL S 32 0 0 224 0 700 20 030 1	Autre	1.00	1.00	20.00	0.000	t	20.000	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
467	CACAHUETES GRILLEES SALEES 1KG 4 460 1	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 12:11:25.7753	2025-10-30 12:11:25.7753
469	WH GLENMORANGIE 18A 43D 70CL S 43 0 0 301 0 700 69 280 1	Autre	1.00	1.00	20.00	0.000	t	69.000	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
471	WHISKY DALMORE 12A 40D 70CL S 40 0 0 280 0 700 51 650 1	Alcool	2.00	2.00	20.00	0.000	t	103.000	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
472	WH TOGOUCHI PREMIUM 40D 70CL S 40 0 0 280 0 700 34 570 1	Autre	1.00	1.00	20.00	0.000	t	34.000	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
473	WH MACALLAN 12A DBCSK 40D 70CL S 40 0 0 280 0 700 74 700 1	Autre	2.00	2.00	20.00	0.000	t	149.000	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
474	WH GLENFIDDICH SB 18A 40D 70CL S 40 0 0 280 0 700 70 070 1	Autre	3.00	3.00	20.00	0.000	t	210.000	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
475	WH MONKEY SHOULDER 40D 70CL S 40 0 0 280 0 700 19 175 6	Autre	1.00	1.00	20.00	0.000	t	115.000	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
476	RIGATONI NAPOL.CECCO	Autre	5.00	5.00	20.00	0.000	t	0.000	2025-10-30 12:11:39.640331	2025-10-30 12:11:39.640331
480	MONSTER ENERGY BOITE 50CL 1 075 24	Autre	2.00	2.00	20.00	0.000	t	51.000	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
482	L'OR ESPRESSO SPLENDENTE 50 CA 13 850 1	Autre	1.00	1.00	20.00	0.000	t	13.000	2025-10-30 12:11:53.816872	2025-10-30 12:11:53.816872
783	DESPERAD 5.9D 65CL VP B 5 9 0 038 0 650 1 957 12	Autre	1.00	1.00	20.00	0.000	t	23.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
785	ROCHAMBEAU ABC ORANGE BRICK 1L 0 813 6	Boissons	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
576	MP FROTTOIR ALIMENTAIRE 25CM 12 150 1	Autre	1.00	1.00	20.00	0.000	t	24.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
771	GILBERT PJ POMME TR BIO*TO25CL 0 700 12	Autre	1.00	1.00	10.00	0.000	t	15.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
790	GILBERT BOISS FRAI/FRAMBTO25CL 0 590 12	Autre	1.00	1.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1194	FR/NL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1246	NOIR BIO 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1247	DECAFEINE ARABICA	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1248	HUILE 4 GRAINES 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1249	MIEL X 25 SACHETS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1250	CASSIS X 25 SACHETS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
587	HT MED RGE 17 LAROS TRINT 75CL T 0 750 12 990 1	Autre	2.00	2.00	20.00	0.000	t	50.000	2025-10-30 12:24:14.204165	2025-10-30 13:30:46.850961
598	VODKA ERISTOFF 35CL D	Alcool	3.00	3.00	20.00	0.000	t	7.000	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
580	MEDOC 75CL MIL CH ARCINS CB T 0 750 10 290 1	Autre	5.00	5.00	20.00	0.000	t	102.000	2025-10-30 12:23:54.959145	2025-10-30 12:29:33.975649
578	BOBINE	Autre	4.00	4.00	20.00	0.000	t	20.000	2025-10-30 12:23:32.662946	2025-10-30 13:22:28.810574
579	LA X JAV TRAD DEGRAISS 5L 3 310 1	Autre	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 12:23:32.662946	2025-10-30 13:22:28.810574
499	MOGU MOGU ANANAS PET 32CLX6 0 918 6	Autre	1.00	1.00	10.00	0.000	t	25.000	2025-10-30 12:16:40.566579	2025-10-30 13:29:20.668268
19	ARO PULPE TOMATE 400f	Autre	0.00	1.00	5.50	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
589	TOUR DE PEZ 17 ST EST 75CL T 0 750 15 290 1	Autre	2.00	2.00	20.00	0.000	t	60.000	2025-10-30 12:24:14.204165	2025-10-30 13:30:46.850961
581	500 SAC ORANGE EPAIS 27X12X47 34 190 1	Autre	1.00	1.00	20.00	0.000	t	68.000	2025-10-30 12:23:54.959145	2025-10-30 12:29:33.975649
20	ARO VINAIGRE B 1L	Alcool	0.00	1.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
588	SIRENE GISCOURS 16 MGX 75CL T 0 750 23 490 1	Autre	2.00	2.00	20.00	0.000	t	130.000	2025-10-30 12:24:14.204165	2025-10-30 13:35:24.289083
602	SET PELLE BALAYETTE GRD MODEL 3 400 1	Autre	1.00	1.00	20.00	0.000	t	3.000	2025-10-30 12:24:35.062022	2025-10-30 12:24:35.062022
577	ST EMILION GC CLOS CURE75CL MI T 0 750 12 490 6	Autre	1.00	1.00	20.00	0.000	t	518.000	2025-10-30 12:23:32.662946	2025-10-30 13:23:51.882142
592	COCA SANS SUCRES 30X33CL OS 0 474 30	Autre	1.00	1.00	10.00	0.000	t	28.000	2025-10-30 12:24:14.204165	2025-10-30 13:30:46.850961
503	HEINZ MAYONNAIS PRO 5L 24 100 1	Autre	1.00	1.00	10.00	0.000	t	144.000	2025-10-30 12:16:40.566579	2025-10-30 13:35:24.289083
585	MGX CH TOUR DE BESSAN	Autre	16.00	16.00	20.00	0.000	t	14.000	2025-10-30 12:24:14.204165	2025-10-30 13:30:46.850961
595	SCHWEPPES I.T. 6X25CL VP 0 721 24	Autre	1.00	1.00	10.00	0.000	t	68.000	2025-10-30 12:24:14.204165	2025-10-30 13:30:46.850961
1304	SALE SACHET 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1305	FLACON 965G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1306	FLACON 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
604	VDK BELVEDERE PURE 40D 20CL S 40 0 0 080 0 200 7 610 1	Autre	4.00	4.00	20.00	0.000	t	30.000	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
606	HEINEKEN 5D BTE 6X33CL B 5 0 0 017 0 330 0 711 24	Autre	1.00	1.00	20.00	0.000	t	17.000	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
616	MC HUILE FRITURE 25L 3 934 25	Autre	1.00	1.00	10.00	0.000	t	490.000	2025-10-30 12:32:17.747406	2025-10-30 13:37:59.565036
608	CONCENTRE TOM L MARTIN FR4/4 3 500 6	Autre	1.00	1.00	20.00	0.000	t	21.000	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
609	TOMATE ENT. PELEE 1/2 MUTTI 1 233 6	Autre	1.00	1.00	20.00	0.000	t	7.000	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
611	LAY'S MAX VINAIGRE 45G 0 633 20	Alcool	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
612	MPRO MINI BOBINE DC 2P	Autre	2.00	2.00	20.00	0.000	t	0.000	2025-10-30 12:30:02.473798	2025-10-30 12:30:02.473798
605	CHAMP VEUVE ELISABETH 75CL M 0 750 10 825 6	Autre	2.00	2.00	20.00	0.000	t	561.000	2025-10-30 12:30:02.473798	2025-10-30 13:28:44.005424
21	BACARDI CARTA BLANCA 70CL	Autre	0.00	24.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
614	MALABAR FRAISE BOITE	Autre	2.00	2.00	5.50	0.000	t	0.000	2025-10-30 12:31:31.948532	2025-10-30 13:05:40.667214
22	BACARDI CARTA ORO 70CL	Autre	0.00	20.39	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
617	MPRO 60 SERV AIRLAID RGE 40X40 8 240 1	Autre	1.00	1.00	20.00	0.000	t	32.000	2025-10-30 12:32:17.747406	2025-10-30 13:21:51.464527
794	CDR RGE A DARTOIS 75CL MIL T 0 750 2 692 6	Autre	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
23	BALLANTINE 35CL	Autre	0.00	15.99	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1365	TORSADE QS 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1366	SPAGHETTI QS 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1367	COQUILLETTE QS 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1368	MACARONI QS 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1369	SPAGHETTI QS 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1370	FUSILLI QS 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1371	FOND CARRE 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1372	MACARONI QS 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1373	NOUILLE SACHET 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1374	LENTILLE BOITE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1375	FLAGEOLET EF BTE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
24	BARRE MARBRE CAC BF	Autre	0.00	3.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
623	CRX PERRON ROLL 20 LAL POM 75C T 0 750 7 290 6	Autre	1.00	1.00	20.00	0.000	t	86.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
25	BARRE MARBREE 600G	Autre	0.00	3.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
624	MC VINAIGRE CIDRE 1L 2 700 1	Alcool	3.00	3.00	10.00	0.000	t	16.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
625	MC VINAIGRE CIDRE BIO* 1L 3 230 1	Alcool	3.00	3.00	10.00	0.000	t	18.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
26	BARRE PATISSIERE 600G	Autre	0.00	3.80	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
626	MC CONDIMENT BLC 1L 2 820 1	Autre	5.00	5.00	10.00	0.000	t	28.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
628	POIVRE BLANC MOULU 1KG ARO 17 500 1	Autre	1.00	1.00	10.00	0.000	t	34.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
629	POIVRE NOIR MOULU 1KG ARO 15 590 1	Autre	1.00	1.00	10.00	0.000	t	30.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
630	MC MOUTARDE DE DIJON 4KG 10 050 1	Autre	1.00	1.00	10.00	0.000	t	20.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
797	MC SAUCE ALGERIENNE	Autre	9.00	9.00	0.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
631	PAIN SP CROQUE LC 1KG MC 2 890 1	Autre	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
633	MPRO PH JUMBO 2P P.OUAT	Autre	3.00	3.00	2.10	0.000	t	10.000	2025-10-30 13:08:21.170149	2025-10-30 13:23:18.387594
800	CAMEMBERT AOP LC	Autre	2.00	2.00	0.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
801	POM BAL DE POINTE 75CL AOC MIL I 0 750 17 450 1	Autre	3.00	3.00	20.00	0.000	t	52.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
802	CH MAZEYRES 14 POM 75CL I 0 750 18 900 1	Autre	2.00	2.00	20.00	0.000	t	37.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1425	PAMPLEMOUSSE X25	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1426	TUBES SALES 85G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1427	TUBES BACON 85G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
27	BELLE ANTI CALCAIRE	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
28	BELLE B.MAÏS MIEL	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
634	WH JWALKER BLACK 12A 40D 70CL S 40 0 0 280 0 700 16 460 1	Autre	6.00	6.00	20.00	0.000	t	294.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
29	BELLE BLÉ S.MIEL	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
636	MOUTON CAD RGE MIL 75CL T 0 750 8 190 6	Autre	1.00	1.00	20.00	0.000	t	194.000	2025-10-30 13:08:54.596243	2025-10-30 13:37:59.565036
30	BELLE BÂT.CH.LAIT	Autre	0.00	2.20	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
637	CDR PRESTIGE RGE MIL75CL AOC T 0 750 3 008 6	Autre	1.00	1.00	20.00	0.000	t	54.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
652	TB	Autre	2.00	2.00	5.50	0.000	t	20.000	2025-10-30 13:08:54.596243	2025-10-30 13:35:24.289083
638	RESV MOUTON CADET MIL STEM 75C T 0 750 11 390 6	Autre	1.00	1.00	20.00	0.000	t	204.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
639	MX MUSCADOR BLC 75CL M 0 750 2 220 6	Autre	1.00	1.00	20.00	0.000	t	39.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
640	SIROP GILBERT GRENADINE 1L PET 2 490 1	Autre	6.00	6.00	10.00	0.000	t	42.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
31	BELLE DÉG.ORANGE	Autre	0.00	1.49	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
32	BELLE DÉG.ULTRA	Autre	0.00	1.49	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
641	SCHWEPPE AGRUME 1.5L 1 768 6	Autre	1.00	1.00	10.00	0.000	t	30.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
654	MPRO PH 2PLIS	Autre	2.00	2.00	20.00	0.000	t	0.000	2025-10-30 13:08:54.596243	2025-10-30 13:37:59.565036
33	BELLE DÉGR.FRAMB	Autre	0.00	1.49	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
642	COCA COLA CHERRY PET 50CL 0 960 12	Autre	1.00	1.00	10.00	0.000	t	33.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
34	BELLE F - CANNELLONI 400G	Autre	0.00	2.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
643	NESTLE DESSERT CORSE	Autre	2.00	2.00	0.00	0.000	t	0.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
35	BELLE F - CASSOULET 800G	Autre	0.00	4.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
36	BELLE F - EPINARD HACHE 790G	Autre	0.00	2.70	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
803	RH LA MAUNY BLC 40D 70CL G 40 0 0 280 0 700 7 500 1	Autre	1.00	1.00	20.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
644	NESTLE DESS.PRAL. LAIT	Autre	1.00	1.00	0.00	0.000	t	21.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
645	MILKA DAIM 3X	Autre	1.00	1.00	0.00	0.000	t	0.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
37	BELLE F - FILET SARDINE CITRON 100G	Autre	0.00	1.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
646	MILKA OREO 3X	Autre	1.00	1.00	0.00	0.000	t	0.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
38	BELLE F - GAUFRETTES CACAO 175G	Autre	0.00	1.80	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
647	ARO CHOC PATISSIER	Autre	2.00	2.00	0.00	0.000	t	0.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
39	BELLE F - PETIT BEURRE CH B150G	Autre	0.00	1.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
40	BELLE F - PETIT POIS 800G	Autre	0.00	3.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
648	TABLETTE M&MS CRISPY 2 360 1	Autre	2.00	2.00	20.00	0.000	t	12.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
649	MILKA RIZ	Autre	1.00	1.00	0.00	0.000	t	0.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
41	BELLE F - POIS CHICHES 800G	Autre	0.00	2.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
650	NESTLE DESSERT LAIT X2 5 150 1	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
42	BELLE F - RAVIOLI BOLOGN. 800G	Autre	0.00	7.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
651	NESTLE DESSERT BLANC	Autre	1.00	1.00	0.00	0.000	t	24.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
653	FREEDENT WHIT MENT FORT 10D 0 446 30	Autre	1.00	1.00	20.00	0.000	t	39.000	2025-10-30 13:08:54.596243	2025-10-30 13:23:51.882142
1484	MANGUE 165G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1485	COUSSIN 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
43	BELLE F - VINAIGRE XERES 50CL	Alcool	0.00	2.99	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
44	BELLE F BOEUF BOURG 400g	Autre	0.00	3.00	5.50	0.000	t	10.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
45	BELLE F CASSOULET 420G	Autre	0.00	1.70	20.00	0.000	t	5.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
46	BELLE F CHOUCROUTE GARNIE 400g	Autre	0.00	2.50	20.00	0.000	t	9.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
658	GOUDALE BOITE 7.2D 50CL B 7 2 0 036 0 500 1 411 12	Autre	1.00	1.00	20.00	0.000	t	32.000	2025-10-30 13:10:55.050915	2025-10-30 13:21:35.225351
47	BELLE F MAIS DOUX 300G	Autre	0.00	1.90	20.00	0.000	t	7.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
48	BELLE F POIS CHICHES 400G	Autre	0.00	1.99	20.00	0.000	t	18.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
49	BELLE F SARDINES FLT TOMATE 100G	Autre	0.00	1.99	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
50	BELLE F SAUCE BOLOG 200G	Autre	0.00	1.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
51	BELLE F SAUCISSES LENT 420g	Autre	0.00	2.50	20.00	0.000	t	8.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
52	BELLE F. JEUNES CAROTTES	Autre	0.00	1.50	20.00	0.000	t	4.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
53	BELLE FR.AD.LAV.14	Autre	0.00	3.60	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
54	BELLE FR.SIROP FR.	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
55	BELLE FTHON ALBACORE 112G	Autre	0.00	3.30	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
56	BELLE GEL D.L.C	Autre	0.00	2.20	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
659	ARO LIQ VAISS MAIN CIT 1LX3 3 730 1	Autre	2.00	2.00	20.00	0.000	t	13.000	2025-10-30 13:10:55.050915	2025-10-30 13:35:24.289083
657	CONNET TALBOT 17 ST JUL 75CL T 0 750 19 990 6	Autre	3.00	3.00	20.00	0.000	t	1317.000	2025-10-30 13:10:55.050915	2025-10-30 13:35:24.289083
57	BELLE GEL WC MARINE	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
58	BELLE GEL WC PIN	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
805	MAIS POP CORN 1KG LEGUMOR 2 890 1	Autre	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
806	BEURRE DX TENDRE1KG PRES.TARTI 6 790 1	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
808	MPRO 50 BOITE KEBAB BIOD	Autre	7.00	7.00	2.10	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
809	50 SAC KRAFT TORSADE 24X12X31 6 950 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
810	CAISSE SES	Autre	1.00	1.00	10.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1524	GLUTEN 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1131	BIO 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1525	ORANGE BIO 90G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1526	SAUVAGE BTE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1527	FRAMBOISE 750 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1528	BOLETS 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1529	MOUTARDE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1530	BIPHASEE ECHALOTES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1531	AL 160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1532	200G BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1533	AIL CIBOULETTE 80G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
59	BELLE MOUCH.ALOÉ V	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
661	SIRENE GISCOURS 17 MGX 75CL T 0 750 22 590 6	Autre	1.00	1.00	20.00	0.000	t	135.000	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
60	BELLE MÈCHE FL.BL.	Autre	0.00	2.99	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
662	COCA SANS SUCRES 25CL VP 0 690 12	Autre	2.00	2.00	10.00	0.000	t	16.000	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
664	CAKE & CHOCO MOELLEUX	Autre	1.00	1.00	0.00	0.000	t	7.000	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
61	BELLE MÈCHE LAV.	Autre	0.00	2.99	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
665	EMMENTAL FR RAPE	Autre	2.00	2.00	0.00	0.000	t	0.000	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
62	BELLE NET.MARINE	Autre	0.00	2.30	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
666	ROUL VEAU VOL OLI 6TR	Boissons	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
63	BELLE NET.MULTI SUR	Autre	0.00	2.30	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
668	EPINARD BRANCHE PALET 2.5KG MC 5 008 4	Autre	1.00	1.00	10.00	0.000	t	20.000	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
669	MANCHE BOIS VERNIS	Autre	1.00	1.00	20.00	0.000	t	3.000	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
670	BALAI SYNTH SOUPL MOUST 5 140 1	Autre	1.00	1.00	20.00	0.000	t	5.000	2025-10-30 13:27:52.525104	2025-10-30 13:27:52.525104
64	BELLE PÉCIAL SAN.N.	Autre	0.00	1.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
671	OEUF 90 M PPA VRAC (PTF) 0 144 90	Autre	2.00	2.00	10.00	0.000	t	25.000	2025-10-30 13:28:09.868901	2025-10-30 13:28:09.868901
65	BELLE SER.ULTRA	Autre	0.00	1.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
673	ORANGINA JAUN 1.5L 1 470 6	Alcool	1.00	1.00	10.00	0.000	t	8.000	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
66	BELLE SER.ULTRA N	Autre	0.00	1.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
674	FANTA ORANGE BTE SLIM 33CL 0 474 24	Autre	1.00	1.00	10.00	0.000	t	11.000	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
67	BELLE SHAMP.US.FRÉQ	Autre	0.00	2.49	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
675	COCA COLA PET 50CL 0 795 24	Autre	1.00	1.00	10.00	0.000	t	19.000	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
676	COCA-COLA CHERRY PET	Autre	1.00	1.00	5.50	0.000	t	2.000	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
677	BADOIT 50CL X6 PET 0 474 30	Autre	2.00	2.00	10.00	0.000	t	28.000	2025-10-30 13:28:28.855834	2025-10-30 13:28:28.855834
679	ARO MINI BOBINE DC 1P	Autre	1.00	1.00	2.10	0.000	t	2.000	2025-10-30 13:28:44.005424	2025-10-30 13:28:44.005424
681	CHATAIGNER RGE BDX	Autre	3.00	3.00	20.00	0.000	t	7.000	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
682	ARO TOMATE ENTIERE PELEE 4/4 1 320 6	Autre	1.00	1.00	10.00	0.000	t	7.000	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
683	ARO TOMATE ENTIERE PELEE 1/2 0 720 6	Autre	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
686	FARINE DE BLE T	Autre	5.00	5.00	20.00	0.000	t	5.000	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
687	50 BTE COUV CHARNIERE	Autre	5.00	5.00	20.00	0.000	t	0.000	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
68	BELVEDERE 20CL	Autre	0.00	17.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
688	ARO 2 TAMPON /EPONG /SYNTH X5 5 560 1	Autre	1.00	1.00	20.00	0.000	t	5.000	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
689	ARO 3 TAMPON A RECURER VERT 6 460 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 13:28:58.358722	2025-10-30 13:28:58.358722
812	ST EMILION GC CLOS CURE75CL MI T 0 750 12 150 6	Autre	1.00	1.00	20.00	0.000	t	72.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1568	CHOCOLAT 5L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1569	VANILLE 5L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1570	NORVEGE 900G 1,2 KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1571	COSSETTES 2.5 KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1572	MYRTILLE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1573	LARDONS FUMES 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1574	ALLUMETTES 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
69	BENS RIZ LONG GRAIN	Autre	0.00	3.50	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
694	400 NAPPES EXTRA BLC MAT 70X70 25 150 1	Autre	1.00	1.00	20.00	0.000	t	25.000	2025-10-30 13:29:29.50403	2025-10-30 13:29:29.50403
696	KIT DE PAIEMENT 3G+ 99 000 1	Autre	1.00	1.00	20.00	0.000	t	99.000	2025-10-30 13:30:29.970994	2025-10-30 13:30:29.970994
697	VODKA ABSOLUT 40D 35CL S 40 0 0 140 0 350 6 370 12	Alcool	1.00	1.00	20.00	0.000	t	76.000	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
699	CAPRISUN MULTI 20CLX10 0 272 10	Autre	4.00	4.00	10.00	0.000	t	10.000	2025-10-30 13:31:16.814255	2025-10-30 13:31:16.814255
565	WH GRANTS TRIPLE WOOD 40D 70CL S 40 0 0 280 0 700 10 382 6	Autre	1.00	1.00	20.00	0.000	t	124.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
566	WH CLAN CAMPBELL 40D 20CL S 40 0 0 080 0 200 3 817 12	Autre	1.00	1.00	20.00	0.000	t	90.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
572	PETIT ECOLIER CHOC.LAIT	Autre	1.00	1.00	0.00	0.000	t	10.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
575	MANCHE BOIS PONCE	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 12:23:12.672006	2025-10-30 13:31:35.960803
1608	SAV CREME BRULEE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1609	BOLOGNAISE 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
409	RHUM LM.BLC 40D 20CL X6 G 40 0 0 080 0 200 2 498 6	Alcool	4.00	4.00	20.00	0.000	t	373.000	2025-10-30 12:10:16.733895	2025-10-30 13:35:24.289083
574	100 SERV 1 PLI 33X33 1 240 1	Autre	2.00	2.00	20.00	0.000	t	9.000	2025-10-30 12:23:12.672006	2025-10-30 13:37:59.565036
1610	CARTON 450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1611	8X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1613	UHT 18%MG 3X20CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1614	FUME 5 BAIES 100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1265	100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1615	GROSSE BOCAL 37CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1616	CHOCO LAIT X 10 350	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1617	BLANQUETTE DE VEAU	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1618	MERLU MARINIERE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1619	POULET BASQUAISE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1620	POELEE PAYSANNE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1621	CHAMPIGNONS 450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1622	LARDONS 450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1623	PIZZA CHORIZO 450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1624	ROULE AU FROMAGE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
702	LEFFE BLONDE 6.6D 25CLX6 VP B 6 6 0 017 0 250 0 680 24	Autre	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
703	LEFFE 6 6D 28X25CL VP B 6 6 0 017 0 250 0 600 28	Autre	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
704	CH JEAN FAURE 16 ST EM GC 75CL T 0 750 29 990 6	Autre	1.00	1.00	20.00	0.000	t	179.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
708	REGISTRE UNIQUE DU PERSONNEL 18 270 1	Autre	1.00	1.00	20.00	0.000	t	18.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
709	SEAU LAVEUR A ROULETTE 15L 5 200 1	Boissons	1.00	1.00	20.00	0.000	t	5.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
712	RH STJAMES BLC	Autre	1.00	1.00	20.00	0.000	t	0.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
713	MARTINI FIERO	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
714	CH GISCOURS 17 MGX 75CL T 0 750 40 490 1	Autre	12.00	12.00	20.00	0.000	t	485.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
715	TOUR DE MONS 17 MGX 75CL T 0 750 14 290 1	Autre	12.00	12.00	20.00	0.000	t	171.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
716	CAB ANJOU RSE M.LAUR MIL 75C T 0 750 2 820 6	Autre	2.00	2.00	20.00	0.000	t	33.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
720	POUBELLE PLASTIQUE 90L BLANCHE 92 000 1	Autre	1.00	1.00	20.00	0.000	t	92.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
70	BLACK LABEL 70CL	Autre	0.00	30.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
500	ARO FRITURE 25L 90 640 1	Autre	1.00	1.00	10.00	0.000	t	630.000	2025-10-30 12:16:40.566579	2025-10-30 13:37:59.565036
813	PUGET CLASSIQUE 50CL 5 000 1	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1663	CHOIX FUME 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1664	CAFE 8X100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1665	LIEGEOIS CAFE 4X100	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1667	PAIN AU LAIT X 15	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1668	FERME COMPLET 500	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1669	SOUS VIDE 220G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1670	FRAICHE X8 360 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1671	TARTE TATIN 600 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1672	20X50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1666	4X100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
725	500 SAC BOUCHER EPAIS 26X12X45 35 620 1	Autre	1.00	1.00	20.00	0.000	t	35.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
727	BDX RGE MIL ROC CAZAD AC 75C T 0 750 3 108 6	Autre	1.00	1.00	20.00	0.000	t	18.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
729	GILBERT PUR JUS POMME TO 25CL 0 505 24	Boissons	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
730	FANTA ORAN PET 50CL PROMO X12 0 799 12	Autre	1.00	1.00	10.00	0.000	t	9.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
731	ORANGINA JAUNE 6X25CL VP 0 690 24	Alcool	1.00	1.00	10.00	0.000	t	16.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
732	PERRIER BOITE 33CL 0 390 24	Autre	3.00	3.00	10.00	0.000	t	28.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
733	STIMOROL S/S MENT/REGL 10DR 0 596 50	Autre	1.00	1.00	20.00	0.000	t	29.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
734	FREEDENT WHIT BUB MENT 10DR 0 452 30	Autre	1.00	1.00	20.00	0.000	t	13.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
735	SUCETTE CORAZON COEUR CERISE 10 500 1	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
736	CANDY FIZZ TRIO BOITE 0 633 24	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
737	HWD STYLE CHLORO 12 GUMS B 0 549 18	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
738	HWD STYLE COCKTAIL 12 GUM 0 549 18	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
739	BUBBLE NROLL 1 123 24	Autre	1.00	1.00	20.00	0.000	t	26.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
740	MANIFOLD FACT TRIPLI	Autre	1.00	1.00	0.00	0.000	t	4.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
1712	15 % 20 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1713	15 % 50 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1714	NATURE 4*125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1716	EPAISSE 30% MG 20	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
486	MOGU MOGU MELON PET 32CLX6 0 920 6	Autre	1.00	1.00	10.00	0.000	t	33.000	2025-10-30 12:15:47.724561	2025-10-30 13:35:24.289083
487	MOGU MOGU CASSIS PET 32 CL X6 0 920 6	Autre	1.00	1.00	10.00	0.000	t	20.000	2025-10-30 12:15:47.724561	2025-10-30 13:35:24.289083
478	HEINEKEN TACT 5D 4X50CL CAN B 5 0 0 025 0 500 0 870 24	Autre	2.00	2.00	20.00	0.000	t	207.000	2025-10-30 12:11:53.816872	2025-10-30 13:37:59.565036
491	PRINGLES CREME OIGNON 40G 0 998 12	Autre	1.00	1.00	10.00	0.000	t	45.000	2025-10-30 12:15:47.724561	2025-10-30 13:35:24.289083
493	MANGUE PRE.MURIE METRO CHEF PEROU C 1 PEROU 0 990 5	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 12:15:47.724561	2025-10-30 13:35:24.289083
742	ST CHINIAN RSE MIL EXCEL.STL75 T 0 750 3 150 6	Autre	1.00	1.00	20.00	0.000	t	52.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
744	MPRO FRITEUSE 8L GDF3008 292 520 1	Autre	1.00	1.00	20.00	0.000	t	292.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
745	PULCO CITRONNA 50CL PET 0 911 12	Autre	1.00	1.00	10.00	0.000	t	10.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
71	Belle F Epinards Branche 380g	Autre	0.00	2.70	20.00	0.000	t	8.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1770	CARBONARA 300G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1133	4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1771	CHOCOLAT 100GX4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1772	CAFE 100GX4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1774	FRAISE 6X120ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1775	COUSCOUS / 440G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1776	CARBONARA 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1625	MER X2 260G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1777	POMME JAUNE 4F BIO CRF Bio 3276550063551 - - - - voir (1) - - - 1 6/1 2/20 22	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1778	POMME BICOLORE 4F	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1779	POMME BICOLORE 6F	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1781	OF FQC N3 2DZFQC 3276550091417 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1782	40/60 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
72	Belle Haricots rouges 400g	Autre	0.00	1.80	5.50	0.000	t	26.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
73	Bonduelle mais 300g	Autre	0.00	2.50	20.00	0.000	t	7.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
366	COGN MEUKOV BLACK VS 40D 70CL S 40 0 0 280 0 700 21 020 1	Autre	1.00	1.00	20.00	0.000	t	197.000	2025-10-30 12:08:25.252336	2025-10-30 13:35:24.289083
484	MEDOC 75CL MIL CH ARCINS CB T 0 750 10 290 6	Autre	2.00	2.00	20.00	0.000	t	2915.000	2025-10-30 12:15:47.724561	2025-10-30 13:35:24.289083
74	Bouillon De Poulet	Autre	0.00	1.99	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
367	PAYS OC CABERN SAUV 25CL MAZET T 0 250 1 470 12	Autre	2.00	2.00	20.00	0.000	t	250.000	2025-10-30 12:08:25.252336	2025-10-30 13:35:24.289083
75	Bouillon de crevette	Autre	0.00	1.99	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
76	Bouillon de poisson	Autre	0.00	1.99	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
391	MC MOUTARDE DIJON 5KG 1 898 5	Autre	1.00	1.00	10.00	0.000	t	40.000	2025-10-30 12:08:39.842775	2025-10-30 13:35:24.289083
512	MX MUSCADOR BLC 75CL M 0 750 2 320 6	Autre	1.00	1.00	20.00	0.000	t	52.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
388	MX MUSCADOR ROSE 75CL M 0 750 2 220 6	Autre	2.00	2.00	20.00	0.000	t	130.000	2025-10-30 12:08:39.842775	2025-10-30 13:35:24.289083
514	KOLA CHAMPION BOITE 33CL 0 541 24	Autre	1.00	1.00	10.00	0.000	t	24.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
515	CRISTALINE FRAISE 50 CL 0 503 24	Autre	1.00	1.00	10.00	0.000	t	24.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
516	VINAIG CRISTAL 8D STIMULA 1L 0 475 12	Alcool	1.00	1.00	10.00	0.000	t	20.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
393	LAY'S BARBECUE SACHET 45G 0 590 20	Autre	1.00	1.00	10.00	0.000	t	39.000	2025-10-30 12:08:39.842775	2025-10-30 13:35:24.289083
490	PRINGLES ORIGINAL 40G 0 933 12	Alcool	1.00	1.00	10.00	0.000	t	87.000	2025-10-30 12:15:47.724561	2025-10-30 13:35:24.289083
492	PRINGLES PAPRIKA 40G 0 998 12	Autre	1.00	1.00	10.00	0.000	t	80.000	2025-10-30 12:15:47.724561	2025-10-30 13:35:24.289083
356	PAIN MIE NATURE LC	Autre	5.00	5.00	0.00	0.000	t	25.000	2025-10-30 12:07:45.054577	2025-10-30 13:35:24.289083
357	P. MIE COMPLET LC	Autre	5.00	5.00	0.00	0.000	t	30.000	2025-10-30 12:07:45.054577	2025-10-30 13:35:24.289083
525	PAIN 100% MIE LC 12X	Autre	12.00	12.00	0.00	0.000	t	164.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
526	MAXI HOT DOG 4X85G LFD 2 280 1	Autre	2.00	2.00	10.00	0.000	t	8.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
344	BRIOCHE TRANCHE	Autre	5.00	5.00	0.00	0.000	t	0.000	2025-10-30 12:06:46.790014	2025-10-30 13:35:24.289083
1819	BIO TR D 4X(1X140G)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1820	BIO TR D 4X(2X140G)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1821	CARR MAPCRF Bio 3523680287839 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
527	EPINARD BRANCHE PALET 2.5KG MC 4 930 1	Autre	8.00	8.00	10.00	0.000	t	326.000	2025-10-30 12:18:34.198825	2025-10-30 13:35:24.289083
722	MPRO DEGRAIS DESINF SA BACT 5L 17 030 1	Autre	1.00	1.00	20.00	0.000	t	34.000	2025-10-30 13:35:24.289083	2025-10-30 13:35:24.289083
559	NETTOYANT JAVEL EUCAL 5 L 7 880 1	Autre	1.00	1.00	20.00	0.000	t	21.000	2025-10-30 12:20:31.953437	2025-10-30 13:35:24.289083
601	ESSOREUR POUR SEAU 15L 3 410 1	Boissons	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 12:24:35.062022	2025-10-30 13:37:59.565036
77	CARIBBEAN SAISON RUM 70CL	Autre	0.00	1.00	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
814	LEFFE BLONDE 75CL 6.6D VP L 6 6 0 050 0 750 2 240 1	Autre	6.00	6.00	20.00	0.000	t	13.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
78	CELLIER .D 75CL	Autre	0.00	7.50	20.00	0.000	t	6.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
815	GALETS BONNAT RGE 16 GRAV 75CL T 0 750 5 490 6	Autre	1.00	1.00	20.00	0.000	t	32.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
769	ST EMILION GC CLOS CURE75CL MI I 0 750 11 990 6	Autre	1.00	1.00	20.00	0.000	t	214.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
79	CERELAC 400 G	Autre	0.00	6.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
80	CHABLIS 75CL	Autre	0.00	18.90	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
81	CHAMPIGNONS 400G	Autre	0.00	2.39	20.00	0.000	t	7.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1067	SAXO CASH KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1069	ARABICA 30 ROBUSTA	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1070	EXPRESSO 50A/50R KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1071	ARABICA/50 ROBUSTA	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1068	KG SAXO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1072	5R LATINO GOUT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1073	SAXO 50X7G 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1074	BOUILLON DE BOEUF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1075	VOLAILLE 1 KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1076	LÉGUMES ET B ŒUF 1	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1077	SEAU 5 KG	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1078	SEAU 1KG	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1079	ANCIENNE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
82	CHARDONNAY GILBERT CHON 70CL	Autre	0.00	9.70	20.00	0.000	t	11.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1080	ANCIENNE 5KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1081	ENDIVE BTE 5/1	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1082	MUNGO BTE 3/1	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1083	SACHET COUSSIN 2,5	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1084	EXTRA RHF 5L PET	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
819	CX GUILLOT MIL CBLAYE	Autre	3.00	3.00	20.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1085	SOUPLE 950G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1086	AOP 7% 5L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1087	BALSAMIQUE BLC 1 L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1088	MODENA IGP 6% 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1092	AMERIQUE LATINE KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1093	LATINE KG SAXO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
820	TOUR PRIGNAC MIL 75CL AOC H M T 0 750 7 890 1	Autre	6.00	6.00	20.00	0.000	t	47.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1094	GELEE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
83	CHAT CHAMP DE MARS 2020 75CL	Autre	0.00	6.99	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1095	BOUILLON 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1096	NATURE 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1097	VERTES 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1098	100X10G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1099	24 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1100	PAIN D'EPICES 470G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
84	CHAT D'ARCINS 2019 75CL	Autre	0.00	19.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1101	HUILE COLZA PPP 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1102	SIMPL 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1103	BIDON 25L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1104	BIDON 5L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1105	CLAIROR BIDON 5L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1106	CLAIROR BIDON 25L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1107	TOURNESOL ET HOVE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1108	HUILE POUR FRITURE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1109	SACHET 200 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1110	RDF 350 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1111	MIRABELLE 325 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1112	PROVENCE 325 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
85	CHAT HAUT POINT 75CL	Autre	0.00	9.90	20.00	0.000	t	6.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1113	FRAISE 350 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1114	MARSEILLE 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1115	PROVENCE 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1116	SARRASIN RDF 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
821	50 MASQUE 3 PLIS NOIR 6 000 1	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
86	CHAT.CAMPAR.75CL	Autre	0.00	12.99	20.00	0.000	t	4.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
680	VANISH GOLD BLC DETACH	Autre	2.00	2.00	20.00	0.000	t	4.000	2025-10-30 13:28:44.005424	2025-10-30 13:37:59.565036
1117	DE NORMANDIE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1118	PONT AVEN 100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1119	BRETAGNE 100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1120	180G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1121	RDF 1/5	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1122	NATUREL RDF 1/5	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1123	QUETSCHE D ALSACE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1124	LS LAIT CRU	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1125	950 G RDF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1126	CASSIS D ILE DE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1127	GATEAU CREUSOIS	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1128	NORMANDIE 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1129	760G RDF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1130	VEGETALES BIO 75 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1132	DECAFEINE STICK	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1134	CEREALES 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1135	ABRICOT AL 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1136	CACAO BIO MH 500 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1137	COCO 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1138	G POCKET	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1139	ARABICA BRESIL 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1140	FROMAGE 90 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1152	HOT 315 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1153	QUATRE PLANTES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1154	HARICOT ROUGE BTE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1155	PUREE DE PIMENT 100	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1156	SAUCE NEMS 90G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1157	SAUCE SOJA 125 ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1158	125 ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1159	ARABICA GOUT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1160	CRF/GJ 2X30CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1161	FRAISE 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1162	ABRICOT 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1164	ROQUEFORT 65G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1165	15 125 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1166	BOUTEILLE PET 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1167	RAPIDE 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1169	100G X4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1170	SSA 100G X4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1171	SESAME 125 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1172	HUILE PEPINS RAISINS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1173	CACAHUETE 90 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1174	FEVES BALLOTIN 250	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1175	MODENA IGP 25CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1176	PUR ARABICA 36X7G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1177	ORANGE 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1178	GRAS X36 250 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1179	CHOCOLAT BELGE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1180	LEVURE BOULANGERE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
822	4BT	Autre	2.00	2.00	0.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
615	WH GLENFIDDICH 15A 40D 70CL S 40 0 0 280 0 700 30 660 1	Autre	5.00	5.00	20.00	0.000	t	765.000	2025-10-30 12:32:17.747406	2025-10-30 13:37:59.565036
1193	295G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
597	500 SAC BLC BRET EPAI 26X12X45 28 580 1	Autre	1.00	1.00	20.00	0.000	t	108.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
1195	TARTIFLETTE 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1197	RAVIOLI PUR BOEUF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1198	250G/ GUYAUX	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1199	TUBO 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1200	LENTILLES 1/2 420G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1201	TAGLIATELLES 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1202	LENTILLES 4/4 840G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1203	PUR PORC 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1204	20A/80R 36X7G 252G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
825	GIN BEEFEATER 40D 70CL D 40 0 0 280 0 700 10 530 1	Alcool	2.00	2.00	20.00	0.000	t	21.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1205	CHOCOLAT 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1207	BOCAL 280G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1208	CHIPS NATURE 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1209	CHIPS ONDULEES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1221	EXTRA 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1222	EXTRA 50 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1223	ETUI CARTON 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
87	CHIVAS 12 70CL	Autre	0.00	29.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1226	370 G 35G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
826	RESV M CADET RGE HT MEDOC 75CL I 0 750 10 990 1	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1227	PROVENCE 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1228	250G X 2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
827	VDF SAUV RIBEAUPIERRE 75CL 8 0 750 1 990 6	Boissons	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
828	CH V.CLIQUOT RADIATING 75CL 3 0 750 30 310 1	Autre	1.00	1.00	20.00	0.000	t	30.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1229	CACAHUETE 2X75G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1230	G X 2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1231	HUILE TOURNESOL 2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1232	HUILE TOURNESOL 1	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1233	HUILE ARACHIDE 1 L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1234	ARABICA DOUX 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1235	BOCAL 370 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1236	PALMIER 100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1237	ALUMINIUM 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1238	GELIFIES BAC 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1239	VERRE DECORE 195 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1241	CONFITURE ORANGES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1243	SPAGHETTI BIO 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1244	NOISETTE BIO 200 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1242	BIO 100 G TC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1245	CRF 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1251	42,5 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1252	BIO 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1253	ORANGE 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1240	BIO EXTRA 360 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1254	ROUGE BIO 50 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1255	POCKET	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1256	ALLEGEE EN MG 1 L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1257	SACHETS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1258	PETALE SALE 75 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1259	COMPLET BIO 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1260	LAIT FOURRE LAIT 200	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1261	BOITE RONDE 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1262	RONDE 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1263	- 4 X 100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1264	BANANE 100 G X 4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1206	100 G X 4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1266	COTE IVOIRE TC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1267	SAUCE AIGRE DOUCE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1268	1 KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1269	PELEE AU JUS 1/2	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1271	BOCAL 250ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1272	37CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
88	CHT CLEMENT PICHON 2016 70CL	Autre	0.00	16.50	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1273	580ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1275	HUILE POUR FONDUE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1276	BALLOTIN 250 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1277	BOITE 3X1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1278	COMP ALL POMMES X	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1279	BIO 120 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1280	CHOCOLAT BIO 185 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1281	1/2 CRF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1282	NATUREL TRANCHE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1283	EXTRA MSC 1/5	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1284	AOP 50 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1285	POIVRE 60 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1286	300G/ SORBIERS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1287	ALU 300G/ SORBIER	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1288	MENTHE BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1289	PELEES AU JUS 4/4	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1290	MARMELADE ORANGE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1291	EXTRA 750G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1292	GELEE MURE 370 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1293	10MN 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1294	10MN 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1295	175 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1296	BCL 72CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1297	SURGELE POMME X10	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1298	SURGELE CHOCOLAT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1300	52% 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1301	MUNGO BTE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1302	BTE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1303	ET MORCEAUX BTE	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1307	120/149 BOITE 5/1 (	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1308	VINAIGRE BOITE 5/1	Alcool	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1309	BOCAL 190G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1310	MN 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1311	CREME ANGLAISE 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1312	MAIS DOUX BTE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1313	SUCRE AJOUTE BTE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
795	CRX PERRON ROLL 19 LAL POM 75C T 0 750 6 690 6	Autre	1.00	1.00	20.00	0.000	t	169.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1314	MAIS DOUX BTE 3/1	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1315	NATURE BOITE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1316	SAUCE TOMATE BTE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1317	70/30 BTE 3/1	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1318	CHARLEVAL 4,1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1319	7/12 BCL 425 ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
511	PAYS OC CHARDONML DELLAC 75CL T 0 750 2 510 6	Autre	1.00	1.00	20.00	0.000	t	188.000	2025-10-30 12:18:34.198825	2025-10-30 13:37:59.565036
829	GAILLAC BLC DX MIL BROZ 75C T 0 750 3 690 6	Autre	1.00	1.00	20.00	0.000	t	22.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1270	BOCAL 450ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1320	212ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1321	RAISINS 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
89	CIROC APPLE 70CL	Autre	0.00	49.99	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1322	TOAST BRIOCHE 125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1323	BRICK CRF 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1324	SQUEEZER 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1325	EN SEL 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1326	PECHES 370G 50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1327	25 SACHETS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
90	CIROC BLEU CLASSIQUE 70CL	Autre	0.00	49.99	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1328	ROUGES X 25 SACHETS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1329	NATUREL 190G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1330	SEL 100G TC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1332	FRITES SALEES 80 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1333	BOUTEILLE 690G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1334	CITRON	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1335	AUX FINES HERBES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1336	MINI BOCAL 314ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1337	CHATAIGNE 370G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1338	POIS CHICHE BTE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1339	MER 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1340	PUR JUS DE POMME	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1341	360G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1342	R 100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1343	FRAMBOISE 370 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1344	DU SOLEIL 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1345	TOMATE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1346	TOMATES 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
91	CIROC RED B 70CL	Autre	0.00	49.99	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1347	EPINARD HACHE BTE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1348	ETUVEE BOITE 3X1/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1349	EF BTE 3X1/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1350	LEGUMES BTE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1351	BOITE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1352	CAROTTE EF BTE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1353	BOUTEILLE 700G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1354	MENTHE 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1355	FRUITS 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1356	REGLISSE 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1357	POUDRE EXPRESSO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1358	MDD	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1274	BTE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1359	EF ETUVEE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1360	FIN BOITE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1362	500ML CRF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1363	BEURRE 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1364	BRICK 2X30 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
92	CLAN CAMPBELLN 35CL	Autre	0.00	10.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1377	AU LAIT X8 200G (	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1378	750G PP BLANC (	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1361	FIN BOITE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1379	PELEEES AU JUS 390	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1380	5/8 BOITE 1/2 PPP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1381	CHOCOLAT 180G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1376	PP BLANC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1382	VARIES PPB 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1383	BOCAL 370G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1384	HUILE DE TOURNESOL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1385	HUILE FRITURE PPB 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1386	PPB 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1388	400G (2X200G)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1389	CHOCOLAT 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1390	VANILLE 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1391	3X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
613	MC HUILE FRITURE 10L 3 996 10	Autre	1.00	1.00	10.00	0.000	t	117.000	2025-10-30 12:30:14.808307	2025-10-30 13:37:59.565036
751	HUILE TOURNESOL 25L ONDOSOL - 93 750 1	Autre	1.00	1.00	10.00	0.000	t	328.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1392	ALL BOCAL 720G (	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1393	POMMES ALL 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1394	CHIEN 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
627	ARO AIL SEMOULE SAC 1KG 8 440 1	Autre	1.00	1.00	10.00	0.000	t	32.000	2025-10-30 13:08:21.170149	2025-10-30 13:37:59.565036
1395	BOCAL 37CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1396	X200 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1397	135G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1398	6X30G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1400	100%R 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1401	FLACON 265 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1402	445 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1403	CHOCOLATS LAIT 445	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1404	CHOCOLATS NOIR 445	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1217	370 G 50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1405	750G 50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1406	LAIT PASTEURISE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1407	X 8 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1408	BIO BABY 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
830	*SUCRE CRISTAL N2 BS SAC 25KG 0 793 25	Autre	1.00	1.00	10.00	0.000	t	19.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
831	CREME FRAI EP 15% 5L PRESIDENT 3 332 5	Autre	6.00	6.00	10.00	0.000	t	99.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
832	CREME FRAI. EP. 30% 3L MC 3 417 3	Autre	5.00	5.00	10.00	0.000	t	51.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
833	CREME FRAI. EP. 30% 5L PPX 17 510 1	Autre	6.00	6.00	10.00	0.000	t	105.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1409	BABY 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1411	COURGE 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1412	RHF 1.8 KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1413	PECHE 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1415	SOFT TOUCH 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1416	HUILE 4 GRAINES 2L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1417	ORANGE X6 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1418	CAHORS RDF 1240G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1419	AMANDES X8 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1420	ACIDULEES CRF 39G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1421	BRETAGNE 85G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1423	SAVEURS DU SUD BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1424	NOIRE PAYS BASQUE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1428	CREME OIGNON 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1429	125G BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1431	BIO BOCAL 190G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1432	KIWI PET 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1433	BRIQUE 50CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1434	NOIR BIO 140G (12)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1435	A CACHER 735G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1436	275G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1437	SAUCE CAESAR RHF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1438	BALSAMIQUE 250 ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1439	BALSAMIQUE 500 ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
603	WHISKY BALLANTINE 40D 35CL S 40 0 0 140 0 350 7 990 1	Alcool	1.00	1.00	20.00	0.000	t	46.000	2025-10-30 12:30:02.473798	2025-10-30 13:37:59.565036
1440	BARBECUE 135G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1441	EF/TF BTE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1442	NOIX 65G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1410	25CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1443	HARICOT ROUGE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1444	PETIT BEURRE BIO 167	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1445	SEL DE MER FIN 1 KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1446	ENDIVE 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
743	TAVEL RSE MIL 75CL MESILLONS T 0 750 5 350 6	Autre	1.00	1.00	20.00	0.000	t	62.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
1447	GOURDES X12	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1448	POINTE 250ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1449	POINTES BCL 314ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1450	EN MG 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1451	ALLÉGÉE EN MG 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1452	D'ALSACE RDF 1400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1453	ÉPICES 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1454	POULE AU POT 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1455	BRICK CRF 2X30CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1414	BIO 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1456	BIO 2X30CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1457	ATLAS 350 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
707	DOLCE GUSTO ESPRESSO X30 6 950 1	Autre	2.00	2.00	10.00	0.000	t	33.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
1141	100G TC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1458	RHUBARBE 370G 50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1218	370G 50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1459	HUILE ARACHIDE 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1460	MOYON	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1462	CORSE SAXO 50X7G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1463	DOUX SAXO 50X7G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1464	490G RDF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1465	160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1466	FRUITS BIO X5 175G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1467	MIEL BIO 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1468	TRANCHÉ BIO 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1469	PELEES 4/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1470	PUR ARABICA 48X7G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1471	20A/80R 48X7G 336G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1472	TUTTI FRUTTI 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1473	EXTRA 25 CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1474	MERGUEZ 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1475	AU LAIT 160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1476	BRUT MORCEAUX	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1477	BOEUF 800G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1478	SAXO KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1479	RATATOUILLE PPP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
834	LA PERRUC.BUCHET.CANNE 4GRX300 5 950 1	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
835	50 GOBELET BAROQUE 10CL 1 450 1	Autre	1.00	1.00	20.00	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1480	2X30CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1481	ARTICHAUD 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
836	50 SAC KRAFT S PLANETE 32X16X39 9 470 1	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1482	X10 70G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
695	50 BTE REPAS 3 COMP GM PULP 26 780 1	Autre	1.00	1.00	20.00	0.000	t	52.000	2025-10-30 13:29:29.50403	2025-10-30 13:37:59.565036
1483	IGP BIO X20 32G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1486	DOUCE BIO X20 32G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1487	CHOCOLAT BLANC BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1488	CHOCOLAT LAIT X200/	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1489	4 VARIETES/ 190G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1490	CHOCOLAT LAIT 175G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1430	125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1491	PAQUET CARRE 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1492	NOISETTE BIO 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1493	BOITE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1494	BIO 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1495	COUSCOUS BIO BCL 72	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1496	CAMOMILLE BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1497	1000 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1498	CRISTAL 8% 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1499	COLORE 6% 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1500	VINAIGRE VIN 6% 1L	Alcool	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1501	SAVEURS 180G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1502	SUCRE VANILLE X10	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1503	LEVURE CHIMIQUE X6	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1504	SAVEURS RDF 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1505	LEGUMES BOCAL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1506	BTE 1/2 MDD	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1507	FARFALLE QS 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1508	PIPE RIGATE QS 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1509	COUSCOUS BTE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1510	FARFALLE QS 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1511	LINGUINE QS 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1512	PIPE RIGATE QS 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1187	PEPINETTES 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1514	FLAGEOLETS 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1515	1/2 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1516	MOUTON 1/2 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1517	SIROP ERABLE 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1518	FLACON 925G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1519	VERRE WHISKY 280G	Alcool	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1520	AU LAIT 300G (	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1521	NATURE ALLEGEE EN	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1522	ROBUSTA KG SAXO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1523	BIO 160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1534	FROMAGE 65G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1535	FROMAGE 80G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1536	AJOUTÉ 125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1537	LEGUMES 3X40G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1538	EXTRA FIN BTE 1/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1539	PYRAMIDES X20	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1540	LÉGUMES 1050G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1542	PALMIERS BIO 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1543	BOCAL 420G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1544	BASILIC 420G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1545	80G TC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1546	EQUATEUR 60% 80G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1547	BOCAL VERRE 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1185	SAUCE BOLOGNAISE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1548	BIO 140G (12)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
838	MC OLIV VERT DENOY 30/33 5/1 7 450 1	Autre	2.00	2.00	10.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1549	NATURE SACHET	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1550	LAIT BIO 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1551	CARAMEL 125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1552	GLACIER DUO 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1553	GRILLE BCL 720ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1554	HUITRES FINES 2,5KGS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1556	N4 2DZFQC 3000046136746 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1557	2 DZ N2 FDC FQC FQC 3000046136777 - - - Emballage	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1558	HUITRES FINES 2KGS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1559	JAMBON FE 1TR 130G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
840	EVIAN 1L PET 0 410 6	Autre	2.00	2.00	10.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
756	*CACAHUETE SALE 1 5KG MC 6 600 1	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
841	FERRERO COLLECTION T	Autre	32.00	32.00	0.00	0.000	t	35.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
842	NESTLE LA BOITE ROUGE	Autre	4.00	4.00	0.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
843	COMTE AOP 10M 1/32 MP.HARMONIE 0 880 13 740	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
844	CHEVRE BUCHE BIO*	Autre	1.00	1.00	0.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
845	CHEVRE BUCHE FONDANT	Autre	1.00	1.00	0.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1560	BULOTS CUITS X 0,180	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1561	POMMES SAUTEES 2.5	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
846	CAMEMBERT	Autre	2.00	2.00	0.00	0.000	t	10.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
807	JB CHOIX 20T	Autre	8.00	8.00	0.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
847	SCISSE SECHE COURBE	Autre	3.00	3.00	0.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
848	ROSETTE DE LYON TRANCHEE	Autre	5.00	5.00	0.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1562	FRITES STEAKHOUSE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1563	FRITES 10/10 2.5KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1564	6/6 2.5KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1565	KG EN CUISINE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1566	NORVEGE 10T 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1567	TRANCHETTE 500 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1575	CUIT SACHET 2,5KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1576	PRE CUIT SACHET 2,5	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1577	PRECUITES 1 KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1578	CHEVRE BUCHE 180G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1579	PARIS DES 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1580	ROTI 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1581	CONSERVATION 550G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1582	JACQUES 30% 8X 120	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1583	CUISSES SV X4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1584	KEBAB 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1585	GRILLER	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1586	TRANCHE 90G RDF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1587	AUVERGNE IGP / 300	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1588	AOP 250 G LS LAIT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1589	ROSETTE LYON 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1590	CRU RDF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1591	ENTIER VERRINE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1592	GACHE VENDEENNE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1593	600 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1594	240 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1595	6 300 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1596	ALIGOT 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1597	PASTEURISE CROUTE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1598	SUR PAILLE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1599	ROUGE X6 RDF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1600	BORDEAUX 180G	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1601	QUICHE LORRAINE X 2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1225	750G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1604	VEGETARIENNE BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1605	AVEC MORCEAUX 1L	Boissons	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1606	MGV 230G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1607	EXOTIQUES 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1626	900ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1627	130G FE PV	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1603	SURGELE 750G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1628	CARAMEL 100GX4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1629	PROFITEROLES 4X90G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1630	12T 450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1461	300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1631	NORVEGE FQC ASC 4T	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1635	CRUDITES 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1636	ECOSSE 4T 140 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1637	DESSERT POMMES X8	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1638	POIRE 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1639	ENTIER PV 8 X125	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1640	4X125GR	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1641	2,2KG PV COUPE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1642	BIO X10	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1643	PRECUITES X2 300 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1644	JAMBON EMMENTAL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1645	POMMES X2 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1646	280 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1647	HUILE AROMATES 500	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1648	HARENG FUME DOUX	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1649	ROQUETTE 125 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1650	FLORENTINE 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1651	BORDELAISE 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1652	BOLOGNAISE 300G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1653	EDULCORES 12X125 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1654	SALADE 130G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1655	2X110G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1656	2X110G FE FESTIF	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1657	EPINARD 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1658	SAUCE 2 MOUTARDES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1659	JAMBON 2X 150G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1660	2 X 125 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1661	STEAK HACHE 15% 6 X	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1673	OSEILLE 400 G MSC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1674	PARISIENNE 400 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1675	PROVENCALE 400	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1676	BOLET 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
93	CORNED  DOLO 340G	Autre	0.00	4.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1677	MG NATURE 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1163	BANANE 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1678	6X50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1679	LAIT ECREME	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1680	ANTILLAIS PGC 4X60G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1681	CHOCOLAT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1682	20% 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1683	1TR FE PV	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1684	2X80G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1685	MG 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1686	TIRAMISU 4X90G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1687	CHOIX 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1688	2X12 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1689	VRAC 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1690	PRECUIT SURG 330G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1691	STEAK HACHE 5% 6 X	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1692	STEAK HACHE 15% 8 X	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
94	COTES DU RHONE 2022 1L	Autre	0.00	13.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1662	VRAC 350 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1693	VRAC 500 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1694	VRAC 650 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1695	HACHE VRAC 5% 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1696	350G BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1697	X 125G FQC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1698	4 X 125G FQC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1699	BURGER BACON 180G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1700	4X125G BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1701	BOEUF 15%MG 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1702	2X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1703	3X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1704	BURGER 190G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1705	VEGGIE BURGER	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1706	SPECIAL FAJITAS 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1707	BOLOGNAISE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1708	EXTRA FIN SACHET	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1387	450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
854	QUEUE CREV CRU PD 26/30 MC 20 670 1	Autre	1.00	1.00	10.00	0.000	t	20.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1709	SEL BRETAGNE FILM	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1710	RATATOUILLE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1711	FINS SURGELES 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1717	EPAISSE 30% MG 50	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1718	SURGELEE 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1715	MG NATURE POT 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
855	VAP CABERNET VIN JEUNE 47CL 3 510 6	Alcool	1.00	1.00	20.00	0.000	t	21.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
856	MP 12 VERRES BIERE LILITH 58CL 14 640 1	Alcool	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1719	FROMAGE 20 X 50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1720	BIO X 6	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1721	125 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1722	POT VERRE 8X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1723	EMINCE 1ER CHOIX	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1724	2 X 230 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1725	WILLIAMS 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1726	BRETAGNE FILM 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1727	BRETAGNE FILM 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
859	FONREAUD MIL LISTRAC 75CL AOC I 0 750 11 100 1	Boissons	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1728	CHOCOLAT 4X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1633	12X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1729	PANACHES 16X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1730	RHUM RAISIN 1L	Alcool	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
860	CH RETOUT 14 HT MEDOC 75CL I 0 750 9 970 1	Autre	2.00	2.00	20.00	0.000	t	19.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
861	CLEMENT PICHON 14 HT MED 75CL I 0 750 12 990 1	Autre	4.00	4.00	20.00	0.000	t	51.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
862	N2 MAUCAILL 15 MOUL 75CL AOC I 0 750 13 092 6	Autre	1.00	1.00	20.00	0.000	t	78.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1731	SUP 2X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1732	2X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1733	NATURE 8X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1734	CARAMEL 4X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1735	FROMAGE 6 X 50G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1736	350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1737	ECOSSE 8T 300 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1738	FUME ECOSSE 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1739	CHEVRE BOITE 180 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1331	100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1740	900G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1741	POULET 900 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1742	PAELLA ROYALE IQF 1	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1743	VANILLE 125 G X 8	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1744	NATURE 0% 8X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1745	CHOCOLATS 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1746	COCKTAIL S/AT450 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1747	CHOUCROUTE GARNIE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1748	VIANDES CT 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1749	POISSONS CT 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1750	CHOIX VPF 2X75G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1751	RIZ CANTONAIS 900 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1752	ROUGES VANILLE 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1753	SUPERIEURE 180G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1754	PB 230G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1755	230 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1756	RONDELLES 1 KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1757	PEHD 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1758	GROS X6	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1759	MOYEN CALIBRE X12	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1760	SACHET 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1762	CAROTTE RAPEE 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1763	CELERI REMOULADE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1764	70%MG 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1765	NORVEGIENNE 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1632	14 TR 550G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1766	MIX 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1768	VANILLE 0% MG 100 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1196	HACHIS PARMENTIER	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1769	270G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1783	ASSORTIES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1784	LAIT CRU FQC 1/4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1785	(1X140G) CARR MAP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1786	NORVEGEFQC 3276555285194 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1787	HTR CANCALE FQC N4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1788	FQCFQC 3276556132077 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1789	HUITRE F CLAIRE N4	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1791	150G COUPE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1792	CHEVRE 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1793	MOZZARELLA 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1794	CHILI SIN CARNE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1795	CURRY 270G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1796	CORAIL 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
864	CH V PELLETIER DEMI-SEC 75CL M 0 750 12 840 1	Autre	5.00	5.00	20.00	0.000	t	64.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
865	PAST S/P BOUQUET CAL3 PC ES C1 ESPAGNE 10 990 1	Autre	1.00	1.00	10.00	0.000	t	10.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
866	GOB FH GRANITY 42CL 1 751 12	Autre	1.00	1.00	20.00	0.000	t	21.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
867	VERRE A PIED 50 VINA JULIETTE 2 730 6	Alcool	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1797	BLEU 40G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1798	AOP FQC 2X40G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1799	150GX2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1800	TOASTS - 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1801	TOASTS - 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
561	WH J.DANIEL'S 70CL 40D S 40 0 0 280 0 700 15 758 6	Autre	1.00	1.00	20.00	0.000	t	451.000	2025-10-30 12:23:12.672006	2025-10-30 13:37:59.565036
1802	TOASTS - 450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1803	JAMBON 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1804	EPINARDS 280G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
779	FLEUR CHAP MIL PST EM	Autre	3.00	3.00	20.00	0.000	t	28.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1805	FROMAGES 280G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
817	BUZET RSE MIL PRIEUR 75CLAOC T 0 750 2 780 6	Autre	1.00	1.00	20.00	0.000	t	34.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1806	HUITRE F CLAIRE N2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1807	HUITRE F CLAIRE N1	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1808	2 DZ N2 SPC FQC FQC 3276559686126 - - - - voir (1) - - - 1 6/1 2/20 22	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1809	N3 2DZFQC 3276559776254 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1810	FQCFQC 3276559776261 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1811	Huîtres Cancale FQC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1812	Marennes-Oléron FQC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1813	normandie 3DZ N°3	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1814	FQCFQC 3276559776315 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1815	HUITRE F CLAIRE N3	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1816	HTR CANCALE FQC N2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1817	BIO TR D+ 4X(1X140G)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1818	BRUNS DE PARIS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1790	(2X140G) SPNP MAP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1823	(4X140G) SPNP MAP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1824	(6X140G) MAP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1825	EMINCES ASC FQC SP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1822	(2X140G) MDC MAP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1826	EQUATEUR 40/60	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1827	BIO TR D+ 6X(2X125G)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1828	(1X140G) MDC MAP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1829	POELEE ASC FQC SP SA	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1830	0,500G FQC/MSC-C-	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1831	PARIS BRUN FQC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1832	BQ BULOT CUIT X 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1833	BQ BULOT CUIT X	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1780	HUITRE MARENNES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1834	OF FQC N3 5KGFQC 3523680422094 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
692	PERRIER BOITE SLIM 33CL 0 402 24	Autre	1.00	1.00	10.00	0.000	t	18.000	2025-10-30 13:29:29.50403	2025-10-30 13:37:59.565036
1835	FQC LABEL ROUGE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
95	Coca Cola Cherry Coke 24x 330ml	Autre	0.00	2.19	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
96	Coca Cola Light	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
97	Coca Cola Zero	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
99	Coca-Cola Cherry	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
100	Coca-Cola Cherry — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1836	CHIPS 400G MSC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1837	DOUX 200G MSC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1838	EPICES MSC 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1555	HTR MARENNES FQC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1839	HTRE N4 SP MARENNE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1840	FQC 2DZFQC 3523680435698 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1841	Filets d'anchois à	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
101	Coca-Cola Citron — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
102	Coca-Cola Goût Original Boîte 15CL x 8 MINI FRIGO PACK	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
103	Coca-Cola Goût Original Boîte 33CL	Alcool	0.00	0.76	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
98	Coca-Cola Can Multipack, 24 X 330 Ml	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
104	Coca-Cola Goût Original IVC 33CL	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
105	Coca-Cola Goût Original IVP 25CL	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
106	Coca-Cola Goût Original IVP 750ML	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
107	Coca-Cola Goût Original LVC 1L	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
108	Coca-Cola Goût Original PET 1,25L	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
109	Coca-Cola Goût Original PET 1,25L x 12	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
110	Coca-Cola Goût Original PET 1,25L x 6	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
111	Coca-Cola Goût Original PET 1L	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
112	Coca-Cola Goût Original PET 50CL	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1842	Salade de poulpe aux	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1843	1 6/1 2/20 22	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1844	BQ MOULES FARCIES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1845	FARCIES 52G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
870	PAYSOC CAB.SAUVMIL R. MAZET 75 K 0 750 1 442 6	Autre	2.00	2.00	20.00	0.000	t	17.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
113	Coca-Cola Goût Original — canette 33 cl	Alcool	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1846	FQC 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1847	AU ROMARIN 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1848	Fromage fouettéet	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
114	Coca-Cola Goût Original — canette 33 cl (DK)	Alcool	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1849	Jacques* Fumet de	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1850	Calamars et Poulpes	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
115	Coca-Cola Goût Original — canette 33 cl (UK)	Alcool	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1851	TOMATE ET THYM	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
116	Coca-Cola Light	Autre	0.00	1.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
872	VDF SAUVIGNON	Autre	1.00	1.00	20.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1852	PARIS BLANC FQC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
117	Coca-Cola Light Citron — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1853	PAVES ASC FQC AP SA	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
118	Coca-Cola Light Sans Caféine — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1854	SOUS AT 6X1KGFQC 3523680448650 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1855	1DZ HUITRE PLATE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1856	BZH N2 FQCFQC 3523680452244 - - - - voir (1) - - -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
119	Coca-Cola Light Taste	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1857	HPDZ0 FQC 3523680452251 - - - - voir (1) - - - 1 6/1 2/20 22	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1858	normandie 1DZ N°3	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
120	Coca-Cola Light — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1859	HTR CANCALE FQC N3	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1860	COUPE 2,2KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
121	Coca-Cola Zero Citron Vert — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1861	395630-ST 700 G MLE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1862	12 MACARONS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1863	AUX CAROTTES 3/2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
122	Coca-Cola Zero Sucre Y3000 — canette 33 cl (édition)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1864	CARREFOUR 2,5KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1865	6X100G CHAT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1867	CHOCOLAT 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1868	AFH 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
123	Coca-Cola Zero Sucre — canette 33 cl	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1869	POUR CHIEN	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1870	SURGELEE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1871	PORTION 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1872	FLEURETTES 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1873	CARREFOUR	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1874	FROMAGES 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1299	400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1875	DE BOIS ROYALE 440G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1541	420G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1876	LEGUMES CUITS 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1877	FOUR 6/6 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1878	POMME RISSOLEE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1879	FETA GRECQUE 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
124	Coca-Cola Zero Sucre — canette 33 cl (DK)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
125	Coca-Cola Zero Sucre — canette 33 cl (pack ref.)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
874	BUCHETTE 4G C3 KG BS 6 750 1	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
875	CEREALES LION 1 3KG 5 650 1	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1880	12 MOIS RAPE 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1881	18 MOIS 100G FR/ES	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1882	X16 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1883	AOP 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1884	FROMAGES 420G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1885	PROSCIUTTO 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1612	6X120ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
126	Compari bitter 1L	Autre	0.00	21.10	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1886	MASCARPONE 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
127	Crème Carbonara	Autre	0.00	3.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
876	CORDON BLEU POULET HALAL 1KG 4 690 1	Autre	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1887	750G CDM	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1888	NATURE 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
877	50 GOB KRAFT 66CL 6 890 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1889	POIVRE 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1890	ANANAS 900ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1891	ANANAS 6X120ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1892	ROUGES 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1893	BAC GLACE COCO 1L	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1168	500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1894	NOIX 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1895	CREME EPAISSE 30%	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1896	PORTIONS X8 240G (	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1897	BAC SORBET MANGUE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
128	DADDY SUCRE CANNE 750G	Autre	0.00	3.30	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
878	CHAMP MUMM 75CL CORDON RGE 3 0 750 20 990 6	Autre	1.00	1.00	20.00	0.000	t	125.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1773	CHOCOLAT 6X120ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1898	POMMES DE TERRE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1899	CAROTTES 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1900	POIVRON 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1901	ROSETTE 12TR / 150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1903	3X300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1904	LEGERE 15% MG 50	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1905	EPAISSE 30% POT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1906	COUPE PV PSA	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1907	CHEDDAR 135G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1908	TANDOORI 135G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1909	120G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1910	ASC 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1911	VAPEUR 750G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1912	CHAMPETRE 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1913	TRANCHES 100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1914	TRANCHE RDF / 100G -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1915	SAUCISSON / 100G -	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1916	LEGUMES BIO 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1917	DECONGELEE BIO	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1918	385G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1919	280G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1920	PIZZA PF THON 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1634	4X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1921	SAUMONS 4X100G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1922	DISCOUNT 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1923	BELGE X8 360G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1924	MAXI 200 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1925	420G IGP	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1926	GARNIR BIO X4 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1927	X10 SIMPLE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1928	JUMBO TIGREES ASC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1422	150G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1929	MORUE 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1930	X20 SIMPLE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1931	X30 SIMPLE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1932	BCL 370ML	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1933	PANES MSC 500G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1866	SACHET 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1934	POULET 900G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1935	PATE PIZZA BIO 260G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1936	BIO 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1761	BIO SURGELE 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1767	SURGELE 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1937	HALAL / 120G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1938	BOURGUIGNON 330G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1939	CHAT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1902	BLANC	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1224	250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
880	90 BTE KEBAB PPE 18 900 1	Autre	1.00	1.00	20.00	0.000	t	18.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
881	50 MASQUE JETABLE NOIR 3 PLIS 5 000 1	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1940	TRES GROS 2X12	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1941	FUME HALAL / 160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1942	HALAL / 160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1943	HALAL 4T / 160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1944	175G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1945	PAELLA 350G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1946	COUSCOUS 350 G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1947	AU JAMBON 300G FE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1948	ENTIER BOCAL / 125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1949	ANCIENNE PGC X2	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1950	SUPERIEURE 4X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1951	CRU PRESSEE NON	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1952	COCOTTE 400G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1513	BOLOGNAISE 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1953	HALAL 160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1602	PASTEURISE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1954	CRU PRESSE NON	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1955	HALAL 4T 160G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1956	BOL 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1957	KG LAIT PASTEURISE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1958	ALPHABET - 600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1959	MELANGE 180G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
882	RED BULL BLUE BOITE 25CL 1 143 24	Autre	1.00	1.00	10.00	0.000	t	27.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
883	COCA COLA BTE SLIM 33CLX30 OS 0 414 30	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1960	AIL ET FINE HERBE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1961	FRAMBOISE 8X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1962	POIRE 8X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1963	RM BCL 37CL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1964	PROFITEROLES 90G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1965	4X117G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1966	PASSION 12X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1967	FRBSE BIO 8X125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1968	X10 350G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1969	X6 210G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
618	SOLIJAVEL+ 4EN1 5L 10 640 1	Autre	1.00	1.00	20.00	0.000	t	60.000	2025-10-30 12:32:17.747406	2025-10-30 13:37:59.565036
1970	SURGELE SACHET 1KG	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1971	CREME BRULEE UHT	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1972	/ 2X75G - LS	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1973	FROMAGE 450G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1399	600G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1974	BLANC 4 TR 300 G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1975	PUREE 300G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1976	EMMENTAL	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1977	NORVEGE 180G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1978	PARISIENNE 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1979	FROMAGES 250G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1980	HYGIÈNE	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1981	BEURRE 200G (	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1982	EMMENTAL 145G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1983	BEURRE 125G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1984	BACON OEUF 200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1985	CRUDITES 145G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
1149	200G	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 14:16:19.499784	2025-10-30 14:16:24.788817
411	CTE BLAYE HT LA POINTE RG 75CL T 0 750 4 250 6	Autre	1.00	1.00	20.00	0.000	t	71.000	2025-10-30 12:10:16.733895	2025-10-30 13:37:59.565036
884	PUY VALLON MIL	Autre	3.00	3.00	20.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
129	DIDON SUCRE MORC.	Autre	0.00	3.50	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
887	COCKTAIL SNACK 1KG METRO CHEF 5 790 1	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
888	RAID AERO FOUR ARAI CAF	Autre	4.00	4.00	2.10	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
890	AROME VANILLE VANILUXE	Autre	20.00	20.00	5.50	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
891	EAU FLEUR ORANG FL.1L SEBALCE 7 740 1	Boissons	1.00	1.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
892	TOPPING FRAISE 1 LITRE 6 790 1	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
893	AROME FLEURS D'ORANGERS 1L PAT 2 530 1	Autre	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
894	AROME VANILLE 1L.SEBALC 11 300 1	Autre	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
895	TOPPING CARAMEL 1L 6 790 1	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
896	AROME VANILLE 1 L 4 680 1	Autre	2.00	2.00	10.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
897	PAIN HOT DOG BRIOCHE X6 LFD 2 410 1	Autre	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
898	BRIOCH BURGER 6X77G LFD 3 190 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
428	BRIOCH BAGEL 4X75G LFD 2 470 1	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 12:10:16.733895	2025-10-30 13:37:59.565036
347	10 PAINS PEPITES LC	Autre	3.00	3.00	0.00	0.000	t	35.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
483	W KNOCKANDO SLOW 18A 43D 70CL S 43 0 0 301 0 700 35 000 1	Autre	1.00	1.00	20.00	0.000	t	3246.000	2025-10-30 12:15:47.724561	2025-10-30 13:37:59.565036
583	MEDOC 75CL MIL CH ARCINS CB T 0 750 8 325 6	Autre	2.00	2.00	20.00	0.000	t	1139.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
130	Dentifrice Haleine Pure 75ml	Autre	0.00	3.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
899	ORANGINA 50CL PET 0 762 12	Alcool	1.00	1.00	10.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
901	*SEMOUL PATES FRAICHE SAC 5K 7 870 1	Autre	1.00	1.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
902	50 GOB KRAFT 18CL 3 090 1	Autre	3.00	3.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
758	ARGUILLE MIL BDX BL MOEL 75C T 0 750 3 108 6	Autre	1.00	1.00	20.00	0.000	t	108.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
131	ERISTOFF 70CL	Autre	0.00	19.50	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
748	CACAHUETES SALEES 2 5KG FBON 11 550 1	Autre	1.00	1.00	10.00	0.000	t	21.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
724	30 BTE NOIR+COUV TRANS	Autre	3.00	3.00	20.00	0.000	t	21.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
823	MP SEAU A CHAMPAGNE 18CM ANSES 15 410 1	Alcool	2.00	2.00	20.00	0.000	t	53.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
132	EXETER CHICKEN 340G	Autre	0.00	2.99	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
904	MP RAFRAICHISSEUR A VIN 14 950 1	Alcool	1.00	1.00	20.00	0.000	t	28.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
133	EXETER CORNED BEEF 198G	Autre	0.00	3.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
908	LOT 2 DOSEURS A BILLE 5CL 11 160 1	Autre	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
134	EXETER CORNED BEEF 340G	Autre	0.00	5.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
910	MEDOC 75CL MIL CH ARCINS CB I 0 750 10 392 6	Autre	1.00	1.00	20.00	0.000	t	62.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
911	MOUTON CAD RGE MIL 75CL I 0 750 7 790 1	Autre	6.00	6.00	20.00	0.000	t	46.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
586	LAMOTH.JOUB MIL CT.BG	Autre	3.00	3.00	20.00	0.000	t	49.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
678	MC HUILE COLZA 25L 2 482 25	Autre	1.00	1.00	10.00	0.000	t	284.000	2025-10-30 13:28:44.005424	2025-10-30 13:37:59.565036
913	80 GOB CART DB PAROI 10CL 4 710 1	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
914	LA X JAV TRAD 1.5L 0 710 1	Autre	2.00	2.00	20.00	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
915	LU BARQUETTE CHOCOLAT	Autre	1.00	1.00	0.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
916	OREO CLASSIQUE POCKET	Autre	1.00	1.00	0.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
917	GAL RIZ COMPLET	Autre	1.00	1.00	0.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
135	FARINE DE BLE 1KG	Autre	0.00	1.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
918	PULCO CITRON VERT 70CL VP 2 190 1	Autre	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
136	FARINE TYPE 55	Autre	0.00	1.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
693	ARO HUILE TOURNESOL 10L 32 300 1	Autre	2.00	2.00	10.00	0.000	t	190.000	2025-10-30 13:29:29.50403	2025-10-30 13:37:59.565036
495	500 SETS XTRA BLC MAT 30X40 10 080 1	Autre	1.00	1.00	20.00	0.000	t	232.000	2025-10-30 12:15:47.724561	2025-10-30 13:37:59.565036
920	50 SAC KRAFT DECOUPE 26X14X29 6 200 1	Autre	2.00	2.00	20.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
921	MPRO LV MAIN 10L 1 440 10	Autre	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
497	MEDOC 75CL MIL CH ARCINS CB T 0 750 8 330 6	Autre	1.00	1.00	20.00	0.000	t	643.000	2025-10-30 12:16:40.566579	2025-10-30 13:37:59.565036
782	CHAMPAGNE R.DE RUINART 75 CL M 0 750 46 700 1	Alcool	3.00	3.00	20.00	0.000	t	373.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
922	SIROP GILBERT CASSIS 1L 3 600 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
750	COCACOLA BOITE SLIM 33CL 0 504 24	Autre	1.00	1.00	10.00	0.000	t	48.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
663	KERNEL HUILE TOURNESOL 5L 12 890 1	Autre	2.00	2.00	10.00	0.000	t	76.000	2025-10-30 13:27:52.525104	2025-10-30 13:37:59.565036
419	MC MAYO HTE FERMETE 4 7KG 12 850 1	Autre	1.00	1.00	10.00	0.000	t	22.000	2025-10-30 12:10:16.733895	2025-10-30 13:37:59.565036
889	CH MOET&CHANDON IMPERIAL 75CL 3 0 750 27 070 1	Autre	2.00	2.00	20.00	0.000	t	108.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
137	Fanta Citron Zéro Sucre — canette 33 cl (UK)	Autre	0.00	0.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
924	MP 6 SALADIERS EMPILABLE 17CM 8 330 1	Autre	2.00	2.00	20.00	0.000	t	16.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
925	ST EMILION GC CLOS CURE75CL MI T 0 750 12 150 1	Autre	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
138	Fanta Citron — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
139	Fanta Citron — canette 33 cl (DK)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
140	Fanta Citron — canette 33 cl (ES)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
141	Fanta Citron — canette 33 cl (slim)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
926	CH L PERRIER LA CUVEE 75CL M 0 750 29 340 6	Autre	1.00	1.00	20.00	0.000	t	176.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
142	Fanta Exotic — canette 33 cl (DK)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
143	Fanta Exotic — canette 33 cl (UK)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
144	Fanta Fraise & Kiwi — canette 33 cl (DK)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
145	Fanta Fraise & Kiwi — canette 33 cl (UK)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
146	Fanta Lemon & Elderflower (Shokata) — canette 33 cl (UK)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
147	Fanta Mangue & Fruit du Dragon — canette 33 cl (UK)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
148	Fanta Orange — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
149	Fanta Orange — canette 33 cl (ES)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
150	Fanta Orange — canette 33 cl (UK)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
151	Fanta Sandía (Pastèque) — canette 33 cl (ES)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
152	Fanta Shokata — canette 33 cl (ES)	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
153	Fish Sauce	Autre	0.00	3.40	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
445	PERRIER 1L PET 0 637 6	Autre	1.00	1.00	10.00	0.000	t	43.000	2025-10-30 12:10:43.935296	2025-10-30 13:37:59.565036
927	POUBELLE PEDALE ESSENTIALS 40L 15 990 1	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
928	SIROP GILBERT CITRON RIOR 1L 2 820 1	Autre	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
931	RHUM STJAMES IMPERIAL 50D 1L E 50 0 0 500 1 000 14 260 1	Alcool	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
660	MOUTON CA RGE MIL BDX 75 CBX T 0 750 9 990 6	Autre	1.00	1.00	20.00	0.000	t	162.000	2025-10-30 13:27:52.525104	2025-10-30 13:37:59.565036
932	MGX AOC 75C MIL PAVIL SMARTIN I 0 750 9 710 6	Autre	2.00	2.00	20.00	0.000	t	116.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
933	PAVEIL DE LUZE 16 MGX 75CL I 0 750 16 790 6	Autre	2.00	2.00	20.00	0.000	t	201.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
934	HT MED GISCOURS 15 HT MED 75CL I 0 750 13 590 1	Autre	18.00	18.00	20.00	0.000	t	244.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
590	IGP MED BLC C. DAUPHINS 25CL T 0 250 1 250 12	Autre	1.00	1.00	20.00	0.000	t	147.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
935	CH MOET&CHANDON IMPERIAL	Autre	1.00	1.00	20.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
591	PELFORTH BT BRUN 6.5D 50CL B 6 5 0 033 0 500 1 451 12	Autre	1.00	1.00	20.00	0.000	t	165.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
571	CH V. CLICQUOT BRUT 75CL M 0 750 35 990 6	Autre	1.00	1.00	20.00	0.000	t	2804.000	2025-10-30 12:23:12.672006	2025-10-30 13:37:59.565036
721	FICELLE DE L'AVEYRON 90G X 5 5 790 1	Autre	1.00	1.00	10.00	0.000	t	15.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
154	GHANA FRESH 400G	Autre	0.00	3.99	20.00	0.000	t	17.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
155	GIBSON'S GIN 70CL	Alcool	0.00	17.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
498	GUINNESS 7.5D 33CL VP B 7 5 0 025 0 330 1 236 24	Autre	2.00	2.00	20.00	0.000	t	1822.000	2025-10-30 12:16:40.566579	2025-10-30 13:37:59.565036
488	SIROP GILBERT GRENAD. NATUR 1L 1 950 1	Autre	2.00	2.00	10.00	0.000	t	132.000	2025-10-30 12:15:47.724561	2025-10-30 13:37:59.565036
607	SCHWEPPES IT SLIM 33CL 0 556 24	Autre	1.00	1.00	10.00	0.000	t	91.000	2025-10-30 12:30:02.473798	2025-10-30 13:37:59.565036
593	FANTA ORANGE PET 50CL 0 813 12	Autre	3.00	3.00	10.00	0.000	t	83.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
594	ORANGINA 50CL PET 0 793 12	Alcool	3.00	3.00	10.00	0.000	t	185.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
494	MPRO PH JUMBO 2P RECYC	Autre	3.00	3.00	2.10	0.000	t	65.000	2025-10-30 12:15:47.724561	2025-10-30 13:37:59.565036
818	BAILEYS IRISH CREME 17D 70CL S 17 0 0 119 0 700 9 150 6	Autre	1.00	1.00	20.00	0.000	t	107.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
672	HEINEKEN 5D 65CL VP B 5 0 0 033 0 650 1 391 12	Autre	12.00	12.00	20.00	0.000	t	568.000	2025-10-30 13:28:28.855834	2025-10-30 13:37:59.565036
937	PAIN HOT DOG X	Autre	6.00	6.00	0.00	0.000	t	33.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
804	30BTE NOIR COUV.TRANS	Autre	5.00	5.00	20.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
938	ACIDE CHLORHYD 1L 1 280 1	Autre	1.00	1.00	20.00	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
156	GRANOLA 200G	Autre	0.00	2.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
939	MESURE A ALCOOLINOX 2 ET 4CL 8 810 1	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
157	GRANT'S WHISKY 70CL	Alcool	0.00	26.90	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
940	POIREAU BOTTE 1KG 10 FR CAT1 FRANCE 1 490 1	Boissons	1.00	1.00	10.00	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
942	ICEBERG LANIERE METRO CHEF 1KG 2 990 1	Autre	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
158	GUILLOTINE VODKA 70CL	Alcool	0.00	49.99	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
510	ST EM 75CL MIL LAJARDE MT AC T 0 750 7 825 6	Autre	1.00	1.00	20.00	0.000	t	1832.000	2025-10-30 12:18:34.198825	2025-10-30 13:37:59.565036
784	DESPERAD 5.9D 33CLX24 VP // B 5 9 0 019 0 330 0 948 24	Autre	2.00	2.00	20.00	0.000	t	259.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
701	COCA-COLA PET 50CLX24 PROMO 0 783 24	Autre	2.00	2.00	10.00	0.000	t	158.000	2025-10-30 13:31:16.814255	2025-10-30 13:37:59.565036
850	NESTLE PUR LIFE 50CL PET 0 195 24	Autre	1.00	1.00	10.00	0.000	t	17.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
909	MAYO CLASSIQUE SQ	Autre	0.40	0.40	0.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
159	HAPPI LIFE GINGER DRINK 0.5L	Alcool	0.00	3.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
160	HAPPY DAYS 180G	Autre	0.00	1.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
582	RHUM DILLON BLC 55D 1L G 55 0 0 550 1 000 11 970 1	Alcool	1.00	1.00	20.00	0.000	t	113.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
622	RICARD 45D 1.5L S 45 0 0 675 1 500 21 990 1	Autre	1.00	1.00	20.00	0.000	t	326.000	2025-10-30 13:08:21.170149	2025-10-30 13:37:59.565036
485	MOUTON CAD RGE MIL 75CL T 0 750 7 990 6	Autre	1.00	1.00	20.00	0.000	t	897.000	2025-10-30 12:15:47.724561	2025-10-30 13:37:59.565036
873	*SEMOUL BLE DUR EXTRA FINE 5K 5 950 1	Autre	1.00	1.00	10.00	0.000	t	10.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
943	FS TOP DOWN	Autre	4.00	4.00	2.10	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
900	CACAHUETES GRILLEES SALEES 1KG 2 830 1	Autre	3.00	3.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
944	TRANCHETTE JB CUIT 2 KG 10 750 1	Autre	2.00	2.00	10.00	0.000	t	21.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
945	MPRO 50BARQ+50 COUV ALU	Autre	15.00	15.00	20.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
923	COGNAC COURCEL *** 70CL 40D D 40 0 0 280 0 700 15 900 1	Alcool	1.00	1.00	20.00	0.000	t	30.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
470	WHISKY CARDHU 12A 40D 70CL S 40 0 0 280 0 700 32 270 1	Autre	2.00	2.00	20.00	0.000	t	1121.000	2025-10-30 12:11:39.640331	2025-10-30 13:37:59.565036
746	WHISKY CARDHU 15A 40D 70CL S 40 0 0 280 0 700 33 440 1	Alcool	6.00	6.00	20.00	0.000	t	1377.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
871	IGP MED RSE C.DAUPHINS 25CL I 0 250 1 190 12	Autre	2.00	2.00	20.00	0.000	t	100.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
747	MC OLIV. VERTES ENT 34/36 5/1 9 250 1	Autre	1.00	1.00	10.00	0.000	t	35.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
946	AROME FAMILIAL	Autre	8.00	8.00	2.10	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
947	MAGGI AROME	Autre	2.00	2.00	0.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
948	RAFFAELLO T	Autre	18.00	18.00	0.00	0.000	t	18.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
667	FUET GEANT	Autre	3.00	3.00	0.00	0.000	t	6.000	2025-10-30 13:27:52.525104	2025-10-30 13:37:59.565036
315	WH GLENFIDDICH 15A 40D 70CL S 40 0 0 280 0 700 44 230 1	Autre	11.00	11.00	20.00	0.000	t	18375.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
950	ACTO CAFARD GEL SERINGUE 25G 11 540 1	Autre	2.00	2.00	20.00	0.000	t	23.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
161	HAUT CHAMBOUSTIN MERLOT 2021	Autre	0.00	11.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
952	RHUM 3RIVIERE 50D 1L E 50 0 0 500 1 000 12 750 1	Alcool	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
863	PULCO CITRON 70CL 2 000 1	Autre	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
954	SIROP GILBERT GINGEMBRE 70CL 2 230 1	Alcool	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
955	SIROP GILBERT VANILLE 70CL 3 090 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
930	SIROP GILBERT FRAISE 1L 3 050 1	Autre	1.00	1.00	10.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
837	50 SAC POI KRAFT 32X22X24 6 980 1	Autre	1.00	1.00	20.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
792	WH J.DANIEL'S 70CL 40D S 40 0 0 280 0 700 13 450 6	Autre	1.00	1.00	20.00	0.000	t	341.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
370	IGP MED RSE C.DAUPHINS 25CL T 0 250 1 350 12	Autre	1.00	1.00	20.00	0.000	t	172.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
610	VINAIG. ALCOOL BLC 1LPET 0 428 12	Alcool	1.00	1.00	10.00	0.000	t	30.000	2025-10-30 12:30:02.473798	2025-10-30 13:37:59.565036
162	HENNESSY 70CL	Autre	0.00	58.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
962	Q.CREV DECO CUIT COCKT 31/40MC 15 290 1	Autre	1.00	1.00	10.00	0.000	t	15.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
963	QUEUE BF 1KG S/V UE 1 392 8 990	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
964	QUEUE BF 1KG S/V UE 1 452 8 990	Autre	1.00	1.00	10.00	0.000	t	13.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
965	BAVETTE ALOYAU PAD S/V UE 2 765 8 990	Autre	1.00	1.00	10.00	0.000	t	24.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
941	OIG CHARC 7/	Autre	10.00	10.00	20.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
966	MPRO NETT MS BACT 5L PIN 8 290 1	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
759	GILBERT NECTAR MANGUE TO 25CL 0 557 12	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
772	GILBERT ABC PAMP ROSE TO 25CL 0 530 12	Boissons	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
788	GILBERT PJ ANANAS COSTA R 25CL 0 562 12	Autre	1.00	1.00	10.00	0.000	t	13.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
717	SIROP GILBERT POMME VERTE 1L 3 170 1	Autre	1.00	1.00	10.00	0.000	t	9.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
851	MAUREL HLE TOURNESOL 5L 1 900 5	Autre	1.00	1.00	10.00	0.000	t	77.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
972	THE VERT MENTHE 50SC TWININGS 4 830 1	Autre	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
973	TORTILLA 25CM X	Autre	12.00	12.00	0.00	0.000	t	74.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
974	HACHE 20%MG 10*	Autre	1.00	1.00	0.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
975	MERGUEZ HAL SPE COUSCOUS 2.5KG 2 490 8 490	Autre	1.00	1.00	10.00	0.000	t	21.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
976	CITR VERT FILET 1KG C1 BRE BRESIL 3 490 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
163	HUILE DE PALME MAMA FUTA	Autre	0.00	1.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
977	DECAP FOUR EXPRESS	Autre	5.00	5.00	2.10	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
978	DBECH NETYANT FRITEUSE 1KG 8 230 1	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
979	MPRO GEL WC JAVEL	Autre	7.00	7.00	2.10	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
980	MPRO LAVE VITRES 5L 4 590 1	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
981	PANTALON POLYVAT PC BLANC T42 31 480 1	Autre	2.00	2.00	20.00	0.000	t	62.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
982	SABOT POLSEC T 42 BRIDE SECUR. 41 820 1	Autre	1.00	1.00	20.00	0.000	t	41.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
983	MP LOT DE 6 PLANCHES HACCP 14 320 1	Autre	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
984	10 CHEM CARTE 3RAB A4 ASS 7 770 1	Autre	1.00	1.00	20.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
824	10 BLOC VEND 60X	Autre	1.00	1.00	5.50	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
985	300 ETIQ TRACABILITE ALIM 98X4 6 960 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
303	PAST 8/12K BOX35 MA MAROC 6 490 1	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 12:05:49.521322	2025-10-30 13:37:59.565036
508	SIGMA 20 RL 57X57X12 THER SBPA 1 201 20	Autre	1.00	1.00	20.00	0.000	t	44.000	2025-10-30 12:17:42.01398	2025-10-30 13:37:59.565036
164	Ice Tea - Saveur Framboise	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
165	Ice Tea Saveurs Pastèque Et Menthe	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
166	JACK DANIEL 200ML	Autre	0.00	11.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
987	BASSE COTE 4F VBF S/P 3 850 8 990	Autre	1.00	1.00	10.00	0.000	t	34.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
311	PAST 8/12K BOX35 MA MAROC 8 990 1	Autre	1.00	1.00	10.00	0.000	t	14.000	2025-10-30 12:06:22.270134	2025-10-30 13:37:59.565036
167	JACK DANIEL'S 70CL	Autre	0.00	27.90	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
168	JACK DANIEL'S APPLE 70CL	Autre	0.00	29.99	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
169	JACK DANIEL'S FIRE 35CL	Autre	0.00	17.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
170	JACK DANIEL'S HONEY 70CL	Autre	0.00	28.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
171	JACK MACKEREL 425G	Autre	0.00	4.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
172	JB WHISKY 35CL	Alcool	0.00	13.90	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
173	JB WHISKY 70CL	Alcool	0.00	18.90	20.00	0.000	t	4.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
174	JC PREMIUM Pollen Filter B40017PR Pollen Filter 240 204 35 VAUXHALL: Astra Mk6, Insignia Mk1, ZAFIRA Mk3, OPEL: Astra J Hatchback	Autre	0.00	3.98	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
175	JEAN DEGAVES 2013 75CL	Autre	0.00	6.99	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
849	WH JWALKER BLACK 12A 40D 70CL D 40 0 0 280 0 700 16 020 6	Autre	2.00	2.00	20.00	0.000	t	729.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
176	JEAN DELLAC CINSAULT	Autre	0.00	6.90	20.00	0.000	t	6.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
177	JP CHENET C-S 75CL	Autre	0.00	7.50	20.00	0.000	t	5.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
988	MAIS POP CORN 5KG LEGUMOR 11 920 1	Autre	1.00	1.00	10.00	0.000	t	11.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
989	OIG ROUGE 6/8 5KG C1 FR FRANCE 3 950 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
711	GIN GIBSONS	Alcool	3.00	3.00	20.00	0.000	t	56.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
990	NUTELLA 1 KG 5 300 1	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
839	CHAMP M&C ICE IMP 75CL 3 0 750 34 490 1	Autre	4.00	4.00	20.00	0.000	t	169.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
991	CHAMP V.CLICQUOT RICH 75CL 3 0 750 34 990 1	Autre	2.00	2.00	20.00	0.000	t	69.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
992	ARO POIVRE NOIR ML SAC 1KG 12 490 1	Autre	1.00	1.00	10.00	0.000	t	12.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
993	50 BTE BURGER KRAFT GRD 6 760 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
995	PORTO DON PABLO RGE 19D 75CL V 0 750 4 620 1	Alcool	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
377	RIOBA NECTAR ABRICOT TO 25CL 0 643 24	Autre	1.00	1.00	10.00	0.000	t	100.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
997	THE VERT MENTHE 25SC FRAICH 2 040 1	Autre	1.00	1.00	10.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
998	CITRON GINGER MIEL 20SC PUKKA 3 690 1	Alcool	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
178	L OCEADE MERLOT 75CL	Autre	0.00	7.90	20.00	0.000	t	5.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
999	CITR VERT FILET 1KG C1 BRE BRESIL 4 490 1	Autre	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
179	LA BRIOCHE TR 500G	Autre	0.00	3.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1000	OIG DOUX 5/7 1KG C1 ESP 5 ESPAGNE 1 990 1	Autre	1.00	1.00	10.00	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
180	LA FLEUR MONDESIR 2024	Autre	0.00	7.90	20.00	0.000	t	6.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1001	AIL BLANC 3 TETES 6/8 C1 FR 20 FRANCE 1 290 1	Autre	1.00	1.00	10.00	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1002	RADIS NOIR PC FR 10 FRANCE 1 290 1	Autre	1.00	1.00	10.00	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1003	SAVONA GEL HYDRO	Hygiene	5.00	5.00	2.10	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1004	100 GOB PAPIER SOUPLE	Autre	1.00	1.00	2.10	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
706	LEFFE BLONDE 6.6D 33CL X20 B 6 6 0 022 0 330 0 720 20	Autre	2.00	2.00	20.00	0.000	t	369.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
1005	CARAIBOS PUR JUS ORANGE 1L 1 542 6	Boissons	1.00	1.00	10.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
181	LA ROSINA 400G	Autre	0.00	2.20	20.00	0.000	t	10.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
684	ARO TOMATE CONCASSEE 4/4 1 313 6	Autre	1.00	1.00	10.00	0.000	t	11.000	2025-10-30 13:28:58.358722	2025-10-30 13:37:59.565036
685	SEL FIN IODE BV	Autre	5.00	5.00	0.00	0.000	t	0.000	2025-10-30 13:28:58.358722	2025-10-30 13:37:59.565036
1006	SAUCE SAMOURAI	Autre	9.00	9.00	2.10	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1007	AMORA KETCHUP TOP DOWN	Autre	5.00	5.00	0.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
798	MC MAYONNAISE TUBE	Autre	8.00	8.00	0.00	0.000	t	25.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1008	MPRO CREME LAVANTE BACT 5L 11 440 1	Autre	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1009	P.TOIL JUMBO 2P	Autre	3.00	3.00	2.10	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
182	LABEL 5 35CL	Autre	0.00	1.00	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1010	RAMASSE-COUVERTS 23X	Autre	3.00	3.00	0.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1011	LOT 24 COUTEAUX A STEAK ARO 0 475 24	Boissons	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
183	LABEL 5 70CL	Autre	0.00	19.90	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
184	LAFAURIE M. CASTILLON 2016	Autre	0.00	10.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1013	CH.COSTIS MIL BDX AOC	Autre	3.00	3.00	20.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1014	ARO CHP. PIED MORC.1/2 0 681 12	Autre	1.00	1.00	10.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1015	FRITE BISTRO STYLE 2.5KG MC CAIN 5 380 1	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1012	50 SAC PAPIER KRAFT 22X10X28 4 610 1	Autre	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
656	MP 6 ASSIETTES PATES 24CM 21 620 1	Autre	1.00	1.00	20.00	0.000	t	123.000	2025-10-30 13:10:43.512798	2025-10-30 13:37:59.565036
1016	KENW-BLENDER BLM	Autre	6.00	6.00	5.50	0.000	t	1.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
185	LE PETIT BEURRE 145	Autre	0.00	1.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
996	LEFFE BLDE 6 6D 24X25CL L 6 6 0 017 0 250 0 520 24	Autre	1.00	1.00	20.00	0.000	t	24.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
970	CACAHUETE GAS SEAU 3KG MC 14 500 1	Boissons	1.00	1.00	10.00	0.000	t	22.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1017	EVOLU GEL HYDRO	Autre	5.00	5.00	2.10	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
402	WHISKY CHIVAS 18ANS 40D 70CL S 40 0 0 280 0 700 42 530 1	Alcool	1.00	1.00	20.00	0.000	t	3121.000	2025-10-30 12:10:16.733895	2025-10-30 13:37:59.565036
705	CH V. CLICQUOT BRUT 75CL M 0 750 31 680 1	Autre	4.00	4.00	20.00	0.000	t	208.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
903	FANTA ORANGE 33CL VP 0 576 12	Autre	1.00	1.00	10.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
477	MPRO BOBINE 2P	Autre	4.00	4.00	20.00	0.000	t	55.000	2025-10-30 12:11:39.640331	2025-10-30 13:37:59.565036
857	WH JWLKER BLACK+6VE 40D 70CLX6 D 40 0 0 280 0 700 16 965 6	Autre	1.00	1.00	20.00	0.000	t	408.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
635	CAMPARI	Autre	1.00	1.00	20.00	0.000	t	0.000	2025-10-30 13:08:54.596243	2025-10-30 13:37:59.565036
1018	PICON BIERE 18D 1L D 18 0 0 180 1 000 7 420 1	Alcool	1.00	1.00	20.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1019	ACIDE CHLORHYDRIQUE 5L 6 060 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
718	MPRO 30 SAC POUB	Autre	1.00	1.00	5.50	0.000	t	4.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
723	BEL MURAIL MILBDX	Autre	3.00	3.00	20.00	0.000	t	77.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
816	CAB ANJOU RSE MIL M.LAUR 75C T 0 750 3 230 6	Autre	5.00	5.00	20.00	0.000	t	226.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
959	PELFORTH BRUN 6.5D 65CL L 6 5 0 042 0 650 2 118 12	Autre	2.00	2.00	20.00	0.000	t	225.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
886	CAPRISUN TROPICAL 20CLX10 0 280 10	Autre	2.00	2.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1020	MAAZA GOYAVE 33CL PET 0 900 8	Autre	1.00	1.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1021	ROCH HARICOTS RGES 4/4 1 130 6	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1022	ROCH MAIS 1/2 0 422 12	Autre	1.00	1.00	10.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1023	HUILE OLIVE VE TUNISIE 75CL 6 940 1	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
776	*SEMOUL BLE DUR MOYEN 5KG REN 7 200 1	Autre	1.00	1.00	10.00	0.000	t	45.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1024	GRO SEL MER SAC 5KG BALEINE 3 980 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
799	MC SAUCE SAMOURAI	Autre	8.00	8.00	0.00	0.000	t	20.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
186	LOTUS RIZ LONG10KG	Autre	0.00	27.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
187	LOUIS MARTIN - TOMATES ENTIERES 765G	Autre	0.00	1.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
787	80 GOB CAR BOISS CHAUDE 10CL 2 300 1	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
188	La fleur de mondésir sémillon	Autre	0.00	9.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
189	Lipt Peche Zero Bib 10l (72x1)	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
190	Lipton Ice Tea Pastèque Menthe	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
191	Lipton Ice Tea Saveur Citron Citron Vert	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
192	Lipton Ice Tea Saveur Citron Citron Vert 1,25 L	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
193	Lipton Ice Tea Saveur Pêche	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
194	Lipton Ice Tea Saveur Pêche 1,25 L	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
195	Lipton Ice Tea Saveur Pêche 1,75 L	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
196	Lipton Ice Tea Saveur Pêche 25 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
197	Lipton Ice Tea Saveur Pêche Sans Sucres	Autre	0.00	1.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
198	Lipton Liptonic L'original Pétillant 1,5 L	Alcool	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
199	Lipton Thé Vert Glacé Saveur Citron Vert Menthe 33 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
200	Liptonic	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1025	MPRO NETT MU AGRUME BACT 5L 7 990 1	Autre	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
361	ARO LIQ VAISS MAIN CIT 20L 24 990 1	Autre	1.00	1.00	20.00	0.000	t	774.000	2025-10-30 12:07:45.054577	2025-10-30 13:37:59.565036
439	WH JACK DANIEL'S 40D 70CL S 40 0 0 280 0 700 16 180 1	Autre	1.00	1.00	20.00	0.000	t	329.000	2025-10-30 12:10:43.935296	2025-10-30 13:37:59.565036
994	WHISKY JB 40D 70CL D 40 0 0 280 0 700 11 020 1	Alcool	1.00	1.00	20.00	0.000	t	22.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
365	VODKA POLIAKOV	Alcool	3.00	3.00	20.00	0.000	t	133.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
466	HEINEKEN PACK 5D 20X25CL VP B 5 0 0 013 0 250 0 589 20	Autre	1.00	1.00	20.00	0.000	t	58.000	2025-10-30 12:11:25.7753	2025-10-30 13:37:59.565036
919	100 SERV 2PLI 39X39 3 270 1	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1027	50 GOB CHAUD KRAFT 12CL 2 430 1	Autre	1.00	1.00	20.00	0.000	t	2.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1028	30 GOB CARTON CHAUD ENJOY 25CL 4 580 1	Autre	1.00	1.00	20.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
201	MACEDOINE 265G	Autre	0.00	1.50	20.00	0.000	t	10.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
202	MAGGI AROME 960G	Autre	0.00	5.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
596	PERRIER 6*50CL PET 0 484 24	Autre	1.00	1.00	10.00	0.000	t	85.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
906	ARO HUILE TOURNESOL 10L 1 430 10	Autre	2.00	2.00	10.00	0.000	t	110.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
936	ARO POIVRE BLANC ML SAC 1KG 13 400 1	Autre	2.00	2.00	10.00	0.000	t	91.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
203	MAIN GOURD - EPINARD HACHES 800G	Autre	0.00	3.30	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
390	ARO SEL FIN BV	Autre	7.00	7.00	0.00	0.000	t	55.000	2025-10-30 12:08:39.842775	2025-10-30 13:37:59.565036
328	AIL EN POUDRE SAC	Autre	5.00	5.00	0.00	0.000	t	0.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
620	COGNAC HENNESSY VS 70CL 40D S 40 0 0 280 0 700 30 890 1	Alcool	1.00	1.00	20.00	0.000	t	803.000	2025-10-30 13:08:21.170149	2025-10-30 13:37:59.565036
621	COGNAC VS DELAITRE 40D 70CL S 40 0 0 280 0 700 14 990 1	Alcool	1.00	1.00	20.00	0.000	t	54.000	2025-10-30 13:08:21.170149	2025-10-30 13:37:59.565036
1029	ARMAGNAC DELAITRE 10A 40D 70CL D 40 0 0 280 0 700 16 700 1	Alcool	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
600	CH MOET&CHANDON IMPERIAL 75CL M 0 750 29 087 6	Autre	1.00	1.00	20.00	0.000	t	2658.000	2025-10-30 12:24:35.062022	2025-10-30 13:37:59.565036
320	LEFFE BLONDE 6.6 BLE 33CL B 6 6 0 022 0 330 0 847 12	Autre	5.00	5.00	20.00	0.000	t	2501.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
333	BARRE MGV KER SUZEL	Autre	8.00	8.00	0.00	0.000	t	0.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
1030	SACHET	Autre	4.00	4.00	0.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
335	BARRE MARBREE	Autre	6.00	6.00	0.00	0.000	t	0.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
1031	LAIT UHT 1/2ECR 1L PPX BK (D 0 640 6	Autre	2.00	2.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
522	PAIN MIE NAT.LC 1KG METRO CHEF 3 030 1	Autre	1.00	1.00	10.00	0.000	t	14.000	2025-10-30 12:18:34.198825	2025-10-30 13:37:59.565036
523	PAIN MIE COMPL.LC	Autre	10.00	10.00	0.00	0.000	t	0.000	2025-10-30 12:18:34.198825	2025-10-30 13:37:59.565036
345	8 PAIN CHOCOLAT LC	Autre	3.00	3.00	0.00	0.000	t	54.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
346	10 PAIN LAIT LC	Autre	3.00	3.00	0.00	0.000	t	30.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
204	MAMA AFRICA - HUILE PALME ROUGE	Autre	0.00	3.50	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
205	MARQUIS DES BOIS 2020 75CL	Autre	0.00	1.00	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
929	SIROP GILBERT MENTHEGLA 1L 2 030 1	Autre	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
509	SIROP GILBERT MELON 1L 3 200 1	Autre	1.00	1.00	10.00	0.000	t	11.000	2025-10-30 12:18:04.059187	2025-10-30 13:37:59.565036
971	SIROP GILBERT PECHE 1L 2 870 1	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
481	COCA COLA PET 50CL 1 025 24	Autre	1.00	1.00	10.00	0.000	t	781.000	2025-10-30 12:11:53.816872	2025-10-30 13:37:59.565036
754	MPRO NETT MS BACT 5L CITRON 7 260 1	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1033	SOLIJAVEL+ 4EN1 CITRON 5L 9 990 1	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1032	PELFORTH BRUN 6.5D 25CL X6 L 6 5 0 016 0 250 0 647 24	Autre	1.00	1.00	20.00	0.000	t	30.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
599	GET	Autre	27.00	27.00	20.00	0.000	t	27.000	2025-10-30 12:24:35.062022	2025-10-30 13:37:59.565036
879	DOLCEGUSTO ESPRES INTEN X16 3 610 1	Autre	1.00	1.00	10.00	0.000	t	26.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
961	EPINARD BRANCHE PALET 2.5KG MC 4 280 1	Autre	2.00	2.00	10.00	0.000	t	65.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1034	50 MASQUE JETABLE BLEU EARLOOP 9 000 1	Autre	1.00	1.00	10.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
691	JAVEL 2 6% 5L 1 220 1	Autre	1.00	1.00	20.00	0.000	t	22.000	2025-10-30 13:28:58.358722	2025-10-30 13:37:59.565036
885	MP 6 ASSIETTES STEAK	Autre	3.00	3.00	20.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1035	CAROTTES RONDELLES 2.5KG MC 3 390 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1036	FRY'N'DIP 2.5KG MCCAIN 4 780 1	Autre	1.00	1.00	10.00	0.000	t	4.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
741	MP 10 BLOC MH METRO 80X	Autre	1.00	1.00	20.00	0.000	t	15.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
770	HEINEKEN 12X33 CL 5D VP L 5 0 0 017 0 330 0 690 12	Autre	1.00	1.00	20.00	0.000	t	253.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
380	PERRIER 6*50CL PET 0 565 24	Autre	1.00	1.00	10.00	0.000	t	467.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
1037	FERRERO ROCHER T30 PAQUES	Autre	3.00	3.00	0.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
949	KINDER SURPRISE T	Autre	6.00	6.00	0.00	0.000	t	24.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
852	250 POT A SAUCE 3 CL 2 920 1	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
853	250 COUV POUR POT A SAUCE 2 610 1	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
786	WH J.DANIEL S	Autre	1.00	1.00	20.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1038	PORTO CRUZ RGE 18D 75CL C 0 750 5 970 1	Alcool	1.00	1.00	20.00	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
569	CDP RSE MAURIN MAURES MIL75CL T 0 750 4 790 6	Autre	1.00	1.00	20.00	0.000	t	373.000	2025-10-30 12:23:12.672006	2025-10-30 13:37:59.565036
1039	VDF CHARDON 12%	Autre	1.00	1.00	20.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
513	SUPER BOCK	Autre	5.20	5.20	20.00	0.000	t	6.000	2025-10-30 12:18:34.198825	2025-10-30 13:37:59.565036
698	CORONA EXT 4.5D 6X	Autre	3.00	3.00	20.00	0.000	t	10.000	2025-10-30 13:31:16.814255	2025-10-30 13:37:59.565036
530	HEINEKEN 5D 6X25CL VP B 5 0 0 013 0 250 0 577 24	Autre	3.00	3.00	20.00	0.000	t	118.000	2025-10-30 12:20:16.389747	2025-10-30 13:37:59.565036
967	SUPER BOCK 5.2D 25CL L 5 2 0 013 0 250 0 480 24	Autre	1.00	1.00	20.00	0.000	t	80.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1040	GRANINI ORANGE 25CL 0 620 12	Autre	1.00	1.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1041	GRANINI ANANAS 25CL 0 647 12	Autre	1.00	1.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
416	RIOBA BOISS TROPICAL TO25CL 0 581 12	Autre	1.00	1.00	10.00	0.000	t	55.000	2025-10-30 12:10:16.733895	2025-10-30 13:37:59.565036
968	GILBERT BOISS POM CANNEL 25CL 0 590 12	Autre	1.00	1.00	10.00	0.000	t	19.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
791	ORANGINA JAUNE 25CLX8 VP 0 500 32	Alcool	1.00	1.00	10.00	0.000	t	79.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1026	CAFE ROBUSTA GRAIN KG ARO 4 890 1	Autre	1.00	1.00	10.00	0.000	t	13.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1042	50 GOBELET BLC 10CL 0 710 1	Autre	1.00	1.00	20.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
454	WHISKY CHIVAS 12A 40D 70CL S 40 0 0 280 0 700 20 860 6	Alcool	1.00	1.00	20.00	0.000	t	1219.000	2025-10-30 12:10:59.277817	2025-10-30 13:37:59.565036
793	WHISKY JB 40D 1L S 40 0 0 400 1 000 15 120 1	Alcool	1.00	1.00	20.00	0.000	t	112.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1043	WH GRANTS T.WOOD 40D70CLX6+KIT D 40 0 0 280 0 700 7 867 6	Autre	1.00	1.00	20.00	0.000	t	47.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
405	VDK ERISTOFF	Autre	3.00	3.00	20.00	0.000	t	14.000	2025-10-30 12:10:16.733895	2025-10-30 13:37:59.565036
869	RICARD 45D 1L D 45 0 0 450 1 000 14 370 1	Autre	1.00	1.00	20.00	0.000	t	95.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
461	MARTINI BLC	Autre	1.00	1.00	20.00	0.000	t	28.000	2025-10-30 12:10:59.277817	2025-10-30 13:37:59.565036
567	MARTINI ROSE	Autre	1.00	1.00	20.00	0.000	t	16.000	2025-10-30 12:23:12.672006	2025-10-30 13:37:59.565036
462	MARTINI RGE	Autre	1.00	1.00	20.00	0.000	t	40.000	2025-10-30 12:10:59.277817	2025-10-30 13:37:59.565036
1044	CH V. PELLETIER BRUT 75CL 3 0 750 10 610 6	Autre	1.00	1.00	20.00	0.000	t	63.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
496	DESPERADOS 5 9D 12X33CL VP B 5 9 0 019 0 330 0 981 12	Autre	3.00	3.00	20.00	0.000	t	2182.000	2025-10-30 12:16:27.234871	2025-10-30 13:37:59.565036
373	RIOBA ABC ORANGE TO 25CL 0 722 24	Autre	1.00	1.00	10.00	0.000	t	180.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
374	RIOBA ABC ANANAS TO 25CL 0 795 24	Autre	1.00	1.00	10.00	0.000	t	186.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
375	RIOBA PUR JUS RAISIN TO 25CL 0 646 12	Boissons	1.00	1.00	10.00	0.000	t	80.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
789	GILBERT PUR JUS MULTI TO 25CL 0 510 12	Boissons	1.00	1.00	10.00	0.000	t	18.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
728	GILBERT NECTAR GOYAVE TO 25CL 0 577 12	Autre	2.00	2.00	10.00	0.000	t	110.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
376	RIOBA NECTAR BANANE TO 25CL 0 673 12	Autre	1.00	1.00	10.00	0.000	t	105.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
479	RED BULL BOITE 25CL 1 020 24	Autre	1.00	1.00	10.00	0.000	t	1256.000	2025-10-30 12:11:53.816872	2025-10-30 13:37:59.565036
905	ORANGINA JAUNE 25CLX8 VP 0 490 32	Alcool	1.00	1.00	10.00	0.000	t	30.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
378	COCA-COLA PET 50CLX24 PROMO 0 922 24	Autre	1.00	1.00	10.00	0.000	t	491.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
206	MILKA CHOCO MOO	Autre	0.00	3.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
1045	DOLCE GUSTO LUNGO X16 3 610 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
573	DOLCE GUSTO ESPRESSO X16 4 480 1	Autre	2.00	2.00	10.00	0.000	t	178.000	2025-10-30 12:23:12.672006	2025-10-30 13:37:59.565036
912	DOLCE GUSTO CAFE AU LAIT X30 7 450 1	Autre	1.00	1.00	10.00	0.000	t	21.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1046	VDF RIBEAUP CHARD 3L J 1 000 2 600 3	Boissons	4.00	4.00	20.00	0.000	t	31.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1047	DANAO MULTIVITAMINE	Autre	9.00	9.00	2.10	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
207	MILKA CHOCO WHITE	Autre	0.00	3.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
468	0	Autre	949.00	949.00	5.50	0.000	t	44.000	2025-10-30 12:11:25.7753	2025-10-30 13:37:59.565036
532	COCA COLAS 25CL VP 0 700 12	Autre	1.00	1.00	10.00	0.000	t	233.000	2025-10-30 12:20:16.389747	2025-10-30 13:37:59.565036
418	MAUREL HLE TOURNESOL 25L 1 780 25	Autre	1.00	1.00	10.00	0.000	t	753.000	2025-10-30 12:10:16.733895	2025-10-30 13:37:59.565036
796	ARO MAYONNAISE POT	Autre	4.00	4.00	0.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
632	MAXI BURGER LC 6X82G MC 0 292 6	Autre	1.00	1.00	10.00	0.000	t	19.000	2025-10-30 13:08:21.170149	2025-10-30 13:37:59.565036
351	MPRO DIST SAVON MOUSSE	Hygiene	7.00	7.00	2.10	0.000	t	0.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
1048	125 BTE SANDW KEBAB 11 590 1	Autre	1.00	1.00	20.00	0.000	t	11.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1049	MPRO 10 TAMPON /EPONG VERT 6 610 1	Autre	1.00	1.00	20.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
690	MPRO 10 BOULE INOX R 60G 9 140 1	Autre	1.00	1.00	20.00	0.000	t	17.000	2025-10-30 13:28:58.358722	2025-10-30 13:37:59.565036
761	DESODO	Autre	3.00	3.00	2.10	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1050	MPRO DESODO PAMPLEMOUSSE	Autre	7.00	7.00	2.10	0.000	t	5.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
557	MPRO DEGRAISSANT UNIVERSEL 5L 15 000 1	Autre	1.00	1.00	20.00	0.000	t	186.000	2025-10-30 12:20:16.389747	2025-10-30 13:37:59.565036
726	MPRO LAVE VITRES	Autre	7.00	7.00	2.10	0.000	t	15.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
1051	MPRO NETT MU POMME BACT 5L 7 990 1	Autre	1.00	1.00	20.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
438	ARO LIQ VAISS MAIN CIT 5L 6 670 1	Autre	1.00	1.00	20.00	0.000	t	71.000	2025-10-30 12:10:16.733895	2025-10-30 13:37:59.565036
858	WHISKY JDANIEL +6V 40D 70CL X6 D 40 0 0 280 0 700 13 447 6	Alcool	1.00	1.00	20.00	0.000	t	614.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
958	VIN FR CHARDON 75CL RIBEAUP 8 0 750 1 990 6	Alcool	1.00	1.00	20.00	0.000	t	33.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
318	BERG MOEL MIL MONDESIR 75C T 0 750 2 890 6	Autre	1.00	1.00	20.00	0.000	t	402.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
558	ROCHE DES ECRINS 33CL PET 0 177 24	Autre	1.00	1.00	10.00	0.000	t	264.000	2025-10-30 12:20:31.953437	2025-10-30 13:37:59.565036
327	OIGNON BLANC POUDRE SAC	Autre	5.00	5.00	0.00	0.000	t	0.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
719	50 POT SAUCE + COUV 6CL 4 010 1	Autre	2.00	2.00	20.00	0.000	t	43.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
986	PAYSOC CAB.SAUVMIL R. MAZET 75 K 0 750 2 142 6	Autre	2.00	2.00	20.00	0.000	t	78.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1052	BDX RGE ENCLOS SADIRAC 75CL I 0 750 1 690 6	Autre	1.00	1.00	20.00	0.000	t	10.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1053	ATLANTIQ IGP OCEADE RSE 75CL K 0 750 1 658 6	Autre	1.00	1.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
710	WH JWALKER BLACK 12A 40D 70CL S 40 0 0 280 0 700 19 868 6	Autre	1.00	1.00	20.00	0.000	t	1244.000	2025-10-30 13:35:24.289083	2025-10-30 13:37:59.565036
957	ROCHE MAZET MERLOT 75CL IGP K 0 750 1 357 6	Autre	1.00	1.00	20.00	0.000	t	48.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
368	BDX RGE CH LES VERGNES 75CL T 0 750 3 325 6	Autre	1.00	1.00	20.00	0.000	t	2826.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
655	IGP MED RGE C. DAUPHINS 25CL T 0 250 1 290 12	Autre	2.00	2.00	20.00	0.000	t	477.000	2025-10-30 13:09:19.982452	2025-10-30 13:37:59.565036
397	ROSE ANJOU MIL M.LAUR 75CL T 0 750 3 390 6	Autre	1.00	1.00	20.00	0.000	t	255.000	2025-10-30 12:09:02.576379	2025-10-30 13:37:59.565036
354	LEFFE BLONDE 75CL 6.6D VP B 6 6 0 050 0 750 2 505 6	Autre	2.00	2.00	20.00	0.000	t	2641.000	2025-10-30 12:07:45.054577	2025-10-30 13:37:59.565036
322	DESPERAD 5.9D 65CL VP B 5 9 0 038 0 650 2 452 12	Autre	1.00	1.00	20.00	0.000	t	1135.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
501	RIZ PARF LOTUS 10KG RDM 24 150 1	Autre	1.00	1.00	10.00	0.000	t	574.000	2025-10-30 12:16:40.566579	2025-10-30 13:37:59.565036
907	*SEMOUL BLE FIN 5KG RENARD 5 950 1	Autre	1.00	1.00	10.00	0.000	t	10.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
381	ARO MAYO ALLEGEE ARO SEAU 5L 10 260 1	Boissons	1.00	1.00	10.00	0.000	t	427.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
777	ARO MOUTARDE DIJON SEAU 5KG 6 590 1	Boissons	1.00	1.00	10.00	0.000	t	90.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
556	100 POT SAUCE 59ML 3 360 1	Autre	1.00	1.00	20.00	0.000	t	127.000	2025-10-30 12:20:16.389747	2025-10-30 13:37:59.565036
764	JAVEL 9 6% 5L 3 690 1	Autre	1.00	1.00	20.00	0.000	t	40.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
463	WHISKY CHIVAS 12A 40D 70CL S 40 0 0 280 0 700 23 640 1	Alcool	1.00	1.00	20.00	0.000	t	400.000	2025-10-30 12:11:25.7753	2025-10-30 13:37:59.565036
1054	RHUM 3RIVIERE BLC 40D 70CL E 40 0 0 280 0 700 8 670 1	Alcool	1.00	1.00	20.00	0.000	t	8.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
465	BAILEYS IRISH CREME 17D 70CL S 17 0 0 119 0 700 11 150 1	Autre	1.00	1.00	20.00	0.000	t	310.000	2025-10-30 12:11:25.7753	2025-10-30 13:37:59.565036
953	SIROP GILBERT MENTHE 1L 1 890 1	Autre	1.00	1.00	10.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
868	BUCHETTE SUCRE 4GX	Autre	10.00	10.00	0.00	0.000	t	0.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1055	TARTE NOIX COCO INTENSE 1KG 6 650 1	Autre	1.00	1.00	10.00	0.000	t	6.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
306	MPRO	Autre	2.00	2.00	5.50	0.000	t	160.000	2025-10-30 12:05:49.521322	2025-10-30 13:37:59.565036
1056	100 PIC NOIR RGE 7CM 3 170 1	Autre	1.00	1.00	20.00	0.000	t	3.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
956	FLUTE OPEN UP 20CL 3 695 6	Autre	1.00	1.00	20.00	0.000	t	50.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1057	VAP OPEN UP TANNIC 55CL 4 835 6	Autre	1.00	1.00	20.00	0.000	t	29.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1058	PACK 6 LUMIGNONS ROUGE MPRO 0 793 6	Autre	2.00	2.00	20.00	0.000	t	9.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
584	PAYS OC CABERN SAUV 25CL MAZET T 0 250 1 530 12	Autre	1.00	1.00	20.00	0.000	t	1228.000	2025-10-30 12:24:14.204165	2025-10-30 13:37:59.565036
369	IGP MED RGE C. DAUPHINS 25CL T 0 250 1 350 12	Autre	2.00	2.00	20.00	0.000	t	1288.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
321	DESPERAD 5.9D 33CL VP // B 5 9 0 019 0 330 1 003 24	Autre	1.00	1.00	20.00	0.000	t	1338.000	2025-10-30 12:06:46.790014	2025-10-30 13:37:59.565036
969	PERRIER 33CL VC 0 720 24	Autre	1.00	1.00	10.00	0.000	t	51.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
619	RUM :	Autre	758807.00	758807.00	2.10	0.000	t	0.000	2025-10-30 13:05:40.667214	2025-10-30 13:37:59.565036
352	HEINEKEN 5D 65CL VP B 5 0 0 033 0 650 1 435 12 80	Autre	2.00	2.00	20.00	0.000	t	18482.000	2025-10-30 12:07:11.398554	2025-10-30 13:37:59.565036
951	MP 10 BLOC MH 96X	Autre	1.00	1.00	20.00	0.000	t	14.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
811	WH JWALKER BLACK 12A 40D 70CL S 40 0 0 280 0 700 19 860 1	Autre	3.00	3.00	20.00	0.000	t	483.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
1059	PAYS OC CABERN SAUV 25CL MAZET K 0 250 1 550 12	Autre	1.00	1.00	20.00	0.000	t	18.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
372	1	Autre	664.00	664.00	20.00	0.000	t	510.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
773	SIROP GILBERT GRENADINE 1L 1 890 1	Autre	2.00	2.00	10.00	0.000	t	89.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
700	COCA COLA REG PET	Autre	1.00	1.00	5.50	0.000	t	14.000	2025-10-30 13:31:16.814255	2025-10-30 13:37:59.565036
489	ROCHES DES ECRINS PET 50CL 0 193 24	Autre	1.00	1.00	10.00	0.000	t	499.000	2025-10-30 12:15:47.724561	2025-10-30 13:37:59.565036
960	PERRIER 50CL PET 0 457 24	Autre	1.00	1.00	10.00	0.000	t	31.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
775	MAUREL HLE TOURNESOL 10L 1 880 10	Autre	1.00	1.00	10.00	0.000	t	169.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
502	GILBERT MAYONAISE BUCH10GX100 0 063 100	Autre	1.00	1.00	10.00	0.000	t	945.000	2025-10-30 12:16:40.566579	2025-10-30 13:37:59.565036
1060	EPINARDS HACHES 2.5KG MC 3 630 1	Autre	2.00	2.00	10.00	0.000	t	7.000	2025-10-30 13:37:59.565036	2025-10-30 13:37:59.565036
360	MPRO ALU	Autre	3.00	3.00	0.00	0.000	t	35.000	2025-10-30 12:07:45.054577	2025-10-30 13:37:59.565036
385	ARO LIQ VAISS MAIN CIT 10L 1 046 10	Autre	1.00	1.00	20.00	0.000	t	535.000	2025-10-30 12:08:25.252336	2025-10-30 13:37:59.565036
208	MOUTARDE FINE 280G	Autre	0.00	2.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
209	Mirinda Boisson Gazeuse Goût Ananas 2 L	Boissons	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
210	Mirinda Boisson Gazeuse Goût Fraise 2 L	Boissons	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
211	Mirinda Boisson Gazeuse Goût Orange 2 L	Boissons	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
212	Mirinda Boisson Gazeuse Goût Pomme Kiwi 2 L	Boissons	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
213	Mirinda Orange 33cl (Pack De 24)	Autre	0.00	19.99	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
214	Mirinda Strawberry 330ml X 24	Autre	0.00	19.40	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
215	Monster Ultra Fiesta Mango	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
216	Muscador blanc	Autre	0.00	4.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
217	Muscador rose	Autre	0.00	4.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
218	NUMBER ONE BOUILLON BOEUF 1KG	Autre	0.00	5.50	5.50	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
219	OREO ORIGINAL 220G x5	Alcool	0.00	4.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
220	PATE DE SARDINELLE	Autre	0.00	3.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
221	PCD PATE ARACHIDE 500G	Autre	0.00	3.60	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
222	PETIT ECOLIER POCK 10	Autre	0.00	4.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
223	PILCHARDS 400G	Autre	0.00	2.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
224	PILCHARDS 425G	Autre	0.00	2.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
225	POLIAKOV 70CL	Autre	0.00	15.90	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
226	PORTO CRUZ 75CL	Alcool	0.00	16.95	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
227	PORTO CRUZ TAWNY 70CL	Alcool	0.00	26.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
228	PRAISE PALM CREAM	Autre	0.00	2.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
229	PRINCE CHOCO 300G	Autre	0.00	2.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
230	PROVENC TOMAT 425G	Autre	0.00	3.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
231	PUY VALLON 70CL	Autre	0.00	11.90	20.00	0.000	t	5.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
232	Pain Au Lait Et Pépites De Chocolat	Autre	0.00	2.80	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
233	Pepsi	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
234	Pepsi 1 L	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
235	Pepsi 1,5L	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
236	Pepsi Max	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
237	Pepsi Zéro Sleek 33 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
238	Pepsi Zéro Sucres 1 L	Autre	0.00	1.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
239	Pepsi Zéro Sucres 50 Cl	Autre	0.00	1.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
240	Pepsi Zéro Sucres Saveur Cerise 1,5 L	Autre	0.00	1.00	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
241	Perle d'asie - riz long parfume QS 20kg	Autre	0.00	47.90	5.50	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
242	Perle d'asie - riz parfume casse 1F 5KG	Autre	0.00	10.90	5.50	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
243	Petit marseillais - fleur d'oranger bio 250ml	Autre	0.00	3.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
244	Picon bière à l’orange 1L	Alcool	0.00	37.50	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
245	Punched Goût Tropical Goyave 50 Cl	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
246	RED LABEL 35CL	Autre	0.00	14.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
247	RIBEAUPIERRE 2023	Boissons	0.00	7.90	5.50	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
248	RIZ LOTUS 2OKG	Autre	0.00	44.99	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
249	RIZ LOTUS LONG 5KG	Autre	0.00	15.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
250	RIZ ROND 1KG	Autre	0.00	2.95	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
251	RIZ SUNMALI 10K	Autre	0.00	24.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
252	ROC DE CAZADE 75CL	Autre	0.00	12.99	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
253	ROCHAMBEAU PAIN AU CHOCO 360G	Boissons	0.00	2.99	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
254	ROCHAMBEAU PAIN AU LAIT 350G	Boissons	0.00	2.80	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
255	ROMA OIL - SUNFLOWER	Autre	0.00	2.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
256	Rochambeau flageolets verts	Boissons	0.00	1.30	5.50	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
257	Rockstar Energy Drink Goût Fraise Citron Vert	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
258	SAMIA HARICO BLANCS	Autre	0.00	1.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
259	SAMIA POIS CHICHES	Autre	0.00	1.99	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
260	SAUCE TOMATE CUISINE.	Autre	0.00	3.50	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
261	SEL DE TABLE 750G	Autre	0.00	1.20	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
262	SMIRNOFF 70CL	Autre	0.00	17.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
263	SMIRNOFF MIXED 70CL	Autre	0.00	4.50	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
264	SOBIESKI 70CL	Autre	0.00	17.90	20.00	0.000	t	4.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
265	SOBIESKI VODKA 35CL	Alcool	0.00	11.90	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
266	ST MICHEL SABLE RETZ 120G	Autre	0.00	2.20	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
267	SUCRE EN POUDRE 1KG	Autre	0.00	2.52	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
268	SUCRE MORCEAUX 1KG	Boissons	0.00	3.50	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
269	Sauce Tomate Basilic	Autre	0.00	2.50	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
270	Sel De Table	Autre	0.00	1.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
271	Smarties 38g	Autre	0.00	109.99	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
272	Sprite Goût Original — canette 33 cl	Alcool	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
273	Sprite Goût Original — canette 33 cl (FR ref.)	Alcool	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
274	Sprite Goût Original — canette 33 cl (UK)	Alcool	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
275	Sprite Goût Original — canette 33 cl (ancien)	Alcool	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
276	Sprite Ice — canette 33 cl	Autre	0.00	0.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
277	TERSOL RIZ PARFUME 1KG	Autre	0.00	3.50	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
278	THON ENTIER 400G	Autre	0.00	4.99	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
279	THON SAUPIQUET 800G	Autre	0.00	7.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
280	TILDA RIZ LONG BASMAT 1KG	Autre	0.00	4.50	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
281	TROFAI 400G	Autre	0.00	3.50	20.00	0.000	t	11.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
282	Thon Au Naturel	Autre	0.00	3.90	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
283	TopoChico TANGY LEMOM LIME	Autre	0.00	1.00	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
284	VIEUX PAPES 75CL	Autre	0.00	14.50	20.00	0.000	t	7.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
285	VILLAGEOISE 0.75L	Autre	0.00	4.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
286	VINAIGRE DE RAISIN	Alcool	0.00	2.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
287	VOLKA PYLA 70CL	Autre	0.00	38.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
288	VOLKA STOLI 70CL	Autre	0.00	16.90	20.00	0.000	t	1.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
289	Vinaigre Balsamique à La Truffe	Alcool	0.00	19.50	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
290	WALIMA	Autre	0.00	1.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
291	WALIMA RIZ LONG ETUVE 1K	Autre	0.00	2.80	5.50	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
292	WILLIAM LAW 700ML	Autre	0.00	21.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
293	WILLIAM PEEL 35CL	Autre	0.00	11.90	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
294	WILLIAM PEEL 70CL	Autre	0.00	19.50	20.00	0.000	t	2.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
295	WYBOROWA VODKA 70CL	Alcool	0.00	25.90	20.00	0.000	t	3.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
296	ZWAN 340G	Autre	0.00	3.90	20.00	0.000	t	0.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
3	$5410316947022	Autre	0.00	1.60	5.50	0.000	t	387.000	2025-10-30 11:54:29.494117	2025-10-30 11:54:29.494117
\.


--
-- Data for Name: produits_barcodes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.produits_barcodes (id, produit_id, code, symbologie, pays_iso2, is_principal, created_at) FROM stdin;
1	1	3258561220734.0	\N	\N	f	2025-10-30 11:54:29.494117
2	2	5000267013602.0	\N	\N	f	2025-10-30 11:54:29.494117
3	3	nan	\N	\N	f	2025-10-30 11:54:29.494117
4	4	8717438769837.0	\N	\N	f	2025-10-30 11:54:29.494117
5	5	3168930159834.0	\N	\N	f	2025-10-30 11:54:29.494117
6	6	3502110001900.0	\N	\N	f	2025-10-30 11:54:29.494117
7	7	3168930161769.0	\N	\N	f	2025-10-30 11:54:29.494117
8	8	3168930161738.0	\N	\N	f	2025-10-30 11:54:29.494117
9	9	3502110009036.0	\N	\N	f	2025-10-30 11:54:29.494117
10	10	3168930159773.0	\N	\N	f	2025-10-30 11:54:29.494117
11	11	3168930159865.0	\N	\N	f	2025-10-30 11:54:29.494117
12	12	3168930159803.0	\N	\N	f	2025-10-30 11:54:29.494117
13	13	7312040017683.0	\N	\N	f	2025-10-30 11:54:29.494117
14	14	3760137910531.0	\N	\N	f	2025-10-30 11:54:29.494117
15	15	3760137911040.0	\N	\N	f	2025-10-30 11:54:29.494117
16	16	8904064616264.0	\N	\N	f	2025-10-30 11:54:29.494117
17	17	6111260550212.0	\N	\N	f	2025-10-30 11:54:29.494117
18	18	3276650116102.0	\N	\N	f	2025-10-30 11:54:29.494117
19	19	3439495112184.0	\N	\N	f	2025-10-30 11:54:29.494117
20	20	3439495113488.0	\N	\N	f	2025-10-30 11:54:29.494117
21	21	5010677014205.0	\N	\N	f	2025-10-30 11:54:29.494117
22	22	3011932009952.0	\N	\N	f	2025-10-30 11:54:29.494117
23	23	5000299610688.0	\N	\N	f	2025-10-30 11:54:29.494117
24	24	3258561020112.0	\N	\N	f	2025-10-30 11:54:29.494117
25	25	3439497015285.0	\N	\N	f	2025-10-30 11:54:29.494117
26	26	3185110012673.0	\N	\N	f	2025-10-30 11:54:29.494117
27	27	3258561510408.0	\N	\N	f	2025-10-30 11:54:29.494117
28	28	3258561040257.0	\N	\N	f	2025-10-30 11:54:29.494117
29	29	3258561040356.0	\N	\N	f	2025-10-30 11:54:29.494117
30	30	3258561020716.0	\N	\N	f	2025-10-30 11:54:29.494117
31	31	3258561500744.0	\N	\N	f	2025-10-30 11:54:29.494117
32	32	3258561510255.0	\N	\N	f	2025-10-30 11:54:29.494117
33	33	3258561500768.0	\N	\N	f	2025-10-30 11:54:29.494117
34	34	3258561240763.0	\N	\N	f	2025-10-30 11:54:29.494117
35	35	3258561240237.0	\N	\N	f	2025-10-30 11:54:29.494117
36	36	3258561212333.0	\N	\N	f	2025-10-30 11:54:29.494117
37	37	3258561220246.0	\N	\N	f	2025-10-30 11:54:29.494117
38	38	3258561019147.0	\N	\N	f	2025-10-30 11:54:29.494117
39	39	3258561020938.0	\N	\N	f	2025-10-30 11:54:29.494117
40	40	3258561211220.0	\N	\N	f	2025-10-30 11:54:29.494117
41	41	3258561211466.0	\N	\N	f	2025-10-30 11:54:29.494117
42	42	3258561240664.0	\N	\N	f	2025-10-30 11:54:29.494117
43	43	3258561180212.0	\N	\N	f	2025-10-30 11:54:29.494117
44	44	3258561240336.0	\N	\N	f	2025-10-30 11:54:29.494117
45	45	3258561240244.0	\N	\N	f	2025-10-30 11:54:29.494117
46	46	3258561240282.0	\N	\N	f	2025-10-30 11:54:29.494117
47	47	3258561211756.0	\N	\N	f	2025-10-30 11:54:29.494117
48	48	3258561211459.0	\N	\N	f	2025-10-30 11:54:29.494117
49	49	3258561220239.0	\N	\N	f	2025-10-30 11:54:29.494117
50	50	3258561142104.0	\N	\N	f	2025-10-30 11:54:29.494117
51	51	3258561240268.0	\N	\N	f	2025-10-30 11:54:29.494117
52	52	3258561211404.0	\N	\N	f	2025-10-30 11:54:29.494117
53	53	3258561500263.0	\N	\N	f	2025-10-30 11:54:29.494117
54	54	3258561301013.0	\N	\N	f	2025-10-30 11:54:29.494117
55	55	3258561221168.0	\N	\N	f	2025-10-30 11:54:29.494117
56	56	3258561650371.0	\N	\N	f	2025-10-30 11:54:29.494117
57	57	32585616510354.0	\N	\N	f	2025-10-30 11:54:29.494117
58	58	3258561510378.0	\N	\N	f	2025-10-30 11:54:29.494117
59	59	3258561670201.0	\N	\N	f	2025-10-30 11:54:29.494117
60	60	3258561510569.0	\N	\N	f	2025-10-30 11:54:29.494117
61	61	3258561510545.0	\N	\N	f	2025-10-30 11:54:29.494117
62	62	3258561510286.0	\N	\N	f	2025-10-30 11:54:29.494117
63	63	3258561500416.0	\N	\N	f	2025-10-30 11:54:29.494117
64	64	3258561670195.0	\N	\N	f	2025-10-30 11:54:29.494117
65	65	3258561670652.0	\N	\N	f	2025-10-30 11:54:29.494117
66	66	3258561670690.0	\N	\N	f	2025-10-30 11:54:29.494117
67	67	3258561640013.0	\N	\N	f	2025-10-30 11:54:29.494117
68	68	5901867816498.0	\N	\N	f	2025-10-30 11:54:29.494117
69	69	5410673005076.0	\N	\N	f	2025-10-30 11:54:29.494117
70	70	5000267024202.0	\N	\N	f	2025-10-30 11:54:29.494117
71	71	3258561211497.0	\N	\N	f	2025-10-30 11:54:29.494117
72	72	3258561211251.0	\N	\N	f	2025-10-30 11:54:29.494117
73	73	3083680025881.0	\N	\N	f	2025-10-30 11:54:29.494117
74	74	3020254463755.0	\N	\N	f	2025-10-30 11:54:29.494117
75	75	3020254463465.0	\N	\N	f	2025-10-30 11:54:29.494117
76	76	3020254463779.0	\N	\N	f	2025-10-30 11:54:29.494117
77	77	3760045044199.0	\N	\N	f	2025-10-30 11:54:29.494117
78	78	3179071000978.0	\N	\N	f	2025-10-30 11:54:29.494117
79	79	7616100005079.0	\N	\N	f	2025-10-30 11:54:29.494117
80	80	4017773301131.0	\N	\N	f	2025-10-30 11:54:29.494117
81	81	3258561210889.0	\N	\N	f	2025-10-30 11:54:29.494117
82	82	3290350555553.0	\N	\N	f	2025-10-30 11:54:29.494117
83	83	3259354503003.0	\N	\N	f	2025-10-30 11:54:29.494117
84	84	3211209139232.0	\N	\N	f	2025-10-30 11:54:29.494117
85	85	3451201439903.0	\N	\N	f	2025-10-30 11:54:29.494117
86	86	3182520295146.0	\N	\N	f	2025-10-30 11:54:29.494117
87	87	80432402931.0	\N	\N	f	2025-10-30 11:54:29.494117
88	88	3760151401206.0	\N	\N	f	2025-10-30 11:54:29.494117
89	89	5010103938235.0	\N	\N	f	2025-10-30 11:54:29.494117
90	90	5010103916738.0	\N	\N	f	2025-10-30 11:54:29.494117
91	91	5010103999991.0	\N	\N	f	2025-10-30 11:54:29.494117
92	92	3163937635008.0	\N	\N	f	2025-10-30 11:54:29.494117
93	93	3047360102088.0	\N	\N	f	2025-10-30 11:54:29.494117
94	94	3439495503272.0	\N	\N	f	2025-10-30 11:54:29.494117
95	95	5449000009500.0	\N	\N	f	2025-10-30 11:54:29.494117
96	96	5449000214812.0	\N	\N	f	2025-10-30 11:54:29.494117
97	97	5449000214799.0	\N	\N	f	2025-10-30 11:54:29.494117
98	98	5449000214911.0	\N	\N	f	2025-10-30 11:54:29.494117
99	99	5449000214843.0	\N	\N	f	2025-10-30 11:54:29.494117
100	100	5449000195364.0	\N	\N	f	2025-10-30 11:54:29.494117
101	101	5942321002590.0	\N	\N	f	2025-10-30 11:54:29.494117
102	102	5449000239761.0	\N	\N	f	2025-10-30 11:54:29.494117
103	103	54490000009960.0	\N	\N	f	2025-10-30 11:54:29.494117
104	104	50112128.0	\N	\N	f	2025-10-30 11:54:29.494117
105	105	54492509.0	\N	\N	f	2025-10-30 11:54:29.494117
106	106	5449000308023.0	\N	\N	f	2025-10-30 11:54:29.494117
107	107	54490147.0	\N	\N	f	2025-10-30 11:54:29.494117
108	108	5449000267412.0	\N	\N	f	2025-10-30 11:54:29.494117
109	109	5000112639995.0	\N	\N	f	2025-10-30 11:54:29.494117
110	110	5449000267467.0	\N	\N	f	2025-10-30 11:54:29.494117
111	111	5449000054227.0	\N	\N	f	2025-10-30 11:54:29.494117
112	112	3174780000363.0	\N	\N	f	2025-10-30 11:54:29.494117
113	113	5449000000996.0	\N	\N	f	2025-10-30 11:54:29.494117
114	113	5000112638769.0	\N	\N	f	2025-10-30 11:54:29.494117
115	114	5740700988349.0	\N	\N	f	2025-10-30 11:54:29.494117
116	115	5000112545326.0	\N	\N	f	2025-10-30 11:54:29.494117
117	116	5449000016560.0	\N	\N	f	2025-10-30 11:54:29.494117
118	117	5449000089229.0	\N	\N	f	2025-10-30 11:54:29.494117
119	118	5449000056672.0	\N	\N	f	2025-10-30 11:54:29.494117
120	119	5000112611786.0	\N	\N	f	2025-10-30 11:54:29.494117
121	120	5449000050205.0	\N	\N	f	2025-10-30 11:54:29.494117
122	121	5449000275165.0	\N	\N	f	2025-10-30 11:54:29.494117
123	122	5449000252920.0	\N	\N	f	2025-10-30 11:54:29.494117
124	123	5449000131805.0	\N	\N	f	2025-10-30 11:54:29.494117
125	123	5000112592054.0	\N	\N	f	2025-10-30 11:54:29.494117
126	123	5000112519945.0	\N	\N	f	2025-10-30 11:54:29.494117
127	124	5740700982965.0	\N	\N	f	2025-10-30 11:54:29.494117
128	125	5000112554359.0	\N	\N	f	2025-10-30 11:54:29.494117
129	126	8000040000802.0	\N	\N	f	2025-10-30 11:54:29.494117
130	127	3038359010507.0	\N	\N	f	2025-10-30 11:54:29.494117
131	128	3165432534008.0	\N	\N	f	2025-10-30 11:54:29.494117
132	129	3760239453462.0	\N	\N	f	2025-10-30 11:54:29.494117
133	130	3014230002601.0	\N	\N	f	2025-10-30 11:54:29.494117
134	131	8410414000466.0	\N	\N	f	2025-10-30 11:54:29.494117
135	132	5010436503018.0	\N	\N	f	2025-10-30 11:54:29.494117
136	133	5010436500000.0	\N	\N	f	2025-10-30 11:54:29.494117
137	134	5010436500017.0	\N	\N	f	2025-10-30 11:54:29.494117
138	135	3258565100063.0	\N	\N	f	2025-10-30 11:54:29.494117
139	136	3483050000041.0	\N	\N	f	2025-10-30 11:54:29.494117
140	137	5000112650402.0	\N	\N	f	2025-10-30 11:54:29.494117
141	138	5449000006004.0	\N	\N	f	2025-10-30 11:54:29.494117
142	139	5740700994203.0	\N	\N	f	2025-10-30 11:54:29.494117
143	140	5449000286932.0	\N	\N	f	2025-10-30 11:54:29.494117
144	141	5449000214829.0	\N	\N	f	2025-10-30 11:54:29.494117
145	142	5740700996153.0	\N	\N	f	2025-10-30 11:54:29.494117
146	142	5740700991691.0	\N	\N	f	2025-10-30 11:54:29.494117
147	143	5000112514124.0	\N	\N	f	2025-10-30 11:54:29.494117
148	143	5000112579390.0	\N	\N	f	2025-10-30 11:54:29.494117
149	143	5000112673036.0	\N	\N	f	2025-10-30 11:54:29.494117
150	144	5740700987984.0	\N	\N	f	2025-10-30 11:54:29.494117
151	145	5000112517163.0	\N	\N	f	2025-10-30 11:54:29.494117
152	145	5000112649710.0	\N	\N	f	2025-10-30 11:54:29.494117
153	146	5000112641998.0	\N	\N	f	2025-10-30 11:54:29.494117
154	147	5000112515848.0	\N	\N	f	2025-10-30 11:54:29.494117
155	148	5449000011527.0	\N	\N	f	2025-10-30 11:54:29.494117
156	149	5449000287038.0	\N	\N	f	2025-10-30 11:54:29.494117
157	150	5000112637946.0	\N	\N	f	2025-10-30 11:54:29.494117
158	150	5000112628937.0	\N	\N	f	2025-10-30 11:54:29.494117
159	150	5000112638783.0	\N	\N	f	2025-10-30 11:54:29.494117
160	150	5000112552119.0	\N	\N	f	2025-10-30 11:54:29.494117
161	151	5449000027153.0	\N	\N	f	2025-10-30 11:54:29.494117
162	152	5449000291677.0	\N	\N	f	2025-10-30 11:54:29.494117
163	153	8710605018684.0	\N	\N	f	2025-10-30 11:54:29.494117
164	154	647458031073.0	\N	\N	f	2025-10-30 11:54:29.494117
165	155	3147690060703.0	\N	\N	f	2025-10-30 11:54:29.494117
166	156	7622210601988.0	\N	\N	f	2025-10-30 11:54:29.494117
167	157	5010327250007.0	\N	\N	f	2025-10-30 11:54:29.494117
168	158	3664284000018.0	\N	\N	f	2025-10-30 11:54:29.494117
169	159	6036000065910.0	\N	\N	f	2025-10-30 11:54:29.494117
170	160	5908234813067.0	\N	\N	f	2025-10-30 11:54:29.494117
171	161	3263281733679.0	\N	\N	f	2025-10-30 11:54:29.494117
172	162	3245995960015.0	\N	\N	f	2025-10-30 11:54:29.494117
173	163	9555008101316.0	\N	\N	f	2025-10-30 11:54:29.494117
174	164	3168930159988.0	\N	\N	f	2025-10-30 11:54:29.494117
175	165	3168930170310.0	\N	\N	f	2025-10-30 11:54:29.494117
176	166	5099873046173.0	\N	\N	f	2025-10-30 11:54:29.494117
177	167	3099873045864.0	\N	\N	f	2025-10-30 11:54:29.494117
178	168	5099873017623.0	\N	\N	f	2025-10-30 11:54:29.494117
179	169	5099873008270.0	\N	\N	f	2025-10-30 11:54:29.494117
180	170	5099873001370.0	\N	\N	f	2025-10-30 11:54:29.494117
181	171	5060095330029.0	\N	\N	f	2025-10-30 11:54:29.494117
182	172	5010103800853.0	\N	\N	f	2025-10-30 11:54:29.494117
183	173	5010103800259.0	\N	\N	f	2025-10-30 11:54:29.494117
184	174	4060800100252.0	\N	\N	f	2025-10-30 11:54:29.494117
185	175	3439495508802.0	\N	\N	f	2025-10-30 11:54:29.494117
186	176	3439495521108.0	\N	\N	f	2025-10-30 11:54:29.494117
187	177	3263286301323.0	\N	\N	f	2025-10-30 11:54:29.494117
188	178	3211209272243.0	\N	\N	f	2025-10-30 11:54:29.494117
189	179	3587222521508.0	\N	\N	f	2025-10-30 11:54:29.494117
190	180	3259356626007.0	\N	\N	f	2025-10-30 11:54:29.494117
191	181	8011988003060.0	\N	\N	f	2025-10-30 11:54:29.494117
192	182	3147699102008.0	\N	\N	f	2025-10-30 11:54:29.494117
193	183	3147690051206.0	\N	\N	f	2025-10-30 11:54:29.494117
194	184	3434435161017.0	\N	\N	f	2025-10-30 11:54:29.494117
195	185	3258561020297.0	\N	\N	f	2025-10-30 11:54:29.494117
196	186	3276650013210.0	\N	\N	f	2025-10-30 11:54:29.494117
197	187	3142952144016.0	\N	\N	f	2025-10-30 11:54:29.494117
198	188	3259356633005.0	\N	\N	f	2025-10-30 11:54:29.494117
199	189	3168930172994.0	\N	\N	f	2025-10-30 11:54:29.494117
200	190	3168930162711.0	\N	\N	f	2025-10-30 11:54:29.494117
201	191	3502110009142.0	\N	\N	f	2025-10-30 11:54:29.494117
202	192	3168930170600.0	\N	\N	f	2025-10-30 11:54:29.494117
203	193	3168930159896.0	\N	\N	f	2025-10-30 11:54:29.494117
204	194	3168930170549.0	\N	\N	f	2025-10-30 11:54:29.494117
205	195	3168930171058.0	\N	\N	f	2025-10-30 11:54:29.494117
206	196	3228881072276.0	\N	\N	f	2025-10-30 11:54:29.494117
207	197	3168930166016.0	\N	\N	f	2025-10-30 11:54:29.494117
208	198	3502110006844.0	\N	\N	f	2025-10-30 11:54:29.494117
209	199	3502110009234.0	\N	\N	f	2025-10-30 11:54:29.494117
210	200	3168930159926.0	\N	\N	f	2025-10-30 11:54:29.494117
211	201	3258561210162.0	\N	\N	f	2025-10-30 11:54:29.494117
212	202	7613033486050.0	\N	\N	f	2025-10-30 11:54:29.494117
213	203	3112940130109.0	\N	\N	f	2025-10-30 11:54:29.494117
214	204	3700019511081.0	\N	\N	f	2025-10-30 11:54:29.494117
215	205	3259353235004.0	\N	\N	f	2025-10-30 11:54:29.494117
216	206	7622300503079.0	\N	\N	f	2025-10-30 11:54:29.494117
217	207	7622300344757.0	\N	\N	f	2025-10-30 11:54:29.494117
218	208	3563490010029.0	\N	\N	f	2025-10-30 11:54:29.494117
219	209	3502110003485.0	\N	\N	f	2025-10-30 11:54:29.494117
220	210	3502110002884.0	\N	\N	f	2025-10-30 11:54:29.494117
221	210	8710398521682.0	\N	\N	f	2025-10-30 11:54:29.494117
222	211	3502110002679.0	\N	\N	f	2025-10-30 11:54:29.494117
223	212	3168930161707.0	\N	\N	f	2025-10-30 11:54:29.494117
224	213	3502110002686.0	\N	\N	f	2025-10-30 11:54:29.494117
225	214	3502110004192.0	\N	\N	f	2025-10-30 11:54:29.494117
226	215	5060751219156.0	\N	\N	f	2025-10-30 11:54:29.494117
227	216	3438931.0	\N	\N	f	2025-10-30 11:54:29.494117
228	217	3438931000597.0	\N	\N	f	2025-10-30 11:54:29.494117
229	218	3020254425715.0	\N	\N	f	2025-10-30 11:54:29.494117
230	219	7623300744663.0	\N	\N	f	2025-10-30 11:54:29.494117
231	220	6044000064000.0	\N	\N	f	2025-10-30 11:54:29.494117
232	221	8710411045058.0	\N	\N	f	2025-10-30 11:54:29.494117
233	222	7622210422026.0	\N	\N	f	2025-10-30 11:54:29.494117
234	223	5110817000256.0	\N	\N	f	2025-10-30 11:54:29.494117
235	224	5110817000232.0	\N	\N	f	2025-10-30 11:54:29.494117
236	225	3147690061007.0	\N	\N	f	2025-10-30 11:54:29.494117
237	226	3147699118368.0	\N	\N	f	2025-10-30 11:54:29.494117
238	227	3147699118351.0	\N	\N	f	2025-10-30 11:54:29.494117
239	228	6034000115215.0	\N	\N	f	2025-10-30 11:54:29.494117
240	229	7622210449283.0	\N	\N	f	2025-10-30 11:54:29.494117
241	230	3258561140629.0	\N	\N	f	2025-10-30 11:54:29.494117
242	231	3439495520729.0	\N	\N	f	2025-10-30 11:54:29.494117
243	232	3439496604008.0	\N	\N	f	2025-10-30 11:54:29.494117
244	233	4060800102683.0	\N	\N	f	2025-10-30 11:54:29.494117
245	234	4060800009449.0	\N	\N	f	2025-10-30 11:54:29.494117
246	235	3502110008329.0	\N	\N	f	2025-10-30 11:54:29.494117
247	236	3502110009357.0	\N	\N	f	2025-10-30 11:54:29.494117
248	237	3168930159742.0	\N	\N	f	2025-10-30 11:54:29.494117
249	238	3502110010049.0	\N	\N	f	2025-10-30 11:54:29.494117
250	239	3502110000651.0	\N	\N	f	2025-10-30 11:54:29.494117
251	240	3502110006295.0	\N	\N	f	2025-10-30 11:54:29.494117
252	241	3276650013753.0	\N	\N	f	2025-10-30 11:54:29.494117
253	242	3276650018826.0	\N	\N	f	2025-10-30 11:54:29.494117
254	243	3574661700823.0	\N	\N	f	2025-10-30 11:54:29.494117
255	244	5010103931502.0	\N	\N	f	2025-10-30 11:54:29.494117
256	245	8710398521712.0	\N	\N	f	2025-10-30 11:54:29.494117
257	246	5000267014807.0	\N	\N	f	2025-10-30 11:54:29.494117
258	247	3439495506723.0	\N	\N	f	2025-10-30 11:54:29.494117
259	248	3276650013289.0	\N	\N	f	2025-10-30 11:54:29.494117
260	249	3276650013265.0	\N	\N	f	2025-10-30 11:54:29.494117
261	250	3276650010011.0	\N	\N	f	2025-10-30 11:54:29.494117
262	251	8847102310031.0	\N	\N	f	2025-10-30 11:54:29.494117
263	252	354295000015.0	\N	\N	f	2025-10-30 11:54:29.494117
264	253	3439496604015.0	\N	\N	f	2025-10-30 11:54:29.494117
265	254	3439496603995.0	\N	\N	f	2025-10-30 11:54:29.494117
266	255	3020254964290.0	\N	\N	f	2025-10-30 11:54:29.494117
267	256	3439497014370.0	\N	\N	f	2025-10-30 11:54:29.494117
268	257	8710398523952.0	\N	\N	f	2025-10-30 11:54:29.494117
269	258	3276650101177.0	\N	\N	f	2025-10-30 11:54:29.494117
270	259	3276650101153.0	\N	\N	f	2025-10-30 11:54:29.494117
271	260	3038359011412.0	\N	\N	f	2025-10-30 11:54:29.494117
272	261	3165720448833.0	\N	\N	f	2025-10-30 11:54:29.494117
273	262	5410316671118.0	\N	\N	f	2025-10-30 11:54:29.494117
274	263	5410316947053.0	\N	\N	f	2025-10-30 11:54:29.494117
275	264	5902738887876.0	\N	\N	f	2025-10-30 11:54:29.494117
276	265	5902738883106.0	\N	\N	f	2025-10-30 11:54:29.494117
277	266	3023470010017.0	\N	\N	f	2025-10-30 11:54:29.494117
278	267	3220035560004.0	\N	\N	f	2025-10-30 11:54:29.494117
279	268	3220034072003.0	\N	\N	f	2025-10-30 11:54:29.494117
280	269	3258561140599.0	\N	\N	f	2025-10-30 11:54:29.494117
281	270	3439495112900.0	\N	\N	f	2025-10-30 11:54:29.494117
282	271	40345192.0	\N	\N	f	2025-10-30 11:54:29.494117
283	272	5449000286291.0	\N	\N	f	2025-10-30 11:54:29.494117
284	272	5449000227966.0	\N	\N	f	2025-10-30 11:54:29.494117
285	272	5449000214775.0	\N	\N	f	2025-10-30 11:54:29.494117
286	272	5449000286314.0	\N	\N	f	2025-10-30 11:54:29.494117
287	273	3665676000869.0	\N	\N	f	2025-10-30 11:54:29.494117
288	274	5000112557695.0	\N	\N	f	2025-10-30 11:54:29.494117
289	275	5449000006288.0	\N	\N	f	2025-10-30 11:54:29.494117
290	276	5449000099976.0	\N	\N	f	2025-10-30 11:54:29.494117
291	277	3513083900008.0	\N	\N	f	2025-10-30 11:54:29.494117
292	278	3760105892142.0	\N	\N	f	2025-10-30 11:54:29.494117
293	279	3165950218695.0	\N	\N	f	2025-10-30 11:54:29.494117
294	280	5011157630274.0	\N	\N	f	2025-10-30 11:54:29.494117
295	281	3700019511180.0	\N	\N	f	2025-10-30 11:54:29.494117
296	282	3760020063191.0	\N	\N	f	2025-10-30 11:54:29.494117
297	283	5449000294746.0	\N	\N	f	2025-10-30 11:54:29.494117
298	284	3175529632302.0	\N	\N	f	2025-10-30 11:54:29.494117
299	285	8719689681104.0	\N	\N	f	2025-10-30 11:54:29.494117
300	286	8411831000572.0	\N	\N	f	2025-10-30 11:54:29.494117
301	287	3760224900018.0	\N	\N	f	2025-10-30 11:54:29.494117
302	288	4750021000065.0	\N	\N	f	2025-10-30 11:54:29.494117
303	289	3527904420224.0	\N	\N	f	2025-10-30 11:54:29.494117
304	290	3760197940783.0	\N	\N	f	2025-10-30 11:54:29.494117
305	291	3760197947799.0	\N	\N	f	2025-10-30 11:54:29.494117
306	292	5010752000307.0	\N	\N	f	2025-10-30 11:54:29.494117
307	293	3107872006523.0	\N	\N	f	2025-10-30 11:54:29.494117
308	294	3107872000507.0	\N	\N	f	2025-10-30 11:54:29.494117
309	295	5900685006197.0	\N	\N	f	2025-10-30 11:54:29.494117
310	296	8710581916028.0	\N	\N	f	2025-10-30 11:54:29.494117
311	297	5425021580495	\N	\N	f	2025-10-30 12:05:49.521322
312	298	3220036870003	\N	\N	f	2025-10-30 12:05:49.521322
313	299	3439495204087	\N	\N	f	2025-10-30 12:05:49.521322
314	300	3528960006599	\N	\N	f	2025-10-30 12:05:49.521322
315	301	3660407045591	\N	\N	f	2025-10-30 12:05:49.521322
316	302	4337182242567	\N	\N	f	2025-10-30 12:05:49.521322
317	303	3760151050565	\N	\N	f	2025-10-30 12:05:49.521322
318	304	4006133246434	\N	\N	f	2025-10-30 12:05:49.521322
319	305	3573972112905	\N	\N	f	2025-10-30 12:05:49.521322
320	306	4337182210054	\N	\N	f	2025-10-30 12:05:49.521322
321	307	4337182222545	\N	\N	f	2025-10-30 12:05:49.521322
322	308	4337182222484	\N	\N	f	2025-10-30 12:05:49.521322
323	309	8410087366258	\N	\N	f	2025-10-30 12:06:22.270134
324	310	3760387550730	\N	\N	f	2025-10-30 12:06:22.270134
325	311	3760298920004	\N	\N	f	2025-10-30 12:06:22.270134
326	312	3439496513850	\N	\N	f	2025-10-30 12:06:22.270134
327	313	4337125000087	\N	\N	f	2025-10-30 12:06:22.270134
328	314	3660131205179	\N	\N	f	2025-10-30 12:06:22.270134
329	315	5010327325125	\N	\N	f	2025-10-30 12:06:46.790014
330	316	3211200184743	\N	\N	f	2025-10-30 12:06:46.790014
331	317	3439495507928	\N	\N	f	2025-10-30 12:06:46.790014
332	318	3259356633067	\N	\N	f	2025-10-30 12:06:46.790014
333	319	4017773301148	\N	\N	f	2025-10-30 12:06:46.790014
334	320	5410228203582	\N	\N	f	2025-10-30 12:06:46.790014
335	321	3155930400530	\N	\N	f	2025-10-30 12:06:46.790014
336	322	3119783016690	\N	\N	f	2025-10-30 12:06:46.790014
337	323	03124488193904	\N	\N	f	2025-10-30 12:06:46.790014
338	324	3124488194741	\N	\N	f	2025-10-30 12:06:46.790014
339	325	5449000214942	\N	\N	f	2025-10-30 12:06:46.790014
340	326	3168930159841	\N	\N	f	2025-10-30 12:06:46.790014
341	327	3295921504202	\N	\N	f	2025-10-30 12:06:46.790014
342	328	3295921144200	\N	\N	f	2025-10-30 12:06:46.790014
343	329	04008400264004	\N	\N	f	2025-10-30 12:06:46.790014
344	330	5000159555722	\N	\N	f	2025-10-30 12:06:46.790014
345	331	5000159461801	\N	\N	f	2025-10-30 12:06:46.790014
346	332	5000159561679	\N	\N	f	2025-10-30 12:06:46.790014
347	333	3185110012673	\N	\N	f	2025-10-30 12:06:46.790014
348	334	3281130011181	\N	\N	f	2025-10-30 12:06:46.790014
349	335	3439497015285	\N	\N	f	2025-10-30 12:06:46.790014
350	336	8445290872036	\N	\N	f	2025-10-30 12:06:46.790014
351	337	3329770048690	\N	\N	f	2025-10-30 12:06:46.790014
352	338	3329770048676	\N	\N	f	2025-10-30 12:06:46.790014
353	339	3329770063273	\N	\N	f	2025-10-30 12:06:46.790014
354	340	3329770063280	\N	\N	f	2025-10-30 12:06:46.790014
355	341	3033491974212	\N	\N	f	2025-10-30 12:06:46.790014
356	342	3033491974175	\N	\N	f	2025-10-30 12:06:46.790014
357	343	3439496002323	\N	\N	f	2025-10-30 12:06:46.790014
358	344	3587222521508	\N	\N	f	2025-10-30 12:06:46.790014
359	345	3439496604015	\N	\N	f	2025-10-30 12:06:46.790014
360	346	3439496603995	\N	\N	f	2025-10-30 12:06:46.790014
361	347	3439496604008	\N	\N	f	2025-10-30 12:06:46.790014
362	348	4337182142485	\N	\N	f	2025-10-30 12:06:46.790014
363	349	3760261148305	\N	\N	f	2025-10-30 12:06:46.790014
364	350	3701479402162	\N	\N	f	2025-10-30 12:06:46.790014
365	351	3439496821689	\N	\N	f	2025-10-30 12:06:46.790014
366	352	3119783018823	\N	\N	f	2025-10-30 12:07:11.398554
367	353	3103220035559	\N	\N	f	2025-10-30 12:07:11.398554
368	354	5410228223580	\N	\N	f	2025-10-30 12:07:45.054577
369	355	3439496010304	\N	\N	f	2025-10-30 12:07:45.054577
370	356	3439496607221	\N	\N	f	2025-10-30 12:07:45.054577
371	357	3439496000657	\N	\N	f	2025-10-30 12:07:45.054577
372	358	4337182249283	\N	\N	f	2025-10-30 12:07:45.054577
373	359	4337182249290	\N	\N	f	2025-10-30 12:07:45.054577
374	360	4337182219897	\N	\N	f	2025-10-30 12:07:45.054577
375	361	3439496810997	\N	\N	f	2025-10-30 12:07:45.054577
376	310	3770015716223	\N	\N	f	2025-10-30 12:08:00.448408
377	362	4337182219835	\N	\N	f	2025-10-30 12:08:00.448408
378	363	3378927661459	\N	\N	f	2025-10-30 12:08:00.448408
379	364	4337182219798	\N	\N	f	2025-10-30 12:08:00.448408
380	365	3147697510607	\N	\N	f	2025-10-30 12:08:25.252336
381	366	3257150100228	\N	\N	f	2025-10-30 12:08:25.252336
382	367	3175529657725	\N	\N	f	2025-10-30 12:08:25.252336
383	368	3259354102060	\N	\N	f	2025-10-30 12:08:25.252336
384	369	03179077103147	\N	\N	f	2025-10-30 12:08:25.252336
385	370	03179077103154	\N	\N	f	2025-10-30 12:08:25.252336
386	371	3439495600360	\N	\N	f	2025-10-30 12:08:25.252336
387	372	3080210003425	\N	\N	f	2025-10-30 12:08:25.252336
388	373	3439495405064	\N	\N	f	2025-10-30 12:08:25.252336
389	374	3439495403794	\N	\N	f	2025-10-30 12:08:25.252336
390	375	3439495405040	\N	\N	f	2025-10-30 12:08:25.252336
391	376	3439495406320	\N	\N	f	2025-10-30 12:08:25.252336
392	377	3439495406368	\N	\N	f	2025-10-30 12:08:25.252336
393	378	5000112557091	\N	\N	f	2025-10-30 12:08:25.252336
394	379	8002270116551	\N	\N	f	2025-10-30 12:08:25.252336
395	380	3179730004804	\N	\N	f	2025-10-30 12:08:25.252336
396	381	3439495111699	\N	\N	f	2025-10-30 12:08:25.252336
397	382	4337182248705	\N	\N	f	2025-10-30 12:08:25.252336
398	383	3281130011129	\N	\N	f	2025-10-30 12:08:25.252336
399	384	3439496303628	\N	\N	f	2025-10-30 12:08:25.252336
400	385	3439496807805	\N	\N	f	2025-10-30 12:08:25.252336
401	386	3439495501568	\N	\N	f	2025-10-30 12:08:39.842775
402	387	3179077103161	\N	\N	f	2025-10-30 12:08:39.842775
403	388	3438935000135	\N	\N	f	2025-10-30 12:08:39.842775
404	389	03439495113495	\N	\N	f	2025-10-30 12:08:39.842775
405	390	03439495112917	\N	\N	f	2025-10-30 12:08:39.842775
406	391	3439495102796	\N	\N	f	2025-10-30 12:08:39.842775
407	392	3168930121961	\N	\N	f	2025-10-30 12:08:39.842775
408	393	3168930104285	\N	\N	f	2025-10-30 12:08:39.842775
409	394	4337182138341	\N	\N	f	2025-10-30 12:08:39.842775
410	395	3430430008678	\N	\N	f	2025-10-30 12:09:02.576379
411	396	3430430008685	\N	\N	f	2025-10-30 12:09:02.576379
412	397	3439495508345	\N	\N	f	2025-10-30 12:09:02.576379
413	398	3211200284900	\N	\N	f	2025-10-30 12:09:02.576379
414	399	3049614222252	\N	\N	f	2025-10-30 12:09:02.576379
415	400	05000267024325	\N	\N	f	2025-10-30 12:09:38.699924
416	401	4337182250159	\N	\N	f	2025-10-30 12:09:38.699924
417	402	5000299225004	\N	\N	f	2025-10-30 12:10:16.733895
418	403	5900685006197	\N	\N	f	2025-10-30 12:10:16.733895
419	404	5410316671118	\N	\N	f	2025-10-30 12:10:16.733895
420	405	8410414000466	\N	\N	f	2025-10-30 12:10:16.733895
421	406	7312040017683	\N	\N	f	2025-10-30 12:10:16.733895
422	407	5901867816498	\N	\N	f	2025-10-30 12:10:16.733895
423	408	3147699102701	\N	\N	f	2025-10-30 12:10:16.733895
424	409	3147690093602	\N	\N	f	2025-10-30 12:10:16.733895
425	410	3147690094708	\N	\N	f	2025-10-30 12:10:16.733895
426	411	3451201439910	\N	\N	f	2025-10-30 12:10:16.733895
427	412	3439495520736	\N	\N	f	2025-10-30 12:10:16.733895
428	413	3447456333011	\N	\N	f	2025-10-30 12:10:16.733895
429	414	13439495521105	\N	\N	f	2025-10-30 12:10:16.733895
430	415	3292350635989	\N	\N	f	2025-10-30 12:10:16.733895
431	416	3439495403824	\N	\N	f	2025-10-30 12:10:16.733895
432	417	3439495405514	\N	\N	f	2025-10-30 12:10:16.733895
433	418	3075711382018	\N	\N	f	2025-10-30 12:10:16.733895
434	419	3439495108811	\N	\N	f	2025-10-30 12:10:16.733895
435	420	08000500121467	\N	\N	f	2025-10-30 12:10:16.733895
436	421	4009900396417	\N	\N	f	2025-10-30 12:10:16.733895
437	422	8723400943907	\N	\N	f	2025-10-30 12:10:16.733895
438	423	4009900017824	\N	\N	f	2025-10-30 12:10:16.733895
439	424	8723400943303	\N	\N	f	2025-10-30 12:10:16.733895
440	425	8723400943204	\N	\N	f	2025-10-30 12:10:16.733895
441	426	8723400943235	\N	\N	f	2025-10-30 12:10:16.733895
442	427	6931722310297	\N	\N	f	2025-10-30 12:10:16.733895
443	428	3587220003525	\N	\N	f	2025-10-30 12:10:16.733895
444	429	3439496623788	\N	\N	f	2025-10-30 12:10:16.733895
445	430	3700133920943	\N	\N	f	2025-10-30 12:10:16.733895
446	431	3378740763996	\N	\N	f	2025-10-30 12:10:16.733895
447	432	3378740764924	\N	\N	f	2025-10-30 12:10:16.733895
448	433	3378740856704	\N	\N	f	2025-10-30 12:10:16.733895
449	434	3378740001623	\N	\N	f	2025-10-30 12:10:16.733895
450	435	2352965012665	\N	\N	f	2025-10-30 12:10:16.733895
451	436	8710438110524	\N	\N	f	2025-10-30 12:10:16.733895
452	437	3760261140354	\N	\N	f	2025-10-30 12:10:16.733895
453	438	3439496807065	\N	\N	f	2025-10-30 12:10:16.733895
454	439	3099873045864	\N	\N	f	2025-10-30 12:10:43.935296
455	440	5000267024325	\N	\N	f	2025-10-30 12:10:43.935296
456	441	3175529665812	\N	\N	f	2025-10-30 12:10:43.935296
457	442	3282946037716	\N	\N	f	2025-10-30 12:10:43.935296
458	443	3124488194734	\N	\N	f	2025-10-30 12:10:43.935296
459	444	3124488151492	\N	\N	f	2025-10-30 12:10:43.935296
460	445	7613035833289	\N	\N	f	2025-10-30 12:10:43.935296
461	446	03174660116702	\N	\N	f	2025-10-30 12:10:43.935296
462	447	5053990164165	\N	\N	f	2025-10-30 12:10:43.935296
463	448	5053990156016	\N	\N	f	2025-10-30 12:10:43.935296
464	449	5053990162710	\N	\N	f	2025-10-30 12:10:43.935296
465	450	5053990155361	\N	\N	f	2025-10-30 12:10:43.935296
466	451	8000500121467	\N	\N	f	2025-10-30 12:10:43.935296
467	452	4337182096870	\N	\N	f	2025-10-30 12:10:43.935296
468	453	5099873089057	\N	\N	f	2025-10-30 12:10:59.277817
469	454	20080432402935	\N	\N	f	2025-10-30 12:10:59.277817
470	455	05000299225332	\N	\N	f	2025-10-30 12:10:59.277817
471	456	05010327248059	\N	\N	f	2025-10-30 12:10:59.277817
472	457	5099873219386	\N	\N	f	2025-10-30 12:10:59.277817
473	458	7312040017355	\N	\N	f	2025-10-30 12:10:59.277817
474	459	5011013100613	\N	\N	f	2025-10-30 12:10:59.277817
475	460	7630040408295	\N	\N	f	2025-10-30 12:10:59.277817
476	461	7630040408639	\N	\N	f	2025-10-30 12:10:59.277817
477	462	7630040408493	\N	\N	f	2025-10-30 12:10:59.277817
478	463	0080432402931	\N	\N	f	2025-10-30 12:11:25.7753
479	464	3760221470026	\N	\N	f	2025-10-30 12:11:25.7753
480	465	5011013100156	\N	\N	f	2025-10-30 12:11:25.7753
481	466	3119780268276	\N	\N	f	2025-10-30 12:11:25.7753
482	467	3490949909033	\N	\N	f	2025-10-30 12:11:25.7753
483	468	0000000031010	\N	\N	f	2025-10-30 12:11:25.7753
484	469	5010494564273	\N	\N	f	2025-10-30 12:11:39.640331
485	470	5000267102573	\N	\N	f	2025-10-30 12:11:39.640331
486	471	5010196111010	\N	\N	f	2025-10-30 12:11:39.640331
487	472	4901903064105	\N	\N	f	2025-10-30 12:11:39.640331
488	473	5010314302863	\N	\N	f	2025-10-30 12:11:39.640331
489	474	5010327325323	\N	\N	f	2025-10-30 12:11:39.640331
490	475	05010327105000	\N	\N	f	2025-10-30 12:11:39.640331
491	476	8001250121240	\N	\N	f	2025-10-30 12:11:39.640331
492	477	3439496827254	\N	\N	f	2025-10-30 12:11:39.640331
493	365	03147691302390	\N	\N	f	2025-10-30 12:11:53.816872
494	478	03119783018847	\N	\N	f	2025-10-30 12:11:53.816872
495	479	9002490205997	\N	\N	f	2025-10-30 12:11:53.816872
496	480	5060335632333	\N	\N	f	2025-10-30 12:11:53.816872
497	481	5449000017673	\N	\N	f	2025-10-30 12:11:53.816872
498	482	8711000705162	\N	\N	f	2025-10-30 12:11:53.816872
499	483	5010103802550	\N	\N	f	2025-10-30 12:15:47.724561
500	484	3211200152551	\N	\N	f	2025-10-30 12:15:47.724561
501	485	3262151637079	\N	\N	f	2025-10-30 12:15:47.724561
502	486	8850389112816	\N	\N	f	2025-10-30 12:15:47.724561
503	487	8850389115374	\N	\N	f	2025-10-30 12:15:47.724561
504	488	3439495407310	\N	\N	f	2025-10-30 12:15:47.724561
505	489	3439497020357	\N	\N	f	2025-10-30 12:15:47.724561
506	490	05053990107476	\N	\N	f	2025-10-30 12:15:47.724561
507	491	05053990107629	\N	\N	f	2025-10-30 12:15:47.724561
508	492	05053990161614	\N	\N	f	2025-10-30 12:15:47.724561
509	493	3439496500768	\N	\N	f	2025-10-30 12:15:47.724561
510	494	3439496823850	\N	\N	f	2025-10-30 12:15:47.724561
511	306	4337182022015	\N	\N	f	2025-10-30 12:15:47.724561
512	495	3281513541618	\N	\N	f	2025-10-30 12:15:47.724561
513	496	3119780268382	\N	\N	f	2025-10-30 12:16:27.234871
514	497	3211200196883	\N	\N	f	2025-10-30 12:16:40.566579
515	498	5000213003756	\N	\N	f	2025-10-30 12:16:40.566579
516	499	8850389110515	\N	\N	f	2025-10-30 12:16:40.566579
517	500	3439495011388	\N	\N	f	2025-10-30 12:16:40.566579
518	501	3276650013203	\N	\N	f	2025-10-30 12:16:40.566579
519	502	3439495107906	\N	\N	f	2025-10-30 12:16:40.566579
520	503	8715700120065	\N	\N	f	2025-10-30 12:16:40.566579
521	360	4337182057321	\N	\N	f	2025-10-30 12:16:40.566579
522	504	3439496802879	\N	\N	f	2025-10-30 12:17:42.01398
523	505	3439496802862	\N	\N	f	2025-10-30 12:17:42.01398
524	306	3439496810003	\N	\N	f	2025-10-30 12:17:42.01398
525	506	5410508209525	\N	\N	f	2025-10-30 12:17:42.01398
526	507	3296280045559	\N	\N	f	2025-10-30 12:17:42.01398
527	508	4337182096900	\N	\N	f	2025-10-30 12:17:42.01398
528	509	3439495401448	\N	\N	f	2025-10-30 12:18:04.059187
529	510	3176484042434	\N	\N	f	2025-10-30 12:18:34.198825
530	511	3439499001736	\N	\N	f	2025-10-30 12:18:34.198825
531	512	3438935000128	\N	\N	f	2025-10-30 12:18:34.198825
532	513	5601164900349	\N	\N	f	2025-10-30 12:18:34.198825
533	514	0054308184412	\N	\N	f	2025-10-30 12:18:34.198825
534	515	3254382048342	\N	\N	f	2025-10-30 12:18:34.198825
535	516	13077311522068	\N	\N	f	2025-10-30 12:18:34.198825
536	517	8000500073698	\N	\N	f	2025-10-30 12:18:34.198825
537	518	04008400223612	\N	\N	f	2025-10-30 12:18:34.198825
538	519	5000159419383	\N	\N	f	2025-10-30 12:18:34.198825
539	520	5000159418553	\N	\N	f	2025-10-30 12:18:34.198825
540	521	4009900522113	\N	\N	f	2025-10-30 12:18:34.198825
541	522	3439496603513	\N	\N	f	2025-10-30 12:18:34.198825
542	523	3439496603506	\N	\N	f	2025-10-30 12:18:34.198825
543	524	3439496622323	\N	\N	f	2025-10-30 12:18:34.198825
544	525	3439496620626	\N	\N	f	2025-10-30 12:18:34.198825
545	526	3587220005130	\N	\N	f	2025-10-30 12:18:34.198825
546	527	4337182138075	\N	\N	f	2025-10-30 12:18:34.198825
547	528	3439496506258	\N	\N	f	2025-10-30 12:19:18.313605
548	529	3434030033627	\N	\N	f	2025-10-30 12:19:57.146464
549	530	03119783018243	\N	\N	f	2025-10-30 12:20:16.389747
550	531	8714800038676	\N	\N	f	2025-10-30 12:20:16.389747
551	532	5449000002921	\N	\N	f	2025-10-30 12:20:16.389747
552	533	5000159461139	\N	\N	f	2025-10-30 12:20:16.389747
553	534	7622210741578	\N	\N	f	2025-10-30 12:20:16.389747
554	535	5000159304238	\N	\N	f	2025-10-30 12:20:16.389747
555	536	7613039047415	\N	\N	f	2025-10-30 12:20:16.389747
556	537	3103220020807	\N	\N	f	2025-10-30 12:20:16.389747
557	538	3439495207354	\N	\N	f	2025-10-30 12:20:16.389747
558	539	3103220035467	\N	\N	f	2025-10-30 12:20:16.389747
559	540	3664346305815	\N	\N	f	2025-10-30 12:20:16.389747
560	541	3664346305846	\N	\N	f	2025-10-30 12:20:16.389747
561	542	3664346305686	\N	\N	f	2025-10-30 12:20:16.389747
562	543	3103220036471	\N	\N	f	2025-10-30 12:20:16.389747
563	544	8710800955555	\N	\N	f	2025-10-30 12:20:16.389747
564	545	3014680059071	\N	\N	f	2025-10-30 12:20:16.389747
565	546	3103228625332	\N	\N	f	2025-10-30 12:20:16.389747
566	547	8724900500881	\N	\N	f	2025-10-30 12:20:16.389747
567	548	3103228030457	\N	\N	f	2025-10-30 12:20:16.389747
568	549	3103228037722	\N	\N	f	2025-10-30 12:20:16.389747
569	550	8436036186265	\N	\N	f	2025-10-30 12:20:16.389747
570	551	3439496622590	\N	\N	f	2025-10-30 12:20:16.389747
571	552	3439496605272	\N	\N	f	2025-10-30 12:20:16.389747
572	553	3587220002313	\N	\N	f	2025-10-30 12:20:16.389747
573	554	3439496603797	\N	\N	f	2025-10-30 12:20:16.389747
574	555	3760049795646	\N	\N	f	2025-10-30 12:20:16.389747
575	556	3573972500504	\N	\N	f	2025-10-30 12:20:16.389747
576	364	4337182057208	\N	\N	f	2025-10-30 12:20:16.389747
577	557	3439496806365	\N	\N	f	2025-10-30 12:20:16.389747
578	558	3439497020371	\N	\N	f	2025-10-30 12:20:31.953437
579	559	3288360005591	\N	\N	f	2025-10-30 12:20:31.953437
580	560	3107872000507	\N	\N	f	2025-10-30 12:23:12.672006
581	561	05099873123454	\N	\N	f	2025-10-30 12:23:12.672006
582	562	3147690094104	\N	\N	f	2025-10-30 12:23:12.672006
583	563	05010103236041	\N	\N	f	2025-10-30 12:23:12.672006
584	564	05099873120422	\N	\N	f	2025-10-30 12:23:12.672006
585	565	05010327250021	\N	\N	f	2025-10-30 12:23:12.672006
586	566	5000299297353	\N	\N	f	2025-10-30 12:23:12.672006
587	461	3011932000829	\N	\N	f	2025-10-30 12:23:12.672006
588	567	3011932000843	\N	\N	f	2025-10-30 12:23:12.672006
589	462	3011932000805	\N	\N	f	2025-10-30 12:23:12.672006
590	568	3251091501038	\N	\N	f	2025-10-30 12:23:12.672006
591	569	3439495507638	\N	\N	f	2025-10-30 12:23:12.672006
592	570	3439499000920	\N	\N	f	2025-10-30 12:23:12.672006
593	571	3049614033872	\N	\N	f	2025-10-30 12:23:12.672006
594	572	3017760111805	\N	\N	f	2025-10-30 12:23:12.672006
595	573	7613037928532	\N	\N	f	2025-10-30 12:23:12.672006
596	574	8420499102801	\N	\N	f	2025-10-30 12:23:12.672006
597	575	3166720014998	\N	\N	f	2025-10-30 12:23:12.672006
598	576	3439496800882	\N	\N	f	2025-10-30 12:23:12.672006
599	577	3760123280952	\N	\N	f	2025-10-30 12:23:32.662946
600	372	3080213000759	\N	\N	f	2025-10-30 12:23:32.662946
601	578	3378920010285	\N	\N	f	2025-10-30 12:23:32.662946
602	360	4337182004981	\N	\N	f	2025-10-30 12:23:32.662946
603	579	8718951542938	\N	\N	f	2025-10-30 12:23:32.662946
604	580	3211209139232	\N	\N	f	2025-10-30 12:23:54.959145
605	581	3522091156000	\N	\N	f	2025-10-30 12:23:54.959145
606	582	3012991301001	\N	\N	f	2025-10-30 12:24:14.204165
607	583	3211200044801	\N	\N	f	2025-10-30 12:24:14.204165
608	584	3175529644848	\N	\N	f	2025-10-30 12:24:14.204165
609	585	3760255776002	\N	\N	f	2025-10-30 12:24:14.204165
610	586	03258690006094	\N	\N	f	2025-10-30 12:24:14.204165
611	587	3286171703125	\N	\N	f	2025-10-30 12:24:14.204165
612	588	3430430007343	\N	\N	f	2025-10-30 12:24:14.204165
613	589	3760050843015	\N	\N	f	2025-10-30 12:24:14.204165
614	590	03179077103161	\N	\N	f	2025-10-30 12:24:14.204165
615	591	03119783012012	\N	\N	f	2025-10-30 12:24:14.204165
616	592	5000112617979	\N	\N	f	2025-10-30 12:24:14.204165
617	593	05449000089120	\N	\N	f	2025-10-30 12:24:14.204165
618	532	05449000002921	\N	\N	f	2025-10-30 12:24:14.204165
619	594	3124488194659	\N	\N	f	2025-10-30 12:24:14.204165
620	595	3124488195168	\N	\N	f	2025-10-30 12:24:14.204165
621	596	03179730004804	\N	\N	f	2025-10-30 12:24:14.204165
622	477	3439496809939	\N	\N	f	2025-10-30 12:24:14.204165
623	597	3522091155102	\N	\N	f	2025-10-30 12:24:14.204165
624	365	3147699102671	\N	\N	f	2025-10-30 12:24:35.062022
625	598	3011938000403	\N	\N	f	2025-10-30 12:24:35.062022
626	599	7610113019214	\N	\N	f	2025-10-30 12:24:35.062022
627	600	3185370374733	\N	\N	f	2025-10-30 12:24:35.062022
628	601	3166720012659	\N	\N	f	2025-10-30 12:24:35.062022
629	602	3166720026007	\N	\N	f	2025-10-30 12:24:35.062022
630	603	5000299610688	\N	\N	f	2025-10-30 12:30:02.473798
631	604	5901041003430	\N	\N	f	2025-10-30 12:30:02.473798
632	605	3292054430019	\N	\N	f	2025-10-30 12:30:02.473798
633	606	03119783017901	\N	\N	f	2025-10-30 12:30:02.473798
634	607	3124488186852	\N	\N	f	2025-10-30 12:30:02.473798
635	608	23142951144011	\N	\N	f	2025-10-30 12:30:02.473798
636	609	08005110060021	\N	\N	f	2025-10-30 12:30:02.473798
637	610	8437003623554	\N	\N	f	2025-10-30 12:30:02.473798
638	390	3439497006849	\N	\N	f	2025-10-30 12:30:02.473798
639	611	3168930140825	\N	\N	f	2025-10-30 12:30:02.473798
640	612	3439496808222	\N	\N	f	2025-10-30 12:30:02.473798
641	613	3439495005530	\N	\N	f	2025-10-30 12:30:14.808307
642	610	18437003623551	\N	\N	f	2025-10-30 12:30:14.808307
643	614	3664346305808	\N	\N	f	2025-10-30 12:31:31.948532
644	615	05010327325125	\N	\N	f	2025-10-30 12:32:17.747406
645	616	3439495005523	\N	\N	f	2025-10-30 12:32:17.747406
646	617	4337182153580	\N	\N	f	2025-10-30 12:32:17.747406
647	618	3346024708605	\N	\N	f	2025-10-30 12:32:17.747406
648	619	60060313500	\N	\N	f	2025-10-30 13:05:40.667214
649	620	3245990250203	\N	\N	f	2025-10-30 13:08:21.170149
650	621	3439495304213	\N	\N	f	2025-10-30 13:08:21.170149
651	622	3163937016005	\N	\N	f	2025-10-30 13:08:21.170149
652	623	3450301173403	\N	\N	f	2025-10-30 13:08:21.170149
653	624	3439495121933	\N	\N	f	2025-10-30 13:08:21.170149
654	625	3439495121957	\N	\N	f	2025-10-30 13:08:21.170149
655	626	3439495121926	\N	\N	f	2025-10-30 13:08:21.170149
656	627	3439495110159	\N	\N	f	2025-10-30 13:08:21.170149
657	628	3439495113051	\N	\N	f	2025-10-30 13:08:21.170149
658	629	3439495113174	\N	\N	f	2025-10-30 13:08:21.170149
659	630	3439495125887	\N	\N	f	2025-10-30 13:08:21.170149
660	631	3439496607283	\N	\N	f	2025-10-30 13:08:21.170149
661	632	3439496607313	\N	\N	f	2025-10-30 13:08:21.170149
662	633	3439496824116	\N	\N	f	2025-10-30 13:08:21.170149
663	306	4337182021858	\N	\N	f	2025-10-30 13:08:21.170149
664	634	5000267024202	\N	\N	f	2025-10-30 13:08:54.596243
665	635	8000040000802	\N	\N	f	2025-10-30 13:08:54.596243
666	636	03262151637079	\N	\N	f	2025-10-30 13:08:54.596243
667	637	03179072001141	\N	\N	f	2025-10-30 13:08:54.596243
668	638	3262151791078	\N	\N	f	2025-10-30 13:08:54.596243
669	639	03438935000128	\N	\N	f	2025-10-30 13:08:54.596243
670	640	3439495407846	\N	\N	f	2025-10-30 13:08:54.596243
671	641	3124488196264	\N	\N	f	2025-10-30 13:08:54.596243
672	642	5449000098887	\N	\N	f	2025-10-30 13:08:54.596243
673	643	7613035946439	\N	\N	f	2025-10-30 13:08:54.596243
674	644	7613032910501	\N	\N	f	2025-10-30 13:08:54.596243
675	645	7622210991140	\N	\N	f	2025-10-30 13:08:54.596243
676	646	7622210990891	\N	\N	f	2025-10-30 13:08:54.596243
677	647	3439497021217	\N	\N	f	2025-10-30 13:08:54.596243
678	648	5000159516273	\N	\N	f	2025-10-30 13:08:54.596243
679	649	7622210439994	\N	\N	f	2025-10-30 13:08:54.596243
680	650	7613035449176	\N	\N	f	2025-10-30 13:08:54.596243
681	651	7613035958425	\N	\N	f	2025-10-30 13:08:54.596243
682	652	8724900260341	\N	\N	f	2025-10-30 13:08:54.596243
683	653	4009900456623	\N	\N	f	2025-10-30 13:08:54.596243
684	654	3439496824154	\N	\N	f	2025-10-30 13:08:54.596243
685	655	3179077103147	\N	\N	f	2025-10-30 13:09:19.982452
686	656	4337182087878	\N	\N	f	2025-10-30 13:10:43.512798
687	657	3661419217242	\N	\N	f	2025-10-30 13:10:55.050915
688	658	3261570002109	\N	\N	f	2025-10-30 13:10:55.050915
689	659	3439496810942	\N	\N	f	2025-10-30 13:10:55.050915
690	660	3262156015148	\N	\N	f	2025-10-30 13:27:52.525104
691	661	3430430008029	\N	\N	f	2025-10-30 13:27:52.525104
692	662	5449000181596	\N	\N	f	2025-10-30 13:27:52.525104
693	663	4820078571051	\N	\N	f	2025-10-30 13:27:52.525104
694	664	7622210122698	\N	\N	f	2025-10-30 13:27:52.525104
695	665	3412290028355	\N	\N	f	2025-10-30 13:27:52.525104
696	666	3459860001103	\N	\N	f	2025-10-30 13:27:52.525104
697	667	3660071100022	\N	\N	f	2025-10-30 13:27:52.525104
698	668	4337182138082	\N	\N	f	2025-10-30 13:27:52.525104
699	669	3166720015001	\N	\N	f	2025-10-30 13:27:52.525104
700	670	3166720028568	\N	\N	f	2025-10-30 13:27:52.525104
701	671	3332930010789	\N	\N	f	2025-10-30 13:28:09.868901
702	672	03119783018823	\N	\N	f	2025-10-30 13:28:28.855834
703	673	3249778011093	\N	\N	f	2025-10-30 13:28:28.855834
704	674	5449000214874	\N	\N	f	2025-10-30 13:28:28.855834
705	675	05449000017673	\N	\N	f	2025-10-30 13:28:28.855834
706	676	5449000267498	\N	\N	f	2025-10-30 13:28:28.855834
707	677	3068320011837	\N	\N	f	2025-10-30 13:28:28.855834
708	372	3080216054278	\N	\N	f	2025-10-30 13:28:44.005424
709	678	3439495022209	\N	\N	f	2025-10-30 13:28:44.005424
710	679	3439496811062	\N	\N	f	2025-10-30 13:28:44.005424
711	680	3059942033482	\N	\N	f	2025-10-30 13:28:44.005424
712	681	3482050181002	\N	\N	f	2025-10-30 13:28:58.358722
713	682	03439495112122	\N	\N	f	2025-10-30 13:28:58.358722
714	683	03439495112139	\N	\N	f	2025-10-30 13:28:58.358722
715	684	03439495010985	\N	\N	f	2025-10-30 13:28:58.358722
716	685	3252378001326	\N	\N	f	2025-10-30 13:28:58.358722
717	686	3422800000344	\N	\N	f	2025-10-30 13:28:58.358722
718	449	05053990162710	\N	\N	f	2025-10-30 13:28:58.358722
719	687	3342690021604	\N	\N	f	2025-10-30 13:28:58.358722
720	688	3439496810461	\N	\N	f	2025-10-30 13:28:58.358722
721	689	3439496810485	\N	\N	f	2025-10-30 13:28:58.358722
722	690	3439496821399	\N	\N	f	2025-10-30 13:28:58.358722
723	691	3288360005676	\N	\N	f	2025-10-30 13:28:58.358722
724	692	7613034579959	\N	\N	f	2025-10-30 13:29:29.50403
725	693	4337182170112	\N	\N	f	2025-10-30 13:29:29.50403
726	390	03165720000246	\N	\N	f	2025-10-30 13:29:29.50403
727	306	4337182021896	\N	\N	f	2025-10-30 13:29:29.50403
728	694	3281517470617	\N	\N	f	2025-10-30 13:29:29.50403
729	695	5410508209419	\N	\N	f	2025-10-30 13:29:29.50403
730	696	4260325421898	\N	\N	f	2025-10-30 13:30:29.970994
731	697	27312040017359	\N	\N	f	2025-10-30 13:31:16.814255
732	698	7501064191459	\N	\N	f	2025-10-30 13:31:16.814255
733	699	4000177158326	\N	\N	f	2025-10-30 13:31:16.814255
734	700	5000112639995	\N	\N	f	2025-10-30 13:31:16.814255
735	701	05000112557091	\N	\N	f	2025-10-30 13:31:16.814255
736	702	05410228233022	\N	\N	f	2025-10-30 13:35:24.289083
737	703	5410228280545	\N	\N	f	2025-10-30 13:35:24.289083
738	704	3760154422185	\N	\N	f	2025-10-30 13:35:24.289083
739	705	3049610004104	\N	\N	f	2025-10-30 13:35:24.289083
740	706	5410228212805	\N	\N	f	2025-10-30 13:35:24.289083
741	707	7613037935080	\N	\N	f	2025-10-30 13:35:24.289083
742	708	3130632066208	\N	\N	f	2025-10-30 13:35:24.289083
743	709	3166720012642	\N	\N	f	2025-10-30 13:35:24.289083
744	710	05000267024240	\N	\N	f	2025-10-30 13:35:24.289083
745	711	3147690060703	\N	\N	f	2025-10-30 13:35:24.289083
746	712	3255537506045	\N	\N	f	2025-10-30 13:35:24.289083
747	713	7630040401357	\N	\N	f	2025-10-30 13:35:24.289083
748	586	3258690006094	\N	\N	f	2025-10-30 13:35:24.289083
749	714	3430430007817	\N	\N	f	2025-10-30 13:35:24.289083
750	715	3760113521416	\N	\N	f	2025-10-30 13:35:24.289083
751	716	3439495507522	\N	\N	f	2025-10-30 13:35:24.289083
752	717	3439495401233	\N	\N	f	2025-10-30 13:35:24.289083
753	593	5449000089120	\N	\N	f	2025-10-30 13:35:24.289083
754	718	3439496820064	\N	\N	f	2025-10-30 13:35:24.289083
755	719	5410555073810	\N	\N	f	2025-10-30 13:35:24.289083
756	720	3019920567002	\N	\N	f	2025-10-30 13:35:24.289083
757	721	3275560101550	\N	\N	f	2025-10-30 13:35:24.289083
758	722	3439496820125	\N	\N	f	2025-10-30 13:35:24.289083
759	723	3258690014075	\N	\N	f	2025-10-30 13:35:24.289083
760	306	4337182021919	\N	\N	f	2025-10-30 13:35:24.289083
761	718	3439496820088	\N	\N	f	2025-10-30 13:35:24.289083
762	724	3342690043309	\N	\N	f	2025-10-30 13:35:24.289083
763	725	3522091161448	\N	\N	f	2025-10-30 13:35:24.289083
764	726	3439496804453	\N	\N	f	2025-10-30 13:35:24.289083
765	727	3542950000077	\N	\N	f	2025-10-30 13:35:24.289083
766	728	3439495405088	\N	\N	f	2025-10-30 13:35:24.289083
767	729	3439495405453	\N	\N	f	2025-10-30 13:35:24.289083
768	730	5000112511987	\N	\N	f	2025-10-30 13:35:24.289083
769	731	3124488195212	\N	\N	f	2025-10-30 13:35:24.289083
770	732	3179732340412	\N	\N	f	2025-10-30 13:35:24.289083
771	733	5700626121305	\N	\N	f	2025-10-30 13:35:24.289083
772	734	4009900500616	\N	\N	f	2025-10-30 13:35:24.289083
773	735	8410805060017	\N	\N	f	2025-10-30 13:35:24.289083
774	736	3587361157156	\N	\N	f	2025-10-30 13:35:24.289083
775	737	7622210721686	\N	\N	f	2025-10-30 13:35:24.289083
776	738	7622210721723	\N	\N	f	2025-10-30 13:35:24.289083
777	739	8713763564918	\N	\N	f	2025-10-30 13:35:24.289083
778	740	3281510034557	\N	\N	f	2025-10-30 13:35:24.289083
779	741	3439494400640	\N	\N	f	2025-10-30 13:35:24.289083
780	742	3483080006327	\N	\N	f	2025-10-30 13:35:24.289083
781	743	3439495501407	\N	\N	f	2025-10-30 13:35:24.289083
782	744	4337147752902	\N	\N	f	2025-10-30 13:35:24.289083
783	745	3124488194710	\N	\N	f	2025-10-30 13:35:24.289083
784	746	5000267116662	\N	\N	f	2025-10-30 13:37:59.565036
785	747	3439495111880	\N	\N	f	2025-10-30 13:37:59.565036
786	748	3270720021631	\N	\N	f	2025-10-30 13:37:59.565036
787	749	3439496809991	\N	\N	f	2025-10-30 13:37:59.565036
788	750	5449000214928	\N	\N	f	2025-10-30 13:37:59.565036
789	751	8423243004581	\N	\N	f	2025-10-30 13:37:59.565036
790	752	3434030025400	\N	\N	f	2025-10-30 13:37:59.565036
791	753	3434030032521	\N	\N	f	2025-10-30 13:37:59.565036
792	754	3439496822600	\N	\N	f	2025-10-30 13:37:59.565036
793	755	3211200153589	\N	\N	f	2025-10-30 13:37:59.565036
794	756	3439495202939	\N	\N	f	2025-10-30 13:37:59.565036
795	757	3147699118368	\N	\N	f	2025-10-30 13:37:59.565036
796	462	3011932000904	\N	\N	f	2025-10-30 13:37:59.565036
797	758	3192370092000	\N	\N	f	2025-10-30 13:37:59.565036
798	759	3439495404784	\N	\N	f	2025-10-30 13:37:59.565036
799	760	3439495400533	\N	\N	f	2025-10-30 13:37:59.565036
800	761	3535031166106	\N	\N	f	2025-10-30 13:37:59.565036
801	761	3535031166045	\N	\N	f	2025-10-30 13:37:59.565036
802	762	3439496820668	\N	\N	f	2025-10-30 13:37:59.565036
803	763	3346024784982	\N	\N	f	2025-10-30 13:37:59.565036
804	764	3288360000022	\N	\N	f	2025-10-30 13:37:59.565036
805	765	3428272950064	\N	\N	f	2025-10-30 13:37:59.565036
806	723	03258690014075	\N	\N	f	2025-10-30 13:37:59.565036
807	766	4337182051855	\N	\N	f	2025-10-30 13:37:59.565036
808	767	3361670900371	\N	\N	f	2025-10-30 13:37:59.565036
809	768	05099873119143	\N	\N	f	2025-10-30 13:37:59.565036
810	769	3760123281461	\N	\N	f	2025-10-30 13:37:59.565036
811	770	3119780259106	\N	\N	f	2025-10-30 13:37:59.565036
812	771	3439495402810	\N	\N	f	2025-10-30 13:37:59.565036
813	772	3439495405026	\N	\N	f	2025-10-30 13:37:59.565036
814	773	3439495400281	\N	\N	f	2025-10-30 13:37:59.565036
815	774	5425032881833	\N	\N	f	2025-10-30 13:37:59.565036
816	775	3265478167007	\N	\N	f	2025-10-30 13:37:59.565036
817	776	3038351887107	\N	\N	f	2025-10-30 13:37:59.565036
818	777	3439495106299	\N	\N	f	2025-10-30 13:37:59.565036
819	778	3185370687598	\N	\N	f	2025-10-30 13:37:59.565036
820	779	3460270056768	\N	\N	f	2025-10-30 13:37:59.565036
821	780	3439495500813	\N	\N	f	2025-10-30 13:37:59.565036
822	781	3439499001484	\N	\N	f	2025-10-30 13:37:59.565036
823	782	3185370283905	\N	\N	f	2025-10-30 13:37:59.565036
824	783	03119783016690	\N	\N	f	2025-10-30 13:37:59.565036
825	784	3770007850744	\N	\N	f	2025-10-30 13:37:59.565036
826	785	3439495406535	\N	\N	f	2025-10-30 13:37:59.565036
827	786	3099873045369	\N	\N	f	2025-10-30 13:37:59.565036
828	787	3595531012501	\N	\N	f	2025-10-30 13:37:59.565036
829	788	3439495405408	\N	\N	f	2025-10-30 13:37:59.565036
830	789	3439495405125	\N	\N	f	2025-10-30 13:37:59.565036
831	790	3439495405576	\N	\N	f	2025-10-30 13:37:59.565036
832	791	3249778013462	\N	\N	f	2025-10-30 13:37:59.565036
833	792	05099873127360	\N	\N	f	2025-10-30 13:37:59.565036
834	793	5010103800457	\N	\N	f	2025-10-30 13:37:59.565036
835	365	3147690059004	\N	\N	f	2025-10-30 13:37:59.565036
836	794	3439495508093	\N	\N	f	2025-10-30 13:37:59.565036
837	795	3450301167655	\N	\N	f	2025-10-30 13:37:59.565036
838	796	3439497009291	\N	\N	f	2025-10-30 13:37:59.565036
839	797	3439495120493	\N	\N	f	2025-10-30 13:37:59.565036
840	798	3439495120318	\N	\N	f	2025-10-30 13:37:59.565036
841	799	3439495120400	\N	\N	f	2025-10-30 13:37:59.565036
842	800	3439495900163	\N	\N	f	2025-10-30 13:37:59.565036
843	801	3700541522142	\N	\N	f	2025-10-30 13:37:59.565036
844	802	3251091518265	\N	\N	f	2025-10-30 13:37:59.565036
845	803	3255611153110	\N	\N	f	2025-10-30 13:37:59.565036
846	786	05099873124543	\N	\N	f	2025-10-30 13:37:59.565036
847	804	3342690043279	\N	\N	f	2025-10-30 13:37:59.565036
848	805	3276650111022	\N	\N	f	2025-10-30 13:37:59.565036
849	806	3428200302392	\N	\N	f	2025-10-30 13:37:59.565036
850	807	3439496310299	\N	\N	f	2025-10-30 13:37:59.565036
851	306	4337182021834	\N	\N	f	2025-10-30 13:37:59.565036
852	808	4337182039211	\N	\N	f	2025-10-30 13:37:59.565036
853	809	3434030032071	\N	\N	f	2025-10-30 13:37:59.565036
854	810	4971850511335	\N	\N	f	2025-10-30 13:37:59.565036
855	811	5000267024233	\N	\N	f	2025-10-30 13:37:59.565036
856	812	3760123281478	\N	\N	f	2025-10-30 13:37:59.565036
857	813	3178050000725	\N	\N	f	2025-10-30 13:37:59.565036
858	814	5410228222958	\N	\N	f	2025-10-30 13:37:59.565036
859	815	3270310012360	\N	\N	f	2025-10-30 13:37:59.565036
860	816	3439495504354	\N	\N	f	2025-10-30 13:37:59.565036
861	817	3439495501971	\N	\N	f	2025-10-30 13:37:59.565036
862	306	4337182021872	\N	\N	f	2025-10-30 13:37:59.565036
863	818	05011013100613	\N	\N	f	2025-10-30 13:37:59.565036
864	819	3251091310852	\N	\N	f	2025-10-30 13:37:59.565036
865	820	3211209133698	\N	\N	f	2025-10-30 13:37:59.565036
866	821	3760322521573	\N	\N	f	2025-10-30 13:37:59.565036
867	822	7611855902123	\N	\N	f	2025-10-30 13:37:59.565036
868	823	4894597971241	\N	\N	f	2025-10-30 13:37:59.565036
869	824	3281519550621	\N	\N	f	2025-10-30 13:37:59.565036
870	825	5000329004111	\N	\N	f	2025-10-30 13:37:59.565036
871	826	3262151940759	\N	\N	f	2025-10-30 13:37:59.565036
872	827	3439495506105	\N	\N	f	2025-10-30 13:37:59.565036
873	828	3049614209994	\N	\N	f	2025-10-30 13:37:59.565036
874	372	03080210003425	\N	\N	f	2025-10-30 13:37:59.565036
875	829	3181340417127	\N	\N	f	2025-10-30 13:37:59.565036
876	830	3174660035317	\N	\N	f	2025-10-30 13:37:59.565036
877	831	3155250003527	\N	\N	f	2025-10-30 13:37:59.565036
878	832	3439496002248	\N	\N	f	2025-10-30 13:37:59.565036
879	833	3262970704310	\N	\N	f	2025-10-30 13:37:59.565036
880	372	3080210001872	\N	\N	f	2025-10-30 13:37:59.565036
881	834	3174660113121	\N	\N	f	2025-10-30 13:37:59.565036
882	835	3573972015619	\N	\N	f	2025-10-30 13:37:59.565036
883	836	3760251128317	\N	\N	f	2025-10-30 13:37:59.565036
884	837	3760251129192	\N	\N	f	2025-10-30 13:37:59.565036
885	306	4337182136514	\N	\N	f	2025-10-30 13:37:59.565036
886	838	3439495111804	\N	\N	f	2025-10-30 13:37:59.565036
887	839	3185370457054	\N	\N	f	2025-10-30 13:37:59.565036
888	840	3068320011707	\N	\N	f	2025-10-30 13:37:59.565036
889	841	8000500247143	\N	\N	f	2025-10-30 13:37:59.565036
890	842	7613036930109	\N	\N	f	2025-10-30 13:37:59.565036
891	843	2164874008802	\N	\N	f	2025-10-30 13:37:59.565036
892	844	3523230019934	\N	\N	f	2025-10-30 13:37:59.565036
893	845	3228021170053	\N	\N	f	2025-10-30 13:37:59.565036
894	846	3228021170039	\N	\N	f	2025-10-30 13:37:59.565036
895	846	3176582033327	\N	\N	f	2025-10-30 13:37:59.565036
896	847	3439496304939	\N	\N	f	2025-10-30 13:37:59.565036
897	848	3177180136878	\N	\N	f	2025-10-30 13:37:59.565036
898	849	5000267024240	\N	\N	f	2025-10-30 13:37:59.565036
899	599	3020881641106	\N	\N	f	2025-10-30 13:37:59.565036
900	850	3700123301714	\N	\N	f	2025-10-30 13:37:59.565036
901	851	3075711380083	\N	\N	f	2025-10-30 13:37:59.565036
902	852	3700222905868	\N	\N	f	2025-10-30 13:37:59.565036
903	853	3700222905875	\N	\N	f	2025-10-30 13:37:59.565036
904	854	03439496420622	\N	\N	f	2025-10-30 13:37:59.565036
905	855	0883314050271	\N	\N	f	2025-10-30 13:37:59.565036
906	856	4337182075899	\N	\N	f	2025-10-30 13:37:59.565036
907	857	5000267120478	\N	\N	f	2025-10-30 13:37:59.565036
908	858	05099873122006	\N	\N	f	2025-10-30 13:37:59.565036
909	859	3760138991614	\N	\N	f	2025-10-30 13:37:59.565036
910	860	3760108630598	\N	\N	f	2025-10-30 13:37:59.565036
911	861	3760151400964	\N	\N	f	2025-10-30 13:37:59.565036
912	862	3760063164831	\N	\N	f	2025-10-30 13:37:59.565036
913	863	3225350000501	\N	\N	f	2025-10-30 13:37:59.565036
914	306	3439496802107	\N	\N	f	2025-10-30 13:37:59.565036
915	306	4337182136477	\N	\N	f	2025-10-30 13:37:59.565036
916	864	3439495600278	\N	\N	f	2025-10-30 13:37:59.565036
917	865	8412276685430	\N	\N	f	2025-10-30 13:37:59.565036
918	866	0883314520286	\N	\N	f	2025-10-30 13:37:59.565036
919	867	0883314661385	\N	\N	f	2025-10-30 13:37:59.565036
920	868	3439495209907	\N	\N	f	2025-10-30 13:37:59.565036
921	869	3163937010003	\N	\N	f	2025-10-30 13:37:59.565036
922	870	3175529655530	\N	\N	f	2025-10-30 13:37:59.565036
923	871	3179077103154	\N	\N	f	2025-10-30 13:37:59.565036
924	872	3439495504460	\N	\N	f	2025-10-30 13:37:59.565036
925	873	3038351886902	\N	\N	f	2025-10-30 13:37:59.565036
926	874	3174660116702	\N	\N	f	2025-10-30 13:37:59.565036
927	875	7613034099280	\N	\N	f	2025-10-30 13:37:59.565036
928	876	3255790607374	\N	\N	f	2025-10-30 13:37:59.565036
929	877	8420499153889	\N	\N	f	2025-10-30 13:37:59.565036
930	586	03258691629582	\N	\N	f	2025-10-30 13:37:59.565036
931	878	13043702103819	\N	\N	f	2025-10-30 13:37:59.565036
932	879	7613036868082	\N	\N	f	2025-10-30 13:37:59.565036
933	880	5900047146875	\N	\N	f	2025-10-30 13:37:59.565036
934	881	56971872203952	\N	\N	f	2025-10-30 13:37:59.565036
935	882	9002490254872	\N	\N	f	2025-10-30 13:37:59.565036
936	883	5000112617955	\N	\N	f	2025-10-30 13:37:59.565036
937	365	3147690061007	\N	\N	f	2025-10-30 13:37:59.565036
938	884	3439495507317	\N	\N	f	2025-10-30 13:37:59.565036
939	885	4337182087854	\N	\N	f	2025-10-30 13:37:59.565036
940	723	3258691592879	\N	\N	f	2025-10-30 13:37:59.565036
941	886	4000177211328	\N	\N	f	2025-10-30 13:37:59.565036
942	887	4337182084549	\N	\N	f	2025-10-30 13:37:59.565036
943	888	5000204024623	\N	\N	f	2025-10-30 13:37:59.565036
944	889	3185370000335	\N	\N	f	2025-10-30 13:37:59.565036
945	890	3660085091620	\N	\N	f	2025-10-30 13:37:59.565036
946	891	3660085000110	\N	\N	f	2025-10-30 13:37:59.565036
947	892	5410056010918	\N	\N	f	2025-10-30 13:37:59.565036
948	893	3278580022218	\N	\N	f	2025-10-30 13:37:59.565036
949	894	3660085902810	\N	\N	f	2025-10-30 13:37:59.565036
950	895	5410056010871	\N	\N	f	2025-10-30 13:37:59.565036
951	896	3278581051101	\N	\N	f	2025-10-30 13:37:59.565036
952	897	3587220001903	\N	\N	f	2025-10-30 13:37:59.565036
953	898	3587220003877	\N	\N	f	2025-10-30 13:37:59.565036
954	899	03124488194659	\N	\N	f	2025-10-30 13:37:59.565036
955	900	3490941705671	\N	\N	f	2025-10-30 13:37:59.565036
956	750	5000112618082	\N	\N	f	2025-10-30 13:37:59.565036
957	901	3038359000010	\N	\N	f	2025-10-30 13:37:59.565036
958	718	3439496820071	\N	\N	f	2025-10-30 13:37:59.565036
959	902	3434030027480	\N	\N	f	2025-10-30 13:37:59.565036
960	903	5449000174567	\N	\N	f	2025-10-30 13:37:59.565036
961	904	4894597971364	\N	\N	f	2025-10-30 13:37:59.565036
962	905	03249778013462	\N	\N	f	2025-10-30 13:37:59.565036
963	906	4337182010289	\N	\N	f	2025-10-30 13:37:59.565036
964	907	3038351887008	\N	\N	f	2025-10-30 13:37:59.565036
965	908	3278845205028	\N	\N	f	2025-10-30 13:37:59.565036
966	909	3265478446003	\N	\N	f	2025-10-30 13:37:59.565036
967	858	05099873105306	\N	\N	f	2025-10-30 13:37:59.565036
968	910	03211200044801	\N	\N	f	2025-10-30 13:37:59.565036
969	911	3262151637758	\N	\N	f	2025-10-30 13:37:59.565036
970	912	7613034365774	\N	\N	f	2025-10-30 13:37:59.565036
971	306	3439496802046	\N	\N	f	2025-10-30 13:37:59.565036
972	913	3434030024717	\N	\N	f	2025-10-30 13:37:59.565036
973	914	8714789934846	\N	\N	f	2025-10-30 13:37:59.565036
974	915	3017760747493	\N	\N	f	2025-10-30 13:37:59.565036
975	916	3017760796590	\N	\N	f	2025-10-30 13:37:59.565036
976	917	3229820794624	\N	\N	f	2025-10-30 13:37:59.565036
977	918	3124480185235	\N	\N	f	2025-10-30 13:37:59.565036
978	919	8420499102689	\N	\N	f	2025-10-30 13:37:59.565036
979	920	3760251128263	\N	\N	f	2025-10-30 13:37:59.565036
980	921	3439496809984	\N	\N	f	2025-10-30 13:37:59.565036
981	922	3439495400311	\N	\N	f	2025-10-30 13:37:59.565036
982	923	3147690044703	\N	\N	f	2025-10-30 13:37:59.565036
983	924	4337182074564	\N	\N	f	2025-10-30 13:37:59.565036
984	925	3760123281164	\N	\N	f	2025-10-30 13:37:59.565036
985	926	3258430033168	\N	\N	f	2025-10-30 13:37:59.565036
986	927	3253920760005	\N	\N	f	2025-10-30 13:37:59.565036
987	928	3439495401981	\N	\N	f	2025-10-30 13:37:59.565036
988	929	3439495401370	\N	\N	f	2025-10-30 13:37:59.565036
989	930	3439495400298	\N	\N	f	2025-10-30 13:37:59.565036
990	931	3255537513043	\N	\N	f	2025-10-30 13:37:59.565036
991	461	3011932000928	\N	\N	f	2025-10-30 13:37:59.565036
992	932	3258691378565	\N	\N	f	2025-10-30 13:37:59.565036
993	933	3450301144533	\N	\N	f	2025-10-30 13:37:59.565036
994	934	3430430007664	\N	\N	f	2025-10-30 13:37:59.565036
995	935	3185370000038	\N	\N	f	2025-10-30 13:37:59.565036
996	936	3439495110357	\N	\N	f	2025-10-30 13:37:59.565036
997	937	8410087040011	\N	\N	f	2025-10-30 13:37:59.565036
998	938	3256630030116	\N	\N	f	2025-10-30 13:37:59.565036
999	939	3364120201950	\N	\N	f	2025-10-30 13:37:59.565036
1000	940	3514730000102	\N	\N	f	2025-10-30 13:37:59.565036
1001	941	3662093119068	\N	\N	f	2025-10-30 13:37:59.565036
1002	942	3439496506234	\N	\N	f	2025-10-30 13:37:59.565036
1003	943	3265479102007	\N	\N	f	2025-10-30 13:37:59.565036
1004	944	3177340021419	\N	\N	f	2025-10-30 13:37:59.565036
1005	945	3439496802947	\N	\N	f	2025-10-30 13:37:59.565036
1006	946	3033710084005	\N	\N	f	2025-10-30 13:37:59.565036
1007	947	3033710084913	\N	\N	f	2025-10-30 13:37:59.565036
1008	948	5413548040592	\N	\N	f	2025-10-30 13:37:59.565036
1009	949	8000500282069	\N	\N	f	2025-10-30 13:37:59.565036
1010	950	3361670361011	\N	\N	f	2025-10-30 13:37:59.565036
1011	951	3439494400626	\N	\N	f	2025-10-30 13:37:59.565036
1012	952	3267130003104	\N	\N	f	2025-10-30 13:37:59.565036
1013	953	3439495400274	\N	\N	f	2025-10-30 13:37:59.565036
1014	954	3439495403992	\N	\N	f	2025-10-30 13:37:59.565036
1015	955	3439495404029	\N	\N	f	2025-10-30 13:37:59.565036
1016	956	0026102878514	\N	\N	f	2025-10-30 13:37:59.565036
1017	957	3175529648709	\N	\N	f	2025-10-30 13:37:59.565036
1018	958	3439495506099	\N	\N	f	2025-10-30 13:37:59.565036
1019	959	3119782991295	\N	\N	f	2025-10-30 13:37:59.565036
1020	960	7613036926478	\N	\N	f	2025-10-30 13:37:59.565036
1021	961	4337182017639	\N	\N	f	2025-10-30 13:37:59.565036
1022	962	03439496420745	\N	\N	f	2025-10-30 13:37:59.565036
1023	963	2331409013925	\N	\N	f	2025-10-30 13:37:59.565036
1024	964	2331409014526	\N	\N	f	2025-10-30 13:37:59.565036
1025	965	2571516027655	\N	\N	f	2025-10-30 13:37:59.565036
1026	306	3439496823003	\N	\N	f	2025-10-30 13:37:59.565036
1027	306	3439496802237	\N	\N	f	2025-10-30 13:37:59.565036
1028	966	3439496822631	\N	\N	f	2025-10-30 13:37:59.565036
1029	967	5601164900714	\N	\N	f	2025-10-30 13:37:59.565036
1030	968	3439495405484	\N	\N	f	2025-10-30 13:37:59.565036
1031	969	3179730103989	\N	\N	f	2025-10-30 13:37:59.565036
1032	970	3439495206814	\N	\N	f	2025-10-30 13:37:59.565036
1033	971	3439495401400	\N	\N	f	2025-10-30 13:37:59.565036
1034	972	5055953900230	\N	\N	f	2025-10-30 13:37:59.565036
1035	973	4337182013648	\N	\N	f	2025-10-30 13:37:59.565036
1036	974	3039050167255	\N	\N	f	2025-10-30 13:37:59.565036
1037	975	2154600024909	\N	\N	f	2025-10-30 13:37:59.565036
1038	976	3470570013064	\N	\N	f	2025-10-30 13:37:59.565036
1039	306	3439496802091	\N	\N	f	2025-10-30 13:37:59.565036
1040	977	3178040693135	\N	\N	f	2025-10-30 13:37:59.565036
1041	978	4000602146621	\N	\N	f	2025-10-30 13:37:59.565036
1042	979	3439496822143	\N	\N	f	2025-10-30 13:37:59.565036
1043	980	4337182036036	\N	\N	f	2025-10-30 13:37:59.565036
1044	981	3115991210448	\N	\N	f	2025-10-30 13:37:59.565036
1045	982	3226139000279	\N	\N	f	2025-10-30 13:37:59.565036
1046	983	4337053592975	\N	\N	f	2025-10-30 13:37:59.565036
1047	984	3130632553005	\N	\N	f	2025-10-30 13:37:59.565036
1048	985	5014702033940	\N	\N	f	2025-10-30 13:37:59.565036
1049	986	3175529652195	\N	\N	f	2025-10-30 13:37:59.565036
1050	987	2992449038509	\N	\N	f	2025-10-30 13:37:59.565036
1051	306	3439496823041	\N	\N	f	2025-10-30 13:37:59.565036
1052	988	3276650111053	\N	\N	f	2025-10-30 13:37:59.565036
1053	989	3662093214015	\N	\N	f	2025-10-30 13:37:59.565036
1054	990	3017620425035	\N	\N	f	2025-10-30 13:37:59.565036
1055	991	3049614152337	\N	\N	f	2025-10-30 13:37:59.565036
1056	992	3439495110388	\N	\N	f	2025-10-30 13:37:59.565036
1057	993	8420499221038	\N	\N	f	2025-10-30 13:37:59.565036
1058	994	5010103800259	\N	\N	f	2025-10-30 13:37:59.565036
1059	995	4017773061431	\N	\N	f	2025-10-30 13:37:59.565036
1060	996	5410228258520	\N	\N	f	2025-10-30 13:37:59.565036
1061	997	3228881015921	\N	\N	f	2025-10-30 13:37:59.565036
1062	998	5060229013910	\N	\N	f	2025-10-30 13:37:59.565036
1063	999	3760042970125	\N	\N	f	2025-10-30 13:37:59.565036
1064	1000	3306540002977	\N	\N	f	2025-10-30 13:37:59.565036
1065	1001	3593248140883	\N	\N	f	2025-10-30 13:37:59.565036
1066	1002	3327180000383	\N	\N	f	2025-10-30 13:37:59.565036
1067	1003	3346024708759	\N	\N	f	2025-10-30 13:37:59.565036
1068	1004	5420035327739	\N	\N	f	2025-10-30 13:37:59.565036
1069	1005	3287121623005	\N	\N	f	2025-10-30 13:37:59.565036
1070	960	3179730005306	\N	\N	f	2025-10-30 13:37:59.565036
1071	1006	3036813710086	\N	\N	f	2025-10-30 13:37:59.565036
1072	1007	8712100751370	\N	\N	f	2025-10-30 13:37:59.565036
1073	1008	3439496820248	\N	\N	f	2025-10-30 13:37:59.565036
1074	1009	3661679121938	\N	\N	f	2025-10-30 13:37:59.565036
1075	1010	8411777411289	\N	\N	f	2025-10-30 13:37:59.565036
1076	1011	4337147998072	\N	\N	f	2025-10-30 13:37:59.565036
1077	360	4337182057284	\N	\N	f	2025-10-30 13:37:59.565036
1078	1012	3760251128348	\N	\N	f	2025-10-30 13:37:59.565036
1079	1013	3251091405695	\N	\N	f	2025-10-30 13:37:59.565036
1080	1014	4337182009085	\N	\N	f	2025-10-30 13:37:59.565036
1081	1015	8710438101027	\N	\N	f	2025-10-30 13:37:59.565036
1082	1016	5011423182131	\N	\N	f	2025-10-30 13:37:59.565036
1083	959	03119782991295	\N	\N	f	2025-10-30 13:37:59.565036
1084	1017	3760100203912	\N	\N	f	2025-10-30 13:37:59.565036
1085	1018	5010103931502	\N	\N	f	2025-10-30 13:37:59.565036
1086	1019	3256630030154	\N	\N	f	2025-10-30 13:37:59.565036
1087	723	03258691592879	\N	\N	f	2025-10-30 13:37:59.565036
1088	1020	8718226329622	\N	\N	f	2025-10-30 13:37:59.565036
1089	1021	3439497014585	\N	\N	f	2025-10-30 13:37:59.565036
1090	1022	3439497014141	\N	\N	f	2025-10-30 13:37:59.565036
1091	1023	3451080000454	\N	\N	f	2025-10-30 13:37:59.565036
1092	1024	3183280012912	\N	\N	f	2025-10-30 13:37:59.565036
1093	1025	3439496822549	\N	\N	f	2025-10-30 13:37:59.565036
1094	1026	3439497007075	\N	\N	f	2025-10-30 13:37:59.565036
1095	1027	3573972000257	\N	\N	f	2025-10-30 13:37:59.565036
1096	1028	8413997457276	\N	\N	f	2025-10-30 13:37:59.565036
1097	1029	3439495303476	\N	\N	f	2025-10-30 13:37:59.565036
1098	1030	3281130014182	\N	\N	f	2025-10-30 13:37:59.565036
1099	1031	3496080210199	\N	\N	f	2025-10-30 13:37:59.565036
1100	1032	03119783017482	\N	\N	f	2025-10-30 13:37:59.565036
1101	1033	3346024708612	\N	\N	f	2025-10-30 13:37:59.565036
1102	599	3020881621108	\N	\N	f	2025-10-30 13:37:59.565036
1103	1034	4894665553270	\N	\N	f	2025-10-30 13:37:59.565036
1104	1035	3439496409726	\N	\N	f	2025-10-30 13:37:59.565036
1105	1036	8710438058529	\N	\N	f	2025-10-30 13:37:59.565036
1106	1037	8000500167113	\N	\N	f	2025-10-30 13:37:59.565036
1107	1038	3147699118351	\N	\N	f	2025-10-30 13:37:59.565036
1108	1039	3439495504453	\N	\N	f	2025-10-30 13:37:59.565036
1109	1040	3503780004314	\N	\N	f	2025-10-30 13:37:59.565036
1110	1041	3503780004444	\N	\N	f	2025-10-30 13:37:59.565036
1111	372	3573972112813	\N	\N	f	2025-10-30 13:37:59.565036
1112	1042	8411457802505	\N	\N	f	2025-10-30 13:37:59.565036
1113	1043	13500879066847	\N	\N	f	2025-10-30 13:37:59.565036
1114	1044	3439495600162	\N	\N	f	2025-10-30 13:37:59.565036
1115	1045	7613037883121	\N	\N	f	2025-10-30 13:37:59.565036
1116	1046	3439495506044	\N	\N	f	2025-10-30 13:37:59.565036
1117	1047	3661505086608	\N	\N	f	2025-10-30 13:37:59.565036
1118	468	0000000421010	\N	\N	f	2025-10-30 13:37:59.565036
1119	1048	5021306054080	\N	\N	f	2025-10-30 13:37:59.565036
1120	1049	3439496801544	\N	\N	f	2025-10-30 13:37:59.565036
1121	1050	3439496823379	\N	\N	f	2025-10-30 13:37:59.565036
1122	1051	3439496822587	\N	\N	f	2025-10-30 13:37:59.565036
1123	1052	3211200152339	\N	\N	f	2025-10-30 13:37:59.565036
1124	1053	3211200135356	\N	\N	f	2025-10-30 13:37:59.565036
1125	1054	3267130032470	\N	\N	f	2025-10-30 13:37:59.565036
1126	1055	3251514078000	\N	\N	f	2025-10-30 13:37:59.565036
1127	1056	5420035305034	\N	\N	f	2025-10-30 13:37:59.565036
1128	1057	0026102878545	\N	\N	f	2025-10-30 13:37:59.565036
1129	1058	3439494502023	\N	\N	f	2025-10-30 13:37:59.565036
1130	1059	03175529644848	\N	\N	f	2025-10-30 13:37:59.565036
1131	1060	4337182014546	\N	\N	f	2025-10-30 13:37:59.565036
1132	1061	3102700090514	\N	\N	f	2025-10-30 14:16:19.499784
1133	1061	3102700090521	\N	\N	f	2025-10-30 14:16:19.499784
1134	1062	3184830027011	\N	\N	f	2025-10-30 14:16:19.499784
1135	1063	3184830027202	\N	\N	f	2025-10-30 14:16:19.499784
1136	1064	3184830027295	\N	\N	f	2025-10-30 14:16:19.499784
1137	1065	3184830027523	\N	\N	f	2025-10-30 14:16:19.499784
1138	1065	3184830027585	\N	\N	f	2025-10-30 14:16:19.499784
1139	1066	3184830027950	\N	\N	f	2025-10-30 14:16:19.499784
1140	1067	3184830028049	\N	\N	f	2025-10-30 14:16:19.499784
1141	1068	3184830028070	\N	\N	f	2025-10-30 14:16:19.499784
1142	1069	3184830028100	\N	\N	f	2025-10-30 14:16:19.499784
1143	1070	3184830028131	\N	\N	f	2025-10-30 14:16:19.499784
1144	1071	3184830028162	\N	\N	f	2025-10-30 14:16:19.499784
1145	1068	3184830028193	\N	\N	f	2025-10-30 14:16:19.499784
1146	1068	3184830028223	\N	\N	f	2025-10-30 14:16:19.499784
1147	1072	3184830028438	\N	\N	f	2025-10-30 14:16:19.499784
1148	1073	3184830028469	\N	\N	f	2025-10-30 14:16:19.499784
1149	1073	3184830049754	\N	\N	f	2025-10-30 14:16:19.499784
1150	1074	3184830049785	\N	\N	f	2025-10-30 14:16:19.499784
1151	1075	3184830049815	\N	\N	f	2025-10-30 14:16:19.499784
1152	1076	3184830049990	\N	\N	f	2025-10-30 14:16:19.499784
1153	1077	3184830052976	\N	\N	f	2025-10-30 14:16:19.499784
1154	1078	3184830052983	\N	\N	f	2025-10-30 14:16:19.499784
1155	1079	3184830053010	\N	\N	f	2025-10-30 14:16:19.499784
1156	1080	3184830053041	\N	\N	f	2025-10-30 14:16:19.499784
1157	1081	3184830054079	\N	\N	f	2025-10-30 14:16:19.499784
1158	1082	3184830054345	\N	\N	f	2025-10-30 14:16:19.499784
1159	1082	3184830054581	\N	\N	f	2025-10-30 14:16:19.499784
1160	1083	3184830056257	\N	\N	f	2025-10-30 14:16:19.499784
1161	1084	3184830061503	\N	\N	f	2025-10-30 14:16:19.499784
1162	1085	3184830062760	\N	\N	f	2025-10-30 14:16:19.499784
1163	1085	3184830063194	\N	\N	f	2025-10-30 14:16:19.499784
1164	1086	3184830063224	\N	\N	f	2025-10-30 14:16:19.499784
1165	1087	3184830063255	\N	\N	f	2025-10-30 14:16:19.499784
1166	1088	3184830063286	\N	\N	f	2025-10-30 14:16:19.499784
1167	1088	3184830063316	\N	\N	f	2025-10-30 14:16:19.499784
1168	1089	3184830063347	\N	\N	f	2025-10-30 14:16:19.499784
1169	1089	3184830063408	\N	\N	f	2025-10-30 14:16:19.499784
1170	1090	3184830063439	\N	\N	f	2025-10-30 14:16:19.499784
1171	1091	3184830063460	\N	\N	f	2025-10-30 14:16:19.499784
1172	1092	3184830067055	\N	\N	f	2025-10-30 14:16:19.499784
1173	1093	3184830067116	\N	\N	f	2025-10-30 14:16:19.499784
1174	1094	3184830067345	\N	\N	f	2025-10-30 14:16:19.499784
1175	1095	3184830067413	\N	\N	f	2025-10-30 14:16:19.499784
1176	1096	3184830067512	\N	\N	f	2025-10-30 14:16:19.499784
1177	1097	3184830067543	\N	\N	f	2025-10-30 14:16:19.499784
1178	1098	3184830067857	\N	\N	f	2025-10-30 14:16:19.499784
1179	1099	3237580162287	\N	\N	f	2025-10-30 14:16:19.499784
1180	1100	3237580171838	\N	\N	f	2025-10-30 14:16:19.499784
1181	1101	3237580190013	\N	\N	f	2025-10-30 14:16:19.499784
1182	1102	3237580190044	\N	\N	f	2025-10-30 14:16:19.499784
1183	1103	3237580190075	\N	\N	f	2025-10-30 14:16:19.499784
1184	1104	3237580190105	\N	\N	f	2025-10-30 14:16:19.499784
1185	1105	3237580190136	\N	\N	f	2025-10-30 14:16:19.499784
1186	1106	3237580190198	\N	\N	f	2025-10-30 14:16:19.499784
1187	1107	3237580194059	\N	\N	f	2025-10-30 14:16:19.499784
1188	1108	3237580194356	\N	\N	f	2025-10-30 14:16:19.499784
1189	1108	3237580194363	\N	\N	f	2025-10-30 14:16:19.499784
1190	1109	3245390021649	\N	\N	f	2025-10-30 14:16:19.499784
1191	1110	3245390028150	\N	\N	f	2025-10-30 14:16:19.499784
1192	1111	3245390029744	\N	\N	f	2025-10-30 14:16:19.499784
1193	1112	3245390029775	\N	\N	f	2025-10-30 14:16:19.499784
1194	1113	3245390039668	\N	\N	f	2025-10-30 14:16:19.499784
1195	1114	3245390039828	\N	\N	f	2025-10-30 14:16:19.499784
1196	1115	3245390039835	\N	\N	f	2025-10-30 14:16:19.499784
1197	1116	3245390065926	\N	\N	f	2025-10-30 14:16:19.499784
1198	1117	3245390075048	\N	\N	f	2025-10-30 14:16:19.499784
1199	1118	3245390084422	\N	\N	f	2025-10-30 14:16:19.499784
1200	1119	3245390084453	\N	\N	f	2025-10-30 14:16:19.499784
1201	1120	3245390097774	\N	\N	f	2025-10-30 14:16:19.499784
1202	1121	3245390121387	\N	\N	f	2025-10-30 14:16:19.499784
1203	1122	3245390140388	\N	\N	f	2025-10-30 14:16:19.499784
1204	1123	3245390146519	\N	\N	f	2025-10-30 14:16:19.499784
1205	1124	3245390158550	\N	\N	f	2025-10-30 14:16:19.499784
1206	1125	3245390163424	\N	\N	f	2025-10-30 14:16:19.499784
1207	1126	3245390172174	\N	\N	f	2025-10-30 14:16:19.499784
1208	1127	3245390191373	\N	\N	f	2025-10-30 14:16:19.499784
1209	1128	3245390206077	\N	\N	f	2025-10-30 14:16:19.499784
1210	1129	3245390208903	\N	\N	f	2025-10-30 14:16:19.499784
1211	1130	3245411164973	\N	\N	f	2025-10-30 14:16:19.499784
1212	1131	3245411253844	\N	\N	f	2025-10-30 14:16:19.499784
1213	1132	3245411344450	\N	\N	f	2025-10-30 14:16:19.499784
1214	1133	3245411400965	\N	\N	f	2025-10-30 14:16:19.499784
1215	1134	3245411443559	\N	\N	f	2025-10-30 14:16:19.499784
1216	1135	3245411443566	\N	\N	f	2025-10-30 14:16:19.499784
1217	1136	3245411640620	\N	\N	f	2025-10-30 14:16:19.499784
1218	1137	3245411670863	\N	\N	f	2025-10-30 14:16:19.499784
1219	1138	3245412038020	\N	\N	f	2025-10-30 14:16:19.499784
1220	1139	3245412059124	\N	\N	f	2025-10-30 14:16:19.499784
1221	1140	3245412256639	\N	\N	f	2025-10-30 14:16:19.499784
1222	1141	3245412304941	\N	\N	f	2025-10-30 14:16:19.499784
1223	1142	3245412367397	\N	\N	f	2025-10-30 14:16:19.499784
1224	1143	3245412414909	\N	\N	f	2025-10-30 14:16:19.499784
1225	1144	3245412414916	\N	\N	f	2025-10-30 14:16:19.499784
1226	1145	3245412417924	\N	\N	f	2025-10-30 14:16:19.499784
1227	1146	3245412435256	\N	\N	f	2025-10-30 14:16:19.499784
1228	1147	3245412563034	\N	\N	f	2025-10-30 14:16:19.499784
1229	1148	3245412563331	\N	\N	f	2025-10-30 14:16:19.499784
1230	1149	3245412568329	\N	\N	f	2025-10-30 14:16:19.499784
1231	1150	3245412568749	\N	\N	f	2025-10-30 14:16:19.499784
1232	1151	3245412569081	\N	\N	f	2025-10-30 14:16:19.499784
1233	1152	3245412569098	\N	\N	f	2025-10-30 14:16:19.499784
1234	1153	3245412589218	\N	\N	f	2025-10-30 14:16:19.499784
1235	1154	3245412621963	\N	\N	f	2025-10-30 14:16:19.499784
1236	1155	3245412654084	\N	\N	f	2025-10-30 14:16:19.499784
1237	1156	3245412654091	\N	\N	f	2025-10-30 14:16:19.499784
1238	1157	3245412654176	\N	\N	f	2025-10-30 14:16:19.499784
1239	1158	3245412654206	\N	\N	f	2025-10-30 14:16:19.499784
1240	1159	3245412699160	\N	\N	f	2025-10-30 14:16:19.499784
1241	1160	3245412718687	\N	\N	f	2025-10-30 14:16:19.499784
1242	1160	3245412718694	\N	\N	f	2025-10-30 14:16:19.499784
1243	1161	3245412730917	\N	\N	f	2025-10-30 14:16:19.499784
1244	1162	3245412730924	\N	\N	f	2025-10-30 14:16:19.499784
1245	1163	3245412730993	\N	\N	f	2025-10-30 14:16:19.499784
1246	1163	3245412742569	\N	\N	f	2025-10-30 14:16:19.499784
1247	1164	3245412749438	\N	\N	f	2025-10-30 14:16:19.499784
1248	1165	3245412826535	\N	\N	f	2025-10-30 14:16:19.499784
1249	1166	3245412849381	\N	\N	f	2025-10-30 14:16:19.499784
1250	1167	3245412885174	\N	\N	f	2025-10-30 14:16:19.499784
1251	1168	3245412886171	\N	\N	f	2025-10-30 14:16:19.499784
1252	1168	3245412886232	\N	\N	f	2025-10-30 14:16:19.499784
1253	1169	3245412890987	\N	\N	f	2025-10-30 14:16:19.499784
1254	1170	3245412891168	\N	\N	f	2025-10-30 14:16:19.499784
1255	1170	3245412891175	\N	\N	f	2025-10-30 14:16:19.499784
1256	1171	3245412933066	\N	\N	f	2025-10-30 14:16:19.499784
1257	1172	3245412934841	\N	\N	f	2025-10-30 14:16:19.499784
1258	1173	3245412937545	\N	\N	f	2025-10-30 14:16:19.499784
1259	1174	3245412954467	\N	\N	f	2025-10-30 14:16:19.499784
1260	1175	3245412961984	\N	\N	f	2025-10-30 14:16:19.499784
1261	1175	3245412962318	\N	\N	f	2025-10-30 14:16:19.499784
1262	1176	3245412975462	\N	\N	f	2025-10-30 14:16:19.499784
1263	1177	3245412980152	\N	\N	f	2025-10-30 14:16:19.499784
1264	1178	3245412997846	\N	\N	f	2025-10-30 14:16:19.499784
1265	1178	3245412997853	\N	\N	f	2025-10-30 14:16:19.499784
1266	1179	3245413187888	\N	\N	f	2025-10-30 14:16:19.499784
1267	1180	3245413419996	\N	\N	f	2025-10-30 14:16:19.499784
1268	1181	3245413426048	\N	\N	f	2025-10-30 14:16:19.499784
1269	1182	3245413442000	\N	\N	f	2025-10-30 14:16:19.499784
1270	1183	3245413458513	\N	\N	f	2025-10-30 14:16:19.499784
1271	1183	3245413487919	\N	\N	f	2025-10-30 14:16:19.499784
1272	1184	3245413495457	\N	\N	f	2025-10-30 14:16:19.499784
1273	1185	3245413505682	\N	\N	f	2025-10-30 14:16:19.499784
1274	1186	3245413532466	\N	\N	f	2025-10-30 14:16:19.499784
1275	1187	3245413532626	\N	\N	f	2025-10-30 14:16:19.499784
1276	1188	3245413532664	\N	\N	f	2025-10-30 14:16:19.499784
1277	1189	3245413704238	\N	\N	f	2025-10-30 14:16:19.499784
1278	1190	3245413730121	\N	\N	f	2025-10-30 14:16:19.499784
1279	1191	3245413730138	\N	\N	f	2025-10-30 14:16:19.499784
1280	1192	3245413730169	\N	\N	f	2025-10-30 14:16:19.499784
1281	1193	3245413754196	\N	\N	f	2025-10-30 14:16:19.499784
1282	1194	3245413808196	\N	\N	f	2025-10-30 14:16:19.499784
1283	1194	3245413913128	\N	\N	f	2025-10-30 14:16:19.499784
1284	1195	3245413951359	\N	\N	f	2025-10-30 14:16:19.499784
1285	1195	3245413951373	\N	\N	f	2025-10-30 14:16:19.499784
1286	1196	3245413955470	\N	\N	f	2025-10-30 14:16:19.499784
1287	1197	3245413965547	\N	\N	f	2025-10-30 14:16:19.499784
1288	1198	3245414009622	\N	\N	f	2025-10-30 14:16:19.499784
1289	1199	3245414021068	\N	\N	f	2025-10-30 14:16:19.499784
1290	1200	3245414145030	\N	\N	f	2025-10-30 14:16:19.499784
1291	1201	3245414145146	\N	\N	f	2025-10-30 14:16:19.499784
1292	1202	3245414145238	\N	\N	f	2025-10-30 14:16:19.499784
1293	1202	3245414146068	\N	\N	f	2025-10-30 14:16:19.499784
1294	1203	3245414146389	\N	\N	f	2025-10-30 14:16:19.499784
1295	1204	3245414249950	\N	\N	f	2025-10-30 14:16:19.499784
1296	1205	3245414263048	\N	\N	f	2025-10-30 14:16:19.499784
1297	1206	3245414349971	\N	\N	f	2025-10-30 14:16:19.499784
1298	1133	3245414376366	\N	\N	f	2025-10-30 14:16:19.499784
1299	1207	3245414480322	\N	\N	f	2025-10-30 14:16:19.499784
1300	1208	3245414649194	\N	\N	f	2025-10-30 14:16:19.499784
1301	1208	3245414649309	\N	\N	f	2025-10-30 14:16:19.499784
1302	1209	3245414658431	\N	\N	f	2025-10-30 14:16:19.499784
1303	1210	3245414658806	\N	\N	f	2025-10-30 14:16:19.499784
1304	1211	3245414659056	\N	\N	f	2025-10-30 14:16:19.499784
1305	1212	3245415141000	\N	\N	f	2025-10-30 14:16:19.499784
1306	1212	3245415141031	\N	\N	f	2025-10-30 14:16:19.499784
1307	1213	3245415141093	\N	\N	f	2025-10-30 14:16:19.499784
1308	1214	3270190006541	\N	\N	f	2025-10-30 14:16:19.499784
1309	1215	3270190006787	\N	\N	f	2025-10-30 14:16:19.499784
1310	1215	3270190006794	\N	\N	f	2025-10-30 14:16:19.499784
1311	1216	3270190006800	\N	\N	f	2025-10-30 14:16:19.499784
1312	1217	3270190007050	\N	\N	f	2025-10-30 14:16:19.499784
1313	1218	3270190007074	\N	\N	f	2025-10-30 14:16:19.499784
1314	1218	3270190007081	\N	\N	f	2025-10-30 14:16:19.499784
1315	1219	3270190007906	\N	\N	f	2025-10-30 14:16:19.499784
1316	1220	3270190007920	\N	\N	f	2025-10-30 14:16:19.499784
1317	1220	3270190007951	\N	\N	f	2025-10-30 14:16:19.499784
1318	1221	3270190008262	\N	\N	f	2025-10-30 14:16:19.499784
1319	1222	3270190008279	\N	\N	f	2025-10-30 14:16:19.499784
1320	1223	3270190008606	\N	\N	f	2025-10-30 14:16:19.499784
1321	1224	3270190009511	\N	\N	f	2025-10-30 14:16:19.499784
1322	1225	3270190111108	\N	\N	f	2025-10-30 14:16:19.499784
1323	1226	3270190114888	\N	\N	f	2025-10-30 14:16:19.499784
1324	1226	3270190114895	\N	\N	f	2025-10-30 14:16:19.499784
1325	1227	3270190115113	\N	\N	f	2025-10-30 14:16:19.499784
1326	1228	3270190117971	\N	\N	f	2025-10-30 14:16:19.499784
1327	1224	3270190118145	\N	\N	f	2025-10-30 14:16:19.499784
1328	1229	3270190118749	\N	\N	f	2025-10-30 14:16:19.499784
1329	1230	3270190118756	\N	\N	f	2025-10-30 14:16:19.499784
1330	1231	3270190118800	\N	\N	f	2025-10-30 14:16:19.499784
1331	1232	3270190118862	\N	\N	f	2025-10-30 14:16:19.499784
1332	1233	3270190118879	\N	\N	f	2025-10-30 14:16:19.499784
1333	1234	3270190119500	\N	\N	f	2025-10-30 14:16:19.499784
1334	1235	3270190121909	\N	\N	f	2025-10-30 14:16:19.499784
1335	1236	3270190122852	\N	\N	f	2025-10-30 14:16:19.499784
1336	1237	3270190124153	\N	\N	f	2025-10-30 14:16:19.499784
1337	1238	3270190124528	\N	\N	f	2025-10-30 14:16:19.499784
1338	1239	3270190124924	\N	\N	f	2025-10-30 14:16:19.499784
1339	1240	3270190127512	\N	\N	f	2025-10-30 14:16:19.499784
1340	1240	3270190127529	\N	\N	f	2025-10-30 14:16:19.499784
1341	1241	3270190127536	\N	\N	f	2025-10-30 14:16:19.499784
1342	1242	3270190127765	\N	\N	f	2025-10-30 14:16:19.499784
1343	1243	3270190127833	\N	\N	f	2025-10-30 14:16:19.499784
1344	1244	3270190127871	\N	\N	f	2025-10-30 14:16:19.499784
1345	1242	3270190128151	\N	\N	f	2025-10-30 14:16:19.499784
1346	1245	3270190128403	\N	\N	f	2025-10-30 14:16:19.499784
1347	1194	3270190128472	\N	\N	f	2025-10-30 14:16:19.499784
1348	1246	3270190128519	\N	\N	f	2025-10-30 14:16:19.499784
1349	1247	3270190128632	\N	\N	f	2025-10-30 14:16:19.499784
1350	1248	3270190130468	\N	\N	f	2025-10-30 14:16:19.499784
1351	1249	3270190130697	\N	\N	f	2025-10-30 14:16:19.499784
1352	1250	3270190130703	\N	\N	f	2025-10-30 14:16:19.499784
1353	1251	3270190133377	\N	\N	f	2025-10-30 14:16:19.499784
1354	1252	3270190134695	\N	\N	f	2025-10-30 14:16:19.499784
1355	1253	3270190136668	\N	\N	f	2025-10-30 14:16:19.499784
1356	1240	3270190136842	\N	\N	f	2025-10-30 14:16:19.499784
1357	1254	3270190136866	\N	\N	f	2025-10-30 14:16:19.499784
1358	1255	3270190138396	\N	\N	f	2025-10-30 14:16:19.499784
1359	1256	3270190139379	\N	\N	f	2025-10-30 14:16:19.499784
1360	1257	3270190150596	\N	\N	f	2025-10-30 14:16:19.499784
1361	1141	3270190151654	\N	\N	f	2025-10-30 14:16:19.499784
1362	1257	3270190153085	\N	\N	f	2025-10-30 14:16:19.499784
1363	1258	3270190155584	\N	\N	f	2025-10-30 14:16:19.499784
1364	1259	3270190156222	\N	\N	f	2025-10-30 14:16:19.499784
1365	1149	3270190156512	\N	\N	f	2025-10-30 14:16:19.499784
1366	1260	3270190156833	\N	\N	f	2025-10-30 14:16:19.499784
1367	1261	3270190159179	\N	\N	f	2025-10-30 14:16:19.499784
1368	1262	3270190168515	\N	\N	f	2025-10-30 14:16:19.499784
1369	1263	3270190171706	\N	\N	f	2025-10-30 14:16:19.499784
1370	1264	3270190171720	\N	\N	f	2025-10-30 14:16:19.499784
1371	1206	3270190171737	\N	\N	f	2025-10-30 14:16:19.499784
1372	1265	3270190173113	\N	\N	f	2025-10-30 14:16:19.499784
1373	1266	3270190174936	\N	\N	f	2025-10-30 14:16:19.499784
1374	1267	3270190177579	\N	\N	f	2025-10-30 14:16:19.499784
1375	1268	3270190178071	\N	\N	f	2025-10-30 14:16:19.499784
1376	1269	3270190178460	\N	\N	f	2025-10-30 14:16:19.499784
1377	1270	3270190178477	\N	\N	f	2025-10-30 14:16:19.499784
1378	1271	3270190178514	\N	\N	f	2025-10-30 14:16:19.499784
1379	1272	3270190178521	\N	\N	f	2025-10-30 14:16:19.499784
1380	1273	3270190178538	\N	\N	f	2025-10-30 14:16:19.499784
1381	1274	3270190178545	\N	\N	f	2025-10-30 14:16:19.499784
1382	1275	3270190178637	\N	\N	f	2025-10-30 14:16:19.499784
1383	1276	3270190179214	\N	\N	f	2025-10-30 14:16:19.499784
1384	1277	3270190180982	\N	\N	f	2025-10-30 14:16:19.499784
1385	1278	3270190181262	\N	\N	f	2025-10-30 14:16:19.499784
1386	1279	3270190182153	\N	\N	f	2025-10-30 14:16:19.499784
1387	1280	3270190182160	\N	\N	f	2025-10-30 14:16:19.499784
1388	1281	3270190184560	\N	\N	f	2025-10-30 14:16:19.499784
1389	1282	3270190185239	\N	\N	f	2025-10-30 14:16:19.499784
1390	1283	3270190185772	\N	\N	f	2025-10-30 14:16:19.499784
1391	1284	3270190189756	\N	\N	f	2025-10-30 14:16:19.499784
1392	1285	3270190190660	\N	\N	f	2025-10-30 14:16:19.499784
1393	1286	3270190191216	\N	\N	f	2025-10-30 14:16:19.499784
1394	1287	3270190191292	\N	\N	f	2025-10-30 14:16:19.499784
1395	1288	3270190192039	\N	\N	f	2025-10-30 14:16:19.499784
1396	1289	3270190192749	\N	\N	f	2025-10-30 14:16:19.499784
1397	1290	3270190194385	\N	\N	f	2025-10-30 14:16:19.499784
1398	1291	3270190194392	\N	\N	f	2025-10-30 14:16:19.499784
1399	1292	3270190194910	\N	\N	f	2025-10-30 14:16:19.499784
1400	1293	3270190195474	\N	\N	f	2025-10-30 14:16:19.499784
1401	1294	3270190195481	\N	\N	f	2025-10-30 14:16:19.499784
1402	1294	3270190195986	\N	\N	f	2025-10-30 14:16:19.499784
1403	1295	3270190198987	\N	\N	f	2025-10-30 14:16:19.499784
1404	1296	3493375072036	\N	\N	f	2025-10-30 14:16:19.499784
1405	1297	3523680256156	\N	\N	f	2025-10-30 14:16:19.499784
1406	1297	3523680256187	\N	\N	f	2025-10-30 14:16:19.499784
1407	1298	3523680256217	\N	\N	f	2025-10-30 14:16:19.499784
1408	1149	3560070017461	\N	\N	f	2025-10-30 14:16:19.499784
1409	1299	3560070048755	\N	\N	f	2025-10-30 14:16:19.499784
1410	1300	3560070049110	\N	\N	f	2025-10-30 14:16:19.499784
1411	1301	3560070098415	\N	\N	f	2025-10-30 14:16:19.499784
1412	1168	3560070131846	\N	\N	f	2025-10-30 14:16:19.499784
1413	1302	3560070134502	\N	\N	f	2025-10-30 14:16:19.499784
1414	1303	3560070134533	\N	\N	f	2025-10-30 14:16:19.499784
1415	1304	3560070142224	\N	\N	f	2025-10-30 14:16:19.499784
1416	1304	3560070152391	\N	\N	f	2025-10-30 14:16:19.499784
1417	1305	3560070152452	\N	\N	f	2025-10-30 14:16:19.499784
1418	1305	3560070152483	\N	\N	f	2025-10-30 14:16:19.499784
1419	1306	3560070152513	\N	\N	f	2025-10-30 14:16:19.499784
1420	1306	3560070155163	\N	\N	f	2025-10-30 14:16:19.499784
1421	1307	3560070155194	\N	\N	f	2025-10-30 14:16:19.499784
1422	1308	3560070155224	\N	\N	f	2025-10-30 14:16:19.499784
1423	1224	3560070159260	\N	\N	f	2025-10-30 14:16:19.499784
1424	1309	3560070161706	\N	\N	f	2025-10-30 14:16:19.499784
1425	1310	3560070166046	\N	\N	f	2025-10-30 14:16:19.499784
1426	1311	3560070177110	\N	\N	f	2025-10-30 14:16:19.499784
1427	1312	3560070178414	\N	\N	f	2025-10-30 14:16:19.499784
1428	1313	3560070178445	\N	\N	f	2025-10-30 14:16:19.499784
1429	1314	3560070178476	\N	\N	f	2025-10-30 14:16:19.499784
1430	1315	3560070181872	\N	\N	f	2025-10-30 14:16:19.499784
1431	1316	3560070181933	\N	\N	f	2025-10-30 14:16:19.499784
1432	1317	3560070188086	\N	\N	f	2025-10-30 14:16:19.499784
1433	1318	3560070188451	\N	\N	f	2025-10-30 14:16:19.499784
1434	1319	3560070197743	\N	\N	f	2025-10-30 14:16:19.499784
1435	1270	3560070197774	\N	\N	f	2025-10-30 14:16:19.499784
1436	1320	3560070198504	\N	\N	f	2025-10-30 14:16:19.499784
1437	1320	3560070203864	\N	\N	f	2025-10-30 14:16:19.499784
1438	1321	3560070204878	\N	\N	f	2025-10-30 14:16:19.499784
1439	1322	3560070204908	\N	\N	f	2025-10-30 14:16:19.499784
1440	1274	3560070206476	\N	\N	f	2025-10-30 14:16:19.499784
1441	1274	3560070206506	\N	\N	f	2025-10-30 14:16:19.499784
1442	1323	3560070218295	\N	\N	f	2025-10-30 14:16:19.499784
1443	1324	3560070220731	\N	\N	f	2025-10-30 14:16:19.499784
1444	1325	3560070223145	\N	\N	f	2025-10-30 14:16:19.499784
1445	1326	3560070224524	\N	\N	f	2025-10-30 14:16:19.499784
1446	1327	3560070230778	\N	\N	f	2025-10-30 14:16:19.499784
1447	1328	3560070232963	\N	\N	f	2025-10-30 14:16:19.499784
1448	1329	3560070235841	\N	\N	f	2025-10-30 14:16:19.499784
1449	1330	3560070249343	\N	\N	f	2025-10-30 14:16:19.499784
1450	1331	3560070261086	\N	\N	f	2025-10-30 14:16:19.499784
1451	1332	3560070267927	\N	\N	f	2025-10-30 14:16:19.499784
1452	1333	3560070268030	\N	\N	f	2025-10-30 14:16:19.499784
1453	1334	3560070272099	\N	\N	f	2025-10-30 14:16:19.499784
1454	1335	3560070272129	\N	\N	f	2025-10-30 14:16:19.499784
1455	1336	3560070272570	\N	\N	f	2025-10-30 14:16:19.499784
1456	1337	3560070272600	\N	\N	f	2025-10-30 14:16:19.499784
1457	1338	3560070273546	\N	\N	f	2025-10-30 14:16:19.499784
1458	1339	3560070274444	\N	\N	f	2025-10-30 14:16:19.499784
1459	1340	3560070275267	\N	\N	f	2025-10-30 14:16:19.499784
1460	1341	3560070276141	\N	\N	f	2025-10-30 14:16:19.499784
1461	1342	3560070277315	\N	\N	f	2025-10-30 14:16:19.499784
1462	1343	3560070279319	\N	\N	f	2025-10-30 14:16:19.499784
1463	1344	3560070279524	\N	\N	f	2025-10-30 14:16:19.499784
1464	1345	3560070280520	\N	\N	f	2025-10-30 14:16:19.499784
1465	1346	3560070280551	\N	\N	f	2025-10-30 14:16:19.499784
1466	1346	3560070282029	\N	\N	f	2025-10-30 14:16:19.499784
1467	1347	3560070283484	\N	\N	f	2025-10-30 14:16:19.499784
1468	1348	3560070301980	\N	\N	f	2025-10-30 14:16:19.499784
1469	1349	3560070302048	\N	\N	f	2025-10-30 14:16:19.499784
1470	1350	3560070302109	\N	\N	f	2025-10-30 14:16:19.499784
1471	1351	3560070302161	\N	\N	f	2025-10-30 14:16:19.499784
1472	1352	3560070303076	\N	\N	f	2025-10-30 14:16:19.499784
1473	1353	3560070309542	\N	\N	f	2025-10-30 14:16:19.499784
1474	1354	3560070319107	\N	\N	f	2025-10-30 14:16:19.499784
1475	1355	3560070319169	\N	\N	f	2025-10-30 14:16:19.499784
1476	1356	3560070319220	\N	\N	f	2025-10-30 14:16:19.499784
1477	1357	3560070319961	\N	\N	f	2025-10-30 14:16:19.499784
1478	1358	3560070320288	\N	\N	f	2025-10-30 14:16:19.499784
1479	1274	3560070322787	\N	\N	f	2025-10-30 14:16:19.499784
1480	1359	3560070322817	\N	\N	f	2025-10-30 14:16:19.499784
1481	1360	3560070323036	\N	\N	f	2025-10-30 14:16:19.499784
1482	1361	3560070323067	\N	\N	f	2025-10-30 14:16:19.499784
1483	1362	3560070323289	\N	\N	f	2025-10-30 14:16:19.499784
1484	1363	3560070325580	\N	\N	f	2025-10-30 14:16:19.499784
1485	1364	3560070328062	\N	\N	f	2025-10-30 14:16:19.499784
1486	1365	3560070328826	\N	\N	f	2025-10-30 14:16:19.499784
1487	1168	3560070328857	\N	\N	f	2025-10-30 14:16:19.499784
1488	1366	3560070328888	\N	\N	f	2025-10-30 14:16:19.499784
1489	1367	3560070328918	\N	\N	f	2025-10-30 14:16:19.499784
1490	1368	3560070328949	\N	\N	f	2025-10-30 14:16:19.499784
1491	1369	3560070328970	\N	\N	f	2025-10-30 14:16:19.499784
1492	1370	3560070329038	\N	\N	f	2025-10-30 14:16:19.499784
1493	1371	3560070329120	\N	\N	f	2025-10-30 14:16:19.499784
1494	1372	3560070329151	\N	\N	f	2025-10-30 14:16:19.499784
1495	1373	3560070329182	\N	\N	f	2025-10-30 14:16:19.499784
1496	1373	3560070329410	\N	\N	f	2025-10-30 14:16:19.499784
1497	1374	3560070329472	\N	\N	f	2025-10-30 14:16:19.499784
1498	1375	3560070330201	\N	\N	f	2025-10-30 14:16:19.499784
1499	1376	3560070330515	\N	\N	f	2025-10-30 14:16:19.499784
1500	1377	3560070330744	\N	\N	f	2025-10-30 14:16:19.499784
1501	1378	3560070330805	\N	\N	f	2025-10-30 14:16:19.499784
1502	1149	3560070330959	\N	\N	f	2025-10-30 14:16:19.499784
1503	1149	3560070334919	\N	\N	f	2025-10-30 14:16:19.499784
1504	1361	3560070334940	\N	\N	f	2025-10-30 14:16:19.499784
1505	1379	3560070335060	\N	\N	f	2025-10-30 14:16:19.499784
1506	1380	3560070335183	\N	\N	f	2025-10-30 14:16:19.499784
1507	1381	3560070339495	\N	\N	f	2025-10-30 14:16:19.499784
1508	1376	3560070339679	\N	\N	f	2025-10-30 14:16:19.499784
1509	1382	3560070339709	\N	\N	f	2025-10-30 14:16:19.499784
1510	1382	3560070339730	\N	\N	f	2025-10-30 14:16:19.499784
1511	1383	3560070340224	\N	\N	f	2025-10-30 14:16:19.499784
1512	1384	3560070340316	\N	\N	f	2025-10-30 14:16:19.499784
1513	1385	3560070340378	\N	\N	f	2025-10-30 14:16:19.499784
1514	1385	3560070340408	\N	\N	f	2025-10-30 14:16:19.499784
1515	1386	3560070340439	\N	\N	f	2025-10-30 14:16:19.499784
1516	1387	3560070341801	\N	\N	f	2025-10-30 14:16:19.499784
1517	1387	3560070341832	\N	\N	f	2025-10-30 14:16:19.499784
1518	1388	3560070342167	\N	\N	f	2025-10-30 14:16:19.499784
1519	1389	3560070342464	\N	\N	f	2025-10-30 14:16:19.499784
1520	1390	3560070342495	\N	\N	f	2025-10-30 14:16:19.499784
1521	1391	3560070342822	\N	\N	f	2025-10-30 14:16:19.499784
1522	1392	3560070343041	\N	\N	f	2025-10-30 14:16:19.499784
1523	1393	3560070343072	\N	\N	f	2025-10-30 14:16:19.499784
1524	1394	3560070344284	\N	\N	f	2025-10-30 14:16:19.499784
1525	1395	3560070350889	\N	\N	f	2025-10-30 14:16:19.499784
1526	1396	3560070355112	\N	\N	f	2025-10-30 14:16:19.499784
1527	1397	3560070359653	\N	\N	f	2025-10-30 14:16:19.499784
1528	1398	3560070359684	\N	\N	f	2025-10-30 14:16:19.499784
1529	1399	3560070361427	\N	\N	f	2025-10-30 14:16:19.499784
1530	1400	3560070361946	\N	\N	f	2025-10-30 14:16:19.499784
1531	1401	3560070368143	\N	\N	f	2025-10-30 14:16:19.499784
1532	1402	3560070368433	\N	\N	f	2025-10-30 14:16:19.499784
1533	1403	3560070368464	\N	\N	f	2025-10-30 14:16:19.499784
1534	1404	3560070368495	\N	\N	f	2025-10-30 14:16:19.499784
1535	1217	3560070369690	\N	\N	f	2025-10-30 14:16:19.499784
1536	1405	3560070369720	\N	\N	f	2025-10-30 14:16:19.499784
1537	1406	3560070370344	\N	\N	f	2025-10-30 14:16:19.499784
1538	1407	3560070371891	\N	\N	f	2025-10-30 14:16:19.499784
1539	1408	3560070378067	\N	\N	f	2025-10-30 14:16:19.499784
1540	1409	3560070378098	\N	\N	f	2025-10-30 14:16:19.499784
1541	1410	3560070379323	\N	\N	f	2025-10-30 14:16:19.499784
1542	1411	3560070379736	\N	\N	f	2025-10-30 14:16:19.499784
1543	1412	3560070386291	\N	\N	f	2025-10-30 14:16:19.499784
1544	1413	3560070386659	\N	\N	f	2025-10-30 14:16:19.499784
1545	1414	3560070387427	\N	\N	f	2025-10-30 14:16:19.499784
1546	1415	3560070393589	\N	\N	f	2025-10-30 14:16:19.499784
1547	1168	3560070393619	\N	\N	f	2025-10-30 14:16:19.499784
1548	1416	3560070396948	\N	\N	f	2025-10-30 14:16:19.499784
1549	1417	3560070400829	\N	\N	f	2025-10-30 14:16:19.499784
1550	1418	3560070401338	\N	\N	f	2025-10-30 14:16:19.499784
1551	1419	3560070403011	\N	\N	f	2025-10-30 14:16:19.499784
1552	1419	3560070404506	\N	\N	f	2025-10-30 14:16:19.499784
1553	1420	3560070405022	\N	\N	f	2025-10-30 14:16:19.499784
1554	1421	3560070406845	\N	\N	f	2025-10-30 14:16:19.499784
1555	1422	3560070407385	\N	\N	f	2025-10-30 14:16:19.499784
1556	1414	3560070409976	\N	\N	f	2025-10-30 14:16:19.499784
1557	1423	3560070410002	\N	\N	f	2025-10-30 14:16:19.499784
1558	1424	3560070412150	\N	\N	f	2025-10-30 14:16:19.499784
1559	1425	3560070415724	\N	\N	f	2025-10-30 14:16:19.499784
1560	1426	3560070418299	\N	\N	f	2025-10-30 14:16:19.499784
1561	1427	3560070418329	\N	\N	f	2025-10-30 14:16:19.499784
1562	1428	3560070419968	\N	\N	f	2025-10-30 14:16:19.499784
1563	1429	3560070420148	\N	\N	f	2025-10-30 14:16:19.499784
1564	1430	3560070420179	\N	\N	f	2025-10-30 14:16:19.499784
1565	1431	3560070420254	\N	\N	f	2025-10-30 14:16:19.499784
1566	1430	3560070421428	\N	\N	f	2025-10-30 14:16:19.499784
1567	1432	3560070423088	\N	\N	f	2025-10-30 14:16:19.499784
1568	1433	3560070423163	\N	\N	f	2025-10-30 14:16:19.499784
1569	1434	3560070427048	\N	\N	f	2025-10-30 14:16:19.499784
1570	1435	3560070427673	\N	\N	f	2025-10-30 14:16:19.499784
1571	1436	3560070427857	\N	\N	f	2025-10-30 14:16:19.499784
1572	1437	3560070429035	\N	\N	f	2025-10-30 14:16:19.499784
1573	1438	3560070429080	\N	\N	f	2025-10-30 14:16:19.499784
1574	1439	3560070429110	\N	\N	f	2025-10-30 14:16:19.499784
1575	1440	3560070430901	\N	\N	f	2025-10-30 14:16:19.499784
1576	1440	3560070430994	\N	\N	f	2025-10-30 14:16:19.499784
1577	1441	3560070434138	\N	\N	f	2025-10-30 14:16:19.499784
1578	1442	3560070434893	\N	\N	f	2025-10-30 14:16:19.499784
1579	1410	3560070438686	\N	\N	f	2025-10-30 14:16:19.499784
1580	1443	3560070439140	\N	\N	f	2025-10-30 14:16:19.499784
1581	1444	3560070439881	\N	\N	f	2025-10-30 14:16:19.499784
1582	1445	3560070441051	\N	\N	f	2025-10-30 14:16:19.499784
1583	1131	3560070443291	\N	\N	f	2025-10-30 14:16:19.499784
1584	1446	3560070445493	\N	\N	f	2025-10-30 14:16:19.499784
1585	1446	3560070445523	\N	\N	f	2025-10-30 14:16:19.499784
1586	1447	3560070446117	\N	\N	f	2025-10-30 14:16:19.499784
1587	1448	3560070450190	\N	\N	f	2025-10-30 14:16:19.499784
1588	1449	3560070450220	\N	\N	f	2025-10-30 14:16:19.499784
1589	1450	3560070454921	\N	\N	f	2025-10-30 14:16:19.499784
1590	1451	3560070454952	\N	\N	f	2025-10-30 14:16:19.499784
1591	1452	3560070456352	\N	\N	f	2025-10-30 14:16:19.499784
1592	1453	3560070464319	\N	\N	f	2025-10-30 14:16:19.499784
1593	1454	3560070464340	\N	\N	f	2025-10-30 14:16:19.499784
1594	1455	3560070464739	\N	\N	f	2025-10-30 14:16:19.499784
1595	1414	3560070464760	\N	\N	f	2025-10-30 14:16:19.499784
1596	1456	3560070464821	\N	\N	f	2025-10-30 14:16:19.499784
1597	1456	3560070464852	\N	\N	f	2025-10-30 14:16:19.499784
1598	1457	3560070465491	\N	\N	f	2025-10-30 14:16:19.499784
1599	1141	3560070472918	\N	\N	f	2025-10-30 14:16:19.499784
1600	1141	3560070472949	\N	\N	f	2025-10-30 14:16:19.499784
1601	1141	3560070472970	\N	\N	f	2025-10-30 14:16:19.499784
1602	1458	3560070473885	\N	\N	f	2025-10-30 14:16:19.499784
1603	1218	3560070473915	\N	\N	f	2025-10-30 14:16:19.499784
1604	1459	3560070475834	\N	\N	f	2025-10-30 14:16:19.499784
1605	1460	3560070475964	\N	\N	f	2025-10-30 14:16:19.499784
1606	1461	3560070477197	\N	\N	f	2025-10-30 14:16:19.499784
1607	1462	3560070477340	\N	\N	f	2025-10-30 14:16:19.499784
1608	1463	3560070477371	\N	\N	f	2025-10-30 14:16:19.499784
1609	1464	3560070478316	\N	\N	f	2025-10-30 14:16:19.499784
1610	1465	3560070478699	\N	\N	f	2025-10-30 14:16:19.499784
1611	1466	3560070478750	\N	\N	f	2025-10-30 14:16:19.499784
1612	1467	3560070478781	\N	\N	f	2025-10-30 14:16:19.499784
1613	1468	3560070478811	\N	\N	f	2025-10-30 14:16:19.499784
1614	1469	3560070479467	\N	\N	f	2025-10-30 14:16:19.499784
1615	1470	3560070479580	\N	\N	f	2025-10-30 14:16:19.499784
1616	1471	3560070479702	\N	\N	f	2025-10-30 14:16:19.499784
1617	1472	3560070480135	\N	\N	f	2025-10-30 14:16:19.499784
1618	1473	3560070482238	\N	\N	f	2025-10-30 14:16:19.499784
1619	1474	3560070482757	\N	\N	f	2025-10-30 14:16:19.499784
1620	1475	3560070484225	\N	\N	f	2025-10-30 14:16:19.499784
1621	1476	3560070484768	\N	\N	f	2025-10-30 14:16:19.499784
1622	1477	3560070485581	\N	\N	f	2025-10-30 14:16:19.499784
1623	1478	3560070486243	\N	\N	f	2025-10-30 14:16:19.499784
1624	1479	3560070486274	\N	\N	f	2025-10-30 14:16:19.499784
1625	1480	3560070490707	\N	\N	f	2025-10-30 14:16:19.499784
1626	1481	3560070490769	\N	\N	f	2025-10-30 14:16:19.499784
1627	1482	3560070494224	\N	\N	f	2025-10-30 14:16:19.499784
1628	1482	3560070494255	\N	\N	f	2025-10-30 14:16:19.499784
1629	1483	3560070497164	\N	\N	f	2025-10-30 14:16:19.499784
1630	1484	3560070499366	\N	\N	f	2025-10-30 14:16:19.499784
1631	1485	3560070500406	\N	\N	f	2025-10-30 14:16:19.499784
1632	1486	3560070502004	\N	\N	f	2025-10-30 14:16:19.499784
1633	1487	3560070503209	\N	\N	f	2025-10-30 14:16:19.499784
1634	1488	3560070504794	\N	\N	f	2025-10-30 14:16:19.499784
1635	1489	3560070504824	\N	\N	f	2025-10-30 14:16:19.499784
1636	1490	3560070507696	\N	\N	f	2025-10-30 14:16:19.499784
1637	1430	3560070508495	\N	\N	f	2025-10-30 14:16:19.499784
1638	1491	3560070510047	\N	\N	f	2025-10-30 14:16:19.499784
1639	1491	3560070510078	\N	\N	f	2025-10-30 14:16:19.499784
1640	1492	3560070510108	\N	\N	f	2025-10-30 14:16:19.499784
1641	1493	3560070513208	\N	\N	f	2025-10-30 14:16:19.499784
1642	1494	3560070519309	\N	\N	f	2025-10-30 14:16:19.499784
1643	1495	3560070520596	\N	\N	f	2025-10-30 14:16:19.499784
1644	1496	3560070520862	\N	\N	f	2025-10-30 14:16:19.499784
1645	1497	3560070521715	\N	\N	f	2025-10-30 14:16:19.499784
1646	1498	3560070526703	\N	\N	f	2025-10-30 14:16:19.499784
1647	1499	3560070526758	\N	\N	f	2025-10-30 14:16:19.499784
1648	1500	3560070526789	\N	\N	f	2025-10-30 14:16:19.499784
1649	1500	3560070530021	\N	\N	f	2025-10-30 14:16:19.499784
1650	1501	3560070530748	\N	\N	f	2025-10-30 14:16:19.499784
1651	1502	3560070531424	\N	\N	f	2025-10-30 14:16:19.499784
1652	1503	3560070531455	\N	\N	f	2025-10-30 14:16:19.499784
1653	1504	3560070532308	\N	\N	f	2025-10-30 14:16:19.499784
1654	1505	3560070535224	\N	\N	f	2025-10-30 14:16:19.499784
1655	1506	3560070544714	\N	\N	f	2025-10-30 14:16:19.499784
1656	1507	3560070546848	\N	\N	f	2025-10-30 14:16:19.499784
1657	1508	3560070546879	\N	\N	f	2025-10-30 14:16:19.499784
1658	1509	3560070553808	\N	\N	f	2025-10-30 14:16:19.499784
1659	1510	3560070553990	\N	\N	f	2025-10-30 14:16:19.499784
1660	1510	3560070554027	\N	\N	f	2025-10-30 14:16:19.499784
1661	1511	3560070555307	\N	\N	f	2025-10-30 14:16:19.499784
1662	1512	3560070555369	\N	\N	f	2025-10-30 14:16:19.499784
1663	1168	3560070555390	\N	\N	f	2025-10-30 14:16:19.499784
1664	1513	3560070558179	\N	\N	f	2025-10-30 14:16:19.499784
1665	1187	3560070558636	\N	\N	f	2025-10-30 14:16:19.499784
1666	1514	3560070558667	\N	\N	f	2025-10-30 14:16:19.499784
1667	1515	3560070558759	\N	\N	f	2025-10-30 14:16:19.499784
1668	1516	3560070558841	\N	\N	f	2025-10-30 14:16:19.499784
1669	1517	3560070563166	\N	\N	f	2025-10-30 14:16:19.499784
1670	1518	3560070574438	\N	\N	f	2025-10-30 14:16:19.499784
1671	1519	3560070577323	\N	\N	f	2025-10-30 14:16:19.499784
1672	1520	3560070582884	\N	\N	f	2025-10-30 14:16:19.499784
1673	1521	3560070584338	\N	\N	f	2025-10-30 14:16:19.499784
1674	1522	3560070588725	\N	\N	f	2025-10-30 14:16:19.499784
1675	1523	3560070593996	\N	\N	f	2025-10-30 14:16:19.499784
1676	1168	3560070594351	\N	\N	f	2025-10-30 14:16:19.499784
1677	1168	3560070595525	\N	\N	f	2025-10-30 14:16:19.499784
1678	1524	3560070595587	\N	\N	f	2025-10-30 14:16:19.499784
1679	1524	3560070600540	\N	\N	f	2025-10-30 14:16:19.499784
1680	1131	3560070600946	\N	\N	f	2025-10-30 14:16:19.499784
1681	1525	3560070600977	\N	\N	f	2025-10-30 14:16:19.499784
1682	1526	3560070604319	\N	\N	f	2025-10-30 14:16:19.499784
1683	1526	3560070606702	\N	\N	f	2025-10-30 14:16:19.499784
1684	1527	3560070607709	\N	\N	f	2025-10-30 14:16:19.499784
1685	1528	3560070609253	\N	\N	f	2025-10-30 14:16:19.499784
1686	1529	3560070612130	\N	\N	f	2025-10-30 14:16:19.499784
1687	1530	3560070612161	\N	\N	f	2025-10-30 14:16:19.499784
1688	1168	3560070614202	\N	\N	f	2025-10-30 14:16:19.499784
1689	1531	3560070617593	\N	\N	f	2025-10-30 14:16:19.499784
1690	1532	3560070617982	\N	\N	f	2025-10-30 14:16:19.499784
1691	1533	3560070618293	\N	\N	f	2025-10-30 14:16:19.499784
1692	1534	3560070618385	\N	\N	f	2025-10-30 14:16:19.499784
1693	1331	3560070618415	\N	\N	f	2025-10-30 14:16:19.499784
1694	1535	3560070618767	\N	\N	f	2025-10-30 14:16:19.499784
1695	1536	3560070621316	\N	\N	f	2025-10-30 14:16:19.499784
1696	1536	3560070621347	\N	\N	f	2025-10-30 14:16:19.499784
1697	1537	3560070657483	\N	\N	f	2025-10-30 14:16:19.499784
1698	1538	3560070658053	\N	\N	f	2025-10-30 14:16:19.499784
1699	1539	3560070659517	\N	\N	f	2025-10-30 14:16:19.499784
1700	1540	3560070668717	\N	\N	f	2025-10-30 14:16:19.499784
1701	1541	3560070669288	\N	\N	f	2025-10-30 14:16:19.499784
1702	1542	3560070669349	\N	\N	f	2025-10-30 14:16:19.499784
1703	1543	3560070669813	\N	\N	f	2025-10-30 14:16:19.499784
1704	1543	3560070669844	\N	\N	f	2025-10-30 14:16:19.499784
1705	1541	3560070669875	\N	\N	f	2025-10-30 14:16:19.499784
1706	1544	3560070669905	\N	\N	f	2025-10-30 14:16:19.499784
1707	1545	3560070669981	\N	\N	f	2025-10-30 14:16:19.499784
1708	1546	3560070670017	\N	\N	f	2025-10-30 14:16:19.499784
1709	1547	3560070671212	\N	\N	f	2025-10-30 14:16:19.499784
1710	1547	3560070677498	\N	\N	f	2025-10-30 14:16:19.499784
1711	1185	3560070677795	\N	\N	f	2025-10-30 14:16:19.499784
1712	1548	3560070679751	\N	\N	f	2025-10-30 14:16:19.499784
1713	1548	3560070680016	\N	\N	f	2025-10-30 14:16:19.499784
1714	1549	3560070680733	\N	\N	f	2025-10-30 14:16:19.499784
1715	1550	3560070682683	\N	\N	f	2025-10-30 14:16:19.499784
1716	1551	3560070685646	\N	\N	f	2025-10-30 14:16:19.499784
1717	1552	3560070686544	\N	\N	f	2025-10-30 14:16:19.499784
1718	1553	3560070689569	\N	\N	f	2025-10-30 14:16:19.499784
1719	1554	3000046136678	\N	\N	f	2025-10-30 14:16:19.499784
1720	1555	3000046136746	\N	\N	f	2025-10-30 14:16:19.499784
1721	1556	3000046136777	\N	\N	f	2025-10-30 14:16:19.499784
1722	1557	3000046137125	\N	\N	f	2025-10-30 14:16:19.499784
1723	1558	3000047136646	\N	\N	f	2025-10-30 14:16:19.499784
1724	1558	3000047137087	\N	\N	f	2025-10-30 14:16:19.499784
1725	1559	3033124672508	\N	\N	f	2025-10-30 14:16:19.499784
1726	1560	3143320004185	\N	\N	f	2025-10-30 14:16:19.499784
1727	1561	3184830031896	\N	\N	f	2025-10-30 14:16:19.499784
1728	1562	3184830031940	\N	\N	f	2025-10-30 14:16:19.499784
1729	1563	3184830031957	\N	\N	f	2025-10-30 14:16:19.499784
1730	1564	3184830031964	\N	\N	f	2025-10-30 14:16:19.499784
1731	1565	3184830031971	\N	\N	f	2025-10-30 14:16:19.499784
1732	1566	3184830032190	\N	\N	f	2025-10-30 14:16:19.499784
1733	1566	3184830032220	\N	\N	f	2025-10-30 14:16:19.499784
1734	1567	3184830032251	\N	\N	f	2025-10-30 14:16:19.499784
1735	1568	3184830032763	\N	\N	f	2025-10-30 14:16:19.499784
1736	1568	3184830032787	\N	\N	f	2025-10-30 14:16:19.499784
1737	1568	3184830032794	\N	\N	f	2025-10-30 14:16:19.499784
1738	1569	3184830032800	\N	\N	f	2025-10-30 14:16:19.499784
1739	1570	3184830032916	\N	\N	f	2025-10-30 14:16:19.499784
1740	1571	3184830034002	\N	\N	f	2025-10-30 14:16:19.499784
1741	1571	3184830034507	\N	\N	f	2025-10-30 14:16:19.499784
1742	1572	3184830034552	\N	\N	f	2025-10-30 14:16:19.499784
1743	1573	3184830034897	\N	\N	f	2025-10-30 14:16:19.499784
1744	1573	3184830034927	\N	\N	f	2025-10-30 14:16:19.499784
1745	1574	3184830034958	\N	\N	f	2025-10-30 14:16:19.499784
1746	1575	3184830035757	\N	\N	f	2025-10-30 14:16:19.499784
1747	1576	3184830035788	\N	\N	f	2025-10-30 14:16:19.499784
1748	1577	3184830054888	\N	\N	f	2025-10-30 14:16:19.499784
1749	1577	3184830054956	\N	\N	f	2025-10-30 14:16:19.499784
1750	1578	3184830061350	\N	\N	f	2025-10-30 14:16:19.499784
1751	1578	3184830063613	\N	\N	f	2025-10-30 14:16:19.499784
1752	1579	3184830065235	\N	\N	f	2025-10-30 14:16:19.499784
1753	1580	3184830065242	\N	\N	f	2025-10-30 14:16:19.499784
1754	1581	3184830066461	\N	\N	f	2025-10-30 14:16:19.499784
1755	1582	3184830066904	\N	\N	f	2025-10-30 14:16:19.499784
1756	1583	3184830067833	\N	\N	f	2025-10-30 14:16:19.499784
1757	1583	3184830101407	\N	\N	f	2025-10-30 14:16:19.499784
1758	1584	3184830101896	\N	\N	f	2025-10-30 14:16:19.499784
1759	1585	3245390021182	\N	\N	f	2025-10-30 14:16:19.499784
1760	1586	3245390021212	\N	\N	f	2025-10-30 14:16:19.499784
1761	1586	3245390021229	\N	\N	f	2025-10-30 14:16:19.499784
1762	1587	3245390021298	\N	\N	f	2025-10-30 14:16:19.499784
1763	1588	3245390026002	\N	\N	f	2025-10-30 14:16:19.499784
1764	1589	3245390028884	\N	\N	f	2025-10-30 14:16:19.499784
1765	1589	3245390037794	\N	\N	f	2025-10-30 14:16:19.499784
1766	1590	3245390038531	\N	\N	f	2025-10-30 14:16:19.499784
1767	1591	3245390048660	\N	\N	f	2025-10-30 14:16:19.499784
1768	1592	3245390068675	\N	\N	f	2025-10-30 14:16:19.499784
1769	1593	3245390068682	\N	\N	f	2025-10-30 14:16:19.499784
1770	1594	3245390089816	\N	\N	f	2025-10-30 14:16:19.499784
1771	1595	3245390089854	\N	\N	f	2025-10-30 14:16:19.499784
1772	1596	3245390134721	\N	\N	f	2025-10-30 14:16:19.499784
1773	1597	3245390135803	\N	\N	f	2025-10-30 14:16:19.499784
1774	1598	3245390138323	\N	\N	f	2025-10-30 14:16:19.499784
1775	1599	3245390208538	\N	\N	f	2025-10-30 14:16:19.499784
1776	1600	3245390222206	\N	\N	f	2025-10-30 14:16:19.499784
1777	1600	3245390222497	\N	\N	f	2025-10-30 14:16:19.499784
1778	1601	3245390227171	\N	\N	f	2025-10-30 14:16:19.499784
1779	1602	3245390233714	\N	\N	f	2025-10-30 14:16:19.499784
1780	1225	3245411155346	\N	\N	f	2025-10-30 14:16:19.499784
1781	1603	3245411171193	\N	\N	f	2025-10-30 14:16:19.499784
1782	1225	3245411171230	\N	\N	f	2025-10-30 14:16:19.499784
1783	1133	3245411205621	\N	\N	f	2025-10-30 14:16:19.499784
1784	1604	3245411217969	\N	\N	f	2025-10-30 14:16:19.499784
1785	1605	3245411236366	\N	\N	f	2025-10-30 14:16:19.499784
1786	1606	3245411307769	\N	\N	f	2025-10-30 14:16:19.499784
1787	1607	3245411439897	\N	\N	f	2025-10-30 14:16:19.499784
1788	1608	3245411439903	\N	\N	f	2025-10-30 14:16:19.499784
1789	1609	3245411440176	\N	\N	f	2025-10-30 14:16:19.499784
1790	1610	3245411442132	\N	\N	f	2025-10-30 14:16:19.499784
1791	1610	3245411442262	\N	\N	f	2025-10-30 14:16:19.499784
1792	1610	3245411640903	\N	\N	f	2025-10-30 14:16:19.499784
1793	1611	3245411640972	\N	\N	f	2025-10-30 14:16:19.499784
1794	1602	3245411692834	\N	\N	f	2025-10-30 14:16:19.499784
1795	1602	3245411730581	\N	\N	f	2025-10-30 14:16:19.499784
1796	1612	3245411816278	\N	\N	f	2025-10-30 14:16:19.499784
1797	1613	3245411851149	\N	\N	f	2025-10-30 14:16:19.499784
1798	1614	3245411891800	\N	\N	f	2025-10-30 14:16:19.499784
1799	1265	3245411891855	\N	\N	f	2025-10-30 14:16:19.499784
1800	1615	3245412001444	\N	\N	f	2025-10-30 14:16:19.499784
1801	1616	3245412051661	\N	\N	f	2025-10-30 14:16:19.499784
1802	1617	3245412059346	\N	\N	f	2025-10-30 14:16:19.499784
1803	1618	3245412059377	\N	\N	f	2025-10-30 14:16:19.499784
1804	1619	3245412062674	\N	\N	f	2025-10-30 14:16:19.499784
1805	1620	3245412064562	\N	\N	f	2025-10-30 14:16:19.499784
1806	1621	3245412149085	\N	\N	f	2025-10-30 14:16:19.499784
1807	1622	3245412149146	\N	\N	f	2025-10-30 14:16:19.499784
1808	1623	3245412149269	\N	\N	f	2025-10-30 14:16:19.499784
1809	1623	3245412158759	\N	\N	f	2025-10-30 14:16:19.499784
1810	1624	3245412158780	\N	\N	f	2025-10-30 14:16:19.499784
1811	1625	3245412158872	\N	\N	f	2025-10-30 14:16:19.499784
1812	1626	3245412194825	\N	\N	f	2025-10-30 14:16:19.499784
1813	1627	3245412291029	\N	\N	f	2025-10-30 14:16:19.499784
1814	1603	3245412379987	\N	\N	f	2025-10-30 14:16:19.499784
1815	1628	3245412404375	\N	\N	f	2025-10-30 14:16:19.499784
1816	1133	3245412404405	\N	\N	f	2025-10-30 14:16:19.499784
1817	1133	3245412414466	\N	\N	f	2025-10-30 14:16:19.499784
1818	1629	3245412435263	\N	\N	f	2025-10-30 14:16:19.499784
1819	1630	3245412477430	\N	\N	f	2025-10-30 14:16:19.499784
1820	1461	3245412477447	\N	\N	f	2025-10-30 14:16:19.499784
1821	1631	3245412477478	\N	\N	f	2025-10-30 14:16:19.499784
1822	1632	3245412567216	\N	\N	f	2025-10-30 14:16:19.499784
1823	1632	3245412567223	\N	\N	f	2025-10-30 14:16:19.499784
1824	1633	3245412570490	\N	\N	f	2025-10-30 14:16:19.499784
1825	1634	3245412570650	\N	\N	f	2025-10-30 14:16:19.499784
1826	1634	3245412570667	\N	\N	f	2025-10-30 14:16:19.499784
1827	1635	3245412697739	\N	\N	f	2025-10-30 14:16:19.499784
1828	1636	3245412729829	\N	\N	f	2025-10-30 14:16:19.499784
1829	1637	3245412730764	\N	\N	f	2025-10-30 14:16:19.499784
1830	1637	3245412730771	\N	\N	f	2025-10-30 14:16:19.499784
1831	1638	3245412730870	\N	\N	f	2025-10-30 14:16:19.499784
1832	1639	3245412735530	\N	\N	f	2025-10-30 14:16:19.499784
1833	1639	3245412749018	\N	\N	f	2025-10-30 14:16:19.499784
1834	1640	3245412782824	\N	\N	f	2025-10-30 14:16:19.499784
1835	1641	3245412793165	\N	\N	f	2025-10-30 14:16:19.499784
1836	1641	3245412824968	\N	\N	f	2025-10-30 14:16:19.499784
1837	1642	3245412846991	\N	\N	f	2025-10-30 14:16:19.499784
1838	1642	3245412847059	\N	\N	f	2025-10-30 14:16:19.499784
1839	1643	3245412950872	\N	\N	f	2025-10-30 14:16:19.499784
1840	1644	3245412978180	\N	\N	f	2025-10-30 14:16:19.499784
1841	1645	3245412991349	\N	\N	f	2025-10-30 14:16:19.499784
1842	1646	3245412997785	\N	\N	f	2025-10-30 14:16:19.499784
1843	1647	3245413153449	\N	\N	f	2025-10-30 14:16:19.499784
1844	1648	3245413153647	\N	\N	f	2025-10-30 14:16:19.499784
1845	1649	3245413157522	\N	\N	f	2025-10-30 14:16:19.499784
1846	1650	3245413161840	\N	\N	f	2025-10-30 14:16:19.499784
1847	1651	3245413162595	\N	\N	f	2025-10-30 14:16:19.499784
1848	1651	3245413168023	\N	\N	f	2025-10-30 14:16:19.499784
1849	1652	3245413284716	\N	\N	f	2025-10-30 14:16:19.499784
1850	1653	3245413439512	\N	\N	f	2025-10-30 14:16:19.499784
1851	1633	3245413442338	\N	\N	f	2025-10-30 14:16:19.499784
1852	1654	3245413537706	\N	\N	f	2025-10-30 14:16:19.499784
1853	1655	3245413575470	\N	\N	f	2025-10-30 14:16:19.499784
1854	1656	3245413575487	\N	\N	f	2025-10-30 14:16:19.499784
1855	1656	3245413575517	\N	\N	f	2025-10-30 14:16:19.499784
1856	1656	3245413575548	\N	\N	f	2025-10-30 14:16:19.499784
1857	1657	3245413588142	\N	\N	f	2025-10-30 14:16:19.499784
1858	1658	3245413588241	\N	\N	f	2025-10-30 14:16:19.499784
1859	1659	3245413730220	\N	\N	f	2025-10-30 14:16:19.499784
1860	1660	3245413750549	\N	\N	f	2025-10-30 14:16:19.499784
1861	1660	3245413750594	\N	\N	f	2025-10-30 14:16:19.499784
1862	1661	3245413750693	\N	\N	f	2025-10-30 14:16:19.499784
1863	1662	3245413750785	\N	\N	f	2025-10-30 14:16:19.499784
1864	1662	3245413750846	\N	\N	f	2025-10-30 14:16:19.499784
1865	1663	3245413771483	\N	\N	f	2025-10-30 14:16:19.499784
1866	1664	3245413812254	\N	\N	f	2025-10-30 14:16:19.499784
1867	1665	3245413812261	\N	\N	f	2025-10-30 14:16:19.499784
1868	1666	3245413812292	\N	\N	f	2025-10-30 14:16:19.499784
1869	1666	3245413812322	\N	\N	f	2025-10-30 14:16:19.499784
1870	1667	3245413821614	\N	\N	f	2025-10-30 14:16:19.499784
1871	1668	3245413824837	\N	\N	f	2025-10-30 14:16:19.499784
1872	1669	3245413841391	\N	\N	f	2025-10-30 14:16:19.499784
1873	1670	3245413852717	\N	\N	f	2025-10-30 14:16:19.499784
1874	1670	3245413865151	\N	\N	f	2025-10-30 14:16:19.499784
1875	1671	3245413870056	\N	\N	f	2025-10-30 14:16:19.499784
1876	1672	3245414076440	\N	\N	f	2025-10-30 14:16:19.499784
1877	1672	3245414087965	\N	\N	f	2025-10-30 14:16:19.499784
1878	1666	3245414091023	\N	\N	f	2025-10-30 14:16:19.499784
1879	1673	3245414091078	\N	\N	f	2025-10-30 14:16:19.499784
1880	1674	3245414091221	\N	\N	f	2025-10-30 14:16:19.499784
1881	1675	3245414091238	\N	\N	f	2025-10-30 14:16:19.499784
1882	1676	3245414094741	\N	\N	f	2025-10-30 14:16:19.499784
1883	1677	3245414098756	\N	\N	f	2025-10-30 14:16:19.499784
1884	1133	3245414117259	\N	\N	f	2025-10-30 14:16:19.499784
1885	1163	3245414117457	\N	\N	f	2025-10-30 14:16:19.499784
1886	1678	3245414144705	\N	\N	f	2025-10-30 14:16:19.499784
1887	1679	3245414187498	\N	\N	f	2025-10-30 14:16:19.499784
1888	1680	3245414229297	\N	\N	f	2025-10-30 14:16:19.499784
1889	1681	3245414250772	\N	\N	f	2025-10-30 14:16:19.499784
1890	1682	3245414491915	\N	\N	f	2025-10-30 14:16:19.499784
1891	1331	3245414510128	\N	\N	f	2025-10-30 14:16:19.499784
1892	1683	3245414594586	\N	\N	f	2025-10-30 14:16:19.499784
1893	1684	3245414637696	\N	\N	f	2025-10-30 14:16:19.499784
1894	1685	3245414638853	\N	\N	f	2025-10-30 14:16:19.499784
1895	1685	3245414638938	\N	\N	f	2025-10-30 14:16:19.499784
1896	1686	3245414658769	\N	\N	f	2025-10-30 14:16:19.499784
1897	1687	3245414663398	\N	\N	f	2025-10-30 14:16:19.499784
1898	1687	3245414663497	\N	\N	f	2025-10-30 14:16:19.499784
1899	1688	3245414667341	\N	\N	f	2025-10-30 14:16:19.499784
1900	1689	3245414667990	\N	\N	f	2025-10-30 14:16:19.499784
1901	1133	3245414669574	\N	\N	f	2025-10-30 14:16:19.499784
1902	1690	3245414777873	\N	\N	f	2025-10-30 14:16:19.499784
1903	1690	3245414777958	\N	\N	f	2025-10-30 14:16:19.499784
1904	1690	3245414778047	\N	\N	f	2025-10-30 14:16:19.499784
1905	1691	3245415074117	\N	\N	f	2025-10-30 14:16:19.499784
1906	1692	3245415074148	\N	\N	f	2025-10-30 14:16:19.499784
1907	1662	3245415074179	\N	\N	f	2025-10-30 14:16:19.499784
1908	1662	3245415074209	\N	\N	f	2025-10-30 14:16:19.499784
1909	1693	3245415074230	\N	\N	f	2025-10-30 14:16:19.499784
1910	1694	3245415074261	\N	\N	f	2025-10-30 14:16:19.499784
1911	1694	3245415327282	\N	\N	f	2025-10-30 14:16:19.499784
1912	1695	3245415327299	\N	\N	f	2025-10-30 14:16:19.499784
1913	1696	3245415327404	\N	\N	f	2025-10-30 14:16:19.499784
1914	1697	3245415330381	\N	\N	f	2025-10-30 14:16:19.499784
1915	1698	3245415395083	\N	\N	f	2025-10-30 14:16:19.499784
1916	1699	3245415620949	\N	\N	f	2025-10-30 14:16:19.499784
1917	1700	3245415635967	\N	\N	f	2025-10-30 14:16:19.499784
1918	1700	3245415702775	\N	\N	f	2025-10-30 14:16:19.499784
1919	1701	3245415851350	\N	\N	f	2025-10-30 14:16:19.499784
1920	1701	3245415851367	\N	\N	f	2025-10-30 14:16:19.499784
1921	1702	3245415851374	\N	\N	f	2025-10-30 14:16:19.499784
1922	1703	3245415851381	\N	\N	f	2025-10-30 14:16:19.499784
1923	1703	3245415851435	\N	\N	f	2025-10-30 14:16:19.499784
1924	1703	3245415851459	\N	\N	f	2025-10-30 14:16:19.499784
1925	1703	3245415887533	\N	\N	f	2025-10-30 14:16:19.499784
1926	1704	3245415888325	\N	\N	f	2025-10-30 14:16:19.499784
1927	1705	3245415888332	\N	\N	f	2025-10-30 14:16:19.499784
1928	1705	3245415897891	\N	\N	f	2025-10-30 14:16:19.499784
1929	1706	3245415899109	\N	\N	f	2025-10-30 14:16:19.499784
1930	1707	3270190020073	\N	\N	f	2025-10-30 14:16:19.499784
1931	1707	3270190020295	\N	\N	f	2025-10-30 14:16:19.499784
1932	1708	3270190020356	\N	\N	f	2025-10-30 14:16:19.499784
1933	1387	3270190020417	\N	\N	f	2025-10-30 14:16:19.499784
1934	1709	3270190020561	\N	\N	f	2025-10-30 14:16:19.499784
1935	1710	3270190020653	\N	\N	f	2025-10-30 14:16:19.499784
1936	1711	3270190020660	\N	\N	f	2025-10-30 14:16:19.499784
1937	1711	3270190020684	\N	\N	f	2025-10-30 14:16:19.499784
1938	1712	3270190020868	\N	\N	f	2025-10-30 14:16:19.499784
1939	1713	3270190020875	\N	\N	f	2025-10-30 14:16:19.499784
1940	1714	3270190020929	\N	\N	f	2025-10-30 14:16:19.499784
1941	1715	3270190020936	\N	\N	f	2025-10-30 14:16:19.499784
1942	1716	3270190020998	\N	\N	f	2025-10-30 14:16:19.499784
1943	1717	3270190021001	\N	\N	f	2025-10-30 14:16:19.499784
1944	1718	3270190021049	\N	\N	f	2025-10-30 14:16:19.499784
1945	1715	3270190021087	\N	\N	f	2025-10-30 14:16:19.499784
1946	1719	3270190021100	\N	\N	f	2025-10-30 14:16:19.499784
1947	1720	3270190021179	\N	\N	f	2025-10-30 14:16:19.499784
1948	1602	3270190021278	\N	\N	f	2025-10-30 14:16:19.499784
1949	1721	3270190021438	\N	\N	f	2025-10-30 14:16:19.499784
1950	1722	3270190021445	\N	\N	f	2025-10-30 14:16:19.499784
1951	1723	3270190021582	\N	\N	f	2025-10-30 14:16:19.499784
1952	1633	3270190022077	\N	\N	f	2025-10-30 14:16:19.499784
1953	1724	3270190022596	\N	\N	f	2025-10-30 14:16:19.499784
1954	1725	3270190022626	\N	\N	f	2025-10-30 14:16:19.499784
1955	1726	3270190022824	\N	\N	f	2025-10-30 14:16:19.499784
1956	1727	3270190022831	\N	\N	f	2025-10-30 14:16:19.499784
1957	1634	3270190023128	\N	\N	f	2025-10-30 14:16:19.499784
1958	1728	3270190023135	\N	\N	f	2025-10-30 14:16:19.499784
1959	1633	3270190023142	\N	\N	f	2025-10-30 14:16:19.499784
1960	1729	3270190023302	\N	\N	f	2025-10-30 14:16:19.499784
1961	1730	3270190023401	\N	\N	f	2025-10-30 14:16:19.499784
1962	1731	3270190023661	\N	\N	f	2025-10-30 14:16:19.499784
1963	1732	3270190023678	\N	\N	f	2025-10-30 14:16:19.499784
1964	1733	3270190023814	\N	\N	f	2025-10-30 14:16:19.499784
1965	1734	3270190024439	\N	\N	f	2025-10-30 14:16:19.499784
1966	1634	3270190024446	\N	\N	f	2025-10-30 14:16:19.499784
1967	1735	3270190024484	\N	\N	f	2025-10-30 14:16:19.499784
1968	1736	3270190024835	\N	\N	f	2025-10-30 14:16:19.499784
1969	1737	3270190025276	\N	\N	f	2025-10-30 14:16:19.499784
1970	1738	3270190025290	\N	\N	f	2025-10-30 14:16:19.499784
1971	1739	3270190025696	\N	\N	f	2025-10-30 14:16:19.499784
1972	1331	3270190026471	\N	\N	f	2025-10-30 14:16:19.499784
1973	1740	3270190026709	\N	\N	f	2025-10-30 14:16:19.499784
1974	1741	3270190026716	\N	\N	f	2025-10-30 14:16:19.499784
1975	1742	3270190026730	\N	\N	f	2025-10-30 14:16:19.499784
1976	1743	3270190026815	\N	\N	f	2025-10-30 14:16:19.499784
1977	1744	3270190026822	\N	\N	f	2025-10-30 14:16:19.499784
1978	1745	3270190028055	\N	\N	f	2025-10-30 14:16:19.499784
1979	1746	3270190028505	\N	\N	f	2025-10-30 14:16:19.499784
1980	1746	3270190179221	\N	\N	f	2025-10-30 14:16:19.499784
1981	1747	3270190179238	\N	\N	f	2025-10-30 14:16:19.499784
1982	1748	3270190194569	\N	\N	f	2025-10-30 14:16:19.499784
1983	1749	3270190194576	\N	\N	f	2025-10-30 14:16:19.499784
1984	1750	3270190199359	\N	\N	f	2025-10-30 14:16:19.499784
1985	1751	3270190202769	\N	\N	f	2025-10-30 14:16:19.499784
1986	1299	3270190202974	\N	\N	f	2025-10-30 14:16:19.499784
1987	1752	3270190203261	\N	\N	f	2025-10-30 14:16:19.499784
1988	1753	3270190203421	\N	\N	f	2025-10-30 14:16:19.499784
1989	1754	3270190204008	\N	\N	f	2025-10-30 14:16:19.499784
1990	1755	3270190204015	\N	\N	f	2025-10-30 14:16:19.499784
1991	1756	3270190204152	\N	\N	f	2025-10-30 14:16:19.499784
1992	1757	3270190204374	\N	\N	f	2025-10-30 14:16:19.499784
1993	1758	3270190205678	\N	\N	f	2025-10-30 14:16:19.499784
1994	1759	3270190205685	\N	\N	f	2025-10-30 14:16:19.499784
1995	1760	3270190207337	\N	\N	f	2025-10-30 14:16:19.499784
1996	1399	3270190207351	\N	\N	f	2025-10-30 14:16:19.499784
1997	1761	3270190207368	\N	\N	f	2025-10-30 14:16:19.499784
1998	1761	3270190207504	\N	\N	f	2025-10-30 14:16:19.499784
1999	1762	3270190207511	\N	\N	f	2025-10-30 14:16:19.499784
2000	1763	3270190207542	\N	\N	f	2025-10-30 14:16:19.499784
2001	1764	3270190207573	\N	\N	f	2025-10-30 14:16:19.499784
2002	1149	3270190207696	\N	\N	f	2025-10-30 14:16:19.499784
2003	1765	3270190207757	\N	\N	f	2025-10-30 14:16:19.499784
2004	1632	3270190207917	\N	\N	f	2025-10-30 14:16:19.499784
2005	1766	3270190207924	\N	\N	f	2025-10-30 14:16:19.499784
2006	1767	3270190208280	\N	\N	f	2025-10-30 14:16:19.499784
2007	1767	3270190209355	\N	\N	f	2025-10-30 14:16:19.499784
2008	1768	3270190210542	\N	\N	f	2025-10-30 14:16:19.499784
2009	1196	3270190213321	\N	\N	f	2025-10-30 14:16:19.499784
2010	1769	3270190214427	\N	\N	f	2025-10-30 14:16:19.499784
2011	1770	3270190214489	\N	\N	f	2025-10-30 14:16:19.499784
2012	1133	3270190216803	\N	\N	f	2025-10-30 14:16:19.499784
2013	1771	3270190216810	\N	\N	f	2025-10-30 14:16:19.499784
2014	1772	3270190216827	\N	\N	f	2025-10-30 14:16:19.499784
2015	1772	3270190217190	\N	\N	f	2025-10-30 14:16:19.499784
2016	1612	3270190217633	\N	\N	f	2025-10-30 14:16:19.499784
2017	1773	3270190217640	\N	\N	f	2025-10-30 14:16:19.499784
2018	1774	3270190217671	\N	\N	f	2025-10-30 14:16:19.499784
2019	1775	3270190250418	\N	\N	f	2025-10-30 14:16:19.499784
2020	1776	3270190253112	\N	\N	f	2025-10-30 14:16:19.499784
2021	1625	3273230242671	\N	\N	f	2025-10-30 14:16:19.499784
2022	1625	3273230245702	\N	\N	f	2025-10-30 14:16:19.499784
2023	1625	3276550063551	\N	\N	f	2025-10-30 14:16:19.499784
2024	1777	3276550063605	\N	\N	f	2025-10-30 14:16:19.499784
2025	1778	3276550063636	\N	\N	f	2025-10-30 14:16:19.499784
2026	1779	3276550063650	\N	\N	f	2025-10-30 14:16:19.499784
2027	1780	3276550091370	\N	\N	f	2025-10-30 14:16:19.499784
2028	1780	3276550091417	\N	\N	f	2025-10-30 14:16:19.499784
2029	1781	3276550237860	\N	\N	f	2025-10-30 14:16:19.499784
2030	1782	3276550278207	\N	\N	f	2025-10-30 14:16:19.499784
2031	1782	3276550309857	\N	\N	f	2025-10-30 14:16:19.499784
2032	1783	3276550419792	\N	\N	f	2025-10-30 14:16:19.499784
2033	1783	3276552322212	\N	\N	f	2025-10-30 14:16:19.499784
2034	1784	3276555064553	\N	\N	f	2025-10-30 14:16:19.499784
2035	1785	3276555285194	\N	\N	f	2025-10-30 14:16:19.499784
2036	1786	3276555790773	\N	\N	f	2025-10-30 14:16:19.499784
2037	1786	3276556131599	\N	\N	f	2025-10-30 14:16:19.499784
2038	1787	3276556131735	\N	\N	f	2025-10-30 14:16:19.499784
2039	1787	3276556132077	\N	\N	f	2025-10-30 14:16:19.499784
2040	1788	3276556140072	\N	\N	f	2025-10-30 14:16:19.499784
2041	1788	3276556242653	\N	\N	f	2025-10-30 14:16:19.499784
2042	1789	3276556275330	\N	\N	f	2025-10-30 14:16:19.499784
2043	1790	3276557403909	\N	\N	f	2025-10-30 14:16:19.499784
2044	1791	3276557540765	\N	\N	f	2025-10-30 14:16:19.499784
2045	1792	3276557876154	\N	\N	f	2025-10-30 14:16:19.499784
2046	1793	3276557877472	\N	\N	f	2025-10-30 14:16:19.499784
2047	1793	3276557880588	\N	\N	f	2025-10-30 14:16:19.499784
2048	1794	3276557883312	\N	\N	f	2025-10-30 14:16:19.499784
2049	1794	3276557902570	\N	\N	f	2025-10-30 14:16:19.499784
2050	1795	3276557902600	\N	\N	f	2025-10-30 14:16:19.499784
2051	1796	3276557961867	\N	\N	f	2025-10-30 14:16:19.499784
2052	1796	3276557978223	\N	\N	f	2025-10-30 14:16:19.499784
2053	1797	3276557978230	\N	\N	f	2025-10-30 14:16:19.499784
2054	1797	3276557978247	\N	\N	f	2025-10-30 14:16:19.499784
2055	1798	3276557978254	\N	\N	f	2025-10-30 14:16:19.499784
2056	1799	3276558020075	\N	\N	f	2025-10-30 14:16:19.499784
2057	1800	3276558274638	\N	\N	f	2025-10-30 14:16:19.499784
2058	1801	3276558274669	\N	\N	f	2025-10-30 14:16:19.499784
2059	1802	3276558293813	\N	\N	f	2025-10-30 14:16:19.499784
2060	1803	3276558361130	\N	\N	f	2025-10-30 14:16:19.499784
2061	1803	3276558361185	\N	\N	f	2025-10-30 14:16:19.499784
2062	1804	3276558361215	\N	\N	f	2025-10-30 14:16:19.499784
2063	1804	3276558361604	\N	\N	f	2025-10-30 14:16:19.499784
2064	1805	3276558361642	\N	\N	f	2025-10-30 14:16:19.499784
2065	1805	3276559042250	\N	\N	f	2025-10-30 14:16:19.499784
2066	1805	3276559382196	\N	\N	f	2025-10-30 14:16:19.499784
2067	1806	3276559382431	\N	\N	f	2025-10-30 14:16:19.499784
2068	1807	3276559655351	\N	\N	f	2025-10-30 14:16:19.499784
2069	1807	3276559686126	\N	\N	f	2025-10-30 14:16:19.499784
2070	1808	3276559757017	\N	\N	f	2025-10-30 14:16:19.499784
2071	1808	3276559776247	\N	\N	f	2025-10-30 14:16:19.499784
2072	1555	3276559776254	\N	\N	f	2025-10-30 14:16:19.499784
2073	1809	3276559776261	\N	\N	f	2025-10-30 14:16:19.499784
2074	1810	3276559776278	\N	\N	f	2025-10-30 14:16:19.499784
2075	1811	3276559776292	\N	\N	f	2025-10-30 14:16:19.499784
2076	1812	3276559776308	\N	\N	f	2025-10-30 14:16:19.499784
2077	1813	3276559776315	\N	\N	f	2025-10-30 14:16:19.499784
2078	1814	3276559776391	\N	\N	f	2025-10-30 14:16:19.499784
2079	1815	3276559776407	\N	\N	f	2025-10-30 14:16:19.499784
2080	1815	3276559790434	\N	\N	f	2025-10-30 14:16:19.499784
2081	1816	3276559790441	\N	\N	f	2025-10-30 14:16:19.499784
2082	1817	3276559858516	\N	\N	f	2025-10-30 14:16:19.499784
2083	1818	3523680256637	\N	\N	f	2025-10-30 14:16:19.499784
2084	1819	3523680287822	\N	\N	f	2025-10-30 14:16:19.499784
2085	1820	3523680287839	\N	\N	f	2025-10-30 14:16:19.499784
2086	1821	3523680288737	\N	\N	f	2025-10-30 14:16:19.499784
2087	1790	3523680300262	\N	\N	f	2025-10-30 14:16:19.499784
2088	1822	3523680308831	\N	\N	f	2025-10-30 14:16:19.499784
2089	1823	3523680308848	\N	\N	f	2025-10-30 14:16:19.499784
2090	1824	3523680308862	\N	\N	f	2025-10-30 14:16:19.499784
2091	1825	3523680312265	\N	\N	f	2025-10-30 14:16:19.499784
2092	1822	3523680317109	\N	\N	f	2025-10-30 14:16:19.499784
2093	1826	3523680338296	\N	\N	f	2025-10-30 14:16:19.499784
2094	1827	3523680345249	\N	\N	f	2025-10-30 14:16:19.499784
2095	1828	3523680376809	\N	\N	f	2025-10-30 14:16:19.499784
2096	1829	3523680377707	\N	\N	f	2025-10-30 14:16:19.499784
2097	1830	3523680390232	\N	\N	f	2025-10-30 14:16:19.499784
2098	1831	3523680394612	\N	\N	f	2025-10-30 14:16:19.499784
2099	1832	3523680412521	\N	\N	f	2025-10-30 14:16:19.499784
2100	1833	3523680420571	\N	\N	f	2025-10-30 14:16:19.499784
2101	1780	3523680422094	\N	\N	f	2025-10-30 14:16:19.499784
2102	1834	3523680429826	\N	\N	f	2025-10-30 14:16:19.499784
2103	1834	3523680429987	\N	\N	f	2025-10-30 14:16:19.499784
2104	1835	3523680430006	\N	\N	f	2025-10-30 14:16:19.499784
2105	1835	3523680432215	\N	\N	f	2025-10-30 14:16:19.499784
2106	1836	3523680434165	\N	\N	f	2025-10-30 14:16:19.499784
2107	1837	3523680434226	\N	\N	f	2025-10-30 14:16:19.499784
2108	1838	3523680434318	\N	\N	f	2025-10-30 14:16:19.499784
2109	1838	3523680435537	\N	\N	f	2025-10-30 14:16:19.499784
2110	1555	3523680435667	\N	\N	f	2025-10-30 14:16:19.499784
2111	1839	3523680435698	\N	\N	f	2025-10-30 14:16:19.499784
2112	1840	3523680439559	\N	\N	f	2025-10-30 14:16:19.499784
2113	1840	3523680439566	\N	\N	f	2025-10-30 14:16:19.499784
2114	1841	3523680439573	\N	\N	f	2025-10-30 14:16:19.499784
2115	1842	3523680439641	\N	\N	f	2025-10-30 14:16:19.499784
2116	1843	3523680439658	\N	\N	f	2025-10-30 14:16:19.499784
2117	1844	3523680439702	\N	\N	f	2025-10-30 14:16:19.499784
2118	1845	3523680439719	\N	\N	f	2025-10-30 14:16:19.499784
2119	1846	3523680439764	\N	\N	f	2025-10-30 14:16:19.499784
2120	1847	3523680440944	\N	\N	f	2025-10-30 14:16:19.499784
2121	1848	3523680440975	\N	\N	f	2025-10-30 14:16:19.499784
2122	1849	3523680440982	\N	\N	f	2025-10-30 14:16:19.499784
2123	1850	3523680440999	\N	\N	f	2025-10-30 14:16:19.499784
2124	1851	3523680441255	\N	\N	f	2025-10-30 14:16:19.499784
2125	1852	3523680441958	\N	\N	f	2025-10-30 14:16:19.499784
2126	1853	3523680448650	\N	\N	f	2025-10-30 14:16:19.499784
2127	1854	3523680452237	\N	\N	f	2025-10-30 14:16:19.499784
2128	1855	3523680452244	\N	\N	f	2025-10-30 14:16:19.499784
2129	1856	3523680452251	\N	\N	f	2025-10-30 14:16:19.499784
2130	1857	3523680452268	\N	\N	f	2025-10-30 14:16:19.499784
2131	1858	3523680460935	\N	\N	f	2025-10-30 14:16:19.499784
2132	1859	3523680462786	\N	\N	f	2025-10-30 14:16:19.499784
2133	1859	3523680462793	\N	\N	f	2025-10-30 14:16:19.499784
2134	1860	3523680462892	\N	\N	f	2025-10-30 14:16:19.499784
2135	1860	3523680468719	\N	\N	f	2025-10-30 14:16:19.499784
2136	1861	3523680468726	\N	\N	f	2025-10-30 14:16:19.499784
2137	1862	3523680481947	\N	\N	f	2025-10-30 14:16:19.499784
2138	1863	3560070015559	\N	\N	f	2025-10-30 14:16:19.499784
2139	1864	3560070046867	\N	\N	f	2025-10-30 14:16:19.499784
2140	1865	3560070054978	\N	\N	f	2025-10-30 14:16:19.499784
2141	1866	3560070057597	\N	\N	f	2025-10-30 14:16:19.499784
2142	1867	3560070105038	\N	\N	f	2025-10-30 14:16:19.499784
2143	1868	3560070109920	\N	\N	f	2025-10-30 14:16:19.499784
2144	1869	3560070118090	\N	\N	f	2025-10-30 14:16:19.499784
2145	1870	3560070120451	\N	\N	f	2025-10-30 14:16:19.499784
2146	1871	3560070122257	\N	\N	f	2025-10-30 14:16:19.499784
2147	1872	3560070122349	\N	\N	f	2025-10-30 14:16:19.499784
2148	1873	3560070123858	\N	\N	f	2025-10-30 14:16:19.499784
2149	1299	3560070123971	\N	\N	f	2025-10-30 14:16:19.499784
2150	1874	3560070124817	\N	\N	f	2025-10-30 14:16:19.499784
2151	1299	3560070124879	\N	\N	f	2025-10-30 14:16:19.499784
2152	1634	3560070133055	\N	\N	f	2025-10-30 14:16:19.499784
2153	1875	3560070134564	\N	\N	f	2025-10-30 14:16:19.499784
2154	1541	3560070134656	\N	\N	f	2025-10-30 14:16:19.499784
2155	1876	3560070140398	\N	\N	f	2025-10-30 14:16:19.499784
2156	1877	3560070143085	\N	\N	f	2025-10-30 14:16:19.499784
2157	1878	3560070143368	\N	\N	f	2025-10-30 14:16:19.499784
2158	1879	3560070149278	\N	\N	f	2025-10-30 14:16:19.499784
2159	1880	3560070151493	\N	\N	f	2025-10-30 14:16:19.499784
2160	1881	3560070157198	\N	\N	f	2025-10-30 14:16:19.499784
2161	1882	3560070166343	\N	\N	f	2025-10-30 14:16:19.499784
2162	1883	3560070198474	\N	\N	f	2025-10-30 14:16:19.499784
2163	1884	3560070200030	\N	\N	f	2025-10-30 14:16:19.499784
2164	1885	3560070202522	\N	\N	f	2025-10-30 14:16:19.499784
2165	1612	3560070207794	\N	\N	f	2025-10-30 14:16:19.499784
2166	1886	3560070212019	\N	\N	f	2025-10-30 14:16:19.499784
2167	1887	3560070242757	\N	\N	f	2025-10-30 14:16:19.499784
2168	1888	3560070257096	\N	\N	f	2025-10-30 14:16:19.499784
2169	1889	3560070257393	\N	\N	f	2025-10-30 14:16:19.499784
2170	1890	3560070258819	\N	\N	f	2025-10-30 14:16:19.499784
2171	1891	3560070258963	\N	\N	f	2025-10-30 14:16:19.499784
2172	1892	3560070259830	\N	\N	f	2025-10-30 14:16:19.499784
2173	1893	3560070261369	\N	\N	f	2025-10-30 14:16:19.499784
2174	1168	3560070262595	\N	\N	f	2025-10-30 14:16:19.499784
2175	1894	3560070266685	\N	\N	f	2025-10-30 14:16:19.499784
2176	1894	3560070317790	\N	\N	f	2025-10-30 14:16:19.499784
2177	1866	3560070321599	\N	\N	f	2025-10-30 14:16:19.499784
2178	1895	3560070323470	\N	\N	f	2025-10-30 14:16:19.499784
2179	1896	3560070323630	\N	\N	f	2025-10-30 14:16:19.499784
2180	1896	3560070324545	\N	\N	f	2025-10-30 14:16:19.499784
2181	1897	3560070335541	\N	\N	f	2025-10-30 14:16:19.499784
2182	1773	3560070335879	\N	\N	f	2025-10-30 14:16:19.499784
2183	1773	3560070335930	\N	\N	f	2025-10-30 14:16:19.499784
2184	1898	3560070343904	\N	\N	f	2025-10-30 14:16:19.499784
2185	1899	3560070343966	\N	\N	f	2025-10-30 14:16:19.499784
2186	1900	3560070345397	\N	\N	f	2025-10-30 14:16:19.499784
2187	1901	3560070346714	\N	\N	f	2025-10-30 14:16:19.499784
2188	1902	3560070348459	\N	\N	f	2025-10-30 14:16:19.499784
2189	1903	3560070348503	\N	\N	f	2025-10-30 14:16:19.499784
2190	1904	3560070349647	\N	\N	f	2025-10-30 14:16:19.499784
2191	1905	3560070349692	\N	\N	f	2025-10-30 14:16:19.499784
2192	1602	3560070349746	\N	\N	f	2025-10-30 14:16:19.499784
2193	1602	3560070349791	\N	\N	f	2025-10-30 14:16:19.499784
2194	1602	3560070349869	\N	\N	f	2025-10-30 14:16:19.499784
2195	1906	3560070350476	\N	\N	f	2025-10-30 14:16:19.499784
2196	1907	3560070351329	\N	\N	f	2025-10-30 14:16:19.499784
2197	1908	3560070351350	\N	\N	f	2025-10-30 14:16:19.499784
2198	1908	3560070354955	\N	\N	f	2025-10-30 14:16:19.499784
2199	1909	3560070355570	\N	\N	f	2025-10-30 14:16:19.499784
2200	1910	3560070355662	\N	\N	f	2025-10-30 14:16:19.499784
2201	1911	3560070356942	\N	\N	f	2025-10-30 14:16:19.499784
2202	1911	3560070356973	\N	\N	f	2025-10-30 14:16:19.499784
2203	1912	3560070357000	\N	\N	f	2025-10-30 14:16:19.499784
2204	1913	3560070357871	\N	\N	f	2025-10-30 14:16:19.499784
2205	1913	3560070357901	\N	\N	f	2025-10-30 14:16:19.499784
2206	1914	3560070357932	\N	\N	f	2025-10-30 14:16:19.499784
2207	1915	3560070357963	\N	\N	f	2025-10-30 14:16:19.499784
2208	1916	3560070358274	\N	\N	f	2025-10-30 14:16:19.499784
2209	1916	3560070360512	\N	\N	f	2025-10-30 14:16:19.499784
2210	1917	3560070366996	\N	\N	f	2025-10-30 14:16:19.499784
2211	1918	3560070367221	\N	\N	f	2025-10-30 14:16:19.499784
2212	1919	3560070370436	\N	\N	f	2025-10-30 14:16:19.499784
2213	1920	3560070371600	\N	\N	f	2025-10-30 14:16:19.499784
2214	1634	3560070372560	\N	\N	f	2025-10-30 14:16:19.499784
2215	1634	3560070373628	\N	\N	f	2025-10-30 14:16:19.499784
2216	1921	3560070374397	\N	\N	f	2025-10-30 14:16:19.499784
2217	1922	3560070379545	\N	\N	f	2025-10-30 14:16:19.499784
2218	1923	3560070383542	\N	\N	f	2025-10-30 14:16:19.499784
2219	1924	3560070384181	\N	\N	f	2025-10-30 14:16:19.499784
2220	1925	3560070386826	\N	\N	f	2025-10-30 14:16:19.499784
2221	1926	3560070391073	\N	\N	f	2025-10-30 14:16:19.499784
2222	1927	3560070392742	\N	\N	f	2025-10-30 14:16:19.499784
2223	1928	3560070393824	\N	\N	f	2025-10-30 14:16:19.499784
2224	1422	3560070395668	\N	\N	f	2025-10-30 14:16:19.499784
2225	1929	3560070404117	\N	\N	f	2025-10-30 14:16:19.499784
2226	1930	3560070431953	\N	\N	f	2025-10-30 14:16:19.499784
2227	1931	3560070432080	\N	\N	f	2025-10-30 14:16:19.499784
2228	1932	3560070434046	\N	\N	f	2025-10-30 14:16:19.499784
2229	1933	3560070439430	\N	\N	f	2025-10-30 14:16:19.499784
2230	1866	3560070444373	\N	\N	f	2025-10-30 14:16:19.499784
2231	1934	3560070445820	\N	\N	f	2025-10-30 14:16:19.499784
2232	1934	3560070447343	\N	\N	f	2025-10-30 14:16:19.499784
2233	1602	3560070451685	\N	\N	f	2025-10-30 14:16:19.499784
2234	1935	3560070467945	\N	\N	f	2025-10-30 14:16:19.499784
2235	1935	3560070476923	\N	\N	f	2025-10-30 14:16:19.499784
2236	1936	3560070482788	\N	\N	f	2025-10-30 14:16:19.499784
2237	1936	3560070482818	\N	\N	f	2025-10-30 14:16:19.499784
2238	1761	3560070484447	\N	\N	f	2025-10-30 14:16:19.499784
2239	1767	3560070484478	\N	\N	f	2025-10-30 14:16:19.499784
2240	1937	3560070486380	\N	\N	f	2025-10-30 14:16:19.499784
2241	1937	3560070489114	\N	\N	f	2025-10-30 14:16:19.499784
2242	1938	3560070489237	\N	\N	f	2025-10-30 14:16:19.499784
2243	1939	3560070495429	\N	\N	f	2025-10-30 14:16:19.499784
2244	1902	3560070495948	\N	\N	f	2025-10-30 14:16:19.499784
2245	1224	3560070496952	\N	\N	f	2025-10-30 14:16:19.499784
2246	1224	3560070497348	\N	\N	f	2025-10-30 14:16:19.499784
2247	1940	3560070501236	\N	\N	f	2025-10-30 14:16:19.499784
2248	1940	3560070501267	\N	\N	f	2025-10-30 14:16:19.499784
2249	1941	3560070503735	\N	\N	f	2025-10-30 14:16:19.499784
2250	1942	3560070503766	\N	\N	f	2025-10-30 14:16:19.499784
2251	1942	3560070503797	\N	\N	f	2025-10-30 14:16:19.499784
2252	1943	3560070503827	\N	\N	f	2025-10-30 14:16:19.499784
2253	1944	3560070504701	\N	\N	f	2025-10-30 14:16:19.499784
2254	1945	3560070504947	\N	\N	f	2025-10-30 14:16:19.499784
2255	1946	3560070504978	\N	\N	f	2025-10-30 14:16:19.499784
2256	1947	3560070505098	\N	\N	f	2025-10-30 14:16:19.499784
2257	1948	3560070505753	\N	\N	f	2025-10-30 14:16:19.499784
2258	1949	3560070506040	\N	\N	f	2025-10-30 14:16:19.499784
2259	1950	3560070506101	\N	\N	f	2025-10-30 14:16:19.499784
2260	1951	3560070506439	\N	\N	f	2025-10-30 14:16:19.499784
2261	1952	3560070507726	\N	\N	f	2025-10-30 14:16:19.499784
2262	1513	3560070507887	\N	\N	f	2025-10-30 14:16:19.499784
2263	1953	3560070509980	\N	\N	f	2025-10-30 14:16:19.499784
2264	1602	3560070512508	\N	\N	f	2025-10-30 14:16:19.499784
2265	1954	3560070512560	\N	\N	f	2025-10-30 14:16:19.499784
2266	1955	3560070513567	\N	\N	f	2025-10-30 14:16:19.499784
2267	1956	3560070514571	\N	\N	f	2025-10-30 14:16:19.499784
2268	1957	3560070514694	\N	\N	f	2025-10-30 14:16:19.499784
2269	1958	3560070523696	\N	\N	f	2025-10-30 14:16:19.499784
2270	1959	3560070530564	\N	\N	f	2025-10-30 14:16:19.499784
2271	1960	3560070533633	\N	\N	f	2025-10-30 14:16:19.499784
2272	1961	3560070535071	\N	\N	f	2025-10-30 14:16:19.499784
2273	1962	3560070535101	\N	\N	f	2025-10-30 14:16:19.499784
2274	1149	3560070536610	\N	\N	f	2025-10-30 14:16:19.499784
2275	1149	3560070536641	\N	\N	f	2025-10-30 14:16:19.499784
2276	1963	3560070540631	\N	\N	f	2025-10-30 14:16:19.499784
2277	1964	3560070541270	\N	\N	f	2025-10-30 14:16:19.499784
2278	1965	3560070541423	\N	\N	f	2025-10-30 14:16:19.499784
2279	1966	3560070542550	\N	\N	f	2025-10-30 14:16:19.499784
2280	1967	3560070542642	\N	\N	f	2025-10-30 14:16:19.499784
2281	1968	3560070543632	\N	\N	f	2025-10-30 14:16:19.499784
2282	1969	3560070543663	\N	\N	f	2025-10-30 14:16:19.499784
2283	1970	3560070552498	\N	\N	f	2025-10-30 14:16:19.499784
2284	1971	3560070554300	\N	\N	f	2025-10-30 14:16:19.499784
2285	1972	3560070555673	\N	\N	f	2025-10-30 14:16:19.499784
2286	1973	3560070555901	\N	\N	f	2025-10-30 14:16:19.499784
2287	1399	3560070557165	\N	\N	f	2025-10-30 14:16:19.499784
2288	1974	3560070558445	\N	\N	f	2025-10-30 14:16:19.499784
2289	1975	3560070558698	\N	\N	f	2025-10-30 14:16:19.499784
2290	1976	3560070559589	\N	\N	f	2025-10-30 14:16:19.499784
2291	1977	3560070559879	\N	\N	f	2025-10-30 14:16:19.499784
2292	1978	3560070561186	\N	\N	f	2025-10-30 14:16:19.499784
2293	1979	3560070561216	\N	\N	f	2025-10-30 14:16:19.499784
2294	1980	3560070562718	\N	\N	f	2025-10-30 14:16:19.499784
2295	1981	3560070564248	\N	\N	f	2025-10-30 14:16:19.499784
2296	1982	3560070565283	\N	\N	f	2025-10-30 14:16:19.499784
2297	1983	3560070565313	\N	\N	f	2025-10-30 14:16:19.499784
2298	1984	3560070565344	\N	\N	f	2025-10-30 14:16:19.499784
2299	1985	3560070565627	\N	\N	f	2025-10-30 14:16:19.499784
2300	1149	3560070566143	\N	\N	f	2025-10-30 14:16:19.499784
\.


--
-- Name: mouvements_stock_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.mouvements_stock_id_seq', 3522, true);


--
-- Name: produits_barcodes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.produits_barcodes_id_seq', 2300, true);


--
-- Name: produits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.produits_id_seq', 1985, true);


--
-- Name: mouvements_stock mouvements_stock_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mouvements_stock
    ADD CONSTRAINT mouvements_stock_pkey PRIMARY KEY (id);


--
-- Name: produits_barcodes produits_barcodes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produits_barcodes
    ADD CONSTRAINT produits_barcodes_pkey PRIMARY KEY (id);


--
-- Name: produits produits_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produits
    ADD CONSTRAINT produits_pkey PRIMARY KEY (id);


--
-- Name: idx_barcode_produit; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_barcode_produit ON public.produits_barcodes USING btree (produit_id);


--
-- Name: idx_mouvements_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mouvements_date ON public.mouvements_stock USING btree (date_mvt);


--
-- Name: idx_mouvements_produit; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mouvements_produit ON public.mouvements_stock USING btree (produit_id);


--
-- Name: uix_barcodes_code_ci; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uix_barcodes_code_ci ON public.produits_barcodes USING btree (lower(code));


--
-- Name: uix_produits_nom_ci; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uix_produits_nom_ci ON public.produits USING btree (lower(nom));


--
-- Name: mouvements_stock trg_update_stock_actuel; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_stock_actuel AFTER INSERT ON public.mouvements_stock FOR EACH ROW EXECUTE FUNCTION public.update_stock_actuel();


--
-- Name: mouvements_stock mouvements_stock_produit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mouvements_stock
    ADD CONSTRAINT mouvements_stock_produit_id_fkey FOREIGN KEY (produit_id) REFERENCES public.produits(id) ON DELETE CASCADE;


--
-- Name: produits_barcodes produits_barcodes_produit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produits_barcodes
    ADD CONSTRAINT produits_barcodes_produit_id_fkey FOREIGN KEY (produit_id) REFERENCES public.produits(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict SXTHT6JLyzxavKCDEFIlbOwAoiF8xp3PdPXN7HbgrYMrVUlf0azQS08ym9iFgiZ

