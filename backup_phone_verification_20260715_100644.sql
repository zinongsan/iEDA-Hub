--
-- PostgreSQL database dump
--

\restrict r5Si0TgYoKD0HyQzL6aUCEHjybAfW7sfIFOODzHWxkMo6NwbNXvr0V3r8ENS6DU

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
-- Name: action_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.action_logs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    action character varying(100) NOT NULL,
    resource_type character varying(50),
    resource_id character varying(100),
    ip_address character varying(45),
    user_agent text,
    details json,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.action_logs OWNER TO postgres;

--
-- Name: TABLE action_logs; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.action_logs IS '用户操作日志表';


--
-- Name: action_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.action_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.action_logs_id_seq OWNER TO postgres;

--
-- Name: action_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.action_logs_id_seq OWNED BY public.action_logs.id;


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
-- Name: action_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.action_logs ALTER COLUMN id SET DEFAULT nextval('public.action_logs_id_seq'::regclass);


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
-- Data for Name: action_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.action_logs (id, user_id, action, resource_type, resource_id, ip_address, user_agent, details, created_at) FROM stdin;
1	117	user.login	user	117	192.168.3.85	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-13 01:33:12.673507+00
2	1	user.login	user	1	192.168.3.85	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-13 02:13:11.45814+00
3	1	user.login	user	1	192.168.3.85	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-13 02:13:17.622955+00
4	1	user.complete_profile	user	1	\N	\N	{"role": "teacher"}	2026-07-13 02:13:59.396607+00
5	1	user.login	user	1	192.168.4.206	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36	null	2026-07-13 02:20:30.307479+00
6	1	user.update_profile	user	1	\N	\N	{"fields": ["real_name", "role", "student_id", "school", "major", "college"]}	2026-07-13 02:23:02.481408+00
7	1	user.login	user	1	192.168.3.85	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-13 03:30:22.911527+00
8	117	user.login	user	117	192.168.2.248	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0	null	2026-07-13 03:41:57.80516+00
9	1	user.login	user	1	192.168.2.244	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-13 05:49:41.14429+00
10	117	user.login	user	117	192.168.2.248	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0	null	2026-07-13 06:54:28.782167+00
11	1	user.login	user	1	192.168.2.244	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-13 07:26:03.827055+00
12	1	user.login	user	1	192.168.4.206	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36	null	2026-07-13 07:52:02.432526+00
13	1	user.login	user	1	192.168.4.206	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36	null	2026-07-13 09:44:31.975841+00
14	1	user.login	user	1	192.168.4.206	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36	null	2026-07-14 02:58:34.63922+00
15	1	ai.qa	knowledge	\N	172.21.0.1	curl/7.81.0	{"question": "\\u4ec0\\u4e48\\u662fEDA\\u5de5\\u5177", "answer": "\\u6839\\u636e\\u4e0a\\u4e0b\\u6587\\uff0cEDA\\uff08Electronic Design Automation\\uff0c\\u7535\\u5b50\\u8bbe\\u8ba1\\u81ea\\u52a8\\u5316\\uff09\\u5de5\\u5177\\u662f**\\u7528\\u4e8e\\u8bbe\\u8ba1\\u548c\\u9a8c\\u8bc1\\u96c6\\u6210\\u7535\\u8def\\u3001\\u5370\\u5237\\u7535\\u8def\\u677f\\u7b49\\u7535\\u5b50\\u7cfb\\u7edf\\u7684\\u8f6f\\u4ef6\\u5de5\\u5177\\u96c6\\u5408**\\u3002", "elapsed_time": 6.755988, "cost": 0.001258, "tokens": {"input": 1194, "output": 32, "total": 1226}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 03:18:00.243307+00
16	1	ai.qa	knowledge	\N	172.21.0.1	curl/7.81.0	{"question": "\\u4ec0\\u4e48\\u662fEDA\\u5de5\\u5177", "answer": "\\u6839\\u636e\\u4e0a\\u4e0b\\u6587\\uff0cEDA\\uff08Electronic Design Automation\\uff0c\\u7535\\u5b50\\u8bbe\\u8ba1\\u81ea\\u52a8\\u5316\\uff09\\u5de5\\u5177\\u662f\\u7528\\u4e8e\\u8bbe\\u8ba1\\u548c\\u9a8c\\u8bc1\\u96c6\\u6210\\u7535\\u8def\\u3001\\u5370\\u5237\\u7535\\u8def\\u677f\\u7b49\\u7535\\u5b50\\u7cfb\\u7edf\\u7684\\u8f6f\\u4ef6\\u5de5\\u5177\\u96c6\\u5408\\u3002", "elapsed_time": 6.449222, "cost": 0.001217, "tokens": {"input": 1157, "output": 30, "total": 1187}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 03:39:03.325963+00
17	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "\\u6280\\u672f\\u6620\\u5c04\\u662f\\u4ec0\\u4e48\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6ca1\\u6709\\u5173\\u4e8e\\u201c\\u6280\\u672f\\u6620\\u5c04\\u201d\\u7684\\u76f8\\u5173\\u4fe1\\u606f\\u3002\\u4e0a\\u4e0b\\u6587\\u4e3b\\u8981\\u4ecb\\u7ecd\\u4e86\\u5e94\\u53d8\\u7845\\u6280\\u672f\\u3001\\u591a\\u91cd\\u56fe\\u5f62\\u6280\\u672f\\u548cEUV\\u5149\\u523b\\uff0c\\u672a\\u6d89\\u53ca\\u6280\\u672f\\u6620\\u5c04\\u7684\\u5b9a\\u4e49\\u6216\\u5185\\u5bb9\\u3002", "elapsed_time": 6.080304, "cost": 0.0015300000000000001, "tokens": {"input": 1458, "output": 36, "total": 1494}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 03:39:16.961982+00
18	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6ca1\\u6709\\u5173\\u4e8e\\u201c\\u5982\\u4f55\\u5199SDC\\u7ea6\\u675f\\u201d\\u7684\\u5177\\u4f53\\u8bed\\u6cd5\\u6216\\u793a\\u4f8b\\u3002\\u4e0a\\u4e0b\\u6587\\u53ea\\u89e3\\u91ca\\u4e86SDC\\u662f\\u4ec0\\u4e48\\u3001\\u5b83\\u7684\\u4f5c\\u7528\\u4ee5\\u53ca\\u4e3a\\u4ec0\\u4e48\\u9700\\u8981\\u5b83\\uff0c\\u4f46\\u6ca1\\u6709\\u63d0\\u4f9b\\u7f16\\u5199SDC\\u7ea6\\u675f\\u7684\\u5177\\u4f53\\u65b9\\u6cd5\\u6216\\u547d\\u4ee4\\u3002\\n\\n\\u5982\\u679c\\u4f60\\u9700\\u8981\\u7f16\\u5199SDC\\u7ea6\\u675f\\uff0c\\u4e00\\u822c\\u9700\\u8981\\u5b66\\u4e60\\u4ee5\\u4e0b\\u57fa\\u672c\\u547d\\u4ee4\\uff08\\u8fd9\\u4e9b\\u4fe1\\u606f\\u4e0d\\u5728\\u5f53\\u524d\\u4e0a\\u4e0b\\u6587\\u4e2d\\uff09\\uff1a\\n- `create_clock`\\uff1a\\u5b9a\\u4e49\\u65f6\\u949f\\n- `set_input_delay` / `set_output_delay`\\uff1a\\u5b9a\\u4e49\\u8f93\\u5165/\\u8f93\\u51fa\\u5ef6\\u8fdf\\n- `s", "elapsed_time": 2.306693, "cost": 0.00148, "tokens": {"input": 1190, "output": 145, "total": 1335}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 03:39:27.692765+00
19	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "\\u6280\\u672f\\u6620\\u5c04\\u662f\\u4ec0\\u4e48\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u662f\\u903b\\u8f91\\u7efc\\u5408\\u7684\\u5173\\u952e\\u6b65\\u9aa4\\uff0c\\u5b83\\u7684\\u4f5c\\u7528\\u662f\\u5c06\\u4e0e\\u5de5\\u827a\\u65e0\\u5173\\u7684\\u5e03\\u5c14\\u7f51\\u7edc\\u6620\\u5c04\\u5230\\u76ee\\u6807\\u5de5\\u827a\\u5e93\\u7684\\u6807\\u51c6\\u5355\\u5143\\u3002\\u7b80\\u5355\\u6765\\u8bf4\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u5c31\\u662f\\u628a\\u4f18\\u5316\\u540e\\u7684\\u903b\\u8f91\\u529f\\u80fd\\u7528\\u5b9e\\u9645\\u7684\\u786c\\u4ef6\\u5355\\u5143\\uff08\\u95e8\\u7535\\u8def\\uff09\\u6765\\u5b9e\\u73b0\\u3002", "elapsed_time": 1.367574, "cost": 0.001431, "tokens": {"input": 1333, "output": 49, "total": 1382}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 03:39:58.809533+00
20	1	user.login	user	1	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-14 04:48:18.80437+00
21	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c**\\u6ca1\\u6709\\u5173\\u4e8e\\u5982\\u4f55\\u7f16\\u5199SDC\\u7ea6\\u675f\\u7684\\u5177\\u4f53\\u8bed\\u6cd5\\u6216\\u547d\\u4ee4\\u4fe1\\u606f**\\u3002\\u4e0a\\u4e0b\\u6587\\u4ec5\\u4ecb\\u7ecd\\u4e86SDC\\u7684\\u6982\\u5ff5\\u3001\\u4f5c\\u7528\\u548c\\u91cd\\u8981\\u6027\\uff0c\\u4f46\\u672a\\u63d0\\u4f9b\\u4efb\\u4f55\\u7f16\\u5199SDC\\u7ea6\\u675f\\u7684\\u793a\\u4f8b\\u6216\\u6307\\u5bfc\\u3002\\n\\n\\u5982\\u679c\\u4f60\\u9700\\u8981\\u5b66\\u4e60\\u5982\\u4f55\\u7f16\\u5199SDC\\u7ea6\\u675f\\uff0c\\u901a\\u5e38\\u9700\\u8981\\u4e86\\u89e3\\u4ee5\\u4e0b\\u57fa\\u672c\\u547d\\u4ee4\\uff08\\u8fd9\\u4e9b\\u4fe1\\u606f\\u4e0d\\u5728\\u5f53\\u524d\\u4e0a\\u4e0b\\u6587\\u4e2d\\uff09\\uff1a\\n\\n1. **\\u65f6\\u949f\\u5b9a\\u4e49**\\uff1a\\u4f7f\\u7528`create_clock`\\u547d\\u4ee4\\u5b9a\\u4e49\\u65f6\\u949f\\u9891\\u7387\\u548c\\u6ce2\\u5f62\\n2. **\\u8f93\\u5165\\u5ef6\\u8fdf**\\uff1a\\u4f7f\\u7528`set_input_delay`\\u7ea6\\u675f\\u8f93", "elapsed_time": 2.662265, "cost": 0.0015599999999999998, "tokens": {"input": 1190, "output": 185, "total": 1375}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 04:48:24.798451+00
22	1	ai.qa	knowledge	\N	172.21.0.1	curl/7.81.0	{"question": "create_clock\\u547d\\u4ee4\\u600e\\u4e48\\u7528", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c`create_clock`\\u547d\\u4ee4\\u7684\\u57fa\\u672c\\u7528\\u6cd5\\u5982\\u4e0b\\uff1a\\n\\n## \\u57fa\\u672c\\u8bed\\u6cd5\\n```tcl\\ncreate_clock -period <\\u5468\\u671f> -name <\\u540d\\u79f0> [\\u65f6\\u949f\\u6e90]\\n```\\n\\n## \\u5173\\u952e\\u53c2\\u6570\\n- **`-period`**\\uff1a\\u65f6\\u949f\\u5468\\u671f\\uff08\\u5355\\u4f4d\\u4e3ans\\uff09\\n- **`-name`**\\uff1a\\u65f6\\u949f\\u540d\\u79f0\\uff08\\u53ef\\u9009\\u4f46\\u63a8\\u8350\\uff09\\n- **`-waveform {rising falling}`**\\uff1a\\u6ce2\\u5f62\\u5b9a\\u4e49\\uff08", "elapsed_time": 9.337828, "cost": 0.001791, "tokens": {"input": 935, "output": 428, "total": 1363}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 04:55:06.689092+00
23	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0cSDC\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\u6709\\u660e\\u786e\\u7684\\u793a\\u4f8b\\u548c\\u683c\\u5f0f\\u8981\\u6c42\\u3002\\u4ee5\\u4e0b\\u662f\\u57fa\\u4e8e\\u4e0a\\u4e0b\\u6587\\u7684\\u5b8c\\u6574\\u56de\\u7b54\\uff1a\\n\\n## SDC\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\n\\n### 1. \\u57fa\\u672c\\u7ed3\\u6784\\n\\nSDC\\u7ea6\\u675f\\u6587\\u4ef6\\u4f7f\\u7528Tcl\\u8bed\\u6cd5\\uff0c\\u901a\\u5e38\\u6309\\u4ee5\\u4e0b\\u987a\\u5e8f\\u7ec4\\u7ec7\\uff1a\\n\\n```tcl\\n# ===================================\\n# 1. \\u65f6\\u949f\\u5b9a\\u4e49\\n# ===================================\\ncreate_cl", "elapsed_time": 4.512427, "cost": 0.00192, "tokens": {"input": 920, "output": 500, "total": 1420}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 04:59:35.618756+00
24	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u57fa\\u4e8e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6211\\u53ef\\u4ee5\\u56de\\u7b54\\u5173\\u4e8eSDC\\u7ea6\\u675f\\u5199\\u6cd5\\u7684\\u95ee\\u9898\\u3002\\n\\n## SDC\\u7ea6\\u675f\\u7684\\u57fa\\u672c\\u5199\\u6cd5\\n\\n\\u6839\\u636e\\u4e0a\\u4e0b\\u6587\\uff0cSDC\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\u4e3b\\u8981\\u5305\\u62ec\\u4ee5\\u4e0b\\u51e0\\u4e2a\\u6838\\u5fc3\\u90e8\\u5206\\uff1a\\n\\n### 1. \\u65f6\\u949f\\u5b9a\\u4e49\\n```tcl\\n# \\u521b\\u5efa\\u65f6\\u949f\\uff0c\\u5468\\u671f\\u4e3a10ns\\uff0c\\u65f6\\u949f\\u540d\\u4e3aclk\\uff0c\\u6307\\u5b9a\\u65f6\\u949f\\u7aef\\u53e3\\ncreate_clock -period 10 -name clk [get_ports clk]\\n```\\n\\n### 2. \\u8f93\\u5165\\u5ef6\\u8fdf\\u7ea6\\u675f\\n```tcl\\n# ", "elapsed_time": 4.474851, "cost": 0.0018, "tokens": {"input": 1008, "output": 396, "total": 1404}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 05:01:17.24346+00
25	1	user.login	user	1	192.168.2.170	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0	null	2026-07-14 05:43:54.945452+00
26	1	user.login	user	1	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-14 05:44:27.313468+00
27	108	user.login	user	108	192.168.2.170	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0	null	2026-07-14 05:46:27.900386+00
28	108	ai.qa	knowledge	\N	192.168.2.170	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0	{"question": "PPA\\u4f18\\u5316\\u601d\\u8def\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u5173\\u4e8ePPA\\uff08Performance, Power, Area\\uff09\\u4f18\\u5316\\u601d\\u8def\\uff0c\\u53ef\\u4ee5\\u603b\\u7ed3\\u5982\\u4e0b\\uff1a\\n\\nPPA\\u4f18\\u5316\\u4e3b\\u8981\\u4ece\\u591a\\u76ee\\u6807\\u4f18\\u5316\\u7684\\u89d2\\u5ea6\\u51fa\\u53d1\\uff0c\\u5177\\u4f53\\u601d\\u8def\\u5305\\u62ec\\uff1a\\n\\n1. **\\u540c\\u65f6\\u8003\\u8651\\u4e09\\u4e2a\\u76ee\\u6807**\\uff1a\\u9762\\u79ef\\uff08Area\\uff09\\u3001\\u5ef6\\u8fdf\\uff08Delay/Performance\\uff09\\u548c\\u529f\\u8017\\uff08Power\\uff09\\u3002\\n\\n2. **\\u4f7f\\u7528\\u6743\\u91cd\\u7cfb\\u6570\\u5e73\\u8861**\\uff1a\\u6839\\u636e\\u4e0d\\u540c\\u8bbe\\u8ba1\\u9700\\u6c42\\uff0c\\u901a\\u8fc7\\u8c03\\u6574\\u6743\\u91cd\\u7cfb\\u6570\\u6765\\u5e73\\u8861\\u9762\\u79ef\\u3001\\u5ef6\\u8fdf\\u548c\\u529f\\u8017\\u4e4b\\u95f4\\u7684trade-off\\u3002\\n\\n", "elapsed_time": 4.448591, "cost": 0.0018339999999999997, "tokens": {"input": 1136, "output": 349, "total": 1485}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 05:52:30.485685+00
29	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u60a8\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u5173\\u4e8e\\u201cSDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\u201d\\u7684\\u95ee\\u9898\\uff0c\\u6211\\u53ef\\u4ee5\\u7ed9\\u51fa\\u4ee5\\u4e0b\\u8be6\\u7ec6\\u89e3\\u7b54\\uff1a\\n\\n## SDC\\u7ea6\\u675f\\u7684\\u7f16\\u5199\\u65b9\\u6cd5\\n\\n### \\u57fa\\u672c\\u7ed3\\u6784\\n\\nSDC\\u7ea6\\u675f\\u6587\\u4ef6\\u901a\\u5e38\\u6309\\u4ee5\\u4e0b\\u987a\\u5e8f\\u7ec4\\u7ec7\\uff1a\\n\\n```tcl\\n# ===================================\\n# 1. \\u65f6\\u949f\\u5b9a\\u4e49\\uff08\\u6838\\u5fc3\\uff09\\n# ===================================\\ncreate_clock -perio", "elapsed_time": 4.647287, "cost": 0.00192, "tokens": {"input": 920, "output": 500, "total": 1420}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 05:57:45.756493+00
30	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "\\u6280\\u672f\\u6620\\u5c04\\u662f\\u4ec0\\u4e48\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u662f\\u903b\\u8f91\\u7efc\\u5408\\u7684\\u5173\\u952e\\u6b65\\u9aa4\\uff0c\\u5b83\\u7684\\u4f5c\\u7528\\u662f\\u5c06\\u4e0e\\u5de5\\u827a\\u65e0\\u5173\\u7684\\u5e03\\u5c14\\u7f51\\u7edc\\u6620\\u5c04\\u5230\\u76ee\\u6807\\u5de5\\u827a\\u5e93\\u7684\\u6807\\u51c6\\u5355\\u5143\\u3002\\u7b80\\u5355\\u6765\\u8bf4\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u5c31\\u662f\\u628a\\u4f18\\u5316\\u540e\\u7684\\u903b\\u8f91\\u529f\\u80fd\\u7528\\u5b9e\\u9645\\u7684\\u786c\\u4ef6\\u5355\\u5143\\uff08\\u95e8\\u7535\\u8def\\uff09\\u6765\\u5b9e\\u73b0\\u3002", "elapsed_time": 1.887877, "cost": 0.001521, "tokens": {"input": 1423, "output": 49, "total": 1472}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 06:01:34.636783+00
31	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "\\u6280\\u672f\\u6620\\u5c04\\u662f\\u4ec0\\u4e48\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u662f\\u903b\\u8f91\\u7efc\\u5408\\u7684\\u5173\\u952e\\u6b65\\u9aa4\\uff0c\\u5b83\\u7684\\u4f5c\\u7528\\u662f\\u5c06\\u4e0e\\u5de5\\u827a\\u65e0\\u5173\\u7684\\u5e03\\u5c14\\u7f51\\u7edc\\u6620\\u5c04\\u5230\\u76ee\\u6807\\u5de5\\u827a\\u5e93\\u7684\\u6807\\u51c6\\u5355\\u5143\\u3002\\u7b80\\u5355\\u6765\\u8bf4\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u5c31\\u662f\\u628a\\u4f18\\u5316\\u540e\\u7684\\u903b\\u8f91\\u529f\\u80fd\\u7528\\u5b9e\\u9645\\u7684\\u786c\\u4ef6\\u5355\\u5143\\uff08\\u95e8\\u7535\\u8def\\uff09\\u6765\\u5b9e\\u73b0\\u3002\\u5176\\u6838\\u5fc3\\u5de5\\u4f5c\\u5305\\u62ec\\uff1a\\u8003\\u8651\\u6807\\u51c6\\u5355\\u5143\\u5e93\\u4e2d\\u7684\\u53ef\\u7528\\u95e8\\u7c7b\\u578b\\uff08\\u5982AND, OR, NAND, NOR, XOR\\u7b49\\uff09\\uff0c\\u4ee5\\u6700\\u5c0f\\u9762\\u79ef\\u3001\\u6700\\u5c0f\\u5ef6\\u8fdf\\u6216\\u6700\\u5c0f\\u529f\\u8017\\u4e3a\\u4f18\\u5316\\u76ee\\u6807\\uff0c\\u4f7f\\u7528\\u56fe\\u5339\\u914d\\u7b97\\u6cd5\\u627e\\u5230\\u6700\\u4f18\\u7684\\u5355\\u5143\\u7ec4\\u5408\\uff0c\\u6700\\u7ec8\\u751f\\u6210\\u5305\\u542b\\u5177\\u4f53\\u6807\\u51c6\\u5355\\u5143\\u5b9e\\u4f8b\\u7684\\u95e8\\u7ea7\\u7f51\\u8868\\u3002", "elapsed_time": 1.969569, "cost": 0.001645, "tokens": {"input": 1423, "output": 111, "total": 1534}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 06:01:44.257604+00
33	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "Espresso\\u7b97\\u6cd5\\u539f\\u7406\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0cEspresso\\u7b97\\u6cd5\\u7684\\u6838\\u5fc3\\u601d\\u60f3\\u662f\\u901a\\u8fc7**\\u8fed\\u4ee3\\u4f18\\u5316**\\uff0c\\u627e\\u5230\\u8986\\u76d6\\u6240\\u67091\\u9879\\uff08minterm\\uff09\\u4e14\\u4e0d\\u8986\\u76d60\\u9879\\uff08maxterm\\uff09\\u7684\\u6700\\u5c0f\\u79ef\\u9879\\u96c6\\u5408\\u3002\\u5177\\u4f53\\u7b97\\u6cd5\\u6b65\\u9aa4\\u5305\\u62ec\\uff1a\\n\\n1. **\\u5c55\\u5f00**\\uff1a\\u5c06\\u8f93\\u5165\\u5e03\\u5c14\\u51fd\\u6570\\u8868\\u793a\\u4e3a\\u79ef\\u9879\\u5217\\u8868\\uff08SOP\\u5f62\\u5f0f\\uff09\\u3002\\n2. **\\u91cd\\u590d\\u6269\\u5c55**\\uff1a\\u5c1d\\u8bd5\\u6269\\u5c55\\u79ef\\u9879\\uff08\\u5982\\u901a\\u8fc7\\u5438\\u6536\\u3001\\u5408\\u5e76\\u76f8\\u90bb\\u9879\\uff09\\u4ee5\\u51cf\\u5c11\\u79ef\\u9879\\u6570\\u91cf\\u3002\\n3. **\\u5197\\u4f59\\u6d88\\u9664**\\uff1a\\u68c0\\u67e5\\u5e76\\u79fb\\u9664\\u88ab\\u5176\\u4ed6\\u79ef\\u9879\\u8986\\u76d6\\u7684\\u5197\\u4f59\\u9879\\uff08\\u5728\\u79fb\\u9664\\u524d\\u9700\\u8fdb\\u884c\\u76f8\\u5bb9\\u6027\\u68c0", "elapsed_time": 3.156646, "cost": 0.0015650000000000002, "tokens": {"input": 1217, "output": 174, "total": 1391}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 06:02:07.445256+00
32	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0cSDC\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\u6709\\u57fa\\u672c\\u7684\\u7ed3\\u6784\\u548c\\u8bed\\u6cd5\\u3002\\u4ee5\\u4e0b\\u662f\\u57fa\\u4e8e\\u4e0a\\u4e0b\\u6587\\u7684\\u56de\\u7b54\\uff1a\\n\\n## SDC\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\n\\n### \\u57fa\\u672c\\u7ed3\\u6784\\n\\nSDC\\u6587\\u4ef6\\u4f7f\\u7528Tcl\\u811a\\u672c\\u8bed\\u6cd5\\uff0c\\u5305\\u542b\\u51e0\\u4e2a\\u5173\\u952e\\u90e8\\u5206\\uff1a\\n\\n### 1. \\u65f6\\u949f\\u5b9a\\u4e49\\n```tcl\\n# \\u521b\\u5efa\\u65f6\\u949f\\uff1a-period \\u6307\\u5b9a\\u5468\\u671f\\uff08ns\\uff09\\uff0c-name \\u6307\\u5b9a\\u65f6\\u949f\\u540d\\ncreate_clock -period 10 -name clk [get_ports clk]\\n```\\n-", "elapsed_time": 4.316251, "cost": 0.0019260000000000002, "tokens": {"input": 1008, "output": 459, "total": 1467}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 06:01:51.070671+00
34	1	ai.qa	knowledge	\N	172.21.0.1	curl/7.81.0	{"question": "\\u6d4b\\u8bd5\\u5411\\u91cf\\u5e93\\u91cd\\u5efa", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c**\\u6ca1\\u6709\\u627e\\u5230\\u5173\\u4e8e\\u201c\\u6d4b\\u8bd5\\u5411\\u91cf\\u5e93\\u91cd\\u5efa\\u201d\\u7684\\u76f8\\u5173\\u4fe1\\u606f**\\u3002\\n\\n\\u4e0a\\u4e0b\\u6587\\u4e3b\\u8981\\u6db5\\u76d6\\u4e86\\u4ee5\\u4e0b\\u5185\\u5bb9\\uff1a\\n- \\u4eff\\u771f\\u7c7b\\u578b\\uff08\\u884c\\u4e3a\\u4eff\\u771f\\u3001RTL\\u4eff\\u771f\\u3001\\u95e8\\u7ea7\\u4eff\\u771f\\u3001\\u540e\\u4eff\\u771f\\uff09\\n- \\u5f62\\u5f0f\\u5316\\u9a8c\\u8bc1\\uff08\\u7b49\\u4ef7", "elapsed_time": 6.826446, "cost": 0.0012610000000000002, "tokens": {"input": 1161, "output": 50, "total": 1211}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:25:44.491487+00
35	1	user.login	user	1	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-14 07:27:31.265805+00
36	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0cSDC\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\u4e3b\\u8981\\u5305\\u542b\\u4ee5\\u4e0b\\u51e0\\u4e2a\\u57fa\\u672c\\u90e8\\u5206\\uff1a\\n\\n## 1. \\u65f6\\u949f\\u5b9a\\u4e49\\n\\n```tcl\\n# \\u521b\\u5efa\\u65f6\\u949f\\ncreate_clock -period 10 -name clk [get_ports clk]\\n```\\n- `-period 10`\\uff1a\\u65f6\\u949f\\u5468\\u671f\\u4e3a10ns\\uff08\\u5bf9\\u5e94100MHz\\uff09\\n- `-name clk`\\uff1a\\u65f6\\u949f\\u540d\\u79f0\\u4e3aclk\\n- `[get_ports clk]`\\uff1a\\u65f6\\u949f\\u6e90\\u7aef\\u53e3\\n\\n## ", "elapsed_time": 9.191321, "cost": 0.001758, "tokens": {"input": 1008, "output": 375, "total": 1383}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:27:46.038022+00
37	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "\\u4ec0\\u4e48\\u662fsetup time\\u548chold time\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u53ef\\u4ee5\\u51c6\\u786e\\u56de\\u7b54\\u8fd9\\u4e2a\\u95ee\\u9898\\uff1a\\n\\n**Setup Time\\uff08\\u5efa\\u7acb\\u65f6\\u95f4\\uff09**\\uff1a\\u5efa\\u7acb\\u65f6\\u95f4\\u662f\\u6570\\u636e\\u4fe1\\u53f7\\u5fc5\\u987b\\u5728\\u65f6\\u949f\\u6709\\u6548\\u6cbf**\\u4e4b\\u524d**\\u4fdd\\u6301\\u7a33\\u5b9a\\u7684\\u6700\\u77ed\\u65f6\\u95f4\\u3002\\u5982\\u679c\\u6570\\u636e\\u5728\\u65f6\\u949f\\u6cbf\\u524d\\u53d8\\u5316\\u592a\\u665a\\uff0c\\u53ef\\u80fd\\u91c7\\u6837\\u9519\\u8bef\\u6570\\u636e\\u3002\\u5176\\u68c0\\u67e5\\u516c\\u5f0f\\u4e3a\\uff1a\\n```\\nTdata_arrival + Tsu \\u2264 Tclk_arrival\\n```\\n\\u8fdd\\u4f8b\\u610f\\u5473\\u7740\\u6570\\u636e\\u592a\\u665a\\u5230\\u8fbe\\u3002\\n\\n**Hold Time\\uff08\\u4fdd\\u6301\\u65f6\\u95f4\\uff09**\\uff1a\\u4fdd\\u6301\\u65f6\\u95f4\\u662f\\u6570\\u636e\\u4fe1\\u53f7\\u5fc5\\u987b\\u5728\\u65f6\\u949f\\u6709\\u6548", "elapsed_time": 2.233422, "cost": 0.001192, "tokens": {"input": 876, "output": 158, "total": 1034}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:28:13.162092+00
38	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "\\u6280\\u672f\\u6620\\u5c04\\u662f\\u4ec0\\u4e48\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u662f\\u903b\\u8f91\\u7efc\\u5408\\u7684\\u5173\\u952e\\u6b65\\u9aa4\\uff0c\\u5b83\\u7684\\u4f5c\\u7528\\u662f\\u5c06\\u4e0e\\u5de5\\u827a\\u65e0\\u5173\\u7684\\u5e03\\u5c14\\u7f51\\u7edc\\u6620\\u5c04\\u5230\\u76ee\\u6807\\u5de5\\u827a\\u5e93\\u7684\\u6807\\u51c6\\u5355\\u5143\\u3002\\u7b80\\u5355\\u6765\\u8bf4\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u5c31\\u662f\\u628a\\u4f18\\u5316\\u540e\\u7684\\u903b\\u8f91\\u529f\\u80fd\\u7528\\u5b9e\\u9645\\u7684\\u786c\\u4ef6\\u5355\\u5143\\uff08\\u95e8\\u7535\\u8def\\uff09\\u6765\\u5b9e\\u73b0\\u3002\\n\\n\\u6280\\u672f\\u6620\\u5c04\\u7684\\u4e3b\\u8981\\u5de5\\u4f5c\\u5305\\u62ec\\uff1a\\u5c06\\u4e0e\\u5de5\\u827a\\u65e0\\u5173\\u7684\\u5e03\\u5c14\\u7f51\\u7edc\\u6620\\u5c04\\u5230\\u76ee\\u6807\\u5de5\\u827a\\u5e93\\u7684\\u6807\\u51c6\\u5355\\u5143\\uff0c\\u8003\\u8651\\u6807\\u51c6\\u5355\\u5143\\u5e93\\u4e2d\\u7684\\u53ef\\u7528\\u95e8\\u7c7b\\u578b\\uff08AND, OR, NAND, NOR, XOR\\u7b49\\uff09\\uff0c\\u4f18\\u5316\\u76ee\\u6807\\u4e3a\\u6700\\u5c0f\\u9762\\u79ef\\u3001\\u6700\\u5c0f\\u5ef6\\u8fdf\\u6216\\u6700\\u5c0f\\u529f\\u8017\\uff0c\\u4f7f\\u7528\\u56fe\\u5339\\u914d\\u7b97\\u6cd5\\u627e\\u5230", "elapsed_time": 1.748773, "cost": 0.001753, "tokens": {"input": 1423, "output": 165, "total": 1588}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:38:20.64837+00
39	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0cSDC\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\u5982\\u4e0b\\uff1a\\n\\n## SDC\\u6587\\u4ef6\\u57fa\\u672c\\u7ed3\\u6784\\u793a\\u4f8b\\n\\n```tcl\\n# ===================================\\n# 1. \\u65f6\\u949f\\u5b9a\\u4e49\\n# ===================================\\ncreate_clock -period 10 -name clk [get_ports clk]\\n\\n# ================", "elapsed_time": 2.817767, "cost": 0.001518, "tokens": {"input": 1008, "output": 255, "total": 1263}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:38:25.84564+00
40	1	user.update_profile	user	1	\N	\N	{"fields": ["real_name", "role", "student_id", "school", "major"]}	2026-07-14 07:41:34.326738+00
41	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6211\\u5c06\\u56de\\u7b54\\u5173\\u4e8eSDC\\u7ea6\\u675f\\u5199\\u6cd5\\u7684\\u95ee\\u9898\\u3002\\n\\n## SDC\\u7ea6\\u675f\\u7684\\u57fa\\u672c\\u5199\\u6cd5\\n\\nSDC\\uff08Synopsys Design Constraints\\uff09\\u7ea6\\u675f\\u6587\\u4ef6\\u4f7f\\u7528Tcl\\u8bed\\u6cd5\\u683c\\u5f0f\\u3002\\u57fa\\u4e8e\\u4e0a\\u4e0b\\u6587\\uff0c\\u4ee5\\u4e0b\\u662f\\u6838\\u5fc3\\u5199\\u6cd5\\uff1a\\n\\n### 1. \\u65f6\\u949f\\u5b9a\\u4e49\\n\\n```tcl\\n# \\u521b\\u5efa\\u4e3b\\u65f6\\u949f\\ncreate_clock -period 10 -name clk [get_ports clk]\\n\\n# \\u53c2\\u6570\\u8bf4\\u660e\\uff1a\\n# -perio", "elapsed_time": 4.416787, "cost": 0.00192, "tokens": {"input": 920, "output": 500, "total": 1420}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:42:13.980453+00
42	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u60a8\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0cSDC\\u7ea6\\u675f\\u7684\\u7f16\\u5199\\u4e3b\\u8981\\u5305\\u542b\\u4ee5\\u4e0b\\u5173\\u952e\\u90e8\\u5206\\u3002\\u4ee5\\u4e0b\\u662f\\u57fa\\u4e8e\\u4e0a\\u4e0b\\u6587\\u7684\\u8be6\\u7ec6\\u8bf4\\u660e\\uff1a\\n\\n## SDC\\u7ea6\\u675f\\u7f16\\u5199\\u57fa\\u672c\\u7ed3\\u6784\\n\\n### 1. \\u65f6\\u949f\\u5b9a\\u4e49\\n```tcl\\n# \\u521b\\u5efa\\u65f6\\u949f\\uff1a\\u5468\\u671f10ns\\uff0c\\u540d\\u79f0clk\\uff0c\\u7aef\\u53e3clk\\ncreate_clock -period 10 -name clk [get_ports clk]\\n```\\n\\n### 2. \\u8f93\\u5165\\u8f93\\u51fa\\u5ef6\\u8fdf\\n```tcl\\n# \\u8bbe\\u7f6e\\u8f93\\u5165\\u5ef6\\u8fdf\\uff1a\\u65f6\\u949fclk\\uff0c\\u6700\\u5927\\u5ef6", "elapsed_time": 4.332701, "cost": 0.0018700000000000001, "tokens": {"input": 1008, "output": 431, "total": 1439}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:42:38.347053+00
44	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0cSDC\\uff08Synopsys Design Constraints\\uff09\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\u9075\\u5faaTcl\\uff08Tool Command Language\\uff09\\u8bed\\u6cd5\\u683c\\u5f0f\\u3002\\u4ee5\\u4e0b\\u662f\\u57fa\\u4e8e\\u4e0a\\u4e0b\\u6587\\u5185\\u5bb9\\u6574\\u7406\\u7684SDC\\u7ea6\\u675f\\u5199\\u6cd5\\u8981\\u70b9\\uff1a\\n\\n## SDC\\u7ea6\\u675f\\u57fa\\u672c\\u8bed\\u6cd5\\u7ed3\\u6784\\n\\n### 1. \\u65f6\\u949f\\u5b9a\\u4e49\\n```tcl\\n# \\u521b\\u5efa\\u65f6\\u949f\\uff1a-period\\u6307\\u5b9a\\u5468\\u671f\\uff08ns\\uff09\\uff0c-name\\u6307\\u5b9a\\u65f6\\u949f\\u540d\\uff0c[get_ports]\\u6307\\u5b9a\\u65f6\\u949f\\u7aef\\u53e3\\ncreate_cl", "elapsed_time": 4.660099, "cost": 0.0020080000000000002, "tokens": {"input": 1008, "output": 500, "total": 1508}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:51:16.879278+00
43	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "\\u6280\\u672f\\u6620\\u5c04\\u662f\\u4ec0\\u4e48\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u662f\\u903b\\u8f91\\u7efc\\u5408\\u7684\\u5173\\u952e\\u6b65\\u9aa4\\uff0c\\u5b83\\u7684\\u4f5c\\u7528\\u662f\\u5c06\\u4e0e\\u5de5\\u827a\\u65e0\\u5173\\u7684\\u5e03\\u5c14\\u7f51\\u7edc\\u6620\\u5c04\\u5230\\u76ee\\u6807\\u5de5\\u827a\\u5e93\\u7684\\u6807\\u51c6\\u5355\\u5143\\u3002\\u7b80\\u5355\\u6765\\u8bf4\\uff0c\\u6280\\u672f\\u6620\\u5c04\\u5c31\\u662f\\u628a\\u4f18\\u5316\\u540e\\u7684\\u903b\\u8f91\\u529f\\u80fd\\u7528\\u5b9e\\u9645\\u7684\\u786c\\u4ef6\\u5355\\u5143\\uff08\\u95e8\\u7535\\u8def\\uff09\\u6765\\u5b9e\\u73b0\\u3002", "elapsed_time": 1.529652, "cost": 0.0014540000000000002, "tokens": {"input": 1356, "output": 49, "total": 1405}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 07:51:04.442857+00
45	1	user.login	user	1	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	null	2026-07-14 09:31:08.397269+00
46	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "SDC\\u7ea6\\u675f\\u5982\\u4f55\\u5199\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0cSDC\\u7ea6\\u675f\\u7684\\u5199\\u6cd5\\u53ef\\u4ee5\\u603b\\u7ed3\\u4e3a\\u4ee5\\u4e0b\\u51e0\\u4e2a\\u6838\\u5fc3\\u90e8\\u5206\\u3002\\u4e0a\\u4e0b\\u6587\\u8be6\\u7ec6\\u4ecb\\u7ecd\\u4e86SDC\\u7684\\u57fa\\u672c\\u7ed3\\u6784\\u3001\\u5e38\\u7528\\u547d\\u4ee4\\u548c\\u6700\\u4f73\\u5b9e\\u8df5\\uff0c\\u4ee5\\u4e0b\\u662f\\u5bf9\\u5982\\u4f55\\u7f16\\u5199SDC\\u7ea6\\u675f\\u7684\\u5b8c\\u6574\\u8bf4\\u660e\\uff1a\\n\\n## SDC\\u7ea6\\u675f\\u7684\\u57fa\\u672c\\u5199\\u6cd5\\n\\n### 1. **\\u65f6\\u949f\\u5b9a\\u4e49**\\n\\u65f6\\u949f\\u662fSDC\\u7ea6\\u675f\\u7684\\u6838\\u5fc3\\uff0c\\u5fc5\\u987b\\u9996\\u5148\\u5b9a\\u4e49\\u3002\\n\\n```tcl\\n# \\u521b\\u5efa\\u4e3b\\u65f6\\u949f\\n# -period: \\u65f6\\u949f\\u5468\\u671f\\uff08ns\\uff09\\n# -name: \\u65f6\\u949f\\u540d\\u79f0\\n# [get_ports]: \\u6307\\u5b9a\\u65f6\\u949f\\u7aef", "elapsed_time": 4.444856, "cost": 0.00192, "tokens": {"input": 920, "output": 500, "total": 1420}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 09:33:31.512376+00
47	1	ai.qa	knowledge	\N	192.168.2.116	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0	{"question": "PPA\\u4f18\\u5316\\u601d\\u8def\\uff1f", "answer": "\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u4e0a\\u4e0b\\u6587\\uff0c\\u5173\\u4e8ePPA\\uff08Performance/Power/Area\\uff0c\\u5373\\u6027\\u80fd/\\u529f\\u8017/\\u9762\\u79ef\\uff09\\u4f18\\u5316\\u601d\\u8def\\uff0c\\u53ef\\u4ee5\\u603b\\u7ed3\\u51fa\\u4ee5\\u4e0b\\u51e0\\u70b9\\uff1a\\n\\n1.  **\\u591a\\u76ee\\u6807\\u4f18\\u5316\\uff08Multi-objective Optimization\\uff09**\\uff1a\\n    *   \\u9700\\u8981**\\u540c\\u65f6\\u8003\\u8651\\u9762\\u79ef\\u3001\\u5ef6\\u8fdf\\u548c\\u529f\\u8017**\\u8fd9\\u4e09\\u4e2a\\u76ee\\u6807\\u3002\\n    *   \\u53ef\\u4ee5\\u4f7f\\u7528**\\u6743\\u91cd\\u7cfb\\u6570**\\u6765\\u5e73\\u8861\\u4e0d\\u540c\\u7684\\u76ee\\u6807\\u3002\\n    *   \\u5e94\\u6839\\u636e**\\u5e94\\u7528\\u573a\\u666f**\\u9009\\u62e9\\u5408\\u9002\\u7684\\u4f18\\u5316\\u7b56", "elapsed_time": 4.956615, "cost": 0.002136, "tokens": {"input": 1136, "output": 500, "total": 1636}, "retrieval_mode": "vector", "sources_count": 5}	2026-07-14 09:47:46.000027+00
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
f9c6d7e8a9b0
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
108	xuxiaofeng@nctieda.com	yiyiyiyi	$2b$12$yfMGekY5Gj6tKyLRKE8c3uCVkU6My7MjaRAzN/0AJaZG8yDgMJRxu	NORMAL	f	t	\N	2026-07-10 10:04:24.511682+00	2026-07-14 05:46:27.898696+00	2026-07-14 05:46:27.897792+00	2026-07-10 10:04:24.737424+00	f	徐晓凤	student	200000000	\N	\N	t	2026-07-10 10:05:46.59127+00	\N	\N	\N	t	t	t	t
7	test1782979330@guochuang.com	test1782979330	$pbkdf2-sha256$29000$OsdYS0mpldJ6r9Uao5Qypg$5V7KZdIPyX3ZoBRjei.pxOdNTGGHucnBCZEB07mrKdc	NORMAL	f	t	\N	2026-07-02 08:02:10.098578+00	2026-07-02 08:02:10.098578+00	\N	\N	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
1	admin@guochuang.com	admin	$pbkdf2-sha256$29000$vdeaM8a4tzaGcO59L0WodQ$3GBthjx1SRJbPVPrARmJG4UVLSlWkTXaN2UcW4tq6Rk	PREMIUM	t	t	\N	2026-06-22 09:31:06.959787+00	2026-07-14 09:31:08.393926+00	2026-07-14 09:31:08.366886+00	\N	t	陈曦	student	1023162811	南京邮电大学	\N	t	2026-07-13 02:13:59.392468+00	教育技术学	教科院	\N	t	t	t	t
117	18862013736@163.com	cxtest	$2b$12$EPGxHfzSKmKm4HlF5L2zteMXW9NxyxqKoGkBrYTevo8vROD1r9BNO	NORMAL	f	t	\N	2026-07-10 15:02:52.276754+00	2026-07-13 06:54:28.779992+00	2026-07-13 06:54:28.779311+00	2026-07-10 15:35:08.888468+00	f	陈曦	student	1023162811	南京邮电大学	18862013736	t	2026-07-10 15:03:14.315542+00	教育技术学	\N	/uploads/avatars/117.jpg	t	t	t	t
60	1494686959@qq.com	zinongsan	$2b$12$1NGnWTJRs5Afv/SgIPv0fuKfRcCO9er3MzYBEE.Qrkz1soPlfeI.W	PREMIUM	f	t	2	2026-07-10 05:56:17.161756+00	2026-07-10 07:12:40.765691+00	\N	2026-07-10 05:56:17.391233+00	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
8	tn1782981827@g.com	tn1782981827	$pbkdf2-sha256$29000$DIEwBuAcQ0iJ0RpDqNX6vw$xiy9TJlIoWLgIxq3fU9KgzIQhcVgwYu4YksIheyZ8W0	NORMAL	f	t	\N	2026-07-02 08:43:47.210475+00	2026-07-02 08:43:47.240185+00	2026-07-02 08:43:47.24578+00	\N	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
3	1479576468@qq.com	test	$pbkdf2-sha256$29000$jbFWSkmp1VoLoRTiXGttbQ$VTYH5XED4lk8nA.bZz9H2LAbreBjqrEjCOk/yzyPQa0	NORMAL	f	t	1	2026-06-23 01:39:09.444632+00	2026-07-10 02:14:03.708305+00	2026-07-10 02:14:03.718169+00	\N	t	\N	\N	\N	\N	\N	f	\N	\N	\N	\N	t	t	t	t
\.


--
-- Name: action_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.action_logs_id_seq', 47, true);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 37, true);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.groups_id_seq', 411, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 235, true);


--
-- Name: action_logs action_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.action_logs
    ADD CONSTRAINT action_logs_pkey PRIMARY KEY (id);


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
-- Name: ix_action_logs_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_action_logs_action ON public.action_logs USING btree (action);


--
-- Name: ix_action_logs_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_action_logs_created_at ON public.action_logs USING btree (created_at);


--
-- Name: ix_action_logs_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_action_logs_user_created ON public.action_logs USING btree (user_id, created_at);


--
-- Name: ix_action_logs_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_action_logs_user_id ON public.action_logs USING btree (user_id);


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
-- Name: action_logs action_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.action_logs
    ADD CONSTRAINT action_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


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

\unrestrict r5Si0TgYoKD0HyQzL6aUCEHjybAfW7sfIFOODzHWxkMo6NwbNXvr0V3r8ENS6DU

