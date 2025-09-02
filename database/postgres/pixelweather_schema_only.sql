--
-- PostgreSQL database dump
--

\restrict ExSekpTLdN5GEVkGJB7rzuMgEuCid0dcxZNAlONy09e6HsecXPlC0GHKA3Kvfjn

-- Dumped from database version 17.5 (Debian 17.5-1.pgdg120+1)
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pixelweather; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA pixelweather;


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: pixelweather; Owner: -
--

CREATE FUNCTION pixelweather.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: posts; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    latitude numeric(8,6) NOT NULL,
    longitude numeric(9,6) NOT NULL,
    suburb_id integer NOT NULL,
    weather_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    likes integer DEFAULT 0 NOT NULL,
    views integer DEFAULT 0 NOT NULL,
    reports integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    comment text
);


--
-- Name: posts_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: posts_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.posts_id_seq OWNED BY pixelweather.posts.id;


--
-- Name: suburbs; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.suburbs (
    id integer NOT NULL,
    suburb_name character varying(63) NOT NULL,
    postcode integer NOT NULL,
    latitude numeric(8,6) NOT NULL,
    longitude numeric(9,6) NOT NULL,
    state_code character varying(3) NOT NULL
);


--
-- Name: suburbs_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.suburbs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: suburbs_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.suburbs_id_seq OWNED BY pixelweather.suburbs.id;


--
-- Name: user_alert_suburb; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.user_alert_suburb (
    id integer NOT NULL,
    user_id integer NOT NULL,
    suburb_id integer NOT NULL
);


--
-- Name: user_alert_suburb_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.user_alert_suburb_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_alert_suburb_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.user_alert_suburb_id_seq OWNED BY pixelweather.user_alert_suburb.id;


--
-- Name: user_alert_time; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.user_alert_time (
    id integer NOT NULL,
    user_id integer NOT NULL,
    start_time time without time zone DEFAULT '00:00:00'::time without time zone NOT NULL,
    end_time time without time zone DEFAULT '23:59:59'::time without time zone NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


--
-- Name: user_alert_time_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.user_alert_time_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_alert_time_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.user_alert_time_id_seq OWNED BY pixelweather.user_alert_time.id;


--
-- Name: user_alert_weather; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.user_alert_weather (
    id integer NOT NULL,
    user_id integer NOT NULL,
    weather_id integer NOT NULL
);


--
-- Name: user_alert_weather_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.user_alert_weather_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_alert_weather_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.user_alert_weather_id_seq OWNED BY pixelweather.user_alert_weather.id;


--
-- Name: user_fcm_tokens; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.user_fcm_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    fcm_token character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: user_fcm_tokens_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.user_fcm_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_fcm_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.user_fcm_tokens_id_seq OWNED BY pixelweather.user_fcm_tokens.id;


--
-- Name: user_like_post; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.user_like_post (
    user_id integer NOT NULL,
    post_id integer NOT NULL
);


--
-- Name: user_report_post; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.user_report_post (
    user_id integer NOT NULL,
    post_id integer NOT NULL,
    report_comment text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: user_saved_suburb; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.user_saved_suburb (
    id integer NOT NULL,
    user_id integer NOT NULL,
    suburb_id integer NOT NULL,
    label character varying(15) NOT NULL
);


--
-- Name: user_saved_suburb_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.user_saved_suburb_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_saved_suburb_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.user_saved_suburb_id_seq OWNED BY pixelweather.user_saved_suburb.id;


--
-- Name: user_view_post; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.user_view_post (
    user_id integer NOT NULL,
    post_id integer NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.users (
    id integer NOT NULL,
    username character varying(31) NOT NULL,
    email character varying(255) NOT NULL,
    password character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.users_id_seq OWNED BY pixelweather.users.id;


--
-- Name: weather_cats; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.weather_cats (
    id integer NOT NULL,
    category character varying(31) NOT NULL
);


--
-- Name: weather_cats_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.weather_cats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weather_cats_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.weather_cats_id_seq OWNED BY pixelweather.weather_cats.id;


--
-- Name: weathers; Type: TABLE; Schema: pixelweather; Owner: -
--

CREATE TABLE pixelweather.weathers (
    id integer NOT NULL,
    category_id integer NOT NULL,
    weather character varying(31) NOT NULL,
    weather_code integer DEFAULT '-1'::integer NOT NULL
);


--
-- Name: weathers_id_seq; Type: SEQUENCE; Schema: pixelweather; Owner: -
--

CREATE SEQUENCE pixelweather.weathers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weathers_id_seq; Type: SEQUENCE OWNED BY; Schema: pixelweather; Owner: -
--

ALTER SEQUENCE pixelweather.weathers_id_seq OWNED BY pixelweather.weathers.id;


--
-- Name: posts id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.posts ALTER COLUMN id SET DEFAULT nextval('pixelweather.posts_id_seq'::regclass);


--
-- Name: suburbs id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.suburbs ALTER COLUMN id SET DEFAULT nextval('pixelweather.suburbs_id_seq'::regclass);


--
-- Name: user_alert_suburb id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_suburb ALTER COLUMN id SET DEFAULT nextval('pixelweather.user_alert_suburb_id_seq'::regclass);


--
-- Name: user_alert_time id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_time ALTER COLUMN id SET DEFAULT nextval('pixelweather.user_alert_time_id_seq'::regclass);


--
-- Name: user_alert_weather id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_weather ALTER COLUMN id SET DEFAULT nextval('pixelweather.user_alert_weather_id_seq'::regclass);


--
-- Name: user_fcm_tokens id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_fcm_tokens ALTER COLUMN id SET DEFAULT nextval('pixelweather.user_fcm_tokens_id_seq'::regclass);


--
-- Name: user_saved_suburb id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_saved_suburb ALTER COLUMN id SET DEFAULT nextval('pixelweather.user_saved_suburb_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.users ALTER COLUMN id SET DEFAULT nextval('pixelweather.users_id_seq'::regclass);


--
-- Name: weather_cats id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.weather_cats ALTER COLUMN id SET DEFAULT nextval('pixelweather.weather_cats_id_seq'::regclass);


--
-- Name: weathers id; Type: DEFAULT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.weathers ALTER COLUMN id SET DEFAULT nextval('pixelweather.weathers_id_seq'::regclass);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (id);


--
-- Name: suburbs suburbs_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.suburbs
    ADD CONSTRAINT suburbs_pkey PRIMARY KEY (id);


--
-- Name: user_alert_suburb user_alert_suburb_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_suburb
    ADD CONSTRAINT user_alert_suburb_pkey PRIMARY KEY (id);


--
-- Name: user_alert_time user_alert_time_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_time
    ADD CONSTRAINT user_alert_time_pkey PRIMARY KEY (id);


--
-- Name: user_alert_weather user_alert_weather_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_weather
    ADD CONSTRAINT user_alert_weather_pkey PRIMARY KEY (id);


--
-- Name: user_fcm_tokens user_fcm_tokens_fcm_token_key; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_fcm_tokens
    ADD CONSTRAINT user_fcm_tokens_fcm_token_key UNIQUE (fcm_token);


--
-- Name: user_fcm_tokens user_fcm_tokens_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_fcm_tokens
    ADD CONSTRAINT user_fcm_tokens_pkey PRIMARY KEY (id);


--
-- Name: user_like_post user_like_post_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_like_post
    ADD CONSTRAINT user_like_post_pkey PRIMARY KEY (user_id, post_id);


--
-- Name: user_report_post user_report_post_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_report_post
    ADD CONSTRAINT user_report_post_pkey PRIMARY KEY (user_id, post_id);


--
-- Name: user_saved_suburb user_saved_suburb_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_saved_suburb
    ADD CONSTRAINT user_saved_suburb_pkey PRIMARY KEY (id);


--
-- Name: user_view_post user_view_post_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_view_post
    ADD CONSTRAINT user_view_post_pkey PRIMARY KEY (user_id, post_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: weather_cats weather_cats_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.weather_cats
    ADD CONSTRAINT weather_cats_pkey PRIMARY KEY (id);


--
-- Name: weathers weathers_pkey; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.weathers
    ADD CONSTRAINT weathers_pkey PRIMARY KEY (id);


--
-- Name: weathers weathers_weather_code_key; Type: CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.weathers
    ADD CONSTRAINT weathers_weather_code_key UNIQUE (weather_code);


--
-- Name: suburbs_index_0; Type: INDEX; Schema: pixelweather; Owner: -
--

CREATE UNIQUE INDEX suburbs_index_0 ON pixelweather.suburbs USING btree (suburb_name, postcode);


--
-- Name: user_alert_suburb_index_4; Type: INDEX; Schema: pixelweather; Owner: -
--

CREATE UNIQUE INDEX user_alert_suburb_index_4 ON pixelweather.user_alert_suburb USING btree (user_id, suburb_id);


--
-- Name: user_alert_time_index_1; Type: INDEX; Schema: pixelweather; Owner: -
--

CREATE UNIQUE INDEX user_alert_time_index_1 ON pixelweather.user_alert_time USING btree (user_id, start_time, end_time);


--
-- Name: user_alert_weather_index_3; Type: INDEX; Schema: pixelweather; Owner: -
--

CREATE UNIQUE INDEX user_alert_weather_index_3 ON pixelweather.user_alert_weather USING btree (user_id, weather_id);


--
-- Name: user_saved_suburb_index_5; Type: INDEX; Schema: pixelweather; Owner: -
--

CREATE UNIQUE INDEX user_saved_suburb_index_5 ON pixelweather.user_saved_suburb USING btree (user_id, label);


--
-- Name: weathers_index_2; Type: INDEX; Schema: pixelweather; Owner: -
--

CREATE UNIQUE INDEX weathers_index_2 ON pixelweather.weathers USING btree (weather, weather_code);


--
-- Name: user_fcm_tokens update_user_fcm_tokens_updated_at; Type: TRIGGER; Schema: pixelweather; Owner: -
--

CREATE TRIGGER update_user_fcm_tokens_updated_at BEFORE UPDATE ON pixelweather.user_fcm_tokens FOR EACH ROW EXECUTE FUNCTION pixelweather.update_updated_at_column();


--
-- Name: posts fk_posts_suburb_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.posts
    ADD CONSTRAINT fk_posts_suburb_id FOREIGN KEY (suburb_id) REFERENCES pixelweather.suburbs(id) ON DELETE CASCADE;


--
-- Name: posts fk_posts_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.posts
    ADD CONSTRAINT fk_posts_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON DELETE CASCADE;


--
-- Name: posts fk_posts_weather_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.posts
    ADD CONSTRAINT fk_posts_weather_id FOREIGN KEY (weather_id) REFERENCES pixelweather.weathers(id) ON DELETE CASCADE;


--
-- Name: user_alert_suburb fk_user_alert_suburb_suburb_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_suburb
    ADD CONSTRAINT fk_user_alert_suburb_suburb_id FOREIGN KEY (suburb_id) REFERENCES pixelweather.suburbs(id) ON DELETE CASCADE;


--
-- Name: user_alert_suburb fk_user_alert_suburb_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_suburb
    ADD CONSTRAINT fk_user_alert_suburb_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON DELETE CASCADE;


--
-- Name: user_alert_time fk_user_alert_time_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_time
    ADD CONSTRAINT fk_user_alert_time_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_alert_weather fk_user_alert_weather_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_weather
    ADD CONSTRAINT fk_user_alert_weather_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON DELETE CASCADE;


--
-- Name: user_alert_weather fk_user_alert_weather_weather_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_alert_weather
    ADD CONSTRAINT fk_user_alert_weather_weather_id FOREIGN KEY (weather_id) REFERENCES pixelweather.weathers(id) ON DELETE CASCADE;


--
-- Name: user_fcm_tokens fk_user_fcm_tokens_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_fcm_tokens
    ADD CONSTRAINT fk_user_fcm_tokens_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON DELETE CASCADE;


--
-- Name: user_like_post fk_user_like_post_post_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_like_post
    ADD CONSTRAINT fk_user_like_post_post_id FOREIGN KEY (post_id) REFERENCES pixelweather.posts(id) ON DELETE CASCADE;


--
-- Name: user_like_post fk_user_like_post_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_like_post
    ADD CONSTRAINT fk_user_like_post_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON DELETE CASCADE;


--
-- Name: user_report_post fk_user_report_post_post_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_report_post
    ADD CONSTRAINT fk_user_report_post_post_id FOREIGN KEY (post_id) REFERENCES pixelweather.posts(id) ON DELETE CASCADE;


--
-- Name: user_report_post fk_user_report_post_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_report_post
    ADD CONSTRAINT fk_user_report_post_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON DELETE CASCADE;


--
-- Name: user_saved_suburb fk_user_saved_suburb_suburb_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_saved_suburb
    ADD CONSTRAINT fk_user_saved_suburb_suburb_id FOREIGN KEY (suburb_id) REFERENCES pixelweather.suburbs(id) ON DELETE CASCADE;


--
-- Name: user_saved_suburb fk_user_saved_suburb_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_saved_suburb
    ADD CONSTRAINT fk_user_saved_suburb_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON DELETE CASCADE;


--
-- Name: user_view_post fk_user_view_post_post_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_view_post
    ADD CONSTRAINT fk_user_view_post_post_id FOREIGN KEY (post_id) REFERENCES pixelweather.posts(id) ON DELETE CASCADE;


--
-- Name: user_view_post fk_user_view_post_user_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.user_view_post
    ADD CONSTRAINT fk_user_view_post_user_id FOREIGN KEY (user_id) REFERENCES pixelweather.users(id) ON DELETE CASCADE;


--
-- Name: weathers fk_weathers_category_id; Type: FK CONSTRAINT; Schema: pixelweather; Owner: -
--

ALTER TABLE ONLY pixelweather.weathers
    ADD CONSTRAINT fk_weathers_category_id FOREIGN KEY (category_id) REFERENCES pixelweather.weather_cats(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict ExSekpTLdN5GEVkGJB7rzuMgEuCid0dcxZNAlONy09e6HsecXPlC0GHKA3Kvfjn

