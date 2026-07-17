--
-- PostgreSQL database dump
--

\restrict lmgsiCFPfXQpqidOEZPlcdeBMoXO7PDxdVgeJExQdP7guFmylrQUnSaJB9pvZPq

-- Dumped from database version 15.17
-- Dumped by pg_dump version 15.17

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
-- Name: user_tier; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_tier AS ENUM (
    'NORMAL',
    'PREMIUM'
);


ALTER TYPE public.user_tier OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    actor_id integer,
    action character varying(50) NOT NULL,
    target character varying(120),
    detail text,
    ip character varying(64),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_logs_id_seq OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.groups (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    description character varying(255),
    tier public.user_tier NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.groups OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.groups_id_seq OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(120) NOT NULL,
    username character varying(50) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    tier public.user_tier NOT NULL,
    is_admin boolean NOT NULL,
    is_active boolean NOT NULL,
    group_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login_at timestamp with time zone,
    password_changed_at timestamp with time zone,
    email_verified boolean DEFAULT true NOT NULL,
    real_name character varying(50),
    role character varying(20),
    student_id character varying(50),
    school character varying(100),
    phone character varying(20),
    profile_completed boolean DEFAULT false NOT NULL,
    profile_completed_at timestamp with time zone,
    major character varying(100),
    college character varying(100),
    avatar_url character varying(255),
    notification_email boolean DEFAULT true NOT NULL,
    notification_system boolean DEFAULT true NOT NULL,
    notification_course boolean DEFAULT true NOT NULL,
    notification_announcement boolean DEFAULT true NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
e8b9c5d6f7g8
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_logs (id, actor_id, action, target, detail, ip, created_at) FROM stdin;
1	1	update_user	2	{"tier":"premium"}	172.21.0.1	2026-06-23 01:14:32.098385+00
2	1	update_user	2	{"tier":"normal"}	172.21.0.1	2026-06-23 01:14:33.310449+00
3	1	create_group	3	\N	\N	2026-06-23 01:15:10.667469+00
4	1	delete_user	2	\N	\N	2026-06-23 01:28:50.528702+00
5	1	update_user	3	{"group_id":3}	172.21.0.1	2026-06-23 01:40:22.69347+00
6	1	update_user	3	{"group_id":1}	172.21.0.1	2026-06-23 01:40:25.365824+00
7	1	update_user	3	{"tier":"premium"}	192.168.3.103	2026-06-23 07:42:33.238061+00
8	1	update_user	3	{"tier":"normal"}	192.168.3.103	2026-06-23 07:42:34.497601+00
9	1	update_user	4	{"group_id":3}	192.168.3.103	2026-06-23 09:14:22.2407+00
10	1	update_user	4	{"group_id":1}	192.168.4.206	2026-06-25 09:37:52.129575+00
11	1	update_user	4	{"group_id":3}	192.168.4.206	2026-06-25 09:37:54.333825+00
12	1	delete_user	11	\N	\N	2026-07-03 01:34:30.568696+00
13	1	delete_user	21	\N	\N	2026-07-06 05:48:27.85848+00
14	1	delete_user	18	\N	\N	2026-07-06 05:48:27.878518+00
15	1	delete_user	23	\N	\N	2026-07-06 06:30:53.342451+00
16	1	delete_user	22	\N	\N	2026-07-06 06:30:53.361637+00
17	1	delete_user	28	\N	\N	2026-07-06 07:38:33.892434+00
18	1	delete_user	27	\N	\N	2026-07-06 07:38:33.909267+00
19	1	delete_user	26	\N	\N	2026-07-06 07:38:33.921817+00
20	1	delete_user	29	\N	\N	2026-07-06 07:50:57.437581+00
21	1	delete_user	4	\N	\N	2026-07-10 03:04:26.844117+00
22	1	update_user	60	{"group_id":2}	192.168.2.194	2026-07-10 07:12:40.778102+00
23	1	delete_user	70	\N	\N	2026-07-10 07:21:54.336318+00
24	1	delete_user	67	\N	\N	2026-07-10 07:24:37.146727+00
25	1	delete_user	75	\N	\N	2026-07-10 07:39:11.913967+00
26	1	delete_user	78	\N	\N	2026-07-10 08:17:01.808341+00
27	1	delete_user	85	\N	\N	2026-07-10 08:22:22.477817+00
28	1	delete_user	88	\N	\N	2026-07-10 08:46:37.04842+00
29	1	delete_user	91	\N	\N	2026-07-10 08:48:30.083655+00
30	1	delete_user	92	\N	\N	2026-07-10 08:55:13.600782+00
31	1	delete_user	95	\N	\N	2026-07-10 08:59:00.384136+00
32	1	delete_user	98	\N	\N	2026-07-10 09:08:18.454698+00
33	1	delete_user	101	\N	\N	2026-07-10 09:30:32.207058+00
34	1	delete_user	104	\N	\N	2026-07-10 09:31:44.180689+00
35	1	delete_user	105	\N	\N	2026-07-10 14:52:52.113073+00
36	1	delete_user	111	\N	\N	2026-07-10 14:56:54.332214+00
37	1	delete_user	114	\N	\N	2026-07-10 15:02:08.863353+00
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.groups (id, name, description, tier, created_at) FROM stdin;
1	普通组	普通用户默认所在组	NORMAL	2026-06-22 09:31:06.938226+00
2	高级组	高级用户组，享受所有高级功能	PREMIUM	2026-06-22 09:31:06.938226+00
3	南京理工大学	教学组	PREMIUM	2026-06-23 01:15:10.658339+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, username, hashed_password, tier, is_admin, is_active, group_id, created_at, updated_at, last_login_at, password_changed_at, email_verified, real_name, role, student_id, school, phone, profile_completed, profile_completed_at, major, college, avatar_url, notification_email, notification_system, notification_course, notification_announcement) FROM stdin;
1	admin@guochuang.com	admin	$pbkdf2-sha256$29000$vdeaM8a4tzaGcO59L0WodQ$3GBthjx1SRJbPVPrARmJG4UVLSlWkTXaN2UcW4tq6Rk	PREMIUM	t	t	\N	2026-06-22 09:31:06.959787+00	2026-07-10 15:02:04.565343+00	2026-07-10 15:02:04.564663+00	\N	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
7	test1782979330@guochuang.com	test1782979330	$pbkdf2-sha256$29000$OsdYS0mpldJ6r9Uao5Qypg$5V7KZdIPyX3ZoBRjei.pxOdNTGGHucnBCZEB07mrKdc	NORMAL	f	t	\N	2026-07-02 08:02:10.098578+00	2026-07-02 08:02:10.098578+00	\N	\N	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
60	1494686959@qq.com	zinongsan	$2b$12$1NGnWTJRs5Afv/SgIPv0fuKfRcCO9er3MzYBEE.Qrkz1soPlfeI.W	PREMIUM	f	t	2	2026-07-10 05:56:17.161756+00	2026-07-10 07:12:40.765691+00	\N	2026-07-10 05:56:17.391233+00	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
8	tn1782981827@g.com	tn1782981827	$pbkdf2-sha256$29000$DIEwBuAcQ0iJ0RpDqNX6vw$xiy9TJlIoWLgIxq3fU9KgzIQhcVgwYu4YksIheyZ8W0	NORMAL	f	t	\N	2026-07-02 08:43:47.210475+00	2026-07-02 08:43:47.240185+00	2026-07-02 08:43:47.24578+00	\N	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
108	xuxiaofeng@nctieda.com	yiyiyiyi	$2b$12$yfMGekY5Gj6tKyLRKE8c3uCVkU6My7MjaRAzN/0AJaZG8yDgMJRxu	NORMAL	f	t	\N	2026-07-10 10:04:24.511682+00	2026-07-10 10:05:46.590115+00	2026-07-10 10:04:24.987711+00	2026-07-10 10:04:24.737424+00	f	徐晓凤	student	200000000	\N	\N	t	2026-07-10 10:05:46.59127+00	\N	\N	\N	t	t	t	t
117	18862013736@163.com	cxtest	$2b$12$EPGxHfzSKmKm4HlF5L2zteMXW9NxyxqKoGkBrYTevo8vROD1r9BNO	NORMAL	f	t	\N	2026-07-10 15:02:52.276754+00	2026-07-12 13:33:29.579518+00	2026-07-12 13:22:43.978732+00	2026-07-10 15:35:08.888468+00	f	陈曦	student	1023162811	南京邮电大学	18862013736	t	2026-07-10 15:03:14.315542+00	教育技术学	\N	/uploads/avatars/117.jpg	t	t	t	t
3	1479576468@qq.com	test	$pbkdf2-sha256$29000$jbFWSkmp1VoLoRTiXGttbQ$VTYH5XED4lk8nA.bZz9H2LAbreBjqrEjCOk/yzyPQa0	NORMAL	f	t	1	2026-06-23 01:39:09.444632+00	2026-07-10 02:14:03.708305+00	2026-07-10 02:14:03.718169+00	\N	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
\.


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 37, true);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.groups_id_seq', 215, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 137, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_actor_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_logs_actor_id ON public.audit_logs USING btree (actor_id);


--
-- Name: ix_groups_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_groups_name ON public.groups USING btree (name);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_group_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_group_id ON public.users USING btree (group_id);


--
-- Name: ix_users_tier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_tier ON public.users USING btree (tier);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: audit_logs audit_logs_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: users users_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict lmgsiCFPfXQpqidOEZPlcdeBMoXO7PDxdVgeJExQdP7guFmylrQUnSaJB9pvZPq

