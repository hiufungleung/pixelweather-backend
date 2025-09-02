--
-- PostgreSQL database dump
--

\restrict 6RId6eODx9oeXV7rSKHzwA16WJ0hm3NNzBkeyqhhYgiaCA2307CvdP3Ebc9jvIQ

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
-- Data for Name: weather_cats; Type: TABLE DATA; Schema: pixelweather; Owner: -
--

COPY pixelweather.weather_cats (id, category) FROM stdin;
1	thunderstorm
2	drizzle
3	rain
4	atmosphere
5	clear
6	clouds
7	windy
8	storm
9	hail
10	feels like
\.


--
-- Name: weather_cats_id_seq; Type: SEQUENCE SET; Schema: pixelweather; Owner: -
--

SELECT pg_catalog.setval('pixelweather.weather_cats_id_seq', 10, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 6RId6eODx9oeXV7rSKHzwA16WJ0hm3NNzBkeyqhhYgiaCA2307CvdP3Ebc9jvIQ

