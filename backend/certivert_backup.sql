--
-- PostgreSQL database dump
--

\restrict hbWTlcrfK1ZPLi9iLoo270NkwrIxOMcut4p7fMPneTgBjOxu8mpD5geLki9Pvf3

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg13+1)

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
-- Name: InstitutionRole; Type: TYPE; Schema: public; Owner: certivert
--

CREATE TYPE public."InstitutionRole" AS ENUM (
    'ISSUER',
    'VERIFIER'
);


ALTER TYPE public."InstitutionRole" OWNER TO certivert;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: Certificate; Type: TABLE; Schema: public; Owner: certivert
--

CREATE TABLE public."Certificate" (
    id text NOT NULL,
    hash text NOT NULL,
    "issuerCode" text NOT NULL,
    "examType" text NOT NULL,
    "examSession" text NOT NULL,
    "candidateNumber" text NOT NULL,
    "certificateNumber" text NOT NULL,
    "fullName" text NOT NULL,
    "dateOfBirth" text NOT NULL,
    "dateOfIssue" text NOT NULL,
    "resultsJson" jsonb NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public."Certificate" OWNER TO certivert;

--
-- Name: Institution; Type: TABLE; Schema: public; Owner: certivert
--

CREATE TABLE public."Institution" (
    id text NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    role public."InstitutionRole" NOT NULL
);


ALTER TABLE public."Institution" OWNER TO certivert;

--
-- Name: VerificationLog; Type: TABLE; Schema: public; Owner: certivert
--

CREATE TABLE public."VerificationLog" (
    id text NOT NULL,
    hash text NOT NULL,
    "verifierCode" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "certificateId" text,
    message text,
    verified boolean NOT NULL,
    "issuerCode" text
);


ALTER TABLE public."VerificationLog" OWNER TO certivert;

--
-- Name: _prisma_migrations; Type: TABLE; Schema: public; Owner: certivert
--

CREATE TABLE public._prisma_migrations (
    id character varying(36) NOT NULL,
    checksum character varying(64) NOT NULL,
    finished_at timestamp with time zone,
    migration_name character varying(255) NOT NULL,
    logs text,
    rolled_back_at timestamp with time zone,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    applied_steps_count integer DEFAULT 0 NOT NULL
);


ALTER TABLE public._prisma_migrations OWNER TO certivert;

--
-- Data for Name: Certificate; Type: TABLE DATA; Schema: public; Owner: certivert
--

COPY public."Certificate" (id, hash, "issuerCode", "examType", "examSession", "candidateNumber", "certificateNumber", "fullName", "dateOfBirth", "dateOfIssue", "resultsJson", "createdAt") FROM stdin;
cmkmi1vp20001dgkfh5f57wu6	c07d38ea1365084e50eaecd2cc075a24a8c726553fe1ec58e836677f618c7eab	ECOL	LGCSE	2015-11	L5683/100298290	LN150014229	MOTLATSI MAHLOMOLA	1997-10-17	2016-08-31	[{"grade": "B(b)", "subject": "Mathematics"}, {"grade": "C(c)", "subject": "Biology"}]	2026-01-20 11:17:13.526
cmkpep1je0001dgdzp57o2leu	e064829648e78a5c104f341ff0d7c910a724f99f062c813f937ce206ad1dc341	ECOL	LGCSE	2015-11	LS682/100293279	LN1500014163	THABANG KHOPOLO	1997-02-15	2016-08-31	[{"grade": "A(a)", "subject": "Physical Science"}, {"grade": "B(b)", "subject": "Accounting"}, {"grade": "C(c)", "subject": "Geography"}, {"grade": "C(c)", "subject": "Mathematics"}, {"grade": "C(c)", "subject": "Sesotho"}, {"grade": "E(e)", "subject": "English Language"}, {"grade": "D(d)", "subject": "Economics"}]	2026-01-22 12:06:34.25
cmkpepcht0003dgdz9u6yyjb6	0b0aaf81a097bc3915f28179959e24271e4b150a4630a894ce610d5aef32f8f3	ECOL	LGCSE	2021-03	LS530/160545278	LM2100002813	MAIPATO MOTSAMAI	2004-03-07	2021-11-03	[{"grade": "B(b)", "subject": "Agriculture"}, {"grade": "C(c)", "subject": "Design and Technology"}, {"grade": "C(c)", "subject": "Religious Studies"}, {"grade": "D(d)", "subject": "English Language"}, {"grade": "D(d)", "subject": "Literature in English"}, {"grade": "D(d)", "subject": "Physical Science"}, {"grade": "D(d)", "subject": "Sesotho"}, {"grade": "E(e)", "subject": "Accounting"}, {"grade": "G(g)", "subject": "Mathematics"}]	2026-01-22 12:06:48.449
cmkpesm7w0005dgdzyuosbcxs	abc51af53a1aa3e2d08f953c6f0842f5925b94171d37e0c0fe5fbd00fa9c9cb9	ECOL	LGCSE	2021-11	LS675/140453620	N2100014388	BOKANG JOHANNES LETSAPO	2001-03-03	2022-07-19	[{"grade": "A(a)", "subject": "History"}, {"grade": "A(a)", "subject": "Sesotho"}, {"grade": "B(b)", "subject": "Agriculture"}, {"grade": "B(b)", "subject": "Physical Science"}, {"grade": "C(c)", "subject": "Mathematics"}, {"grade": "D(d)", "subject": "English Language"}, {"grade": "C(c)", "subject": "Business Studies"}]	2026-01-22 12:09:21.02
cmkpfomxh0007dgdzhmb9alfe	f57a2e8e6babc35b55c7e804bbbeda3d0660fa1fec48dbcb32834fb7531c7f1e	ECOL	LGCSE	2016-11	LS618/110344217	LN1600000491	TS'EPISO MOKOALELI	1999-10-22	2017-08-30	[{"grade": "B(b)", "subject": "Sesotho"}, {"grade": "D(d)", "subject": "Agriculture"}, {"grade": "D(d)", "subject": "Biology"}, {"grade": "D(d)", "subject": "English Language"}, {"grade": "D(d)", "subject": "Literature in English"}, {"grade": "D(d)", "subject": "Physical Science"}, {"grade": "D(d)", "subject": "Religious Studies"}, {"grade": "E(e)", "subject": "Accounting"}, {"grade": "E(e)", "subject": "Mathematics"}]	2026-01-22 12:34:14.933
\.


--
-- Data for Name: Institution; Type: TABLE DATA; Schema: public; Owner: certivert
--

COPY public."Institution" (id, code, name, "createdAt", "updatedAt", role) FROM stdin;
cmkgx6xxr0000dgv4wdy0mjcs	ECOL	ECOL	2026-01-16 13:34:26.894	2026-01-16 13:34:26.894	ISSUER
cmkgx6xy30001dgv4lomn0spc	LUCT	LUCT	2026-01-16 13:34:26.908	2026-01-16 13:34:26.908	VERIFIER
cmkgx6xy60002dgv43zxyeewo	NUL	NUL	2026-01-16 13:34:26.91	2026-01-16 13:34:26.91	VERIFIER
cmkgx6xy80003dgv459qoxi0y	LP	LP	2026-01-16 13:34:26.912	2026-01-16 13:34:26.912	VERIFIER
\.


--
-- Data for Name: VerificationLog; Type: TABLE DATA; Schema: public; Owner: certivert
--

COPY public."VerificationLog" (id, hash, "verifierCode", "createdAt", "certificateId", message, verified, "issuerCode") FROM stdin;
cmkmi2lwe0003dgkfkjpqeo73	c07d38ea1365084e50eaecd2cc075a24a8c726553fe1ec58e836677f618c7eab	LUCT	2026-01-20 11:17:47.486	cmkmi1vp20001dgkfh5f57wu6	Certificate found	t	\N
cmknsx93z0003dg576wgtrc0o	c07d38ea1365084e50eaecd2cc075a24a8c726553fe1ec58e836677f618c7eab	LUCT	2026-01-21 09:09:19.583	cmkmi1vp20001dgkfh5f57wu6	Certificate found	t	\N
cmkmgv0yt0003dgamioweil1y	9038de1580d151b34429028f2fb3e1918c76bebfe53d2de32f398d343aef5ba5	LUCT	2026-01-20 10:43:54.149	\N	FOUND	t	\N
cmkmhhxtd0007dgam5lc50i4v	9038de1580d151b34429028f2fb3e1918c76bebfe53d2de32f398d343aef5ba5	LUCT	2026-01-20 11:01:43.153	\N	FOUND	t	\N
cmkmhi7f90009dgam2ylan0yk	9038de1580d151b34429028f2fb3e1918c76bebfe53d2de32f398d343aef5ba5	LUCT	2026-01-20 11:01:55.606	\N	FOUND	t	\N
cmkmjuf1s0001dgyt152hubsj	9038de1580d151b34429028f2fb3e1918c76bebfe53d2de32f398d343aef5ba5	LUCT	2026-01-20 12:07:24.591	\N	Certificate found	t	\N
cmkmhijsu000ddgama2md1koe	a62db3102bdb5a56f6ba02910330d1f1e7c2d0f386ad78884cea4579515c0c91	LUCT	2026-01-20 11:02:11.646	\N	FOUND	t	\N
cmkmhj6l8000hdgamma7gha5t	a62db3102bdb5a56f6ba02910330d1f1e7c2d0f386ad78884cea4579515c0c91	LUCT	2026-01-20 11:02:41.18	\N	FOUND	t	\N
\.


--
-- Data for Name: _prisma_migrations; Type: TABLE DATA; Schema: public; Owner: certivert
--

COPY public._prisma_migrations (id, checksum, finished_at, migration_name, logs, rolled_back_at, started_at, applied_steps_count) FROM stdin;
02e59777-bfeb-4f92-af3d-239e08c6b428	f8bfde7ebfb2ba6a0f8c102bb4eacd942ce4358e0bb5e1d9f9a642ebe4424466	2026-01-16 10:34:35.075117+00	20260116103435_init	\N	\N	2026-01-16 10:34:35.016548+00	1
aaab7fbd-1280-4e93-901c-6e50e2bdaa30	a0a6b3e8ffe808917002c4a153d211ac76be8f728109d20bd00c2ce55d89d384	2026-01-16 10:52:30.540082+00	20260116105230_add_models	\N	\N	2026-01-16 10:52:30.524906+00	1
25b4155f-9eb0-4611-9547-17060e3ce194	8c756a5d8f4f9f9cf572003ace3c9841a2a4e43a5ed1fb123d598251b2c7c839	2026-01-16 13:23:11.411862+00	20260116132311_cleanup_schema	\N	\N	2026-01-16 13:23:11.396524+00	1
5c6ad62f-84d3-428d-9c4a-35fa5403d229	b9e8227768bf030ed720ce51ad93ce541a82fdd9de1c1e9cd1dd7951fcce10bd	2026-01-26 07:46:48.369449+00	20260126074648_unique_issuer_certnumber	\N	\N	2026-01-26 07:46:48.346378+00	1
\.


--
-- Name: Certificate Certificate_pkey; Type: CONSTRAINT; Schema: public; Owner: certivert
--

ALTER TABLE ONLY public."Certificate"
    ADD CONSTRAINT "Certificate_pkey" PRIMARY KEY (id);


--
-- Name: Institution Institution_pkey; Type: CONSTRAINT; Schema: public; Owner: certivert
--

ALTER TABLE ONLY public."Institution"
    ADD CONSTRAINT "Institution_pkey" PRIMARY KEY (id);


--
-- Name: VerificationLog VerificationLog_pkey; Type: CONSTRAINT; Schema: public; Owner: certivert
--

ALTER TABLE ONLY public."VerificationLog"
    ADD CONSTRAINT "VerificationLog_pkey" PRIMARY KEY (id);


--
-- Name: _prisma_migrations _prisma_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: certivert
--

ALTER TABLE ONLY public._prisma_migrations
    ADD CONSTRAINT _prisma_migrations_pkey PRIMARY KEY (id);


--
-- Name: Certificate_hash_key; Type: INDEX; Schema: public; Owner: certivert
--

CREATE UNIQUE INDEX "Certificate_hash_key" ON public."Certificate" USING btree (hash);


--
-- Name: Certificate_issuerCode_idx; Type: INDEX; Schema: public; Owner: certivert
--

CREATE INDEX "Certificate_issuerCode_idx" ON public."Certificate" USING btree ("issuerCode");


--
-- Name: Institution_code_key; Type: INDEX; Schema: public; Owner: certivert
--

CREATE UNIQUE INDEX "Institution_code_key" ON public."Institution" USING btree (code);


--
-- Name: VerificationLog_hash_idx; Type: INDEX; Schema: public; Owner: certivert
--

CREATE INDEX "VerificationLog_hash_idx" ON public."VerificationLog" USING btree (hash);


--
-- Name: VerificationLog_issuerCode_idx; Type: INDEX; Schema: public; Owner: certivert
--

CREATE INDEX "VerificationLog_issuerCode_idx" ON public."VerificationLog" USING btree ("issuerCode");


--
-- Name: VerificationLog_verifierCode_idx; Type: INDEX; Schema: public; Owner: certivert
--

CREATE INDEX "VerificationLog_verifierCode_idx" ON public."VerificationLog" USING btree ("verifierCode");


--
-- Name: Certificate Certificate_issuerCode_fkey; Type: FK CONSTRAINT; Schema: public; Owner: certivert
--

ALTER TABLE ONLY public."Certificate"
    ADD CONSTRAINT "Certificate_issuerCode_fkey" FOREIGN KEY ("issuerCode") REFERENCES public."Institution"(code) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: VerificationLog VerificationLog_certificateId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: certivert
--

ALTER TABLE ONLY public."VerificationLog"
    ADD CONSTRAINT "VerificationLog_certificateId_fkey" FOREIGN KEY ("certificateId") REFERENCES public."Certificate"(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: VerificationLog VerificationLog_verifierCode_fkey; Type: FK CONSTRAINT; Schema: public; Owner: certivert
--

ALTER TABLE ONLY public."VerificationLog"
    ADD CONSTRAINT "VerificationLog_verifierCode_fkey" FOREIGN KEY ("verifierCode") REFERENCES public."Institution"(code) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict hbWTlcrfK1ZPLi9iLoo270NkwrIxOMcut4p7fMPneTgBjOxu8mpD5geLki9Pvf3

